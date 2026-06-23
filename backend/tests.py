import os
os.environ["USE_MODAL_SANDBOX"] = "true"
os.environ["MODAL_APP_NAME"] = "sandbox-learning"

from app.services.modal_sandbox_service import ModalSandboxService

svc = ModalSandboxService()
svc.create_backend()
backend = svc.create_sandbox()
print(type(backend))  # should print <class 'langchain_modal...ModalSandbox'>

result = backend.execute("python3 --version")
print(result)

svc.terminate_sandbox()
print("Terminated cleanly")