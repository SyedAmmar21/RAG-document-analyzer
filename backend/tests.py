from app.services.sandbox.cube.cube_sandbox_service import CubeSandboxService
from app.services.sandbox.cube.cube_sandbox_initializer import CubeSandboxInitializer

service = CubeSandboxService()

sandbox = service.create_sandbox()

initializer = CubeSandboxInitializer(sandbox)
initializer.initialize()


def run(command):
    print("=" * 80)
    print(command)
    print("=" * 80)

    result = sandbox.commands.run(
        command,
        user="root",
    )

    print("Exit Code:", result.exit_code)

    if result.stdout:
        print("STDOUT")
        print(result.stdout)

    if result.stderr:
        print("STDERR")
        print(result.stderr)

    return result


# Test 1
run("which officecli")

# Test 2
run("officecli --version")

# Test 3
run("mkdir -p /workspace/output")

# Test 4
run("officecli create /workspace/output/test.pptx")
run(r"""
cat << 'EOF' >/tmp/test.json
[
  {
    "command":"add",
    "path":"/",
    "type":"slide",
    "props":{
      "title":"Hello World"
    }
  }
]
EOF
""")
run(
    "cat /tmp/test.json | officecli batch /workspace/output/test.pptx"
)
run("ls -la /workspace/output")
print("\nDone.")