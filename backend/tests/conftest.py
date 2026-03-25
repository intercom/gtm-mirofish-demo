"""Shared fixtures for backend tests."""

import os
import pytest

from app import create_app
from app.config import Config
from app.models.task import TaskManager


class TestConfig(Config):
    """Override config for testing — no real API keys needed."""
    TESTING = True
    DEBUG = False
    LLM_API_KEY = "test-key"
    ZEP_API_KEY = "test-zep-key"
    AUTH_ENABLED = False


@pytest.fixture()
def app(tmp_path):
    """Create a Flask app with test config and isolated upload dir."""
    TestConfig.UPLOAD_FOLDER = str(tmp_path / "uploads")
    os.makedirs(TestConfig.UPLOAD_FOLDER, exist_ok=True)

    application = create_app(config_class=TestConfig)
    yield application


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def _reset_task_manager():
    """Clear TaskManager singleton state between tests."""
    tm = TaskManager()
    tm._tasks.clear()
    yield
    tm._tasks.clear()
