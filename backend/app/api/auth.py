"""
Auth API
Login, logout, and token validation endpoints.
Works in demo mode when AUTH_ENABLED is false — returns a mock demo user.
"""

import hashlib
import hmac
import json
import time

from flask import Blueprint, current_app, jsonify, request, session

auth_bp = Blueprint('api_auth', __name__, url_prefix='/api/auth')

DEMO_USER = {
    'email': 'demo@intercom.io',
    'name': 'Demo User',
    'picture': None,
}

TOKEN_TTL = 60 * 60 * 24  # 24 hours


def _make_token(email):
    """Create a simple HMAC-based token encoding email + expiry."""
    secret = current_app.config.get('SECRET_KEY', 'mirofish-gtm-demo-secret')
    expires = int(time.time()) + TOKEN_TTL
    payload = f'{email}:{expires}'
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f'{payload}:{sig}'


def _verify_token(token):
    """Verify token and return email if valid, else None."""
    secret = current_app.config.get('SECRET_KEY', 'mirofish-gtm-demo-secret')
    parts = token.split(':')
    if len(parts) != 3:
        return None
    email, expires_str, sig = parts
    try:
        expires = int(expires_str)
    except ValueError:
        return None
    if time.time() > expires:
        return None
    expected = hmac.new(secret.encode(), f'{email}:{expires_str}'.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return email


def _get_user_from_session():
    """Return user dict from Flask session (used when AUTH_ENABLED + OAuth)."""
    user = session.get('user')
    if not user:
        return None
    return {
        'email': user.get('email'),
        'name': user.get('name'),
        'picture': user.get('picture'),
    }


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user. In demo mode, returns a demo user + token."""
    auth_enabled = current_app.config.get('AUTH_ENABLED', False)

    if not auth_enabled:
        token = _make_token(DEMO_USER['email'])
        return jsonify({'user': DEMO_USER, 'token': token})

    # When auth is enabled, check if user already has a session (via OAuth)
    user = _get_user_from_session()
    if user:
        token = _make_token(user['email'])
        return jsonify({'user': user, 'token': token})

    return jsonify({'error': 'Authentication required'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear server-side session."""
    session.clear()
    return jsonify({'ok': True})


@auth_bp.route('/me', methods=['GET'])
def me():
    """Validate token and return current user."""
    auth_enabled = current_app.config.get('AUTH_ENABLED', False)

    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

    if not auth_enabled:
        # Demo mode: accept any valid token, fall back to demo user
        if token:
            email = _verify_token(token)
            if email:
                return jsonify({'user': {'email': email, 'name': 'Demo User', 'picture': None}})
        return jsonify({'user': DEMO_USER})

    # Auth enabled: try token first, then session
    if token:
        email = _verify_token(token)
        if email:
            user = _get_user_from_session()
            if user and user['email'] == email:
                return jsonify({'user': user})
            return jsonify({'user': {'email': email, 'name': email.split('@')[0], 'picture': None}})

    user = _get_user_from_session()
    if user:
        return jsonify({'user': user})

    return jsonify({'error': 'Not authenticated'}), 401
