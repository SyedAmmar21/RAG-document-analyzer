---
name: presentation-design
description: |
  Use this skill only when the user explicitly requests a presentation that should look beautiful, modern, polished, premium, professional, executive, minimal, visually appealing, investor-ready, consultant-style, or otherwise places emphasis on presentation design rather than only content generation.
---

# Presentation Design Director

This skill improves the visual quality of PowerPoint presentations.

It is **NOT** a replacement for the OfficeCLI PPTX skill.

Its responsibility is to decide the presentation's visual identity, storytelling, layout rhythm, and design language before OfficeCLI creates the slides.

OfficeCLI remains responsible for:

- commands
- syntax
- slide creation
- editing
- validation
- charts
- positioning
- Office document generation

---

# When To Use

Load this skill ONLY if the user requests things like:

- beautiful presentation
- professional slides
- modern presentation
- executive presentation
- premium design
- polished deck
- clean slides
- visually appealing
- investor deck
- startup pitch deck
- Apple style
- Google style
- McKinsey style
- consulting style
- redesign this presentation
- improve slide design
- make the slides prettier

If the user simply requests a presentation without mentioning design quality, do NOT use this skill.

---

# Core Philosophy

The audience should understand the slide within 3 seconds.

Good presentation design is achieved through:

- clarity
- hierarchy
- whitespace
- consistency
- visual storytelling

Never make slides visually busy simply because there is available space.

Every visual element must serve a purpose.

---

# Step 1 — Determine Design Intent

Before creating any slide, determine:

Audience

Examples

- Executives
- Investors
- Customers
- Engineers
- Students
- Researchers
- General Public

Purpose

Examples

- Inform
- Teach
- Pitch
- Sell
- Report
- Present findings
- Training

Tone

Examples

- Professional
- Corporate
- Friendly
- Premium
- Luxury
- Academic
- Technical
- Minimal
- Modern

---

# Step 2 — Choose A Design Mode

Select ONE design mode.

## Executive

For:

- business reports
- management
- board meetings
- finance

Characteristics

- minimal
- lots of whitespace
- large typography
- few colors
- charts over bullets

---

## Modern SaaS

For

- startups
- technology
- AI
- software

Characteristics

- rounded cards
- gradients
- clean icons
- colorful accents
- minimal text

---

## Investor Pitch

Characteristics

- large headlines
- KPI slides
- market visuals
- timeline
- traction slides
- premium appearance

---

## Academic

Characteristics

- clean
- structured
- diagrams
- minimal decoration
- emphasis on readability

---

## Technical

Characteristics

- process diagrams
- architecture
- flowcharts
- comparison tables
- restrained colors

---

## Marketing

Characteristics

- strong imagery
- bold typography
- hero slides
- high visual impact

---

# Step 3 — Create One Visual Identity

Choose ONE consistent visual identity.

Examples

- Executive dark
- Bright minimal
- Glassmorphism
- Soft gradients
- Flat corporate
- Premium black
- Blue consulting
- Startup colorful

Maintain consistency across the entire presentation.

Do not mix multiple design languages.

---

# Step 4 — Select One Motif

Every presentation should have one recognizable motif.

Examples

- Rounded cards
- Section numbers
- Corner accents
- Colored header band
- Floating panels
- Gradient backgrounds
- Circular icon containers
- Timeline dots

Reuse the motif throughout the deck.

Do not introduce new decorative styles halfway through.

---

# Step 5 — Plan The Story

Every slide must have one purpose.

Possible purposes

- Cover
- Agenda
- Section Divider
- Problem
- Opportunity
- Process
- Timeline
- Architecture
- KPI
- Comparison
- Recommendation
- Conclusion

Avoid slides that attempt to explain multiple unrelated ideas.

---

# Step 5.5 — Convert Content Into Designed Slides

Do not treat presentation design as formatting.

Treat every slide as a design problem.

Before implementing a slide, determine:

- the slide's primary message
- the visual focal point
- the most appropriate slide archetype

