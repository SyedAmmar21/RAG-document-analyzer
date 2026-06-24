from app.services.sandbox.session_store import get_backend

backend = get_backend("test-thread")

command = "export PATH=/root/.local/bin:$PATH && officecli --version"

result = backend.execute(command)

print(result.exit_code)
print(result.output)