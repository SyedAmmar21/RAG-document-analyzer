# Sandbox Parity Changes

## Purpose

This document explains all changes made to the Modal sandbox and Cube sandbox so they behave the same way from the AI agent's point of view.

The goal of these changes was:

- keep the current architecture
- keep backend swapability
- avoid prompt rewrites
- make Modal and Cube return the same execution results
- make document downloads work the same way

This document is written in simple language so the structure is easy to follow.

## Big Picture

The agent uses one shared tool:

`sandbox_execute(command)`

That tool should not care whether the real sandbox is:

- Modal
- Cube / E2B

Before these changes, both backends existed, but they did not behave exactly the same.

The main problems were:

- Cube and Modal did not return the same execution result format
- command failures could behave differently
- download logic leaked provider-specific behavior
- the sandbox enable check still used a Modal-only flag
- edited files could change inside the sandbox but not get synced back to local outputs

## Main Design After The Changes

Now both providers follow the same pattern:

`sandbox_execute`
-> session store picks backend
-> backend adapter runs command
-> backend adapter returns the same result shape
-> query route downloads output files the same way
-> frontend receives the same kind of download link

## Files Changed

These are the files that were added or updated.

### New files

- `backend/app/services/sandbox/backend_contract.py`
- `backend/app/services/sandbox/modal/modal_backend.py`

### Updated files

- `backend/app/services/sandbox/cube/cube_backend.py`
- `backend/app/services/sandbox/cube/cube_sandbox_service.py`
- `backend/app/services/sandbox/cube/cube_sandbox_initializer.py`
- `backend/app/services/sandbox/modal/modal_sandbox_service.py`
- `backend/app/services/sandbox/session_store.py`
- `backend/app/services/rag_agent_service.py`
- `backend/app/routers/query.py`
- `backend/app/routers/documents.py`

## 1. Shared Backend Contract

File:

- `backend/app/services/sandbox/backend_contract.py`

This file was added so both backends follow the same rules.

### What it contains

#### `SandboxCommandResult`

This is the shared result object.

It always contains:

- `exit_code`
- `stdout`
- `stderr`
- `output`

`output` is the combined text output.

This means the AI agent now sees the same result shape no matter which backend is used.

#### `SandboxBackend`

This is a small protocol describing what a backend should support.

It expects:

- `execute(command)`
- `download_file_bytes(path)`
- `terminate()`

This keeps the provider interface clear without redesigning the project.

#### `sandbox_enabled()`

Before, the shared tool checked `USE_MODAL_SANDBOX`, which was too Modal-specific.

Now:

- if provider is `cube`, it checks `CUBE_TEMPLATE_ID`
- otherwise it checks `USE_MODAL_SANDBOX`

This makes backend selection more neutral.

#### `build_command_preamble()`

This creates a standard shell setup before every command.

It now sets:

- `PATH=/root/.local/bin:$PATH`
- `HOME=/root`
- `LC_ALL=C.UTF-8`
- `LANG=C.UTF-8`
- `mkdir -p /workspace/output`
- `cd /workspace`
- `set -o pipefail`

This helps both backends run commands in a more consistent environment.

#### `officecli_install_command()`

This gives both backends the same OfficeCLI install command.

Behavior:

- if `OFFICECLI_VERSION` is set, both backends install that exact version
- if not set, both install the latest version from the installer script

This reduces version drift between Modal and Cube.

#### `result_from_object()` and `result_from_exception()`

These helpers normalize backend results.

They convert backend-specific objects or exceptions into one shared `SandboxCommandResult`.

Important rule:

- normal command failures should become `exit_code != 0`
- they should not crash the agent if they are just normal shell or CLI failures

## 2. Modal Backend Adapter

File:

- `backend/app/services/sandbox/modal/modal_backend.py`

This file was added.

Before, Modal returned the raw `ModalSandbox` wrapper directly.

Now Modal goes through a small adapter just like Cube.

### What it does

#### `execute(command)`

- runs `self.sandbox.execute(command)`
- normalizes the result into `SandboxCommandResult`
- if Modal throws something that is really just a command-exit style failure, it gets translated into a normal result
- logs command details in the same style as Cube

#### `download_file_bytes(path)`

This hides Modal-specific download behavior.

It tries:

