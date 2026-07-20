# Current Modal Sandbox Implementation

## Purpose

This document explains how the project currently uses Modal for sandboxed document generation and editing. It is intentionally focused on the sandbox layer only, so it can serve as a reference when replacing Modal with a future Cube-based sandbox running on company infrastructure.

This is based on the current code in the repository as of July 20, 2026.

## Executive Summary

The project currently has **two sandbox-related paths**:

1. **Active agent sandbox path**
   - Used when the Deep Agent needs to create or modify Office documents with `OfficeCLI`.
   - Creates a live Modal sandbox on demand.
   - Reuses one sandbox per chat `thread_id`.
   - Downloads generated files from the sandbox back into backend storage.

2. **Legacy export path**
   - Used by the older `/generate-presentation` backend route.
   - Calls a deployed Modal Function named `analyze_file` in the `sandbox-learning` app.
   - Can fall back to a local Python implementation if the deployed function is stale.

If the goal is to move from Modal to Cube, the **agent sandbox path is the main implementation to replace first**. The legacy export path should either be migrated separately or removed after the agent path becomes the only supported sandbox workflow.

## File Map

### Primary files

- `backend/app/services/modal_sandbox_service.py`
- `backend/app/services/sandbox/session_store.py`
- `backend/app/services/rag_agent_service.py`
- `backend/app/routers/query.py`

### Legacy / compatibility files

- `backend/app/services/sandbox_service.py`
- `backend/app/services/office_document_service.py`
- `backend/modal_sandbox/sandbox.py`
- `backend/app/routers/documents.py`

### Supporting operational files

- `backend/app/services/scheduler_service.py`
- `docker-compose.yml`

## Architecture Overview

### 1. Live agent sandbox path

The current live path for sandbox execution is:

`/query` route  
-> Deep Agent creation  
-> agent tool `sandbox_execute(command)`  
-> thread-scoped sandbox lookup  
-> Modal sandbox creation or reuse  
-> command execution inside sandbox  
-> changed files tracked in session state  
-> files downloaded to backend storage after agent finishes

### 2. Legacy export path

The older export path is:

`/generate-presentation` route  
-> `OfficeDocumentService.create_presentation()`  
-> `OfficeDocumentService.export_document()`  
-> `run_sandbox(payload)`  
-> `modal.Function.from_name("sandbox-learning", "analyze_file")`  
-> remote Modal Function or local fallback in `backend/modal_sandbox/sandbox.py`

## Current Modal Sandbox Implementation

### ModalSandboxService

`backend/app/services/modal_sandbox_service.py` is the low-level lifecycle wrapper for the live sandbox path.

Key behavior:

- Reads `USE_MODAL_SANDBOX` and `MODAL_APP_NAME` from environment variables (`lines 40-45`).
- Looks up or creates a Modal app with `modal.App.lookup(..., create_if_missing=True)` (`lines 57-73`).
- Builds a Debian-based Modal image (`lines 104-116`).
- Installs:
  - `curl`
  - `libicu-dev`
  - `OfficeCLI` via a remote install script
- Creates a sandbox with:
  - `timeout=1800`
  - `idle_timeout=1800`
  (`lines 118-124`)
- Wraps the resulting `modal.Sandbox` with `langchain_modal.ModalSandbox` (`line 127`).
- Exposes termination through `terminate_sandbox()` (`lines 132-149`).

Important details:

- When `USE_MODAL_SANDBOX=false`, `create_sandbox()` returns a no-op object whose `execute()` raises (`lines 83-94`).
- Command execution is **not** implemented here. This service only creates and terminates the sandbox. Actual commands are run later through the returned `ModalSandbox` object.

### Session store and sandbox reuse

`backend/app/services/sandbox/session_store.py` adds thread-scoped lifecycle management on top of `ModalSandboxService`.

Key behavior:

- Stores one sandbox session per `thread_id` in an in-memory dictionary (`lines 40-41`).
- Reuses an existing sandbox if it is still alive by running `echo alive` inside it (`lines 52-64`).
- Recreates the sandbox if that liveness check fails (`lines 66-75`).
- Protects session creation and access with a process-local lock (`lines 41`, `52`, `77`).
- Tracks:
  - `backend`
  - `service`
  - `last_used`
  - `current_document`
  - `pending_output_files`
  (`lines 31-37`)

