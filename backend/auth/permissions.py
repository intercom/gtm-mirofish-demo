"""
Permission checking middleware for role-based access control.

Provides decorators to protect API routes based on user roles and granular permissions.
When AUTH_ENABLED is false, all checks are bypassed for demo/development mode.

Role hierarchy: admin > editor > viewer > guest
"""

import functools
from flask import g, jsonify, request
from app.config import Config


# --- Role hierarchy (higher number = more privilege) ---

ROLE_LEVELS = {
    'guest': 1,
    'viewer': 2,
    'editor': 3,
    'admin': 4,
}

# --- Permission-to-minimum-role mapping ---

ROLE_PERMISSIONS = {
    'admin': {
        'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
        'view_reports', 'create_reports',
        'manage_agents', 'manage_templates',
        'manage_settings', 'manage_users',
    },
    'editor': {
        'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
        'view_reports', 'create_reports',
        'manage_agents', 'manage_templates',
    },
    'viewer': {
        'view_simulations', 'view_reports',
    },
    'guest': {
        'view_simulations', 'view_reports',
    },
}


def _get_user_role():
    """Return the current user's role from g.user, defaulting to 'guest'."""
    user = getattr(g, 'user', None)
    if not user:
        return 'guest'
    return user.get('role', 'guest')


def _get_user_permissions():
    """Return the set of permissions for the current user's role."""
    role = _get_user_role()
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS['guest'])


def has_role(required_role):
    """Check if current user meets the minimum role level."""
    user_level = ROLE_LEVELS.get(_get_user_role(), 0)
    required_level = ROLE_LEVELS.get(required_role, 0)
    return user_level >= required_level


def has_permission(permission):
    """Check if current user has a specific permission."""
    return permission in _get_user_permissions()


def requires_role(role):
    """Decorator that checks the user has the specified role or higher.

    Usage:
        @requires_role('editor')
        def create_simulation():
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            if not Config.AUTH_ENABLED:
                return f(*args, **kwargs)

            if not has_role(role):
                user_role = _get_user_role()
                return jsonify({
                    'error': f'Insufficient role: requires {role} or higher, you have {user_role}',
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator


def requires_permission(permission):
    """Decorator that checks the user has a specific permission.

    Usage:
        @requires_permission('create_simulations')
        def start_simulation():
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            if not Config.AUTH_ENABLED:
                return f(*args, **kwargs)

            if not has_permission(permission):
                user_role = _get_user_role()
                return jsonify({
                    'error': f'Permission denied: {permission} not granted for role {user_role}',
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
