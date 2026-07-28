# Problem Summary

The original chat path used one `create_deep_agent` instance with a general
research prompt, a large OfficeCLI wrapper skill, and an optional presentation
design skill. Planning was an instruction rather than a state transition. The
model could load OfficeCLI context and immediately call `sandbox_execute`, so
the same model step was deciding both *what a slide should communicate* and
*how to express it with OfficeCLI*.

There was also a separate `POST /generate-presentation` path. It accepted only
a title and a list of strings, created one textbox per slide through OfficeCLI,
and fell back to `python-pptx` title/bullet layouts. This bypassed the DeepAgent,
the design skill, recipes, and QA entirely.

# Root Cause

Ranked by confidence:

1. **Very high — the legacy endpoint encoded the failure mode.** Its data model
   could not express a primary visual, layout, or recipe, and its implementation
   explicitly generated title/text slides (with a title/bullet fallback).
2. **Very high — planning was advisory, not a workflow precondition.** Nothing
   prevented `sandbox_execute` from being the first OfficeCLI action for a deck.
3. **High — the OfficeCLI phase still owned layout decisions.** No persistent,
   slide-level contract linked a message to an archetype and then to a recipe.
4. **High — recipe retrieval occurred at the wrong time.** The broad OfficeCLI
   skill and its large reference material competed with the general research
   prompt. Recipe content was not retrieved immediately before recipe selection.
5. **High — quality behavior was conditional.** `presentation-design` was only
   requested for style-heavy briefs, while ordinary decks were allowed to use
   OfficeCLI defaults.
6. **Medium — there was no required delivery QA transition.** A successful file
   write ended the flow even when the deck had not been validated or inspected.

The evidence supports planning, ordering, and retrieval as the primary
bottlenecks—not OfficeCLI syntax correctness. Context length and model attention
are contributing risks, particularly because a large generic reference can make
the easiest valid primitive (a textbox) more salient than a recipe. The refactor
therefore changes control flow rather than adding design advice alone.

# Changes Made

| File | Change | Expected behavioral impact |
| --- | --- | --- |
| `backend/app/services/presentation_workflow.py` | Added validated deck/slide schemas, presentation phases, recipe coverage checks, PPTX execution gate, and QA state. | Turns planning and per-slide recipe selection into executable preconditions. |
| `backend/app/services/rag_agent_service.py` | Added planning, recipe-guidance, recipe-selection, and QA tools; gated `sandbox_execute`; elevated the presentation control plane in the agent prompt. | OfficeCLI cannot begin a detected PPTX workflow before the model has fixed all slide types and recipes. |
| `backend/app/routers/query.py` | Detects presentation requests and enables the per-agent workflow gate. | The DeepAgent/LangGraph invocation receives the correct presentation state from the first user message. |
| `backend/app/skills/presentation-design/SKILL.md` | Reframed design as planning for every deck and aligned it with the enforced tools. | Design affects the plan rather than being optional prose that can be ignored during generation. |
| `backend/app/skills/presentation-planning/SKILL.md` | Added a narrow planning skill with archetypes and the plan contract. | Separates narrative/layout choice from OfficeCLI implementation. |
| `backend/app/skills/presentation-recipe-selection/SKILL.md` | Added a narrow recipe-selection skill that retrieves the official OfficeCLI skill after planning. | Keeps recipe material adjacent to the decision and avoids duplicating OfficeCLI docs. |
| `backend/app/skills/officecli/SKILL.md` | Updated only the project-owned wrapper section above the official-documentation separator. | OfficeCLI is explicitly an implementation engine for the approved contract and must finish with QA. |
| `backend/app/services/office_document_service.py` | Removed PPTX support from the underspecified generic export path and deprecated its title/string adapter. | Prevents a parallel code path from silently recreating simplistic decks. |
| `backend/app/routers/documents.py` | Returns HTTP 409 for the deprecated legacy presentation endpoint. | Forces callers to migrate to the planned DeepAgent flow instead of bypassing it. |

No content below the OfficeCLI skill's official-documentation separator was
changed, and no OfficeCLI recipe documentation was copied into project skills.

# Architecture Before

```text
User
  |
  +--> POST /query --> DeepAgent / implicit LangGraph
  |                     |
  |                     +--> optional presentation-design advice
  |                     +--> broad OfficeCLI skill
  |                     +--> sandbox_execute --> OfficeCLI
  |                                              (model still chooses layout)
  |
  +--> POST /generate-presentation --> title + strings
                                      --> textbox-per-slide OfficeCLI
                                      --> python-pptx title/bullet fallback
```