Important details:

- Idle cleanup threshold is `3600` seconds (`line 23`).
- `cleanup_idle()` removes old sessions and terminates their Modal sandboxes (`lines 113-137`).
- `set_current_document()` stores the active Office document for future edits (`lines 139-145`).
- `record_output_files()` records generated or modified filenames for later download (`lines 148-170`).
- `consume_output_files()` returns and clears the tracked filenames after a request finishes (`lines 173-183`).

### Agent tool wiring

`backend/app/services/rag_agent_service.py` is where the sandbox becomes usable by the Deep Agent.

The important functions are:

- `_get_output_file_state(backend)` (`lines 240-255`)
- `sandbox_execute(command)` (`lines 697-765`)
- `get_current_document()` (`lines 767-793`)

#### `sandbox_execute(command)`

This is the core live integration point.

Behavior:

- Checks `USE_MODAL_SANDBOX` and returns a failed tool response if disabled (`lines 735-736`).
- Obtains the thread sandbox via `get_backend(thread_id)` (`line 738`).
- Reads file state from `/workspace/output` before execution using a `find` command (`lines 241-255`, then `739`).
- Prepends `/root/.local/bin` to `PATH` so `officecli` is available (`lines 741-743`).
- Executes the given shell command inside the Modal sandbox with `backend.execute(command)` (`line 746`).
- Reads file state again after execution (`line 747`).
- Detects changed output files by comparing before/after timestamps (`lines 748-752`).
- Records changed output files into thread session state (`lines 754-758`).
- Returns a plain-text tool result containing:
  - `exit_code`
  - command `output`
  - current output directory listing
  - tracked output files
  (`lines 760-764`)

#### Agent instructions

The Deep Agent prompt explicitly tells the model to use `sandbox_execute` for document generation (`lines 937-948`) and gives extra rules for batching `OfficeCLI` operations (`lines 1074-1085`).

This means the current sandbox behavior is partly implemented in Python and partly implemented in prompt instructions.

### Query route post-processing

`backend/app/routers/query.py` handles the file download step after the agent finishes.

Key behavior:

- The `/query` route invokes the agent with a `thread_id` in the config (`lines 207-226`).
- After the agent returns, it calls `consume_output_files(thread_id)` (`line 230`).
- It looks up the existing sandbox without creating a new one (`line 231`).
- For each tracked file, it downloads bytes from the sandbox path `/workspace/output/<filename>` (`lines 233-240`).
- Download prefers the underlying Modal filesystem API when available:
  - `sandbox_backend._sandbox.filesystem.read_bytes(...)`
  - otherwise `sandbox_backend.download_files(...)`
  (`lines 29-48`)
- Downloaded files are saved locally under `storage/outputs` (`lines 242-245`).
- A frontend download URL is added as `/download/<filename>` (`line 246`).
- For `pptx`, `docx`, and `xlsx`, the file becomes the thread's `current_document` for future edits (`lines 248-258`).
- The sandbox copy is intentionally kept, not deleted, so future edits can continue against the same sandbox file (`lines 260-261`).

## Legacy Export Path

The codebase still contains an older export pipeline that is separate from the live agent sandbox.

### `run_sandbox(payload)`

`backend/app/services/sandbox_service.py` is a thin gateway around a deployed Modal Function.

Behavior:

- Looks up `modal.Function.from_name("sandbox-learning", "analyze_file")` (`lines 23-26`).
- Calls `.remote(payload)` (`line 29`).
- If the deployed function does not understand the new `export_document` action, it falls back to local Python code by importing `modal_sandbox.sandbox.process_payload` (`lines 30-42`).

This path does **not** create a live Modal sandbox. It calls a deployed serverless-style Modal function instead.

### `OfficeDocumentService`

`backend/app/services/office_document_service.py` is the service layer for that legacy export path.

Behavior:

- Supports `pptx`, `docx`, `xlsx`, and `pdf` (`lines 18-23`).
- Builds a generic `export_document` payload (`lines 46-50`).
- Sends it through `run_sandbox(payload)` (`line 52`).
- Persists returned bytes into `backend/storage/outputs` using a UUID filename (`lines 95-108`).

### `/generate-presentation`

`backend/app/routers/documents.py` still exposes this older route:

- `POST /generate-presentation`
- Calls `OfficeDocumentService.create_presentation(...)`

