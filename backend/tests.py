from app.services.modal_sandbox_service import ModalSandboxService

service = ModalSandboxService()
backend = service.create_sandbox()

commands = [
    "export PATH=/root/.local/bin:$PATH && dotnet --info",
    "export PATH=/root/.local/bin:$PATH && officecli --version",
    "export PATH=/root/.local/bin:$PATH && officecli help pptx",
    "export PATH=/root/.local/bin:$PATH && officecli create /workspace/output/test.pptx",
    "export PATH=/root/.local/bin:$PATH && ls -lah /workspace/output",
]

for cmd in commands:
    print("\n" + "=" * 80)
    print(cmd)
    print("=" * 80)

    result = backend.execute(cmd)

    print("Exit code:", result.exit_code)
    print(result.output)