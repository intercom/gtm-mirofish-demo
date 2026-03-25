"""
Audit Log API
Stores and serves security-relevant audit trail entries.
Supports filtering by action, user, date range, and text search.
"""

import csv
import hashlib
import io
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, Response

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

# In-memory audit log storage (newest first on retrieval)
_audit_entries = []

# Valid action types for filtering
ACTION_TYPES = [
    'login', 'logout',
    'simulation_created', 'simulation_deleted',
    'report_generated',
    'graph_built',
    'settings_updated',
    'role_changed', 'user_removed',
    'key_created', 'key_revoked',
    'permission_denied',
]


def record_event(action, actor='system', resource_type=None, resource_id=None,
                 details=None, ip_address=None):
    """Append an audit entry. Call from anywhere in the backend."""
    entry = {
        'id': hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}-{action}-{actor}".encode()
        ).hexdigest()[:16],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': action,
        'actor': actor,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'details': details or '',
        'ip_address': ip_address or '',
    }
    _audit_entries.append(entry)
    return entry


def _generate_demo_entries():
    """Generate realistic demo audit entries for display when log is empty."""
    now = datetime.now(timezone.utc)
    demos = [
        ('login', 'alice@intercom.io', 'user', 'u-001',
         'SSO login via Google', 0),
        ('simulation_created', 'alice@intercom.io', 'simulation', 'sim-4f2a',
         'Scenario: Competitive positioning analysis', 2),
        ('graph_built', 'system', 'graph', 'g-8bc1',
         'Knowledge graph built from seed text (342 nodes)', 5),
        ('settings_updated', 'bob@intercom.io', 'settings', None,
         'Changed LLM provider to Anthropic', 18),
        ('report_generated', 'alice@intercom.io', 'report', 'rpt-12e0',
         'Exported simulation report as PDF', 30),
        ('login', 'carol@intercom.io', 'user', 'u-003',
         'SSO login via Google', 45),
        ('simulation_created', 'bob@intercom.io', 'simulation', 'sim-7d9f',
         'Scenario: Enterprise expansion GTM', 60),
        ('permission_denied', 'guest@external.com', 'settings', None,
         'Attempted admin settings access', 75),
        ('role_changed', 'alice@intercom.io', 'user', 'u-004',
         'Changed dave@intercom.io from viewer to editor', 90),
        ('key_created', 'bob@intercom.io', 'api_key', 'key-a1',
         'Created API key for CI integration', 120),
        ('simulation_deleted', 'alice@intercom.io', 'simulation', 'sim-2c01',
         'Removed stale simulation run', 180),
        ('logout', 'carol@intercom.io', 'user', 'u-003',
         'Session ended', 200),
        ('graph_built', 'system', 'graph', 'g-ef42',
         'Knowledge graph rebuilt (518 nodes, 1204 edges)', 240),
        ('login', 'bob@intercom.io', 'user', 'u-002',
         'SSO login via Okta', 300),
        ('report_generated', 'bob@intercom.io', 'report', 'rpt-55a3',
         'Generated competitive analysis report', 360),
        ('settings_updated', 'alice@intercom.io', 'settings', None,
         'Updated simulation defaults: 300 agents, 72h', 420),
        ('simulation_created', 'carol@intercom.io', 'simulation', 'sim-bb10',
         'Scenario: Product-led growth messaging test', 500),
        ('key_revoked', 'alice@intercom.io', 'api_key', 'key-old',
         'Revoked expired staging API key', 600),
        ('login', 'dave@intercom.io', 'user', 'u-004',
         'SSO login via Google', 720),
        ('report_generated', 'carol@intercom.io', 'report', 'rpt-91c7',
         'Exported agent influence network as CSV', 900),
    ]

    entries = []
    for action, actor, res_type, res_id, detail, minutes_ago in demos:
        ts = now - timedelta(minutes=minutes_ago)
        entry_id = hashlib.sha256(
            f"demo-{action}-{actor}-{minutes_ago}".encode()
        ).hexdigest()[:16]
        entries.append({
            'id': entry_id,
            'timestamp': ts.isoformat(),
            'action': action,
            'actor': actor,
            'resource_type': res_type,
            'resource_id': res_id or '',
            'details': detail,
            'ip_address': '10.0.0.1',
        })
    return entries


def _get_entries():
    """Return real entries if any exist, otherwise demo data."""
    if _audit_entries:
        return list(_audit_entries)
    return _generate_demo_entries()


def _filter_entries(entries, args):
    """Apply query-string filters to an entry list."""
    action = args.get('action')
    if action:
        entries = [e for e in entries if e['action'] == action]

    user = args.get('user')
    if user:
        q = user.lower()
        entries = [e for e in entries if q in e['actor'].lower()]

    since = args.get('since')
    if since:
        entries = [e for e in entries if e['timestamp'] >= since]

    until = args.get('until')
    if until:
        entries = [e for e in entries if e['timestamp'] <= until]

    search = args.get('search')
    if search:
        q = search.lower()
        entries = [
            e for e in entries
            if q in (e.get('resource_type') or '').lower()
            or q in (e.get('resource_id') or '').lower()
            or q in (e.get('details') or '').lower()
        ]

    return entries


@audit_bp.route('/logs', methods=['GET'])
def get_audit_logs():
    """
    GET /api/audit/logs
    Query params: action, user, since, until, search, limit, offset
    """
    entries = _get_entries()
    entries = _filter_entries(entries, request.args)

    # Sort newest-first
    entries.sort(key=lambda e: e['timestamp'], reverse=True)

    total = len(entries)
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    page = entries[offset:offset + limit]

    return jsonify({
        'success': True,
        'data': {
            'logs': page,
            'total': total,
            'limit': limit,
            'offset': offset,
            'action_types': ACTION_TYPES,
        },
    })


@audit_bp.route('/logs/export', methods=['GET'])
def export_audit_csv():
    """
    GET /api/audit/logs/export
    Same filters as /logs but returns CSV download.
    """
    entries = _get_entries()
    entries = _filter_entries(entries, request.args)
    entries.sort(key=lambda e: e['timestamp'], reverse=True)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Timestamp', 'Action', 'User', 'Resource Type',
                     'Resource ID', 'Details', 'IP Address'])
    for e in entries:
        writer.writerow([
            e['timestamp'], e['action'], e['actor'],
            e.get('resource_type', ''), e.get('resource_id', ''),
            e.get('details', ''), e.get('ip_address', ''),
        ])

    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=audit_log.csv'},
    )
