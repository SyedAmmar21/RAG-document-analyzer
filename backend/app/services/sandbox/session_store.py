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

from langchain_modal import ModalSandbox

from app.services.modal_sandbox_service import ModalSandboxService


logger = logging.getLogger(__name__)

IDLE_TIMEOUT_SECONDS = 3600


@dataclass
class SandboxSession:
    backend: ModalSandbox
    service: ModalSandboxService
    last_used: float


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
            existing_session.last_used = now
            logger.info("Reusing Modal sandbox backend for thread_id=%s", thread_id)
            return existing_session.backend

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
        )

    logger.info("Created Modal sandbox backend for thread_id=%s", thread_id)
    return backend


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
