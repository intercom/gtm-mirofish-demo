"""
Shared fixtures for backend integration tests.
"""

import pytest
from app import create_app
from app.config import Config


class TestConfig(Config):
    """Test configuration with auth disabled by default."""
    TESTING = True
    SECRET_KEY = 'test-secret'
    AUTH_ENABLED = False
    AUTH_PROVIDER = 'google'
    AUTH_ALLOWED_DOMAIN = 'intercom.io'


class AuthEnabledConfig(TestConfig):
    """Test configuration with auth enabled."""
    AUTH_ENABLED = True


@pytest.fixture()
def app():
    """Flask app with auth disabled."""
    app = create_app(TestConfig)
    yield app


@pytest.fixture()
def client(app):
    """Test client with auth disabled."""
    return app.test_client()


@pytest.fixture()
def auth_app():
    """Flask app with auth enabled."""
    app = create_app(AuthEnabledConfig)
    yield app


@pytest.fixture()
def auth_client(auth_app):
    """Test client with auth enabled."""
    return auth_app.test_client()
