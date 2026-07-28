---
name: presentation-recipe-selection
description: Bind a completed presentation plan to official OfficeCLI recipe guidance before PPTX generation.
---

# Presentation Recipe Selection

Use this skill only after `create_presentation_plan` succeeds.

1. Call `load_presentation_recipe_guidance`.
2. Read the returned official OfficeCLI skill content.
3. Map every planned slide to the most specific recipe or reusable pattern
   returned there. Prefer that recipe over custom composition.
4. Call `select_presentation_recipes` with one exact official reference and
   rationale per slide.

Do not copy OfficeCLI recipe documentation into this skill. Do not invent a
recipe name. If the official guidance has no suitable recipe, record the
documented fallback/custom pattern it specifies and retain the slide archetype
from the approved plan.

After recipe selection succeeds, OfficeCLI is only an implementation phase. It
may choose validated syntax and positioning, but it may not change slide type,
primary visual, or recipe.
