"""
backend/app/services/cube_sandbox_service.py

CubeSandbox lifecycle service.

Responsibilities
----------------
- Read CubeSandbox configuration
- Create remote sandboxes
- Return an E2B Sandbox object
- Destroy sandboxes

This service intentionally does NOT implement:
    - OfficeCLI logic
    - File upload/download wrappers
    - RAG logic
    - AI workflows

Those belong in higher layers.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from app.services.sandbox.cube.cube_sidecar import CubeSidecar

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


class CubeSandboxService:
    """
    CubeSandbox lifecycle manager.

    Creates and owns one sandbox instance.
    """

    def __init__(self):

        # ---------------------------------------------------------
        # Configuration
        # ---------------------------------------------------------

        self.api_url = os.getenv("E2B_API_URL")
        self.api_key = os.getenv("E2B_API_KEY")
        self.template_id = os.getenv("CUBE_TEMPLATE_ID")
        self.ssl_cert = os.getenv("SSL_CERT_FILE")

        self.workspace = "/workspace"

        # Current sandbox
        self.sandbox: Optional[Sandbox] = None

        logger.info("CubeSandboxService initialized.")


    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _run_command(self, command: str):
        """
        Execute a shell command inside the sandbox.

        Returns the Execution object from the E2B SDK.
        """

        if self.sandbox is None:
            raise RuntimeError("Sandbox has not been created.")

        logger.info("Executing command:\n%s", command)

        execution = self.sandbox.commands.run(
            command,
            timeout=600,
        )

        return execution

    def _install_icu(self):
        """
        Install ICU libraries required by OfficeCLI.
        """

        logger.info("Installing ICU...")

        result = self._run_command(
            "apt-get update && apt-get install -y libicu-dev"
        )

        return result

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def create_sandbox(self):

        CubeSidecar.initialize()

        logger.info("Connecting to CubeSandbox...")

        sandbox = Sandbox.create(
            template=os.environ["CUBE_TEMPLATE_ID"],
            timeout=1800,
        )
        self.sandbox = sandbox

        logger.info(
            "CubeSandbox created successfully. Sandbox ID: %s",
            sandbox.sandbox_id,
        )

        return sandbox
    
    
    def terminate_sandbox(self) -> None:
        """
        Destroy the current sandbox.

        Safe to call multiple times.
        """

        if self.sandbox is None:
            logger.info("No sandbox to terminate.")
            return

        try:
            self.sandbox.kill()
            logger.info("Sandbox terminated successfully.")

        except Exception:
            logger.exception("Failed to terminate sandbox.")

        finally:
            self.sandbox = None
