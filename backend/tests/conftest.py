"""
Shared pytest fixtures for backend integration tests.

Provides a Flask test client with a fresh app instance per session,
plus common mock helpers for service-layer dependencies.
"""

import pytest
from app import create_app
from app.config import Config


class TestConfig(Config):
    """Overrides for test environment — no external keys needed."""
    TESTING = True
    DEBUG = False
    LLM_API_KEY = "test-key"
    ZEP_API_KEY = "test-zep-key"


@pytest.fixture(scope="session")
def app():
    """Create a Flask app instance for the full test session."""
    application = create_app(config_class=TestConfig)
    yield application


@pytest.fixture(scope="session")
def client(app):
    """Flask test client — sends requests without a running server."""
    return app.test_client()
