"""
Salesforce CRM API — mock data for GTM dashboard visualizations.

Returns simulated Salesforce-style CRM data (accounts, pipeline, health scores)
so the frontend can render the Salesforce overview dashboard without a real
Salesforce connection.
"""

from flask import Blueprint, jsonify

salesforce_bp = Blueprint('salesforce', __name__, url_prefix='/api/salesforce')

MOCK_STATS = {
    'total_accounts': 247,
    'total_arr': 18_400_000,
    'avg_health_score': 72,
    'pipeline_value': 6_350_000,
    'industry_breakdown': [
        {'industry': 'SaaS', 'count': 78},
        {'industry': 'Fintech', 'count': 52},
        {'industry': 'Healthcare', 'count': 38},
        {'industry': 'E-commerce', 'count': 34},
        {'industry': 'Media', 'count': 24},
        {'industry': 'Other', 'count': 21},
    ],
    'stage_distribution': [
        {'stage': 'Prospecting', 'count': 42},
        {'stage': 'Qualification', 'count': 35},
        {'stage': 'Proposal', 'count': 28},
        {'stage': 'Negotiation', 'count': 19},
        {'stage': 'Closed Won', 'count': 64},
        {'stage': 'Closed Lost', 'count': 17},
    ],
}


@salesforce_bp.route('/stats', methods=['GET'])
def get_stats():
    """Return aggregate Salesforce CRM statistics for the overview dashboard."""
    return jsonify({'success': True, 'data': MOCK_STATS})
