from dataclasses import dataclass
from unittest import result


@dataclass
class ExecuteResult:
    exit_code: int
    output: str


class CubeSandboxBackend:
    """
    Wrapper around the E2B CubeSandbox SDK.

    Exposes a Modal-like interface so the rest of the
    application does not need to know which sandbox
    provider is being used.
    """

    def __init__(self, sandbox):
        self.sandbox = sandbox

    def execute(self, command: str) -> ExecuteResult:
        result = self.sandbox.commands.run(
            command,
            user="root",
        )
         
        print("===== COMMAND =====")
        print(command)

        print("===== EXIT CODE =====")
        print(result.exit_code)

        print("===== STDOUT =====")
        print(result.stdout)

        print("===== STDERR =====")
        print(result.stderr)

        files = self.sandbox.commands.run(
            "ls -lah /workspace/output 2>/dev/null || true",
            user="root",
        )


        print("===== OUTPUT FOLDER =====")
        print(files.stdout)

        output = ""

        if result.stdout:
            output += result.stdout

        if result.stderr:
            output += result.stderr

        return ExecuteResult(
            exit_code=result.exit_code,
            output=output,
        )

    def terminate(self):
        self.sandbox.kill()