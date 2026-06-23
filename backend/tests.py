"""
Confirms the sandbox backend executes commands correctly.
Run with: uv run pytest tests/sandbox/test_sandbox_execute.py -v
"""
import os
os.environ["USE_MODAL_SANDBOX"] = "true"
os.environ["MODAL_APP_NAME"] = "sandbox-learning"

import pytest
from app.services.sandbox.session_store import get_backend, _sessions, _sessions_lock


def teardown_function():
    with _sessions_lock:
        _sessions.clear()


def test_execute_returns_response():
    backend = get_backend("thread-exec-test")
    result = backend.execute("echo hello")
    assert result.output.strip() == "hello"
    assert result.exit_code == 0
    assert result.truncated is False


def test_execute_python_version():
    backend = get_backend("thread-python-test")
    result = backend.execute("python3 --version")
    assert result.exit_code == 0
    assert "Python" in result.output


def test_execute_failed_command():
    backend = get_backend("thread-fail-test")
    result = backend.execute("this-command-does-not-exist")
    assert result.exit_code != 0


def test_execute_write_and_read_file():
    backend = get_backend("thread-file-test")

    # Write a file
    write = backend.execute("echo 'test content' > /tmp/test.txt")
    assert write.exit_code == 0

    # Read it back
    read = backend.execute("cat /tmp/test.txt")
    assert read.exit_code == 0
    assert "test content" in read.output