"""
User Management API
CRUD operations for user accounts and roles.
Works in demo mode with in-memory storage when no auth backend is configured.
"""

import threading
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

VALID_ROLES = ['admin', 'editor', 'viewer', 'guest']

_lock = threading.Lock()
_users = {}
_seeded = False


def _seed_demo_users():
    """Populate demo users on first access."""
    global _seeded
    if _seeded:
        return
    _seeded = True
    now = datetime.now(timezone.utc).isoformat()
    demo = [
        {'email': 'admin@intercom.io', 'name': 'Alice Chen', 'role': 'admin', 'last_active': now},
        {'email': 'editor@intercom.io', 'name': 'Bob Martinez', 'role': 'editor', 'last_active': now},
        {'email': 'viewer@intercom.io', 'name': 'Carol Wang', 'role': 'viewer', 'last_active': now},
        {'email': 'guest@intercom.io', 'name': 'Dave Kim', 'role': 'guest', 'last_active': now},
    ]
    for u in demo:
        _users[u['email']] = u


def _get_users():
    with _lock:
        _seed_demo_users()
        return list(_users.values())


@users_bp.route('', methods=['GET'])
def list_users():
    """List all users with roles."""
    return jsonify({'success': True, 'data': _get_users()})


@users_bp.route('/roles', methods=['GET'])
def list_roles():
    """List available roles."""
    roles = [
        {'id': 'admin', 'label': 'Admin', 'description': 'Full access to all features and settings'},
        {'id': 'editor', 'label': 'Editor', 'description': 'Can create and run simulations'},
        {'id': 'viewer', 'label': 'Viewer', 'description': 'Read-only access to simulations and reports'},
        {'id': 'guest', 'label': 'Guest', 'description': 'Limited access, view public content only'},
    ]
    return jsonify({'success': True, 'data': roles})


@users_bp.route('/<email>/role', methods=['PUT'])
def update_role(email):
    """Change a user's role."""
    data = request.get_json() or {}
    new_role = data.get('role', '')

    if new_role not in VALID_ROLES:
        return jsonify({'success': False, 'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400

    with _lock:
        _seed_demo_users()
        user = _users.get(email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        old_role = user['role']
        user['role'] = new_role
        return jsonify({'success': True, 'data': {'email': email, 'old_role': old_role, 'new_role': new_role}})


@users_bp.route('/<email>', methods=['DELETE'])
def remove_user(email):
    """Remove a user's access."""
    with _lock:
        _seed_demo_users()
        user = _users.pop(email, None)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        return jsonify({'success': True, 'data': {'email': email, 'removed': True}})


@users_bp.route('/invite', methods=['POST'])
def invite_user():
    """Invite a new user by email."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    name = (data.get('name') or '').strip()
    role = data.get('role', 'viewer')

    if not email or '@' not in email:
        return jsonify({'success': False, 'error': 'Valid email is required'}), 400

    if role not in VALID_ROLES:
        return jsonify({'success': False, 'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400

    with _lock:
        _seed_demo_users()
        if email in _users:
            return jsonify({'success': False, 'error': 'User already exists'}), 409

        now = datetime.now(timezone.utc).isoformat()
        user = {'email': email, 'name': name or email.split('@')[0].title(), 'role': role, 'last_active': now}
        _users[email] = user
        return jsonify({'success': True, 'data': user}), 201
