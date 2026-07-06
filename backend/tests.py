from app.services.sandbox.session_store import get_backend

backend = get_backend("officecli-test")

commands = [
    "export PATH=/root/.local/bin:$PATH && mkdir -p /workspace/output",
    "export PATH=/root/.local/bin:$PATH && officecli create /workspace/output/test.pptx --force",
    "export PATH=/root/.local/bin:$PATH && officecli add /workspace/output/test.pptx / --type slide",
]

for i, cmd in enumerate(commands, 1):
    print(f"\n===== COMMAND {i} =====")
    print(cmd)

    result = backend.execute(cmd)

    print("Exit:", result.exit_code)
    print(result.output)