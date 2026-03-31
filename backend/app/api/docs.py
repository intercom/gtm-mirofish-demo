"""
API Documentation — auto-discovers all registered Flask routes.

Returns route metadata (path, method, description, category) by inspecting
Flask's url_map at runtime, so the docs stay in sync with the code automatically.
"""

import re

from flask import Blueprint, current_app, jsonify

docs_bp = Blueprint('docs', __name__, url_prefix='/api/v1/docs')

_SKIP_METHODS = {'HEAD', 'OPTIONS'}
_SKIP_PATHS = {'/api/csrf-token', '/api/v1/docs/routes'}

_CATEGORY_MAP = {
    'core': 'Core',
    'aggregation': 'Aggregation',
    'agent_memory': 'Agent Memory',
    'agent_prompts': 'Agent Prompts',
    'agents': 'Agents',
    'analytics': 'Analytics',
    'api_keys': 'API Keys',
    'attribution': 'Attribution',
    'audit': 'Audit',
    'audit_log': 'Audit Log',
    'auth': 'Auth',
    'batch': 'Batch',
    'beliefs': 'Beliefs',
    'branches': 'Branches',
    'cache': 'Cache',
    'campaigns': 'Campaigns',
    'comparison': 'Comparison',
    'cost_model': 'Cost Model',
    'cpq': 'CPQ',
    'data_pipeline': 'Data Pipeline',
    'deals': 'Deals',
    'debate': 'Debate',
    'decisions': 'Decisions',
    'errors': 'Error Tracking',
    'graph': 'Knowledge Graph',
    'gtm': 'GTM Scenarios',
    'gtm_dashboard': 'GTM Dashboard',
    'health': 'Health',
    'insights': 'Insights',
    'memory': 'Memory',
    'memory_config': 'Memory Config',
    'memory_transfer': 'Memory Transfer',
    'metrics': 'Metrics',
    'oauth': 'OAuth',
    'orders': 'Order-to-Cash',
    'personality': 'Personality',
    'personas': 'Personas',
    'pipeline': 'Pipeline',
    'predictions': 'Predictions',
    'reconciliation': 'Reconciliation',
    'report': 'Report',
    'report_builder': 'Report Builder',
    'revenue': 'Revenue',
    'salesforce': 'Salesforce CRM',
    'services': 'Services',
    'sessions': 'Sessions',
    'settings': 'Settings',
    'simulation': 'Simulation',
    'team': 'Team',
    'templates': 'Templates',
    'temporal_memory': 'Temporal Memory',
    'users': 'Users',
}


def _to_rest_path(flask_path):
    """Convert Flask path params (<type:name> or <name>) to :name format."""
    return re.sub(r'<(?:\w+:)?(\w+)>', r':\1', flask_path)


def _first_doc_line(func):
    """Return first meaningful line from a view function's docstring."""
    if not func or not func.__doc__:
        return ''
    for line in func.__doc__.strip().split('\n'):
        text = line.strip()
        if text and not re.match(r'^(GET|POST|PUT|PATCH|DELETE)\s+/', text):
            return text
    return ''


@docs_bp.route('/routes', methods=['GET'])
def list_routes():
    """List all registered API routes with their HTTP methods and descriptions."""
    routes = []

    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue

        path = rule.rule
        if path in _SKIP_PATHS:
            continue
        if not (path.startswith('/api') or path.startswith('/health') or path.startswith('/auth')):
            continue

        methods = sorted(rule.methods - _SKIP_METHODS)
        if not methods:
            continue

        view_func = current_app.view_functions.get(rule.endpoint)
        description = _first_doc_line(view_func)

        parts = rule.endpoint.split('.')
        bp_name = parts[0] if len(parts) > 1 else 'core'
        category = _CATEGORY_MAP.get(bp_name, bp_name.replace('_', ' ').title())

        display_path = _to_rest_path(path)

        for method in methods:
            routes.append({
                'method': method,
                'path': display_path,
                'description': description,
                'category': category,
            })

    routes.sort(key=lambda r: (r['category'], r['path'], r['method']))
    return jsonify({'success': True, 'data': routes, 'count': len(routes)})
