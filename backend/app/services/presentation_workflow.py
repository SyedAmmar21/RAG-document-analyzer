"""Presentation-specific control plane for the DeepAgent OfficeCLI workflow.

This module deliberately contains no OfficeCLI command or recipe documentation.
OfficeCLI remains the source of truth for syntax and recipe content; this module
only enforces the order in which the model is allowed to make decisions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath

from pydantic import BaseModel, Field, field_validator, model_validator


class PresentationPhase(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    PLAN_REQUIRED = "plan_required"
    RECIPE_RETRIEVAL_REQUIRED = "recipe_retrieval_required"
    RECIPE_SELECTION_REQUIRED = "recipe_selection_required"
    GENERATION_READY = "generation_ready"
    QA_COMPLETE = "qa_complete"


ARCHETYPES = {
    "hero",
    "executive_summary",
    "feature_cards",
    "comparison",
    "timeline",
    "process",
    "architecture",
    "dashboard",
    "data_insight",
    "recommendation",
    "closing",
    "section_divider",
    "market_landscape",
    "traction",
}


class SlidePlan(BaseModel):
    slide_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1)
    archetype: str
    primary_visual: str = Field(min_length=1)
    supporting_elements: list[str] = Field(min_length=1, max_length=6)
    information_density: str = Field(pattern=r"^(minimal|balanced|information_rich|executive)$")
    recipe_goal: str = Field(min_length=1)

    @field_validator("archetype")
    @classmethod
    def validate_archetype(cls, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ARCHETYPES:
            raise ValueError(
                "archetype must be one of: " + ", ".join(sorted(ARCHETYPES))
            )
        return normalized

    @field_validator("supporting_elements")
    @classmethod
    def forbid_empty_supporting_elements(cls, value: list[str]) -> list[str]:
        cleaned = [element.strip() for element in value if element and element.strip()]
        if not cleaned:
            raise ValueError("supporting_elements must contain at least one concrete element")
        return cleaned


class DeckPlan(BaseModel):
    deck_type: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    visual_identity: str = Field(min_length=1)
    motif: str = Field(min_length=1)
    officecli_skill: str = Field(pattern=r"^(pptx|pitch-deck)$")


class PresentationPlan(BaseModel):
    deck: DeckPlan
    slides: list[SlidePlan] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def validate_slide_sequence(self) -> "PresentationPlan":
        expected = list(range(1, len(self.slides) + 1))
        actual = [slide.slide_number for slide in self.slides]
        if actual != expected:
            raise ValueError("slide_number values must be sequential starting at 1")

        archetypes = [slide.archetype for slide in self.slides]
        if len(archetypes) > 2 and all(
            archetypes[index] == archetypes[index - 1]
            for index in range(1, len(archetypes))
        ):
            raise ValueError("the deck cannot use one repeated archetype for every slide")
        return self


class RecipeSelection(BaseModel):
    slide_number: int = Field(ge=1)
    officecli_recipe: str = Field(min_length=1, max_length=240)
    rationale: str = Field(min_length=1, max_length=500)


class RecipeSelectionSet(BaseModel):
    selections: list[RecipeSelection] = Field(min_length=1)


@dataclass
class PresentationWorkflow:
    """Per-agent state that makes planning a precondition for PPTX generation."""

    presentation_requested: bool = False
    phase: PresentationPhase = field(init=False)
    plan: PresentationPlan | None = None
    recipe_selections: dict[int, RecipeSelection] = field(default_factory=dict)
    qa_path: str | None = None

    def __post_init__(self) -> None:
        self.phase = (
            PresentationPhase.PLAN_REQUIRED
            if self.presentation_requested
            else PresentationPhase.NOT_APPLICABLE
        )

    @staticmethod
    def _parse_json(raw_json: str) -> object:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc.msg}") from exc

    def register_plan(self, plan_json: str) -> PresentationPlan:
        if not self.presentation_requested:
            self.presentation_requested = True

        plan = PresentationPlan.model_validate(self._parse_json(plan_json))
        self.plan = plan
        self.recipe_selections.clear()
        self.qa_path = None
        self.phase = PresentationPhase.RECIPE_RETRIEVAL_REQUIRED
        return plan

    def recipe_skill_to_load(self) -> str:
        if self.phase != PresentationPhase.RECIPE_RETRIEVAL_REQUIRED or self.plan is None:
            raise ValueError("create and validate the presentation plan before loading recipe guidance")
        return self.plan.deck.officecli_skill

    def mark_recipe_guidance_loaded(self) -> None:
        if self.phase != PresentationPhase.RECIPE_RETRIEVAL_REQUIRED:
            raise ValueError("recipe guidance can only be loaded immediately after planning")
        self.phase = PresentationPhase.RECIPE_SELECTION_REQUIRED

    def register_recipe_selections(self, selections_json: str) -> dict[int, RecipeSelection]:
        if self.phase != PresentationPhase.RECIPE_SELECTION_REQUIRED or self.plan is None:
            raise ValueError("load the official PPTX skill before selecting recipes")

        selection_set = RecipeSelectionSet.model_validate(self._parse_json(selections_json))
        expected_slide_numbers = {slide.slide_number for slide in self.plan.slides}
        selected_slide_numbers = {item.slide_number for item in selection_set.selections}

        if selected_slide_numbers != expected_slide_numbers:
            raise ValueError(
                "recipe selections must cover every planned slide exactly once; "
                f"expected {sorted(expected_slide_numbers)}, got {sorted(selected_slide_numbers)}"
            )
        if len(selection_set.selections) != len(selected_slide_numbers):
            raise ValueError("recipe selections contain duplicate slide_number values")

        self.recipe_selections = {
            item.slide_number: item for item in selection_set.selections
        }
        self.phase = PresentationPhase.GENERATION_READY
        return self.recipe_selections

    def assert_officecli_generation_allowed(self, command: str) -> None:
        """Reject PPTX OfficeCLI work that tries to skip the control plane."""
        if not self.presentation_requested or "officecli" not in command.lower():
            return

        # A presentation request must establish its plan before *any* OfficeCLI
        # command. This keeps retrieval, recipe choice, and implementation in a
        # deterministic order instead of allowing the model to start drawing.
        if self.phase != PresentationPhase.GENERATION_READY:
            raise ValueError(
                "PPTX generation is locked. First call create_presentation_plan, "
                "load_presentation_recipe_guidance, and select_presentation_recipes."
            )

    def prepare_qa(self, presentation_path: str) -> str:
        if self.phase != PresentationPhase.GENERATION_READY:
            raise ValueError("presentation QA requires a recipe-approved generation plan")

        path = PurePosixPath(presentation_path)
        if path.suffix.lower() != ".pptx" or path.parent != PurePosixPath("/workspace/output"):
            raise ValueError("QA accepts only a .pptx file directly under /workspace/output")

        return str(path)

    def record_qa(self, presentation_path: str) -> str:
        checked_path = self.prepare_qa(presentation_path)
        self.qa_path = checked_path
        self.phase = PresentationPhase.QA_COMPLETE
        return checked_path

    def plan_summary(self) -> str:
        if self.plan is None:
            return "No presentation plan has been registered."
        rows = [
            f"{slide.slide_number}. {slide.archetype} | {slide.recipe_goal}"
            for slide in self.plan.slides
        ]
        return "\n".join(rows)


def is_presentation_request(user_query: str) -> bool:
    """Conservative routing used to enable the PPTX workflow gate."""
    return bool(
        re.search(
            r"\b(power\s*point|presentation|slide deck|slides|pptx?|pitch deck|deck)\b",
            user_query,
            flags=re.IGNORECASE,
        )
    )
