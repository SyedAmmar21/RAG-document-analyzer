"""
backend/app/services/cube_sandbox_initializer.py

Initializes a newly-created CubeSandbox so it is ready to execute OfficeCLI.
"""

from __future__ import annotations

import logging

from e2b_code_interpreter import Sandbox
from app.services.sandbox.backend_contract import officecli_install_command

logger = logging.getLogger(__name__)

if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


class CubeSandboxInitializer:

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------

    def initialize(self):

        logger.info("Initializing CubeSandbox...")

        self.install_icu()

        self.install_officecli()

        self.verify_officecli()

        logger.info("CubeSandbox initialization complete.")

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def run_command(self, command: str):

        logger.info(command)

        result = self.sandbox.commands.run(
            command,
            user="root",
            timeout=600,
        )

        if result.error:
            raise RuntimeError(result.error)

        return result

    # ---------------------------------------------------------
    # Installation
    # ---------------------------------------------------------

    def install_icu(self):

        logger.info("Installing libicu-dev...")

        self.run_command(
            "apt-get update && apt-get install -y libicu-dev"
        )

    def install_officecli(self):

        logger.info("Installing OfficeCLI...")

        self.run_command(
            officecli_install_command()
        )

    def verify_officecli(self):

        logger.info("Verifying OfficeCLI...")

        result = self.run_command(
            """
            export PATH=/root/.local/bin:$PATH

            which officecli

            officecli --version
            """
        )

        print(result)
