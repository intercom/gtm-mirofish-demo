"""Shared fixtures for backend tests."""

import os
import pytest

# Ensure env vars are set before any app code imports Config at module level
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("ZEP_API_KEY", "test-zep-key")
os.environ.setdefault("LLM_PROVIDER", "openai")

from app import create_app
from app.config import Config
from app.models.task import TaskManager


@pytest.fixture()
def app():
    """Create a Flask application for testing."""
    application = create_app(Config)
    application.config["TESTING"] = True
    yield application


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_task_manager():
    """Reset the TaskManager singleton state between tests."""
    tm = TaskManager()
    tm._tasks.clear()
    yield
    tm._tasks.clear()
