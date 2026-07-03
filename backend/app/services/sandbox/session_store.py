"""
Thread-scoped Modal sandbox session store.

Creates one sandbox backend per conversation thread and reuses it across
follow-up turns until the session has been idle for too long.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import PurePosixPath

from langchain_modal import ModalSandbox

from app.services.modal_sandbox_service import ModalSandboxService
from typing import Optional

logger = logging.getLogger(__name__)

IDLE_TIMEOUT_SECONDS = 3600

@dataclass
class WorkingDocument:
    filename: str
    path: str
    file_type: str

@dataclass
class SandboxSession:
    backend: ModalSandbox
    service: ModalSandboxService
    last_used: float
    current_document: Optional[WorkingDocument] = None
    pending_output_files: list[str] | None = None


_sessions: dict[str, SandboxSession] = {}
_sessions_lock = threading.Lock()


def get_backend(thread_id: str) -> ModalSandbox:
    """
    Return the sandbox backend for a conversation thread.

    Reuses an existing sandbox when available; otherwise creates and stores one.
    """
    now = time.time()

    with _sessions_lock:
        existing_session = _sessions.get(thread_id)
        if existing_session is not None:
            try:
                existing_session.backend.execute("echo alive")
                existing_session.last_used = now

                logger.info(
                    "Reusing Modal sandbox backend for thread_id=%s",
                    thread_id,
                )

                return existing_session.backend

            except Exception:
                logger.warning(
                    "Sandbox for thread_id=%s is dead. Recreating.",
                    thread_id,
                )

                _sessions.pop(thread_id, None)

    service = ModalSandboxService()
    backend = service.create_sandbox()

    with _sessions_lock:
        existing_session = _sessions.get(thread_id)
        if existing_session is not None:
            existing_session.last_used = now
            service.terminate_sandbox()
            logger.info(
                "Reusing concurrently-created Modal sandbox backend for thread_id=%s",
                thread_id,
            )
            return existing_session.backend

        _sessions[thread_id] = SandboxSession(
            backend=backend,
            service=service,
            last_used=now,
            pending_output_files=[],
        )

    logger.info("Created Modal sandbox backend for thread_id=%s", thread_id)
    return backend


def get_existing_backend(thread_id: str) -> ModalSandbox | None:
    """
    Return an existing sandbox backend for a conversation thread.

    This helper never creates a sandbox. It only returns a tracked backend
    instance or None when the thread has not used sandbox execution yet.
    """
    with _sessions_lock:
        session = _sessions.get(thread_id)
        if session is None:
            return None
        return session.backend


def cleanup_idle() -> None:
    """
    Terminate and remove thread sandboxes that have been idle too long.
    """
    cutoff = time.time() - IDLE_TIMEOUT_SECONDS

    with _sessions_lock:
        expired_sessions = [
            (thread_id, session)
            for thread_id, session in _sessions.items()
            if session.last_used < cutoff
        ]

        for thread_id, _session in expired_sessions:
            _sessions.pop(thread_id, None)

    for thread_id, session in expired_sessions:
        try:
            session.service.terminate_sandbox()
            logger.info("Cleaned up idle Modal sandbox for thread_id=%s", thread_id)
        except Exception:
            logger.exception(
                "Failed to clean up idle Modal sandbox for thread_id=%s",
                thread_id,
            )

def set_current_document(thread_id: str, document: WorkingDocument) -> None:
    """Store the current working document for a thread."""

    with _sessions_lock:
        session = _sessions.get(thread_id)
        if session is not None:
            session.current_document = document


def record_output_files(thread_id: str, file_paths: list[str]) -> None:
    """Track sandbox output files produced or updated for a thread."""

    normalized_filenames = []
    for file_path in file_paths:
        filename = PurePosixPath(file_path).name
        if filename:
            normalized_filenames.append(filename)

    if not normalized_filenames:
        return

    with _sessions_lock:
        session = _sessions.get(thread_id)
        if session is None:
            return

        if session.pending_output_files is None:
            session.pending_output_files = []

        for filename in normalized_filenames:
            if filename not in session.pending_output_files:
                session.pending_output_files.append(filename)


def consume_output_files(thread_id: str) -> list[str]:
    """Return and clear tracked sandbox output files for a thread."""

    with _sessions_lock:
        session = _sessions.get(thread_id)
        if session is None or not session.pending_output_files:
            return []

        filenames = list(session.pending_output_files)
        session.pending_output_files.clear()
        return filenames


def get_current_document(thread_id: str) -> WorkingDocument | None:
    """Return the current working document for a thread."""

    with _sessions_lock:
        session = _sessions.get(thread_id)

        if session is None:
            return None

        return session.current_document
