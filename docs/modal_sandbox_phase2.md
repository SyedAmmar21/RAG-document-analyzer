# Modal Sandbox Phase 2

## Overview

Phase 2 wires Modal Sandbox into the existing Deep Agent by attaching a
thread-scoped `backend` to `create_deep_agent(...)`.

The backend is reused across follow-up turns for the same conversation thread
and cleaned up after 3600 seconds of inactivity.

## Sandbox Lifecycle Diagram

```text
Frontend chat session
        |
        v
Generate/persist thread_id
        |
        v
POST /query
        |
        v
get_deep_rag_agent(..., thread_id=...)
        |
        v
get_backend(thread_id)
   |                     |
   | existing session    | no session
   v                     v
reuse backend      ModalSandboxService()
update last_used   -> create_backend()
                   -> create_sandbox()
                   -> store session
        |
        v
create_deep_agent(..., backend=sandbox_backend)
        |
        v
Agent automatically receives sandbox tools
        |
        v
Existing scheduler job calls cleanup_idle()
        |
        v
Idle sessions older than 3600s are terminated
```

## Thread Reuse Strategy

- Each chat session gets one `thread_id`.
- The frontend keeps that `thread_id` stable for the lifetime of the chat
  component.
- The backend passes the same `thread_id` into the deep agent factory and into
  LangGraph `configurable.thread_id`.
- `get_backend(thread_id)` reuses the existing Modal sandbox backend when that
  thread asks another question.
- `cleanup_idle()` terminates sessions idle longer than 3600 seconds.

## Tool Exposure

Passing `backend=` into `create_deep_agent(...)` automatically gives the agent:

- `execute`
- `read_file`
- `write_file`
- `edit_file`
- `ls`
- `glob`
- `grep`

## Exact Lines Changed In Existing Files

### `backend/app/services/rag_agent_service.py`

- Added `from app.services.sandbox.session_store import get_backend`
- Added `thread_id: str = "default"` to `get_deep_rag_agent(...)`
- Added `sandbox_backend = get_backend(thread_id)`
- Added `backend=sandbox_backend` to `create_deep_agent(...)`

### `backend/app/services/scheduler_service.py`

- Added `from app.services.sandbox.session_store import cleanup_idle`
- Added `cleanup_idle()` to the existing scheduled background job

### `backend/app/routers/query.py`

- Added `from uuid import uuid4`
- Added `thread_id: str = "default"` to `QueryRequest`
- Passed `thread_id=request.thread_id` into `get_deep_rag_agent(...)`
- Added `configurable.thread_id` to the existing `agent.invoke(...)` config
- Added a field-search-specific thread id for sandbox reuse/isolation

### `frontend/src/services/api.js`

- Added `thread_id` to the `queryAgent(...)` payload contract

### `frontend/src/components/ChatWindow.jsx`

- Added a stable per-chat `threadId`
- Sent `thread_id: threadId` with each query request
