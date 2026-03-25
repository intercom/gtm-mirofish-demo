"""
Audit log API — read-only access to security event history.
"""

from flask import Blueprint, jsonify, request, session
from app.config import Config
from auth.audit_log import read_log, enforce_retention

audit_bp = Blueprint('audit', __name__, url_prefix='/api/v1/auth')


def _is_admin() -> bool:
    """Check if the current session user has admin role."""
    if not Config.AUTH_ENABLED:
        return True
    user = session.get('user', {})
    return user.get('role') == 'admin'


@audit_bp.route('/audit-log', methods=['GET'])
def get_audit_log():
    """Return recent audit log entries.

    Query params:
        limit (int): Max entries to return, default 50, max 500.
        action (str): Filter by action type.

    Returns 403 if auth is enabled and user is not admin.
    """
    if Config.AUTH_ENABLED and not _is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    limit = min(int(request.args.get('limit', 50)), 500)
    action = request.args.get('action')

    enforce_retention()
    entries = read_log(limit=limit, action=action)

    return jsonify({'entries': entries, 'count': len(entries)})
