"""Shared fixtures for backend integration tests."""

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    """Test configuration — no real API keys needed for data endpoint tests."""
    TESTING = True
    DEBUG = False
    LLM_API_KEY = "test-key"
    ZEP_API_KEY = "test-zep-key"


@pytest.fixture()
def app():
    """Create a Flask app with test configuration."""
    app = create_app(config_class=TestConfig)
    yield app


@pytest.fixture()
def client(app):
    """Flask test client for making HTTP requests."""
    return app.test_client()
