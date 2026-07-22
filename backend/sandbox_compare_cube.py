from app.services.sandbox.cube.cube_sandbox_service import CubeSandboxService
from app.services.sandbox.cube.cube_sandbox_initializer import CubeSandboxInitializer

service = CubeSandboxService()

sandbox = service.create_sandbox()

initializer = CubeSandboxInitializer(sandbox)
initializer.initialize()

def run(cmd):
    print("\n" + "=" * 80)
    print(cmd)
    print("=" * 80)

    result = sandbox.commands.run(
        cmd,
        user="root",
    )

    print("Exit Code:", result.exit_code)

    print("\nSTDOUT")
    print(result.stdout)

    print("\nSTDERR")
    print(result.stderr)

    return result

run("""
officecli --version
uname -m
which officecli
pwd
""")

print("\n" + "=" * 80)
print("Excel Create + Batch Test")
print("=" * 80)

run("""
mkdir -p /workspace/output

officecli create /workspace/output/test.xlsx

echo '[
{
  "command":"set",
  "path":"/Sheet1/A1",
  "props":{
    "value":"Hello"
  }
}
]' | officecli batch /workspace/output/test.xlsx

ls -lah /workspace/output
""")