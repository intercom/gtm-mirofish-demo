"""Shared fixtures for demo_app integration tests."""

import sys
from pathlib import Path

import pytest

# Ensure the backend directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo_app import app  # noqa: E402


@pytest.fixture()
def client():
    """Flask test client with fresh state for each test."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        # Reset all in-memory state before each test
        c.post("/api/demo/reset")
        yield c
        c.post("/api/demo/reset")
