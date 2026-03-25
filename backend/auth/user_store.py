"""
File-based user store for RBAC.

Stores user records with roles in backend/data/users.json.
First user to be added automatically receives the admin role.
Thread-safe via file locking pattern (read-modify-write with atomicity).
"""

import json
import os
import threading
from datetime import datetime

from .rbac import Role, DEFAULT_ROLE, get_permissions_for_role

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

_lock = threading.Lock()


def _read_store():
    """Read the users file, returning the parsed dict."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        return {"users": []}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_store(data):
    """Write the users dict back to disk atomically."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = USERS_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_FILE)


def get_user(email):
    """Get a user record by email, or None if not found."""
    store = _read_store()
    for u in store["users"]:
        if u["email"] == email:
            return u
    return None


def upsert_user(email, name=None, picture_url=None, role=None):
    """
    Create or update a user. First user auto-gets admin role.

    Returns the user dict (with permissions included).
    """
    now = datetime.utcnow().isoformat() + "Z"

    with _lock:
        store = _read_store()
        existing = None
        for u in store["users"]:
            if u["email"] == email:
                existing = u
                break

        if existing:
            if name:
                existing["name"] = name
            if picture_url:
                existing["picture_url"] = picture_url
            if role:
                existing["role"] = role if isinstance(role, str) else role.value
            existing["last_login"] = now
            _write_store(store)
            return _enrich(existing)

        # New user — first user gets admin, others get default role
        is_first = len(store["users"]) == 0
        assigned_role = Role.ADMIN.value if is_first else (role or DEFAULT_ROLE.value)
        if not isinstance(assigned_role, str):
            assigned_role = assigned_role.value

        user = {
            "email": email,
            "name": name or email.split("@")[0],
            "picture_url": picture_url or "",
            "role": assigned_role,
            "created_at": now,
            "last_login": now,
        }
        store["users"].append(user)
        _write_store(store)
        return _enrich(user)


def set_user_role(email, new_role):
    """Change a user's role. Returns updated user or None if not found."""
    if isinstance(new_role, Role):
        new_role = new_role.value

    with _lock:
        store = _read_store()
        for u in store["users"]:
            if u["email"] == email:
                u["role"] = new_role
                _write_store(store)
                return _enrich(u)
    return None


def remove_user(email):
    """Remove a user. Returns True if removed, False if not found."""
    with _lock:
        store = _read_store()
        before = len(store["users"])
        store["users"] = [u for u in store["users"] if u["email"] != email]
        if len(store["users"]) < before:
            _write_store(store)
            return True
    return False


def list_users():
    """List all users with enriched permission data."""
    store = _read_store()
    return [_enrich(u) for u in store["users"]]


def _enrich(user):
    """Add computed permissions list to a user dict (non-destructive copy)."""
    enriched = dict(user)
    enriched["permissions"] = sorted(get_permissions_for_role(user["role"]))
    return enriched