- `_sandbox.filesystem.read_bytes(...)`
- then `download_files(...)`

The rest of the app no longer needs to know Modal details.

#### `terminate()`

This terminates the underlying Modal sandbox.

### Why this matters

Now Modal is not a special case anymore.
It follows the same adapter pattern as Cube.

## 3. Cube Backend Adapter

File:

- `backend/app/services/sandbox/cube/cube_backend.py`

This file already existed, but it was updated.

### What changed

#### Shared result format

Before, Cube returned a custom object with:

- `exit_code`
- `output`

Now Cube returns the same shared result shape as Modal:

- `exit_code`
- `stdout`
- `stderr`
- `output`

#### Command failure handling

Before, Cube could fail in a way that was too close to a Python exception path.

Now:

- command failures are translated into `SandboxCommandResult` when possible
- the agent can inspect the error and repair the command

This is important for OfficeCLI because the agent often needs to recover from bad syntax.

#### `download_file_bytes(path)`

Cube now exposes the same download method name as Modal.

It tries:

- `sandbox.files.read(..., format="bytes")`
- if that fails, it falls back to `sandbox.download_url(...)`

This keeps the provider-specific logic inside the backend adapter.

#### Logging

Cube now logs:

- command
- exit code
- stdout
- stderr
- output folder listing

in the same structure as Modal.

## 4. Cube Sandbox Service

File:

- `backend/app/services/sandbox/cube/cube_sandbox_service.py`

### What changed

The created sandbox is now stored in:

- `self.sandbox`

### Why this matters

Before, Cube created the sandbox and returned it, but did not keep it on the service object.

That made cleanup and termination less reliable.

Now `terminate_sandbox()` can properly kill the sandbox it created.

## 5. Cube Sandbox Initializer

File:

- `backend/app/services/sandbox/cube/cube_sandbox_initializer.py`

### What changed

Cube now uses the shared `officecli_install_command()`.

### Why this matters

Before, Cube had its own installer path and version behavior.

Now Modal and Cube install OfficeCLI the same way.

That gives better parity.

## 6. Modal Sandbox Service

File:

- `backend/app/services/sandbox/modal/modal_sandbox_service.py`

### What changed

Modal now also uses the shared `officecli_install_command()`.

### Why this matters

This keeps OfficeCLI installation aligned across both providers.

## 7. Session Store

File:

- `backend/app/services/sandbox/session_store.py`

### What changed

The session store now wraps both providers in backend adapters:

- Modal uses `ModalSandboxBackend`
- Cube uses `CubeSandboxBackend`

### Why this matters

Before:

- Cube used an adapter
- Modal did not

Now both go through the same pattern, which makes the rest of the app simpler and more consistent.

### What did not change

The session store still handles:

- one sandbox per thread
- sandbox reuse
- idle cleanup
- current document tracking
- pending output file tracking

So the architecture is preserved.

## 8. `sandbox_execute()` Changes

File:

- `backend/app/services/rag_agent_service.py`

This is the main shared tool the AI agent uses.

### What changed

#### Provider-neutral enable check

Before:

- it only checked `USE_MODAL_SANDBOX`

Now:

- it uses `sandbox_enabled()`

So it works properly with Cube too.

#### Standardized shell environment

Before executing a command, it now prepends the shared command preamble.

That means both providers get the same basic shell setup.

#### Shared result output

The tool now returns:

- `exit_code`
- `stdout`
- `stderr`
- `output`
- `output_dir_listing`
- `tracked_output_files`

This makes debugging easier and gives the agent better information.

#### OfficeCLI batch validation

The previous JSON validation for `officecli batch` was kept.

That behavior did not get removed.

### Important edit-sync fix

This file also got one more important update later:

if a successful OfficeCLI command edits the current document but the timestamp diff misses it, the current document is force-tracked for re-download.

In simple terms:

- timestamp diff is still the first check
- but if OfficeCLI succeeds and no changed file is detected
- the current working document is added to `tracked_output_files`

### Why this matters

Before:

- a file could be edited inside the sandbox
- but not get copied back to local `storage/outputs`

Now:

- edits are much less likely to be missed

This is especially important when the filename stays the same.

## 9. Query Route Download Pipeline

File:

- `backend/app/routers/query.py`

