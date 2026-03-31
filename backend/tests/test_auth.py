"""
Integration tests for auth endpoints and middleware.

Tests the require_auth decorator, validate_email_domain helper,
and the /api/v1/settings/auth-status endpoint through Flask's test client.
"""

import pytest
from flask import Blueprint, jsonify, session

from auth.middleware import auth_required, _validate_email_domain as validate_email_domain


# ---------------------------------------------------------------------------
# Test-only blueprint: a protected endpoint to exercise @auth_required
# ---------------------------------------------------------------------------
_test_bp = Blueprint('test_auth', __name__)


@_test_bp.route('/api/test/protected')
@auth_required
def protected_endpoint():
    return jsonify({'message': 'ok'})


@pytest.fixture()
def client_with_protected(app):
    """Client whose app includes the test-only protected endpoint."""
    app.register_blueprint(_test_bp)
    return app.test_client()


@pytest.fixture()
def auth_client_with_protected(auth_app):
    """Auth-enabled client whose app includes the test-only protected endpoint."""
    auth_app.register_blueprint(_test_bp)
    return auth_app.test_client()


# ===================================================================
# require_auth decorator — auth disabled (passthrough)
# ===================================================================

class TestRequireAuthDisabled:
    """When AUTH_ENABLED=false the decorator should be transparent."""

    def test_passes_through_without_session(self, client_with_protected):
        resp = client_with_protected.get('/api/test/protected')
        assert resp.status_code == 200
        assert resp.get_json()['message'] == 'ok'


# ===================================================================
# require_auth decorator — auth enabled
# ===================================================================

class TestRequireAuthEnabled:
    """When AUTH_ENABLED=true, unauthenticated requests should be rejected."""

    def test_json_request_returns_401(self, auth_client_with_protected):
        resp = auth_client_with_protected.get(
            '/api/test/protected',
            headers={'Accept': 'application/json'},
        )
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Authentication required'

    def test_json_content_type_returns_401(self, auth_client_with_protected):
        resp = auth_client_with_protected.get(
            '/api/test/protected',
            content_type='application/json',
        )
        assert resp.status_code == 401

    def test_browser_request_returns_401(self, auth_client_with_protected):
        """auth_required returns 401 JSON for all unauthenticated requests."""
        resp = auth_client_with_protected.get(
            '/api/test/protected',
            headers={'Accept': 'text/html'},
        )
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Authentication required'

    def test_authenticated_session_passes(self, auth_client_with_protected):
        with auth_client_with_protected.session_transaction() as sess:
            sess['user'] = {
                'email': 'dev@intercom.io',
                'name': 'Test User',
            }
        resp = auth_client_with_protected.get('/api/test/protected')
        assert resp.status_code == 200
        assert resp.get_json()['message'] == 'ok'


# ===================================================================
# validate_email_domain
# ===================================================================

class TestValidateEmailDomain:
    """validate_email_domain reads AUTH_ALLOWED_DOMAIN from app config."""

    def test_allowed_domain(self, app):
        with app.app_context():
            assert validate_email_domain('user@intercom.io') is True

    def test_wrong_domain(self, app):
        with app.app_context():
            assert validate_email_domain('user@gmail.com') is False

    def test_empty_email(self, app):
        with app.app_context():
            assert validate_email_domain('') is False

    def test_none_email(self, app):
        with app.app_context():
            # _validate_email_domain expects a string; None is handled by callers
            with pytest.raises(TypeError):
                validate_email_domain(None)

    def test_no_at_sign(self, app):
        with app.app_context():
            assert validate_email_domain('invalid-email') is False

    def test_subdomain_not_matched(self, app):
        with app.app_context():
            assert validate_email_domain('user@sub.intercom.io') is False


# ===================================================================
# /api/v1/settings/auth-status endpoint
# ===================================================================

class TestAuthStatusEndpoint:

    def test_auth_disabled_returns_minimal(self, client):
        resp = client.get('/api/v1/settings/auth-status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authEnabled'] is False
        assert data['provider'] is None
        assert data['allowedDomain'] is None
        assert data['user'] is None

    def test_auth_enabled_no_session(self, auth_client):
        resp = auth_client.get('/api/v1/settings/auth-status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authEnabled'] is True
        assert data['provider'] == 'google'
        assert data['allowedDomain'] == 'intercom.io'
        assert data['user'] is None

    def test_auth_enabled_with_session_user(self, auth_client):
        with auth_client.session_transaction() as sess:
            sess['user'] = {
                'email': 'dev@intercom.io',
                'name': 'Test User',
                'picture': 'https://example.com/avatar.png',
            }
        resp = auth_client.get('/api/v1/settings/auth-status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authEnabled'] is True
        assert data['user'] is not None
        assert data['user']['email'] == 'dev@intercom.io'
        assert data['user']['name'] == 'Test User'
        assert data['user']['picture'] == 'https://example.com/avatar.png'

    def test_auth_enabled_session_user_partial_fields(self, auth_client):
        """Session user missing optional fields should still work."""
        with auth_client.session_transaction() as sess:
            sess['user'] = {'email': 'dev@intercom.io'}
        resp = auth_client.get('/api/v1/settings/auth-status')
        data = resp.get_json()
        assert data['user']['email'] == 'dev@intercom.io'
        assert data['user']['name'] is None
        assert data['user']['picture'] is None
