import logging

from app.services.sandbox.backend_contract import (
    SandboxCommandResult,
    log_command_result,
    result_from_exception,
    result_from_object,
)

logger = logging.getLogger(__name__)


class CubeSandboxBackend:
    """
    Wrapper around the E2B CubeSandbox SDK.

    Exposes a Modal-like interface so the rest of the
    application does not need to know which sandbox
    provider is being used.
    """

    def __init__(self, sandbox):
        self.sandbox = sandbox

    def execute(self, command: str) -> SandboxCommandResult:
        try:
            raw_result = self.sandbox.commands.run(
                command,
                user="root",
            )
            result = result_from_object(raw_result)
            if result is None:
                raise RuntimeError(
                    f"Cube backend returned an unsupported result type: {type(raw_result)!r}"
                )
        except Exception as exc:
            result = result_from_exception(exc)
            if result is None:
                raise

        output_files = self._output_listing()
        log_command_result(logger, "cube", command, result, output_files)
        return result

    def download_file_bytes(self, sandbox_path: str) -> bytes | None:
        try:
            return self.sandbox.files.read(
                sandbox_path,
                format="bytes",
                user="root",
                gzip=False,
            )
        except Exception:
            url = self.sandbox.download_url(sandbox_path)
            import httpx

            with httpx.Client(headers={"Accept-Encoding": "identity"}) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.content

    def upload_file_bytes(self, sandbox_path: str, content: bytes) -> None:
        self.sandbox.files.write(
            sandbox_path,
            content,
            user="root",
            gzip=False,
        )

    def terminate(self):
        self.sandbox.kill()

    def _output_listing(self) -> str:
        try:
            raw_result = self.sandbox.commands.run(
                "ls -lah /workspace/output 2>/dev/null || true",
                user="root",
            )
            result = result_from_object(raw_result)
            if result is None:
                return "<unavailable>"
            return result.stdout or result.output or "<empty>"
        except Exception:
            return "<unavailable>"
