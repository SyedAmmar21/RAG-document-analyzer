---
name: presentation-planning
description: Create the mandatory slide-by-slide implementation contract for every PowerPoint request before OfficeCLI is used.
---

# Presentation Planning Control Plane

This skill is for the first phase of every PPTX request. It deliberately does
not contain OfficeCLI commands or recipe text.

First turn the user's intent and any retrieved evidence into one cohesive deck.
Then call `create_presentation_plan` with the entire deck before loading
OfficeCLI guidance or using `sandbox_execute`.

Each slide must specify a single purpose and one concrete archetype:

- hero
- executive_summary
- feature_cards
- comparison
- timeline
- process
- architecture
- dashboard
- data_insight
- recommendation
- closing
- section_divider
- market_landscape
- traction

For every slide, identify the primary visual and supporting elements that make
the message understandable without a bullet-list fallback. `recipe_goal` is a
plain-language retrieval target, such as "KPI dashboard recipe" or "two-column
comparison recipe". It is not a guessed OfficeCLI recipe name.

The plan is complete only when all slides are numbered sequentially and the
deck has intentional layout rhythm. Do not choose OfficeCLI syntax, generate
commands, or revise archetypes during implementation.

Choose `officecli_skill: "pitch-deck"` only for a fundraising deck. Use
`officecli_skill: "pptx"` for every other static business presentation.
