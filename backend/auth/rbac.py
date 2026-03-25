"""
Role-Based Access Control (RBAC) model.

Defines roles, permissions, and the mapping between them.
Roles are hierarchical: admin > editor > viewer > guest.
"""

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(str, Enum):
    VIEW_SIMULATIONS = "view_simulations"
    CREATE_SIMULATIONS = "create_simulations"
    EDIT_SIMULATIONS = "edit_simulations"
    DELETE_SIMULATIONS = "delete_simulations"
    VIEW_REPORTS = "view_reports"
    CREATE_REPORTS = "create_reports"
    MANAGE_AGENTS = "manage_agents"
    MANAGE_TEMPLATES = "manage_templates"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_USERS = "manage_users"
    MANAGE_API_KEYS = "manage_api_keys"


# Hierarchy order (higher index = more privileged)
ROLE_HIERARCHY = [Role.GUEST, Role.VIEWER, Role.EDITOR, Role.ADMIN]

ROLE_PERMISSIONS = {
    Role.GUEST: {
        Permission.VIEW_SIMULATIONS,
        Permission.VIEW_REPORTS,
    },
    Role.VIEWER: {
        Permission.VIEW_SIMULATIONS,
        Permission.VIEW_REPORTS,
    },
    Role.EDITOR: {
        Permission.VIEW_SIMULATIONS,
        Permission.CREATE_SIMULATIONS,
        Permission.EDIT_SIMULATIONS,
        Permission.DELETE_SIMULATIONS,
        Permission.VIEW_REPORTS,
        Permission.CREATE_REPORTS,
        Permission.MANAGE_AGENTS,
        Permission.MANAGE_TEMPLATES,
    },
    Role.ADMIN: set(Permission),
}

DEFAULT_ROLE = Role.VIEWER


def role_has_permission(role, permission):
    """Check if a role grants a specific permission."""
    if isinstance(role, str):
        role = Role(role)
    if isinstance(permission, str):
        permission = Permission(permission)
    return permission in ROLE_PERMISSIONS.get(role, set())


def role_at_least(user_role, required_role):
    """Check if user_role is equal to or higher than required_role in hierarchy."""
    if isinstance(user_role, str):
        user_role = Role(user_role)
    if isinstance(required_role, str):
        required_role = Role(required_role)
    return ROLE_HIERARCHY.index(user_role) >= ROLE_HIERARCHY.index(required_role)


def get_permissions_for_role(role):
    """Return the set of permission strings for a given role."""
    if isinstance(role, str):
        role = Role(role)
    return {p.value for p in ROLE_PERMISSIONS.get(role, set())}


def get_all_roles():
    """Return all roles with their permissions, ordered by hierarchy."""
    return [
        {
            "name": role.value,
            "permissions": sorted(p.value for p in ROLE_PERMISSIONS[role]),
            "level": idx,
        }
        for idx, role in enumerate(ROLE_HIERARCHY)
    ]
