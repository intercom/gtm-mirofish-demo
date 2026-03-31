"""
Integration tests for auth API endpoints.

Tests the /api/auth/* (simple HMAC-token auth) and /auth/* (OAuth JWT flow)
endpoints through Flask's test client.
"""

import time
from unittest.mock import patch, MagicMock

import jwt
import pytest


# ===================================================================
# /api/auth/login
# ===================================================================

class TestApiAuthLogin:
    """POST /api/auth/login — demo-mode and session-based login."""

    def test_demo_mode_returns_user_and_token(self, client):
        resp = client.post('/api/auth/login')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['user']['email'] == 'demo@intercom.io'
        assert data['user']['name'] == 'Demo User'
        assert 'token' in data
        # Token should be a 3-part HMAC string: email:expiry:sig
        parts = data['token'].split(':')
        assert len(parts) == 3
        assert parts[0] == 'demo@intercom.io'

    def test_auth_enabled_without_session_returns_401(self, auth_client):
        resp = auth_client.post('/api/auth/login')
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Authentication required'

    def test_auth_enabled_with_session_returns_user(self, auth_client):
        with auth_client.session_transaction() as sess:
            sess['user'] = {
                'email': 'dev@intercom.io',
                'name': 'Dev User',
                'picture': 'https://example.com/pic.jpg',
            }
        resp = auth_client.post('/api/auth/login')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['user']['email'] == 'dev@intercom.io'
        assert data['user']['name'] == 'Dev User'
        assert 'token' in data


# ===================================================================
# /api/auth/logout
# ===================================================================

class TestApiAuthLogout:
    """POST /api/auth/logout — session clearing."""

    def test_logout_returns_ok(self, client):
        resp = client.post('/api/auth/logout')
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True

    def test_logout_clears_session(self, client):
        with client.session_transaction() as sess:
            sess['user'] = {'email': 'test@intercom.io'}
        resp = client.post('/api/auth/logout')
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert 'user' not in sess


# ===================================================================
# /api/auth/me
# ===================================================================

class TestApiAuthMe:
    """GET /api/auth/me — token validation and user retrieval."""

    def test_demo_mode_no_token_returns_demo_user(self, client):
        resp = client.get('/api/auth/me')
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'demo@intercom.io'
        assert user['name'] == 'Demo User'

    def test_demo_mode_with_valid_token(self, client):
        # First get a token via login
        login_resp = client.post('/api/auth/login')
        token = login_resp.get_json()['token']

        resp = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}',
        })
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'demo@intercom.io'

    def test_demo_mode_with_invalid_token_falls_back_to_demo(self, client):
        resp = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid:token:data',
        })
        assert resp.status_code == 200
        assert resp.get_json()['user']['email'] == 'demo@intercom.io'

    def test_demo_mode_with_expired_token_falls_back_to_demo(self, app, client):
        # Build a token with an expiry in the past
        import hashlib
        import hmac as hmac_mod
        secret = app.config.get('SECRET_KEY', 'mirofish-gtm-demo-secret')
        expires = int(time.time()) - 100
        payload = f'demo@intercom.io:{expires}'
        sig = hmac_mod.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        expired_token = f'{payload}:{sig}'

        resp = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {expired_token}',
        })
        assert resp.status_code == 200
        assert resp.get_json()['user']['email'] == 'demo@intercom.io'

    def test_auth_enabled_no_token_no_session_returns_401(self, auth_client):
        resp = auth_client.get('/api/auth/me')
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Not authenticated'

    def test_auth_enabled_with_session_only(self, auth_client):
        with auth_client.session_transaction() as sess:
            sess['user'] = {
                'email': 'dev@intercom.io',
                'name': 'Dev User',
                'picture': None,
            }
        resp = auth_client.get('/api/auth/me')
        assert resp.status_code == 200
        assert resp.get_json()['user']['email'] == 'dev@intercom.io'

    def test_auth_enabled_with_valid_token_and_matching_session(self, auth_client):
        with auth_client.session_transaction() as sess:
            sess['user'] = {
                'email': 'dev@intercom.io',
                'name': 'Dev User',
                'picture': 'https://example.com/pic.jpg',
            }
        # Get token through login
        login_resp = auth_client.post('/api/auth/login')
        token = login_resp.get_json()['token']

        resp = auth_client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}',
        })
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'dev@intercom.io'
        assert user['name'] == 'Dev User'

    def test_auth_enabled_with_valid_token_no_session(self, auth_app, auth_client):
        # Manually craft an HMAC token
        import hashlib
        import hmac as hmac_mod
        secret = auth_app.config.get('SECRET_KEY', 'mirofish-gtm-demo-secret')
        expires = int(time.time()) + 3600
        payload = f'dev@intercom.io:{expires}'
        sig = hmac_mod.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        token = f'{payload}:{sig}'

        resp = auth_client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}',
        })
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'dev@intercom.io'
        # Without session, name is derived from email
        assert user['name'] == 'dev'

    def test_auth_enabled_with_malformed_token_returns_401(self, auth_client):
        resp = auth_client.get('/api/auth/me', headers={
            'Authorization': 'Bearer not-a-valid-token',
        })
        assert resp.status_code == 401


