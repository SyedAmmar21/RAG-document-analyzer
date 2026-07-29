from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class SandboxCommandResult:
    exit_code: int
    stdout: str
    stderr: str
    output: str


@runtime_checkable
class SandboxBackend(Protocol):
    def execute(self, command: str) -> SandboxCommandResult:
        ...

    def upload_file_bytes(self, sandbox_path: str, content: bytes) -> None:
        ...

    def download_file_bytes(self, sandbox_path: str) -> bytes | None:
        ...

    def terminate(self) -> None:
        ...


def sandbox_enabled() -> bool:
    provider = os.getenv("SANDBOX_PROVIDER", "modal").lower()

    if provider == "cube":
        return bool(os.getenv("CUBE_TEMPLATE_ID"))

    return os.getenv("USE_MODAL_SANDBOX", "false").lower() == "true"


def build_command_preamble() -> str:
    return (
        "export PATH=/root/.local/bin:$PATH && "
        "export HOME=/root && "
        "export LC_ALL=C.UTF-8 && "
        "export LANG=C.UTF-8 && "
        "mkdir -p /workspace/output && "
        "cd /workspace && "
        "set -o pipefail && "
    )


def officecli_install_command() -> str:
    version = os.getenv("OFFICECLI_VERSION", "").strip()
    if version:
        return (
            "curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh "
            f"| OFFICECLI_VERSION={version} bash"
        )

    return "curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash"


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def result_from_object(value: Any) -> SandboxCommandResult | None:
    if value is None:
        return None

    stdout = _stringify(getattr(value, "stdout", ""))
    stderr = _stringify(getattr(value, "stderr", ""))
    output = _stringify(getattr(value, "output", "")) or f"{stdout}{stderr}"

    exit_code = getattr(value, "exit_code", None)
    if exit_code is None:
        exit_code = getattr(value, "returncode", None)
    if exit_code is None:
        code = getattr(value, "code", None)
        if isinstance(code, int):
            exit_code = code

    if exit_code is None:
        return None

    return SandboxCommandResult(
        exit_code=int(exit_code),
        stdout=stdout,
        stderr=stderr,
        output=output,
    )


def result_from_exception(exc: BaseException) -> SandboxCommandResult | None:
    result = result_from_object(exc)
    if result is not None:
        return result

    message = _stringify(exc)
    lowered_name = exc.__class__.__name__.lower()

    if "commandexit" in lowered_name or "non-zero" in message.lower():
        return SandboxCommandResult(
            exit_code=1,
            stdout="",
            stderr=message,
            output=message,
        )

    return None


def log_command_result(
    logger: logging.Logger,
    provider: str,
    command: str,
    result: SandboxCommandResult,
    output_files: str | None = None,
) -> None:
    logger.info(
        (
            "[%s sandbox]\n"
            "COMMAND:\n%s\n"
            "EXIT CODE:\n%s\n"
            "STDOUT:\n%s\n"
            "STDERR:\n%s\n"
            "OUTPUT FILES:\n%s"
        ),
        provider,
        command,
        result.exit_code,
        result.stdout or "<empty>",
        result.stderr or "<empty>",
        output_files or "<unknown>",
    )
