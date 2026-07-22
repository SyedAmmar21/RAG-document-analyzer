from app.services.sandbox.modal.modal_sandbox_service import ModalSandboxService

print("=" * 80)
print("Create Modal Sandbox")
print("=" * 80)

service = ModalSandboxService()

sandbox = service.create_sandbox()

# LangChain ModalSandbox wrapper exposes the underlying Modal sandbox here
modal_sandbox = sandbox._sandbox


def run(cmd: str):
    process = modal_sandbox.exec(
        "bash",
        "-lc",
        cmd,
    )

    process.wait()

    print("Exit Code:", process.returncode)

    print("\nSTDOUT")
    print(process.stdout.read())

    print("\nSTDERR")
    print(process.stderr.read())

###############################################################################
# TEST 1
###############################################################################

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

###############################################################################
# TEST 2
###############################################################################

run("""
mkdir -p /workspace/output

officecli create /workspace/output/test.pptx
""")

###############################################################################
# TEST 3
###############################################################################

run(r"""
mkdir -p /workspace/output

officecli create /workspace/output/test2.pptx

cat <<'EOF' | officecli batch /workspace/output/test2.pptx
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

###############################################################################
# TEST 4
###############################################################################

run("""
ls -lah /workspace/output
""")