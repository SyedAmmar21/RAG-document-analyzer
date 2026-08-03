---
name: workbook-design
description: |
  Use when planning or reviewing an Excel workbook. It defines a professional,
  reader-friendly workbook structure; OfficeCLI remains responsible for workbook
  implementation and syntax.
---

# Workbook Design

## Purpose

Plan the workbook the user should receive before building it. This skill guides
workbook organization and review only; it does not introduce a planning pipeline
or teach OfficeCLI commands.

Use it for analysis workbooks, trackers, models, operational workbooks, and
data-backed business reports.

## Start With The Decision

Determine, briefly and internally:

- audience and the questions they need answered;
- primary metrics, dimensions, and time period;
- whether the workbook is a tracker, analysis, model, or dashboard;
- source-data limits, assumptions, and refresh expectations.

Design the first sheet so a reader can understand the key result and where to
go next without inspecting formulas or raw data.

## Workbook Structure

Use only the sheets that serve the task. A common professional pattern is:

1. `Summary` or `Dashboard`: key KPIs, conclusions, notable changes, and concise
   charts or tables.
2. `Analysis`: calculations, pivots, scenario comparisons, or supporting views.
3. `Data`: normalized source data in a clean table.
4. `Assumptions` or `Inputs`: editable drivers, definitions, and source notes.
5. `Reference` or `Lookup`: stable mappings, lists, or methodology notes.

For a simple tracker, a single well-structured sheet plus an optional summary is
better than several mostly empty sheets. Use short, clear sheet names and order
them from reader-facing to supporting detail.

## Separate Inputs, Logic, And Outputs

- Keep raw data separate from analysis and presentation sheets.
- Place user-editable inputs in a clearly labeled area or dedicated sheet.
- Keep calculations close to the data they explain, but do not mix calculation
  scaffolding into a reader-facing dashboard.
- Do not hard-code repeated values inside formulas when an assumption or lookup
  is more transparent.
- Label assumptions, units, time periods, currencies, and data sources.
- Preserve source data as supplied unless cleanup is necessary and disclosed.

## Summary And Dashboard Guidance

A summary sheet should answer the most important questions at a glance:

- What happened or what is the current position?
- What changed versus the relevant comparison period or target?
- Why does it matter?
- What requires attention or action?

Limit the summary to the metrics and visuals that support those answers. Prefer
clear KPI blocks, trend charts, ranked tables, and short insight callouts over a
dashboard filled with every available metric.

## Tables, Calculations, And Charts

- Use one clean header row; avoid merged cells in data tables.
- Give every table a descriptive title and consistently formatted columns.
- Use formulas for derived values so changes flow through the workbook.
- Apply totals and subtotals only where they clarify the analysis.
- Include a visible check or reconciliation when correctness depends on a total.
- Choose charts for patterns over time, comparisons, composition, or distribution;
  keep tables when exact values and lookup are more important.
- Give charts informative titles, labeled axes where relevant, and a readable
  scale; avoid decorative charts that do not add insight.

## Formatting And Readability

- Apply one consistent visual language for titles, headers, input cells, formulas,
  outputs, totals, and notes.
- Use restrained color with a semantic purpose; do not rely on color alone to
  communicate meaning.
- Format dates, currencies, percentages, decimals, and negative values consistently.
- Size columns and rows for readability, freeze key headers when a sheet is long,
  and avoid unnecessary blank space.
- Keep notes close to the cells or visuals they explain.
- Avoid hidden logic, unexplained abbreviations, and excessively wide worksheets.

## Pre-Delivery Review

Before handing off the workbook, check:

- Can the intended reader identify the key answer from the first sheet?
- Are worksheets named, ordered, and scoped clearly?
- Are raw data, inputs, calculations, and outputs separated appropriately?
- Do formulas, totals, and calculations use consistent units and references?
- Do tables and charts have clear labels and a stated purpose?
- Are editable assumptions distinguishable from calculated or source values?
- Is formatting consistent, readable, and free of distracting visual noise?

OfficeCLI implements the approved design. This skill does not prescribe
OfficeCLI commands, workbook syntax, or a mandatory execution sequence.
