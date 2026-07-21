"""
CubeSandbox Dev Sidecar

Initializes the CubeSandbox development sidecar once for the entire
application. Every service should call CubeSidecar.initialize() before
creating a sandbox.

Nothing happens if it has already been initialized.
"""

import threading

from dotenv import load_dotenv
from app.services.sandbox.cube.dev_sidecar import setup_dev_sidecar


class CubeSidecar:
    _initialized = False
    _lock = threading.Lock()

    @classmethod
    def initialize(cls):
        with cls._lock:
            if cls._initialized:
                return

            load_dotenv()
            setup_dev_sidecar()

            cls._initialized = True