Never default to a title with bullet points simply because the source material is written as bullets.

Instead, reorganize the information into visual structures whenever possible.

Choose the slide archetype that best communicates the message.

Examples

- 2–4 key ideas → feature cards
- comparison → side-by-side comparison
- process → workflow diagram
- timeline → timeline layout
- metrics → KPI cards
- architecture → architecture diagram
- hierarchy → layered diagram
- categories → card grid
- recommendations → prioritized cards
- summary → dashboard layout
- strengths vs weaknesses → comparison panels

Only use traditional bullet lists when the information genuinely cannot be communicated more clearly through a visual layout.

The presentation should reorganize information rather than simply restyle text.

---

# Step 5.6 — Prefer Visual Composition

Each slide should feel intentionally designed rather than text placed on a blank canvas.

When a slide contains only a few ideas, increase their visual prominence instead of leaving large empty areas.

Prefer using large visual components such as:

- feature cards
- comparison panels
- KPI blocks
- highlighted callouts
- process blocks
- timelines
- dashboards
- architecture blocks
- image-and-text compositions

Avoid layouts where a title sits above one or two isolated text boxes surrounded by large unused space.

The visual components should occupy the composition naturally while preserving comfortable whitespace.

Whitespace should frame the design, not replace it.
---

# Step 6 — Layout Rhythm

Do not reuse the same slide archetype simply because it is easy to generate.

A professional presentation intentionally varies its visual composition.

Consecutive slides should normally use different archetypes unless they are part of the same repeated data series.

For example:

Hero
↓

Cards
↓

Comparison
↓

Timeline
↓

Chart + Insight
↓

Process
↓

Summary

The audience should immediately feel that each slide was designed for its specific message rather than filled using a template.
---

# Step 7 — Visual Hierarchy

Every slide must contain a clear focal point.

Examples

- main number
- title
- diagram
- chart
- hero image

The audience should immediately know where to look first.

Supporting information should never compete with the primary message.

---

# Step 8 — Information Density

Choose the appropriate density.

Minimal

- very few words
- large visuals

Balanced

- standard business presentation

Information Rich

- research
- technical
- engineering

Executive

- high-level only
- details belong in speaker notes

---

# Step 9 — Design Rules

Prefer

- whitespace
- alignment
- consistency
- simple palettes
- strong typography
- charts over large bullet lists
- icons only when meaningful

Avoid

- unnecessary decorations
- clipart
- emoji
- rainbow color palettes
- inconsistent spacing
- tiny text
- crowded slides
- duplicate visuals
- repeated layouts

---

# Step 10 — Design Review

Before finishing the presentation, mentally review every slide.

Ask:

Does every slide belong to the same presentation?

Does the presentation feel consistent?

Does every slide have a single focus?

Would removing an element improve the slide?

Is there sufficient whitespace?

Would an executive be comfortable presenting these slides?

If improvements can be made without changing the user's requested content, make them before final generation.
---

# Design Planning Requirement

Before OfficeCLI creates any slide, internally create a design plan for the entire presentation.

For every slide decide:

- slide purpose
- slide archetype
- primary visual
- secondary supporting elements
- information density

Only after every slide has an intended visual composition should OfficeCLI begin implementing the presentation.

Do not decide layouts one slide at a time during generation.
---

# Relationship With OfficeCLI

This skill does not replace OfficeCLI.

After deciding the presentation design strategy:

1. Load the OfficeCLI PPTX skill.

2. Follow the OfficeCLI workflow exactly.

3. Apply the chosen design language consistently during implementation.

If any design recommendation conflicts with OfficeCLI capabilities or documentation, OfficeCLI documentation takes precedence.

---

# Goal

The final presentation should look intentionally designed rather than automatically generated.

Prioritize:

- clarity
- professionalism
- consistency
- storytelling
- visual hierarchy
- restrained use of color
- effective whitespace

A successful presentation is one that communicates quickly and confidently while maintaining a polished appearance.