# ===================================================================
# /auth/login (OAuth redirect)
# ===================================================================

class TestOAuthLogin:
    """GET /auth/login — redirect to OAuth provider."""

    def test_auth_disabled_returns_404(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 404
        assert resp.get_json()['error'] == 'Authentication is not enabled'

    def test_google_redirect(self, auth_app, auth_client):
        auth_app.config['GOOGLE_CLIENT_ID'] = 'test-client-id'
        resp = auth_client.get('/auth/login')
        assert resp.status_code == 302
        location = resp.headers['Location']
        assert 'accounts.google.com' in location
        assert 'test-client-id' in location
        assert 'state=' in location

    def test_google_missing_client_id_returns_500(self, auth_app, auth_client):
        auth_app.config.pop('GOOGLE_CLIENT_ID', None)
        resp = auth_client.get('/auth/login')
        assert resp.status_code == 500
        assert 'not configured' in resp.get_json()['error']

    def test_okta_redirect(self, auth_app, auth_client):
        auth_app.config['AUTH_PROVIDER'] = 'okta'
        auth_app.config['OKTA_CLIENT_ID'] = 'okta-id'
        auth_app.config['OKTA_ISSUER'] = 'https://dev.okta.com/oauth2/default'
        resp = auth_client.get('/auth/login')
        assert resp.status_code == 302
        location = resp.headers['Location']
        assert 'dev.okta.com' in location
        assert 'okta-id' in location

    def test_okta_missing_config_returns_500(self, auth_app, auth_client):
        auth_app.config['AUTH_PROVIDER'] = 'okta'
        auth_app.config.pop('OKTA_CLIENT_ID', None)
        auth_app.config.pop('OKTA_ISSUER', None)
        resp = auth_client.get('/auth/login')
        assert resp.status_code == 500

    def test_unknown_provider_returns_400(self, auth_app, auth_client):
        auth_app.config['AUTH_PROVIDER'] = 'unsupported'
        resp = auth_client.get('/auth/login')
        assert resp.status_code == 400
        assert 'Unknown auth provider' in resp.get_json()['error']

    def test_sets_oauth_state_in_session(self, auth_app, auth_client):
        auth_app.config['GOOGLE_CLIENT_ID'] = 'test-client-id'
        auth_client.get('/auth/login')
        with auth_client.session_transaction() as sess:
            assert 'oauth_state' in sess


# ===================================================================
# /auth/callback (OAuth callback)
# ===================================================================

class TestOAuthCallback:
    """GET /auth/callback — code exchange and JWT issuance."""

    def test_auth_disabled_returns_404(self, client):
        resp = client.get('/auth/callback?code=test&state=test')
        assert resp.status_code == 404

    def test_error_param_redirects_to_frontend(self, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        resp = auth_client.get('/auth/callback?error=access_denied')
        assert resp.status_code == 302
        assert 'testfrontend:3000/login?error=access_denied' in resp.headers['Location']

    def test_missing_state_redirects_with_error(self, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        resp = auth_client.get('/auth/callback?code=test')
        assert resp.status_code == 302
        assert 'invalid_state' in resp.headers['Location']

    def test_invalid_state_redirects_with_error(self, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'correct-state'
        resp = auth_client.get('/auth/callback?code=test&state=wrong-state')
        assert resp.status_code == 302
        assert 'invalid_state' in resp.headers['Location']

    def test_missing_code_redirects_with_error(self, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'
        resp = auth_client.get('/auth/callback?state=valid-state')
        assert resp.status_code == 302
        assert 'no_code' in resp.headers['Location']

    @patch('auth.oauth_routes._exchange_google')
    def test_successful_google_callback(self, mock_exchange, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        auth_app.config['AUTH_ALLOWED_DOMAIN'] = 'intercom.io'
        mock_exchange.return_value = {
            'email': 'dev@intercom.io',
            'name': 'Dev User',
            'picture': 'https://example.com/pic.jpg',
        }
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'

        resp = auth_client.get('/auth/callback?code=auth-code&state=valid-state')
        assert resp.status_code == 302
        location = resp.headers['Location']
        assert 'testfrontend:3000/login?callback=true' in location
        assert 'token=' in location

        # Verify auth cookie was set in response
        set_cookie_headers = resp.headers.getlist('Set-Cookie')
        assert any('auth_token=' in h for h in set_cookie_headers)

        # Verify session was populated
        with auth_client.session_transaction() as sess:
            assert sess['user']['email'] == 'dev@intercom.io'

    @patch('auth.oauth_routes._exchange_google')
    def test_domain_not_allowed_redirects_with_error(self, mock_exchange, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        auth_app.config['AUTH_ALLOWED_DOMAIN'] = 'intercom.io'
        mock_exchange.return_value = {
            'email': 'user@gmail.com',
            'name': 'External User',
            'picture': '',
        }
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'

        resp = auth_client.get('/auth/callback?code=auth-code&state=valid-state')
        assert resp.status_code == 302
        assert 'domain_not_allowed' in resp.headers['Location']

    @patch('auth.oauth_routes._exchange_google')
    def test_token_exchange_failure_redirects_with_error(self, mock_exchange, auth_app, auth_client):
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        mock_exchange.side_effect = Exception('Token exchange failed')
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'

        resp = auth_client.get('/auth/callback?code=bad-code&state=valid-state')
        assert resp.status_code == 302
        assert 'token_exchange_failed' in resp.headers['Location']

    @patch('auth.oauth_routes._exchange_okta')
    def test_successful_okta_callback(self, mock_exchange, auth_app, auth_client):
        auth_app.config['AUTH_PROVIDER'] = 'okta'
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        auth_app.config['AUTH_ALLOWED_DOMAIN'] = 'intercom.io'
        mock_exchange.return_value = {
            'email': 'dev@intercom.io',
            'name': 'Okta User',
            'picture': '',
        }
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'

        resp = auth_client.get('/auth/callback?code=okta-code&state=valid-state')
        assert resp.status_code == 302
        assert 'callback=true' in resp.headers['Location']

    def test_unknown_provider_redirects_with_error(self, auth_app, auth_client):
        auth_app.config['AUTH_PROVIDER'] = 'unsupported'
        auth_app.config['FRONTEND_URL'] = 'http://testfrontend:3000'
        with auth_client.session_transaction() as sess:
            sess['oauth_state'] = 'valid-state'

        resp = auth_client.get('/auth/callback?code=test&state=valid-state')
        assert resp.status_code == 302
        assert 'unknown_provider' in resp.headers['Location']


# ===================================================================
# /auth/logout (OAuth)
# ===================================================================

class TestOAuthLogout:
    """POST /auth/logout — session + cookie clearing."""

    def test_logout_clears_session_and_cookie(self, auth_client):
        with auth_client.session_transaction() as sess:
            sess['user'] = {'email': 'dev@intercom.io'}
            sess['oauth_state'] = 'some-state'

        resp = auth_client.post('/auth/logout')
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True

        with auth_client.session_transaction() as sess:
            assert 'user' not in sess
            assert 'oauth_state' not in sess

    def test_logout_deletes_auth_cookie(self, auth_client):
        # Set the cookie first
        auth_client.set_cookie('auth_token', 'test-token', domain='localhost')
        resp = auth_client.post('/auth/logout')
        assert resp.status_code == 200
        # Response should contain Set-Cookie that expires the auth_token
        set_cookie_headers = resp.headers.getlist('Set-Cookie')
        auth_cookie_cleared = any(
            'auth_token=' in h and ('Max-Age=0' in h or 'expires=' in h.lower())
            for h in set_cookie_headers
        )
        assert auth_cookie_cleared


# ===================================================================
# /auth/me (OAuth JWT)
# ===================================================================

class TestOAuthMe:
    """GET /auth/me — JWT-based user retrieval."""

    def test_no_token_auth_disabled_returns_demo_user(self, client):
        resp = client.get('/auth/me')
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'demo@intercom.io'

    def test_no_token_auth_enabled_returns_401(self, auth_client):
        resp = auth_client.get('/auth/me')
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Not authenticated'

    def test_valid_jwt_in_bearer_header(self, auth_app, auth_client):
        secret = auth_app.config['SECRET_KEY']
        token = jwt.encode({
            'email': 'dev@intercom.io',
            'name': 'Dev User',
            'picture': 'https://example.com/pic.jpg',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }, secret, algorithm='HS256')

        resp = auth_client.get('/auth/me', headers={
            'Authorization': f'Bearer {token}',
        })
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'dev@intercom.io'
        assert user['name'] == 'Dev User'

    def test_valid_jwt_in_cookie(self, auth_app, auth_client):
        secret = auth_app.config['SECRET_KEY']
        token = jwt.encode({
            'email': 'dev@intercom.io',
            'name': 'Cookie User',
            'picture': '',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }, secret, algorithm='HS256')

        auth_client.set_cookie('auth_token', token, domain='localhost')
        resp = auth_client.get('/auth/me')
        assert resp.status_code == 200
        user = resp.get_json()['user']
        assert user['email'] == 'dev@intercom.io'
        assert user['name'] == 'Cookie User'

    def test_expired_jwt_returns_401(self, auth_app, auth_client):
        secret = auth_app.config['SECRET_KEY']
        token = jwt.encode({
            'email': 'dev@intercom.io',
            'name': 'Dev User',
            'iat': int(time.time()) - 7200,
            'exp': int(time.time()) - 3600,
        }, secret, algorithm='HS256')

        resp = auth_client.get('/auth/me', headers={
            'Authorization': f'Bearer {token}',
        })
        assert resp.status_code == 401
        assert resp.get_json()['error'] == 'Invalid or expired token'

    def test_invalid_jwt_returns_401(self, auth_client):
        resp = auth_client.get('/auth/me', headers={
            'Authorization': 'Bearer not.a.valid.jwt',
        })
        assert resp.status_code == 401

    def test_jwt_signed_with_wrong_secret_returns_401(self, auth_client):
        token = jwt.encode({
            'email': 'dev@intercom.io',
            'exp': int(time.time()) + 3600,
        }, 'wrong-secret', algorithm='HS256')

        resp = auth_client.get('/auth/me', headers={
            'Authorization': f'Bearer {token}',
        })
        assert resp.status_code == 401

    def test_bearer_header_takes_precedence_over_cookie(self, auth_app, auth_client):
        secret = auth_app.config['SECRET_KEY']
        header_token = jwt.encode({
            'email': 'header@intercom.io',
            'name': 'Header User',
            'picture': '',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }, secret, algorithm='HS256')
        cookie_token = jwt.encode({
            'email': 'cookie@intercom.io',
            'name': 'Cookie User',
            'picture': '',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,
        }, secret, algorithm='HS256')

        auth_client.set_cookie('auth_token', cookie_token, domain='localhost')
        resp = auth_client.get('/auth/me', headers={
            'Authorization': f'Bearer {header_token}',
        })
        assert resp.status_code == 200
        assert resp.get_json()['user']['email'] == 'header@intercom.io'