This file handles what happens after the agent finishes.

### Before

The route:

- consumed `tracked_output_files`
- downloaded the files
- saved them under `storage/outputs`
- returned `download_urls`

But the download behavior still depended on provider-specific backend details before normalization.

Also, the UI only displayed `answer`, so `download_urls` could be present without being visible in chat.

### What changed

#### Backend-neutral download

The route now calls:

- `download_file_bytes(...)`

on the backend adapter.

So the route no longer needs to know if it is talking to Modal or Cube.

#### Output persistence

Downloaded files are still written to:

- `backend/storage/outputs`

This part of the architecture was preserved.

#### Current document fallback for “download it”

If the user asks something like:

- `download it`

and there are no new tracked files for that turn, the route now checks the current thread document and re-exposes its existing local download URL if the file exists.

This helps follow-up download requests work better.

#### Answer augmentation

If there are download URLs, the route now appends them directly into the returned answer text.

This was added because the existing frontend chat view only renders the answer text.

So now the user can actually see the generated download link in chat without changing prompt behavior.

## 10. Generated File Download Endpoint

File:

- `backend/app/routers/documents.py`

### What changed

A new route was added:

- `GET /download/{filename}`

### What it does

It serves generated files from:

- `backend/storage/outputs`

using `FileResponse`.

It also:

- checks the file exists
- prevents invalid filenames from escaping the outputs directory
- sends the file as an attachment

### Why this matters

Before, the backend could return `/download/...` URLs but there was no real dedicated route serving generated output files.

Now the route exists and both providers use it in the same way.

## 11. Full Download Flow After The Changes

This is now the full flow for generated documents.

### Create or edit flow

1. The agent calls `sandbox_execute(...)`
2. The backend runs the command in Modal or Cube
3. The result comes back in the same shape
4. Changed files are detected
5. If timestamp diff misses an OfficeCLI edit, the current document fallback adds the file anyway
6. `record_output_files(...)` stores the filename
7. `/query` later calls `consume_output_files(...)`
8. The backend downloads bytes from the sandbox through `download_file_bytes(...)`
9. The file is written to `backend/storage/outputs`
10. `/download/<filename>` is returned
11. The answer text also includes the download link

### Follow-up “download it” flow

1. User asks for download
2. If no new file was generated this turn, `/query` checks `current_document`
3. If the local file exists in `storage/outputs`, it returns `/download/<filename>`
4. The answer text includes that link

## 12. What Was Not Changed

These parts were intentionally preserved:

- DeepAgents
- LangGraph
- OfficeCLI itself
- overall session-store architecture
- prompt-first workflow for OfficeCLI
- output directory contract `/workspace/output`
- local output storage contract `backend/storage/outputs`

## 13. Why These Changes Help

These changes improve parity in simple ways.

### For the agent

- same result fields from both providers
- better recovery after command failures
- fewer backend-specific surprises

### For downloads

- both providers now use the same download path
- generated files are exposed the same way
- edited files are more likely to sync back correctly

### For debugging

- both providers log similar execution details
- easier to compare Modal vs Cube behavior

## 14. Simple Summary

If you want the shortest version:

- a shared backend contract was added
- Modal got a backend adapter
- Cube was updated to match the same contract
- both providers now install OfficeCLI the same way
- the shared tool now returns the same result format for both
- file downloads now go through a backend-neutral method
- a real `/download/{filename}` route was added
- edited files now have a fallback sync so they do not get stuck only inside the sandbox

## 15. Suggested Mental Model

The easiest way to think about the structure now is:

### Layer 1: Agent layer

- `sandbox_execute(...)`

This is what the AI sees.

### Layer 2: Session layer

- `session_store.py`

This chooses Modal or Cube and keeps one sandbox per thread.

### Layer 3: Backend adapter layer

- `ModalSandboxBackend`
- `CubeSandboxBackend`

These make both providers look the same.

### Layer 4: Real provider layer

- Modal SDK
- E2B / Cube SDK

This is where the actual sandbox runs.

### Layer 5: Download persistence layer

- `query.py`
- `documents.py`
- `storage/outputs`

This is how generated files come back out of the sandbox and reach the frontend.

## 16. Date

This document reflects the sandbox parity changes made on July 22, 2026.
