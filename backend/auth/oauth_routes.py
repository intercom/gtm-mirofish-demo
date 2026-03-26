"""
OAuth flow endpoints for Google and Okta SSO.

Supports JWT session tokens via Bearer header and httpOnly cookie.
When AUTH_ENABLED=false, /auth/me returns a mock demo user.
"""

import secrets
import time
from urllib.parse import urlencode

import httpx
import jwt
from flask import Blueprint, current_app, jsonify, redirect, request, session

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24


def _jwt_secret():
    return current_app.config['SECRET_KEY']


def _frontend_url():
    return current_app.config.get('FRONTEND_URL', 'http://localhost:3000')


def _redirect_uri():
    return current_app.config.get(
        'OAUTH_REDIRECT_URI',
        request.host_url.rstrip('/') + '/auth/callback',
    )


def _okta_config():
    cfg = current_app.config
    issuer = cfg.get('OKTA_ISSUER', '')
    return {
        'client_id': cfg.get('OKTA_CLIENT_ID', ''),
        'client_secret': cfg.get('OKTA_CLIENT_SECRET', ''),
        'auth_url': f'{issuer}/v1/authorize' if issuer else '',
        'token_url': f'{issuer}/v1/token' if issuer else '',
        'userinfo_url': f'{issuer}/v1/userinfo' if issuer else '',
    }


def _create_token(user_data):
    payload = {
        'sub': user_data['email'],
        'email': user_data['email'],
        'name': user_data.get('name', ''),
        'picture': user_data.get('picture', ''),
        'iat': int(time.time()),
        'exp': int(time.time()) + JWT_EXPIRY_HOURS * 3600,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def _decode_token(token):
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _validate_domain(email):
    if not email or '@' not in email:
        return False
    domain = email.split('@')[-1]
    return domain == current_app.config.get('AUTH_ALLOWED_DOMAIN', 'intercom.io')


# ── Google token exchange ────────────────────────────────

def _exchange_google(code, redirect_uri):
    resp = httpx.post(GOOGLE_TOKEN_URL, data={
        'code': code,
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }, timeout=15)
    resp.raise_for_status()
    access_token = resp.json()['access_token']

    info = httpx.get(GOOGLE_USERINFO_URL, headers={
        'Authorization': f'Bearer {access_token}',
    }, timeout=15)
    info.raise_for_status()
    data = info.json()
    return {'email': data['email'], 'name': data.get('name', ''), 'picture': data.get('picture', '')}


# ── Okta token exchange ──────────────────────────────────

def _exchange_okta(code, redirect_uri):
    okta = _okta_config()
    resp = httpx.post(okta['token_url'], data={
        'code': code,
        'client_id': okta['client_id'],
        'client_secret': okta['client_secret'],
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }, timeout=15)
    resp.raise_for_status()
    access_token = resp.json()['access_token']

    info = httpx.get(okta['userinfo_url'], headers={
        'Authorization': f'Bearer {access_token}',
    }, timeout=15)
    info.raise_for_status()
    data = info.json()
    return {'email': data.get('email', ''), 'name': data.get('name', ''), 'picture': data.get('picture', '')}


# ── Routes ────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET'])
def login():
    """Redirect to OAuth provider consent page."""
    if not current_app.config.get('AUTH_ENABLED'):
        return jsonify({'error': 'Authentication is not enabled'}), 404

    provider = current_app.config.get('AUTH_PROVIDER', 'google')
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    redir = _redirect_uri()

    if provider == 'google':
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        if not client_id:
            return jsonify({'error': 'Google OAuth not configured'}), 500
        params = {
            'client_id': client_id,
            'redirect_uri': redir,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'select_account',
        }
        return redirect(f'{GOOGLE_AUTH_URL}?{urlencode(params)}')

    if provider == 'okta':
        okta = _okta_config()
        if not okta['client_id'] or not okta['auth_url']:
            return jsonify({'error': 'Okta OAuth not configured'}), 500
        params = {
            'client_id': okta['client_id'],
            'redirect_uri': redir,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
        }
        return redirect(f'{okta["auth_url"]}?{urlencode(params)}')

    return jsonify({'error': f'Unknown auth provider: {provider}'}), 400


@auth_bp.route('/callback', methods=['GET'])
def callback():
    """Handle OAuth callback — exchange code, validate domain, issue JWT."""
    if not current_app.config.get('AUTH_ENABLED'):
        return jsonify({'error': 'Authentication is not enabled'}), 404

    frontend = _frontend_url()

    error = request.args.get('error')
    if error:
        return redirect(f'{frontend}/login?error={error}')

    code = request.args.get('code')
    state = request.args.get('state')

    if not state or state != session.pop('oauth_state', None):
        return redirect(f'{frontend}/login?error=invalid_state')

    if not code:
        return redirect(f'{frontend}/login?error=no_code')

    provider = current_app.config.get('AUTH_PROVIDER', 'google')
    redir = _redirect_uri()

    try:
        if provider == 'google':
            user_data = _exchange_google(code, redir)
        elif provider == 'okta':
            user_data = _exchange_okta(code, redir)
        else:
            return redirect(f'{frontend}/login?error=unknown_provider')
    except Exception:
        current_app.logger.exception('OAuth token exchange failed')
        return redirect(f'{frontend}/login?error=token_exchange_failed')

    if not _validate_domain(user_data.get('email', '')):
        allowed = current_app.config.get('AUTH_ALLOWED_DOMAIN', 'intercom.io')
        return redirect(f'{frontend}/login?error=domain_not_allowed&domain={allowed}')

    token = _create_token(user_data)
    session['user'] = user_data

    response = redirect(f'{frontend}/login?callback=true&token={token}')
    response.set_cookie(
        'auth_token',
        token,
        httponly=True,
        secure=not current_app.debug,
        samesite='Lax',
        max_age=JWT_EXPIRY_HOURS * 3600,
    )
    return response


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear session and auth cookie."""
    session.pop('user', None)
    session.pop('oauth_state', None)
    response = jsonify({'ok': True})
    response.delete_cookie('auth_token')
    return response


@auth_bp.route('/me', methods=['GET'])
def me():
    """Return current user info from JWT (Bearer header or cookie)."""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header[7:] if auth_header.startswith('Bearer ') else None

    if not token:
        token = request.cookies.get('auth_token')

    if not token:
        if not current_app.config.get('AUTH_ENABLED'):
            return jsonify({
                'user': {
                    'email': 'demo@intercom.io',
                    'name': 'Demo User',
                    'picture': '',
                }
            })
        return jsonify({'error': 'Not authenticated'}), 401

    payload = _decode_token(token)
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401

    return jsonify({
        'user': {
            'email': payload['email'],
            'name': payload.get('name', ''),
            'picture': payload.get('picture', ''),
        }
    })