This route is still Modal-dependent, but it is not the same implementation as the live agent sandbox flow.

### Remote payload processor

`backend/modal_sandbox/sandbox.py` is the implementation behind the legacy Modal Function.

Behavior:

- Declares the Modal app `sandbox-learning` (`line 3`).
- Defines `process_payload(payload)` (`lines 270-305`).
- Normalizes old presentation payloads into the generic export format (`lines 17-41`).
- Dispatches by `document_type` (`lines 254-267`).
- For `pptx`, it attempts another remote Modal function call to `officecli-create-ppt.create_ppt` (`lines 44-67`).
- For failures or stale remote behavior, it falls back to local in-function Python generation.
- Exposes `analyze_file(payload)` as the actual Modal Function (`lines 308-310`).

This path is better described as a **Modal function-based export service**, not a persistent interactive sandbox.

## Runtime Contracts and Assumptions

### Environment variables

The active sandbox path depends on:

- `USE_MODAL_SANDBOX`
- `MODAL_APP_NAME`

These are read in `ModalSandboxService` and the agent tool path.

### Docker dependency

`docker-compose.yml` mounts the local Modal credentials file into the backend container:

- `C:/Users/USER/.modal.toml:/root/.modal.toml` (`docker-compose.yml:53`)

That means current backend execution assumes Modal credentials are available inside the container filesystem.

### Output directory contract

The live agent sandbox flow assumes:

- sandbox-generated files are written to `/workspace/output` inside the sandbox
- downloaded files are stored under `backend/storage/outputs` on the backend side

This path contract appears in both agent instructions and Python logic.

### OfficeCLI path contract

The live sandbox path assumes OfficeCLI is installed under `/root/.local/bin` in the sandbox image. Every command prepends that path manually before execution.

### Session persistence model

Sandbox sessions are:

- process-local
- memory-backed
- keyed by `thread_id`

They are **not** stored in Redis or the database. If the backend process restarts, all sandbox session state is lost.

## Operational Behavior

### How cleanup works

Idle cleanup is triggered from `backend/app/services/scheduler_service.py`.

After each scheduled news ingestion run, `cleanup_idle()` is called (`line 70`).

This means sandbox cleanup is currently piggybacking on the scheduler, not running from a dedicated sandbox janitor.

### What "current document" means

When the agent creates or updates a file and it gets downloaded successfully:

- `pptx`, `docx`, and `xlsx` files are stored as the thread's `current_document`
- later edit requests are supposed to call `get_current_document()`
- the agent can then continue editing the file that still exists in the sandbox

This is an important continuity feature and will matter for Cube migration.

## What Is Modal-Specific Today

These are the main places coupled directly to Modal:

### Live sandbox path

- `modal.App.lookup(...)`
- `modal.Image.debian_slim()`
- `.apt_install(...)`
- `.run_commands(...)`
- `modal.Sandbox.create(...)`
- `modal.enable_output()`
- `langchain_modal.ModalSandbox`
- access to underlying `_sandbox.filesystem.read_bytes(...)`

### Legacy path

- `modal.Function.from_name(...)`
- `.remote(...)`
- `@app.function(...)`
- `modal.App("sandbox-learning")`

### Infrastructure dependency

- mounted `~/.modal.toml` credentials file

## Important Gaps and Risks in the Current Design

These are worth knowing before migration.

### 1. Two different sandbox models exist

The repository currently mixes:

- a persistent live sandbox model for the agent
- a function-call export model for older routes

This makes migration more complex unless one path is chosen as the future standard.

### 2. Session state is in-process only

`_sessions` lives in Python memory. A backend restart loses:

- sandbox handles
- pending output file tracking
- current document state

### 3. Cleanup is indirectly scheduled

Sandbox cleanup currently depends on the news scheduler eventually calling `cleanup_idle()`. It is not tied directly to request lifecycle or a dedicated cleanup loop.

### 4. Sandbox behavior depends on prompt instructions

The agent is told through prompt text how to:

- create output directories
- use `officecli`
- batch operations
- avoid invalid `touch`-created Office files

Some behavior is therefore policy-driven rather than enforced by a strict Python API.

### 5. Live path and legacy path use different generation engines

The live path uses shell commands plus `OfficeCLI`.  
The legacy path uses a Modal Function with Python generators and another remote function for PowerPoint.

