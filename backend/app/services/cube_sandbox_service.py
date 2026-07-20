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

    def create_sandbox(self) -> Sandbox:
        """
        Create a CubeSandbox instance.
        """

        # ---------------------------------------------------------
        # Validate configuration
        # ---------------------------------------------------------

        if not self.api_url:
            raise RuntimeError("E2B_API_URL is not configured.")

        if not self.api_key:
            raise RuntimeError("E2B_API_KEY is not configured.")

        if not self.template_id:
            raise RuntimeError("CUBE_TEMPLATE_ID is not configured.")

        # ---------------------------------------------------------
        # Configure SDK
        # ---------------------------------------------------------

        os.environ["E2B_API_URL"] = self.api_url
        os.environ["E2B_API_KEY"] = self.api_key

        if self.ssl_cert:
            os.environ["SSL_CERT_FILE"] = self.ssl_cert

        logger.info("Connecting to CubeSandbox...")

        # ---------------------------------------------------------
        # Create sandbox
        # ---------------------------------------------------------

        self.sandbox = Sandbox.create(
            template=self.template_id,
            timeout=1800,
        )

        logger.info(
            "CubeSandbox created successfully. Sandbox ID: %s",
            self.sandbox.sandbox_id,
        )

        return self.sandbox

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