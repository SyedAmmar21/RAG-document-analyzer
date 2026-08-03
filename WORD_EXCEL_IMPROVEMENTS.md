# Word and Excel Quality Improvements

## Files Changed

| File | Change |
| --- | --- |
| `backend/app/skills/report-design/SKILL.md` | Added lightweight guidance for professional Word report structure, writing, visual organization, recommendations, appendices, and review. |
| `backend/app/skills/workbook-design/SKILL.md` | Added lightweight guidance for professional Excel workbook structure, summary sheets, data separation, calculations, charts, formatting, and review. |
| `backend/app/skills/officecli/SKILL.md` | Added a short routing and quality-review note above the embedded official OfficeCLI reference. The official reference itself is unchanged. |
| `backend/app/services/rag_agent_service.py` | Instructed the existing agent to apply the relevant design skill for new Word and Excel documents, using an internal lightweight outline rather than a new workflow. |

## Why These Changes Were Made

OfficeCLI already provides the implementation capability for `.docx` and `.xlsx`
files. The gap was deciding what a reader-ready report or workbook should look
like before implementation.

The new skills separate that editorial and analytical judgment from OfficeCLI:

- `report-design` focuses on narrative order, executive summaries, findings,
  evidence, recommendations, comparisons, procedures, callouts, and appendices.
- `workbook-design` focuses on reader-facing workbook organization, dashboards,
  clear worksheet roles, data and calculation separation, tables, charts, and
  consistent formatting.

Both skills deliberately avoid OfficeCLI commands and syntax. This keeps the
existing OfficeCLI skill as the implementation authority.

## Expected Improvement

Generated Word reports should be easier to scan and act on, with a clear
executive narrative, meaningful section order, and stronger use of tables,
callouts, procedures, and appendices where appropriate.

Generated Excel workbooks should open on a clearer summary, have better-named
and better-ordered worksheets, separate source data from calculations and
outputs, and use consistent, purposeful formatting and charts.

## Why No Architectural Changes Were Necessary

The existing agent already loads skills from `app/skills` and routes Office
document implementation through the existing `sandbox_execute` and OfficeCLI
path. The improvement only adds advisory design guidance and a concise prompt
reminder at the point documents are generated.

No LangGraph states, tools, planning pipelines, orchestration layers, or
presentation-workflow changes were added. PowerPoint behavior is untouched.