That means "sandboxed document generation" is not implemented in one single consistent way yet.

## Cube Migration Seams

If Modal is replaced with Cube, these are the best seams to target.

### 1. Replace `ModalSandboxService` first

Best file to swap:

- `backend/app/services/modal_sandbox_service.py`

Why:

- it is the main lifecycle abstraction already
- `session_store.py` depends on it, not directly on most Modal APIs

Recommended future shape:

- keep the class name temporarily or rename to something neutral like `SandboxRuntimeService`
- replace:
  - Modal app lookup
  - image creation
  - sandbox creation
  - termination
- return an object with an equivalent interface for:
  - `execute(command)`
  - file download access
  - termination

### 2. Define a provider-neutral sandbox interface

Right now the code relies informally on `ModalSandbox`.

A better migration step would be to introduce a small internal interface such as:

- `execute(command: str) -> SandboxCommandResult`
- `read_bytes(path: str) -> bytes`
- `terminate() -> None`
- maybe `is_alive() -> bool`

Then:

- Modal implementation becomes one adapter
- Cube implementation becomes another adapter

### 3. Move file download logic behind the sandbox abstraction

Current download code in `query.py` knows about:

- `sandbox_backend._sandbox.filesystem.read_bytes`
- `sandbox_backend.download_files(...)`

That should move behind one method on the sandbox adapter, for example:

- `download_file_bytes(path: str) -> bytes | None`

This is one of the biggest provider-specific leaks in the current code.

### 4. Keep `session_store.py` mostly intact

`session_store.py` is a good candidate to preserve with minimal changes.

Its responsibilities are generic:

- thread-scoped reuse
- liveness check
- idle cleanup
- current-document tracking
- pending-output tracking

The main change would be replacing the exact liveness command and the stored backend type.

### 5. Decide what to do with the legacy export path

There are two reasonable options:

1. Migrate it too
   - Replace `run_sandbox(payload)` and the Modal function implementation with Cube-backed export execution.

2. Remove it
   - Deprecate `/generate-presentation`
   - Route all document generation through the Deep Agent sandbox path only

If the long-term architecture is "agent creates documents inside Cube", removing the legacy path may simplify the migration.

### 6. Externalize sandbox provisioning details

The current Modal image definition is embedded directly in Python.

For Cube, it would likely be better to separate:

- runtime image selection
- package installation
- OfficeCLI installation
- timeouts
- workspace mount rules
- auth / server endpoint config

That will make local dev, staging, and company-server environments easier to manage.

## Recommended Migration Order

1. Introduce a provider-neutral sandbox adapter interface.
2. Refactor `query.py` download logic behind that interface.
3. Refactor `modal_sandbox_service.py` into a generic sandbox runtime service.
4. Add a Cube implementation alongside the Modal implementation.
5. Switch `session_store.py` to use the generic service.
6. Test live agent creation, edit continuity, file download, and idle cleanup.
7. Decide whether to migrate or remove the legacy `/generate-presentation` path.

## Concrete Current Flow Example

For a user request like "Create a PowerPoint about gold market risks":

1. Frontend sends `POST /query` with a `thread_id`.
2. `query.py` creates a Deep Agent for that thread.
3. The agent decides to use `sandbox_execute(...)`.
4. `sandbox_execute(...)` calls `get_backend(thread_id)`.
5. `session_store.py` either reuses an existing sandbox or creates one through `ModalSandboxService`.
6. The command runs inside the Modal sandbox with `OfficeCLI`.
7. The tool detects changed files in `/workspace/output`.
8. Those filenames are stored in `pending_output_files`.
9. After agent completion, `query.py` downloads the files from the sandbox.
10. Files are saved to backend `storage/outputs`.
11. Download URLs are returned to the frontend.
12. If the file is an Office document, it becomes the `current_document` for later edits in the same thread.

## Bottom Line

The current implementation already has a useful separation between:

- sandbox lifecycle creation
- thread-scoped reuse
- agent command execution
- post-run file download

That is good news for migration.

The biggest blockers to a clean Modal -> Cube transition are:

- direct Modal API usage in `modal_sandbox_service.py`
- Modal-specific file download logic in `query.py`
- the presence of the separate legacy Modal Function export path

If those three areas are normalized behind one internal sandbox abstraction, moving execution to Cube on your company server should be much simpler.
