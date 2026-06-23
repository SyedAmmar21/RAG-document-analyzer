# Modal Sandbox – Phase 1 Documentation

## 1️⃣ Old architecture
```
FastAPI
 └─ OfficeDocumentService
     └─ sandbox_service (uses modal.Function.from_name)
         └─ modal.Function.from_name("sandbox‑learning", "analyze_file")
             └─ remote execution of ``analyze_file``
```
* `sandbox_service.run_sandbox(payload)` builds a generic payload and forwards it to a **Modal Function**.
* The FastAPI layer has no awareness of sandbox lifecycles – it simply calls the remote function.
* Export logic (`_create_pdf/_docx/_pptx/_xlsx`) lives inside the remote function.

## 2️⃣ New architecture (Phase 1)
```
FastAPI
 └─ LangChain Agent
     └─ ModalSandboxService  ← **creates / terminates** sandbox
         └─ ModalSandbox (langchain_modal)
             └─ sandbox (Modal)
                 └─ OfficeCLI (runs inside sandbox)
                     └─ generate / read / write / edit / grep / glob
Generated files → Storage
```
* **Agent** stays in FastAPI and decides *when* an export is required.
* **ModalSandboxService** handles sandbox lifecycle (`create_backend`, `create_sandbox`, `terminate_sandbox`).
* **ModalSandbox** (from `langchain_modal`) exposes `execute(...)` – the Agent calls this directly.
* The previous `sandbox_service.py` remains unchanged for backward compatibility.

## 3️⃣ Sandbox lifecycle (Phase 1)
| Step | Action | Method |
|------|--------|--------|
| **Init** | Load env vars, decide if sandbox is enabled | `__init__` |
| **Backend lookup** | `modal.App.lookup(app_name)` – creates the app if missing | `create_backend` |
| **Create** | `modal.Sandbox.create(app)` → `ModalSandbox(sandbox=…)` | `create_sandbox` |
| **Use** | Agent calls `sandbox.execute(<function>, **kwargs)` | *no extra code* |
| **Terminate** | `sandbox.terminate()` – releases resources | `terminate_sandbox` |

*If `USE_MODAL_SANDBOX` is false, `create_sandbox` returns a lightweight dummy that raises on `execute` – this prevents accidental execution in local dev.*

## 4️⃣ Future phases (preview)
* **Phase 2** – Add a thin wrapper (`ModalSandboxExecutor`) that validates payloads before sending them to the sandbox.
* **Phase 3** – Replace the old `sandbox_service.run_sandbox` calls with a new service that internally uses `ModalSandboxService`.
* **Phase 4** – Introduce a storage abstraction for generated files and a cleanup job.

---

## 5️⃣ Environment variables
Add the following entries to your environment (or `.env` file):
```dotenv
USE_MODAL_SANDBOX=true              # Enable the new sandbox path
MODAL_APP_NAME=sandbox-learning     # Modal app that contains the sandbox
```

---

## 6️⃣ Validation steps (to be run after implementation)
1. **Import sanity check**
   ```bash
   python -c "from backend.app.services.modal_sandbox_service import ModalSandboxService; print('OK')"
   ```
2. **Create & terminate a sandbox** (run in a fresh terminal):
   ```python
   from backend.app.services.modal_sandbox_service import ModalSandboxService

   svc = ModalSandboxService()
   sandbox = svc.create_sandbox()          # should log creation
   # Example no‑op execution (will raise if env disabled)
   # result = sandbox.execute("some_function", arg=1)
   svc.terminate_sandbox()                # should log termination
   ```
3. **Run existing test suite** – ensures `sandbox_service.py` still works:
   ```bash
   cd backend
   pytest -q
   ```
4. **Check logs** – confirm that INFO logs appear for each lifecycle method.

---

*All existing tests continue to pass because `sandbox_service.py` is untouched. The new service is isolated and can be unit‑tested independently.*
