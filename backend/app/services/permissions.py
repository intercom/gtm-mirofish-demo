"""
Permission-aware API response service.

Computes per-resource permissions based on the current user's role,
and injects a `permissions` dict into API responses so the frontend
knows exactly which actions are allowed.

Role hierarchy: admin > editor > viewer > guest
When AUTH_ENABLED=false (demo mode), defaults to admin.
"""

from flask import session
from ..config import Config


ROLES = ('guest', 'viewer', 'editor', 'admin')
ROLE_RANK = {role: i for i, role in enumerate(ROLES)}

# Per-resource-type permission definitions.
# Each key maps to the minimum role required to perform that action.
RESOURCE_PERMISSIONS = {
    'simulation': {
        'can_view': 'viewer',
        'can_create': 'editor',
        'can_edit': 'editor',
        'can_delete': 'admin',
        'can_start': 'editor',
        'can_stop': 'editor',
    },
    'report': {
        'can_view': 'viewer',
        'can_generate': 'editor',
        'can_delete': 'admin',
        'can_download': 'viewer',
        'can_chat': 'viewer',
    },
    'project': {
        'can_view': 'viewer',
        'can_create': 'editor',
        'can_edit': 'editor',
        'can_delete': 'admin',
        'can_build': 'editor',
    },
    'settings': {
        'can_view': 'viewer',
        'can_edit': 'editor',
        'can_manage': 'admin',
    },
    'scenario': {
        'can_view': 'viewer',
        'can_simulate': 'editor',
    },
}


def get_current_role():
    """Return the current user's role from session, or 'admin' in demo mode."""
    if not Config.AUTH_ENABLED:
        return 'admin'
    user = session.get('user')
    if not user:
        return 'guest'
    return user.get('role', 'viewer')


def compute_permissions(resource_type):
    """
    Compute a permissions dict for the given resource type
    based on the current user's role.

    Returns e.g. {"can_view": True, "can_edit": True, "can_delete": False}
    """
    role = get_current_role()
    role_rank = ROLE_RANK.get(role, 0)
    perms = RESOURCE_PERMISSIONS.get(resource_type, {})
    return {
        action: role_rank >= ROLE_RANK.get(min_role, 0)
        for action, min_role in perms.items()
    }


def inject_permissions(response_data, resource_type):
    """
    Add a 'permissions' field to a response data dict.

    Usage in an endpoint:
        data = project.to_dict()
        return jsonify({"success": True, "data": inject_permissions(data, 'project')})
    """
    if isinstance(response_data, dict):
        response_data['permissions'] = compute_permissions(resource_type)
    return response_data


def inject_permissions_list(items, resource_type):
    """
    Add 'permissions' to each item in a list response.

    Usage:
        data = [p.to_dict() for p in projects]
        return jsonify({"success": True, "data": inject_permissions_list(data, 'project')})
    """
    perms = compute_permissions(resource_type)
    for item in items:
        if isinstance(item, dict):
            item['permissions'] = perms
    return items
