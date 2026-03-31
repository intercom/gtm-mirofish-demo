"""
Authentication middleware for MiroFish GTM Demo.

Provides JWT-based auth decorators and a before_request hook that
loads g.user from the token on every request.

When AUTH_ENABLED=false (default), all decorators pass through.
"""

import functools
from datetime import datetime, timezone, timedelta

import jwt
from flask import current_app, g, jsonify, request

PUBLIC_PREFIXES = ('/health', '/api/v1/health', '/auth/')

TOKEN_ALGORITHM = 'HS256'
TOKEN_DEFAULT_TTL = timedelta(hours=24)


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def create_token(payload, ttl=None):
    """Create a signed JWT token.

    Args:
        payload: Dict with user claims (email, name, picture, role, …).
        ttl: Optional timedelta for token lifetime. Defaults to 24 hours.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    claims = {
        **payload,
        'iat': now,
        'exp': now + (ttl or TOKEN_DEFAULT_TTL),
    }
    return jwt.encode(claims, current_app.config['SECRET_KEY'], algorithm=TOKEN_ALGORITHM)


def decode_token(token):
    """Decode and validate a JWT token.

    Returns the payload dict on success, or None if the token is
    invalid, expired, or has a bad signature.
    """
    try:
        return jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=[TOKEN_ALGORITHM],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_token():
    """Extract JWT from Authorization header or cookie."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return request.cookies.get('mirofish_token')


def _validate_email_domain(email):
    """Return True if *email* belongs to the allowed domain."""
    allowed = current_app.config.get('AUTH_ALLOWED_DOMAIN')
    if not allowed:
        return True
    domain = email.split('@')[-1] if '@' in email else ''
    return domain == allowed


def _load_user():
    """Try to populate g.user from the request's JWT token."""
    g.user = None
    token = _extract_token()
    if not token:
        return

    payload = decode_token(token)
    if not payload:
        return

    email = payload.get('email', '')
    if not _validate_email_domain(email):
        return

    g.user = {
        'email': email,
        'name': payload.get('name'),
        'picture': payload.get('picture'),
        'role': payload.get('role', 'viewer'),
    }


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def auth_required(f):
    """Require a valid JWT when AUTH_ENABLED is true.

    Returns 401 JSON if the user is not authenticated.
    When AUTH_ENABLED=false the decorator is a no-op.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config.get('AUTH_ENABLED'):
            return f(*args, **kwargs)

        if not g.get('user'):
            _load_user()

        if not g.get('user'):
            return jsonify({'error': 'Authentication required'}), 401

        return f(*args, **kwargs)
    return decorated


def auth_optional(f):
    """Attach user info to g.user if a valid token is present.

    The request always proceeds regardless of auth state.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not g.get('user'):
            _load_user()
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# App-level integration
# ---------------------------------------------------------------------------

def init_auth_middleware(app):
    """Register a before_request hook that loads g.user on every request.

    Public routes (/health, /auth/*) skip user loading for efficiency.
    """
    @app.before_request
    def _before_request_load_user():
        g.user = None
        if not app.config.get('AUTH_ENABLED'):
            return
        if any(request.path.startswith(p) for p in PUBLIC_PREFIXES):
            return
        _load_user()
