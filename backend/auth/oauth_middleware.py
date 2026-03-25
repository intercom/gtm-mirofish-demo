"""
Optional OAuth middleware for protecting the demo in production deployments.
Enable via AUTH_ENABLED=true in .env
"""

import functools
from flask import current_app, redirect, request, session, jsonify


def require_auth(f):
    """Decorator to require authentication when AUTH_ENABLED is true."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config.get('AUTH_ENABLED', False):
            return f(*args, **kwargs)

        if 'user' not in session:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            return redirect('/login')

        return f(*args, **kwargs)
    return decorated


def validate_email_domain(email):
    """Check if email belongs to allowed domain."""
    if not email:
        return False
    allowed = current_app.config.get('AUTH_ALLOWED_DOMAIN', '')
    domain = email.split('@')[-1] if '@' in email else ''
    return domain == allowed
