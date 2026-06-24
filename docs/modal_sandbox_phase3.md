# Modal Sandbox Phase 3

## Overview

Phase 3 removes the agent's dependence on the old hardcoded Office export path
for document generation guidance and replaces it with an autonomous sandbox
workflow.

Instead of being told to use a fixed export tool, the Deep Agent is now guided
to:

- use its sandbox `execute` tool directly
- run `officecli` commands inside the Modal sandbox
- save generated artifacts to `/workspace/output/`
- let the backend download completed files back to host storage after the agent
  finishes

This keeps document generation agent-driven instead of pipeline-driven.

## What Changed

### 1. `backend/app/skills/Officecli_skill.md`

The top section of the OfficeCLI skill was rewritten so the agent now sees the
correct Phase 3 behavior first.

Before:

- the skill told the agent to use `office_document_tool`
- output expectations pointed to host-style storage behavior
- the skill did not clearly enforce sandbox-first execution

After:

- the skill tells the agent to use `execute(...)` directly
- output must be written to `/workspace/output/<filename>.<format>`
- the agent must create the output directory before generation
- the agent must load the appropriate OfficeCLI specialized skill first
- the agent must check `exit_code == 0` after every command
- the agent is explicitly told not to use hardcoded services or Python Office
  libraries

Why this matters:

- the first section of the skill is the highest-signal instruction block the
  agent sees
- updating it removes confusion with the old hardcoded export path
- the agent can now reason about document structure and issue OfficeCLI
  commands autonomously

### 2. `backend/app/services/rag_agent_service.py`

The `system_prompt` inside `get_deep_rag_agent(...)` was updated only in the
`AVAILABLE TOOLS` area.

Before:

- the prompt still framed document generation around `office_document_tool`

After:

- the prompt now instructs the agent to use `execute`
- it tells the agent to follow the OfficeCLI skill
- it defines `/workspace/output/` as the required save location
- it reminds the agent to create the directory first
- it reinforces loading the correct OfficeCLI skill and checking exit codes
- it states the supported formats: `pptx`, `docx`, `xlsx`, `pdf`

Why this matters:

- even if the sandbox tools are already attached technically, the agent still
  needs prompt-level awareness that document generation is something it can do
  directly
- this change aligns prompt guidance with the actual Phase 2 tool exposure

### 3. `backend/app/routers/query.py`

A post-invoke download step was added immediately after `agent.invoke(...)`.

The new logic:

1. reuses the same sandbox session with `get_backend(request.thread_id)`
2. checks `/workspace/output/` for generated files
3. downloads each generated file from the sandbox
4. saves each file into `storage/outputs/`
5. appends public download paths like `/download/<filename>` to the API
   response
6. removes the file from the sandbox after download to avoid stale
   re-delivery on later requests
7. wraps the entire block in `try/except` so file transfer issues never break
   the main answer

Additional small supporting changes:

- added `Path` import for writing downloaded files
- added `logging` and a module logger for safe warning output
- returned `download_urls` when present

Why this matters:

- the agent can already generate files in the sandbox, but the user cannot use
  them unless the backend pulls them back out
- this closes the loop from generation to delivery without introducing a new
  document-export pipeline

## New Runtime Flow

```text
User asks for a document
        |
        v
Deep Agent reads updated OfficeCLI skill + updated system prompt
        |
        v
Agent uses sandbox execute tool directly
        |
        v
execute("mkdir -p /workspace/output")
execute("officecli load_skill <format-skill>")
execute("officecli ...")
        |
        v
Artifact saved in /workspace/output/ inside sandbox
        |
        v
agent.invoke(...) completes
        |
        v
query.py post-processing runs
        |
        v
ls /workspace/output/
download_files(...)
write host copy to storage/outputs/
rm sandbox copy
        |
        v
API response includes download_urls
```

## Architectural Intent

This phase is intentionally narrow.

It does not add:

- a new export service
- a new agent tool
- a new hardcoded generation function
- a second document pipeline

Instead, it completes the migration by connecting three already-existing
pieces:

- Phase 2 sandbox tool access
- OfficeCLI skill instructions
- response-time file download from sandbox to host

That means the agent remains responsible for planning document structure,
choosing commands, and iterating on failures, while the backend only handles
delivery after the artifact exists.

## Files Touched

- `backend/app/skills/Officecli_skill.md`
- `backend/app/services/rag_agent_service.py`
- `backend/app/routers/query.py`

## Validation Notes

Recommended checks after this phase:

1. Ask the agent to generate a `.pptx`, `.docx`, `.xlsx`, or `.pdf`
2. Confirm the agent uses sandbox execution rather than the old export tool
3. Confirm the file appears in `storage/outputs/`
4. Confirm the API response includes `download_urls`
5. Confirm the sandbox copy is removed after download

## Summary

Phase 3 finishes the behavioral migration for autonomous document generation.

The agent now has:

- correct skill instructions
- correct prompt instructions
- automatic backend delivery of generated files

Together, these changes let document creation happen through sandbox execution
and OfficeCLI reasoning, rather than through hardcoded export plumbing.
