from __future__ import annotations

import logging

from app.services.sandbox.backend_contract import (
    SandboxCommandResult,
    log_command_result,
    result_from_exception,
    result_from_object,
)

logger = logging.getLogger(__name__)


class ModalSandboxBackend:
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self._sandbox = getattr(sandbox, "_sandbox", None)

    def execute(self, command: str) -> SandboxCommandResult:
        try:
            raw_result = self.sandbox.execute(command)
            result = result_from_object(raw_result)
            if result is None:
                raise RuntimeError(
                    f"Modal backend returned an unsupported result type: {type(raw_result)!r}"
                )
        except Exception as exc:
            result = result_from_exception(exc)
            if result is None:
                raise

        output_files = self._output_listing()
        log_command_result(logger, "modal", command, result, output_files)
        return result

    def download_file_bytes(self, sandbox_path: str) -> bytes | None:
        filesystem = getattr(self._sandbox, "filesystem", None)

        if filesystem is not None:
            read_bytes = getattr(filesystem, "read_bytes", None)
            if callable(read_bytes):
                return read_bytes(sandbox_path)

        results = self.sandbox.download_files([sandbox_path])
        if results and results[0].content is not None:
            return results[0].content

        return None

    def terminate(self) -> None:
        if self._sandbox is not None:
            self._sandbox.terminate()

    def _output_listing(self) -> str:
        try:
            raw_result = self.sandbox.execute("ls -lah /workspace/output 2>/dev/null || true")
            result = result_from_object(raw_result)
            if result is None:
                return "<unavailable>"
            return result.stdout or result.output or "<empty>"
        except Exception:
            return "<unavailable>"
