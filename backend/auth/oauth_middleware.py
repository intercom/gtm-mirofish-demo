"""
Optional OAuth middleware for protecting the demo in production deployments.
Enable via AUTH_ENABLED=true in .env
"""

import functools
from flask import redirect, request, session, jsonify
from app.config import Config
from auth.audit_log import log_event


def require_auth(f):
    """Decorator to require authentication when AUTH_ENABLED is true."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not Config.AUTH_ENABLED:
            return f(*args, **kwargs)

        if 'user' not in session:
            log_event(
                action='permission_denied',
                actor_email='anonymous',
                target=request.path,
                details={'reason': 'no_session'},
            )
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('/login')

        return f(*args, **kwargs)
    return decorated


def validate_email_domain(email):
    """Check if email belongs to allowed domain."""
    if not email:
        return False
    domain = email.split('@')[-1] if '@' in email else ''
    allowed = domain == Config.AUTH_ALLOWED_DOMAIN
    if not allowed and email:
        log_event(
            action='permission_denied',
            actor_email=email,
            details={'reason': 'invalid_domain', 'domain': domain},
        )
    return allowed