# Architecture After

```text
User presentation request
  |
  v
Query router classifies request as PPTX
  |
  v
DeepAgent / LangGraph with PresentationWorkflow state
  |
  +--> create_presentation_plan (validated deck + every slide archetype)
  |
  +--> load_presentation_recipe_guidance
  |       `--> official `officecli load_skill pptx|pitch-deck`
  |
  +--> select_presentation_recipes (one exact reference per slide)
  |
  +--> sandbox_execute --> OfficeCLI generation of the approved contract
  |
  +--> qa_presentation --> `officecli validate` + `officecli view ... issues`
  |
  v
Deliver tracked PPTX

Legacy title/string endpoint --> HTTP 409 migration response
```

# New Planning Flow

1. The router identifies a PowerPoint/deck request and initializes the workflow
   in `PLAN_REQUIRED`.
2. The agent gathers any needed source evidence, then creates the full deck
   plan in one `create_presentation_plan` call. The validator requires deck
   intent and, for every sequential slide: purpose, archetype, primary visual,
   supporting elements, density, and recipe goal.
3. The workflow loads exactly one official OfficeCLI presentation skill after
   planning. It uses `pitch-deck` only for fundraising; otherwise `pptx`.
4. The agent maps every plan row to an exact recipe/reference from that returned
   official guidance with `select_presentation_recipes`. Coverage must be exact;
   duplicates and missing slides are rejected.
5. Only then does the gate allow OfficeCLI execution. The generation phase may
   resolve documented syntax and positioning but may not change archetypes,
   primary visuals, or recipes.
6. `qa_presentation` runs OfficeCLI structural validation and issue inspection.
   A tool failure returns the phase to generation-ready for a targeted repair.
7. The existing output-file tracking/download path delivers the resulting file.

# Prompt Hierarchy

For PPTX work the runtime hierarchy is now:

1. **Code-enforced `PresentationWorkflow` phases** — not bypassable by prompt
   wording when using `sandbox_execute`.
2. **Presentation control-plane system prompt** — directs tool order and states
   that OfficeCLI cannot choose slide type.
3. **Validated slide plan and selected recipe references** — the binding
   implementation contract.
4. **Official OfficeCLI skill returned by `officecli load_skill`** — the source
   of syntax and recipe details.
5. **Presentation design/planning skills** — support visual reasoning but do
   not issue commands.
6. **Generic OfficeCLI wrapper and general research prompt** — still applicable,
   but cannot override the control plane.

# OfficeCLI Workflow

The application does not maintain its own recipe catalogue. After the slide
archetypes are settled, `load_presentation_recipe_guidance` runs the official
`officecli load_skill` command and returns the resulting content at the point of
selection. `select_presentation_recipes` records one reference per slide before
the sandbox gate opens. This is deliberately a split retrieval design: planning
does not need the long syntax reference, and generation does not need to decide
the layout.

The OfficeCLI wrapper remains authoritative for supported commands and syntax.
Custom construction is allowed only where official guidance has no suitable
recipe, and it must still implement the already-approved archetype.

# Remaining Limitations

- Recipe references are validated for complete slide coverage, but OfficeCLI
  currently does not expose a structured recipe registry that the application
  can use to prove a reference name was copied verbatim from loaded guidance.
- `qa_presentation` validates the OpenXML document and checks OfficeCLI issues;
  it does not yet render slide images for model-visible aesthetic review.
- Archetype choice, message editing, chart data selection, and visual judgment
  still depend on Claude's reasoning quality and the source evidence supplied.
- Presentation-request routing is lexical. Unusual terminology that does not
  mention PowerPoint, slides, deck, presentation, or PPT may require a future
  intent classifier.
- The workflow state is per agent invocation. A multi-turn edit of an existing
  deck should be given its own plan-aware edit contract in a future iteration.

# Future Improvements

- Add structured recipe metadata or a parser for `load_skill` output so recipe
  references can be validated against the exact loaded set.
- Render a slide contact sheet after generation and add a visual QA node that
  checks clipping, density, repeated layouts, and whitespace before delivery.
- Persist approved plans and recipe selections with the working-document state
  to support controlled revisions across turns.
- Add a dedicated intent classifier and a deck-type router (board, investor,
  consulting, product, technical) before planning.
- Add plan/recipe/QA telemetry to measure archetype diversity, recipe adoption,
  retry rates, and presentation-quality outcomes.
- Replace the deprecated legacy endpoint with a versioned API that accepts the
  full plan schema or delegates to the same DeepAgent workflow.
