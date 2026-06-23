"""
backend/app/services/modal_sandbox_service.py
Phase 1 – Modal Sandbox infrastructure.

Provides a thin lifecycle wrapper around LangChain’s ModalSandbox.
It is **not** responsible for executing commands – the sandbox itself
exposes an ``execute()`` method that callers use directly.

Environment variables
---------------------
USE_MODAL_SANDBOX – set to "true" to enable the sandbox path.
MODAL_APP_NAME    – name of the Modal app that contains the sandbox
                    (default: "sandbox-learning").
"""

import os
import logging
from typing import Optional

from langchain_modal import ModalSandbox
import modal

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure a handler exists in environments where the root logger has none.
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


class ModalSandboxService:
    """Manage the creation and termination of a Modal sandbox.

    The service is deliberately lightweight – it only creates a sandbox,
    returns a bound ``ModalSandbox`` instance, and can terminate the sandbox
    when the caller is done.  All execution is delegated to the sandbox’s
    ``execute`` method, so no ``execute_command`` helper is needed here.
    """

    def __init__(self):
        # Environment flag – useful for unit‑tests or local dev where the
        # sandbox should be bypassed.
        self.use_sandbox: bool = os.getenv("USE_MODAL_SANDBOX", "false").lower() == "true"
        self.app_name: str = os.getenv("MODAL_APP_NAME", "sandbox-learning")
        self._sandbox: Optional[modal.Sandbox] = None
        self._modal_app: Optional[modal.App] = None

        logger.info(
            "ModalSandboxService initialized (use_sandbox=%s, app_name=%s)",
            self.use_sandbox,
            self.app_name,
        )

    # ---------------------------------------------------------------------
    # Lifecycle helpers
    # ---------------------------------------------------------------------
    def create_backend(self) -> modal.App:
        """Look up (or create) the Modal ``App`` that hosts the sandbox.

        Returns
        -------
        modal.App
            The looked‑up Modal application.
        """
        try:
            self._modal_app = modal.App.lookup(self.app_name, create_if_missing=True)
            logger.info("Modal app %s looked up/created successfully.", self.app_name)
            return self._modal_app
        except Exception as exc:  # pragma: no cover – defensive
            logger.exception("Failed to look up Modal app %s", self.app_name)
            raise RuntimeError(
                f"Unable to initialise Modal app '{self.app_name}'."
            ) from exc

    def create_sandbox(self) -> ModalSandbox:
        """Create a new sandbox instance bound to the previously looked‑up app.

        Returns
        -------
        ModalSandbox
            A ready‑to‑use sandbox wrapper.
        """
        if not self.use_sandbox:
            logger.warning(
                "USE_MODAL_SANDBOX is false – returning a no‑op sandbox for local dev."
            )

            class _NoOpSandbox:
                def execute(self, *_, **__):  # pragma: no cover – never used in prod
                    raise RuntimeError(
                        "Modal sandbox is disabled (USE_MODAL_SANDBOX=false)."
                    )

            return _NoOpSandbox()  # type: ignore

        if self._modal_app is None:
            self.create_backend()

        try:
            # ``modal.Sandbox.create`` returns a sandbox that can be passed to
            # ``ModalSandbox`` from LangChain.
            self._sandbox = modal.Sandbox.create(app=self._modal_app)
            logger.info("Modal sandbox created successfully.")
            return ModalSandbox(sandbox=self._sandbox)
        except Exception as exc:  
            logger.exception("Failed to create Modal sandbox.")
            raise RuntimeError("Could not create Modal sandbox.") from exc

    def terminate_sandbox(self) -> None:
        """Gracefully terminate the sandbox, releasing resources.

        It is safe to call this method multiple times – if the sandbox has
        already been terminated the call becomes a no‑op.
        """
        if not self._sandbox:
            logger.info("No sandbox to terminate.")
            return

        try:
            self._sandbox.terminate()
            logger.info("Modal sandbox terminated successfully.")
        except Exception as exc:  # pragma: no cover – defensive
            # Termination failures should not crash the process; log and continue.
            logger.exception("Error terminating Modal sandbox – ignoring.")
        finally:
            self._sandbox = None
