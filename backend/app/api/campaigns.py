"""
Campaigns API
Serves campaign performance data, ROI comparison, and efficiency metrics.
Works in demo mode with built-in mock data when no external data source is configured.
"""

from flask import Blueprint, jsonify, request

campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/api/campaigns')

DEMO_CAMPAIGNS = [
    {
        'id': 'camp-001',
        'name': 'Intercom AI Email Drip',
        'channel': 'email',
        'status': 'active',
        'spend': 42000,
        'revenue': 186000,
        'leads': 840,
        'acquisitions': 68,
    },
    {
        'id': 'camp-002',
        'name': 'Google Ads — Support',
        'channel': 'paid',
        'status': 'active',
        'spend': 85000,
        'revenue': 221000,
        'leads': 1200,
        'acquisitions': 94,
    },
    {
        'id': 'camp-003',
        'name': 'LinkedIn ABM Campaign',
        'channel': 'paid',
        'status': 'active',
        'spend': 62000,
        'revenue': 148000,
        'leads': 520,
        'acquisitions': 41,
    },
    {
        'id': 'camp-004',
        'name': 'SaaStr Booth + Talk',
        'channel': 'events',
        'status': 'completed',
        'spend': 95000,
        'revenue': 310000,
        'leads': 380,
        'acquisitions': 52,
    },
    {
        'id': 'camp-005',
        'name': 'Partner Co-Sell (AWS)',
        'channel': 'partner',
        'status': 'active',
        'spend': 18000,
        'revenue': 92000,
        'leads': 160,
        'acquisitions': 22,
    },
    {
        'id': 'camp-006',
        'name': 'Product Hunt Launch',
        'channel': 'organic',
        'status': 'completed',
        'spend': 5000,
        'revenue': 34000,
        'leads': 620,
        'acquisitions': 38,
    },
    {
        'id': 'camp-007',
        'name': 'Zendesk Displacement SEO',
        'channel': 'organic',
        'status': 'active',
        'spend': 31000,
        'revenue': 87000,
        'leads': 950,
        'acquisitions': 56,
    },
    {
        'id': 'camp-008',
        'name': 'Facebook Retargeting',
        'channel': 'paid',
        'status': 'paused',
        'spend': 28000,
        'revenue': 19000,
        'leads': 310,
        'acquisitions': 12,
    },
    {
        'id': 'camp-009',
        'name': 'Webinar Series Q1',
        'channel': 'events',
        'status': 'completed',
        'spend': 22000,
        'revenue': 64000,
        'leads': 440,
        'acquisitions': 29,
    },
    {
        'id': 'camp-010',
        'name': 'Cold Outbound (SDR)',
        'channel': 'outbound',
        'status': 'active',
        'spend': 74000,
        'revenue': 58000,
        'leads': 280,
        'acquisitions': 18,
    },
]


def _enrich(campaign):
    """Add computed ROI and efficiency fields."""
    spend = campaign['spend']
    revenue = campaign['revenue']
    leads = campaign['leads']
    acquisitions = campaign['acquisitions']
    return {
        **campaign,
        'roi': round((revenue - spend) / spend * 100, 1) if spend else 0,
        'cpl': round(spend / leads, 2) if leads else 0,
        'cpa': round(spend / acquisitions, 2) if acquisitions else 0,
    }


@campaigns_bp.route('', methods=['GET'])
def list_campaigns():
    """List campaigns with optional type/status filter."""
    channel = request.args.get('channel')
    status = request.args.get('status')

    results = DEMO_CAMPAIGNS
    if channel:
        results = [c for c in results if c['channel'] == channel]
    if status:
        results = [c for c in results if c['status'] == status]

    return jsonify({'campaigns': [_enrich(c) for c in results]})


@campaigns_bp.route('/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get a single campaign with cost breakdown."""
    match = next((c for c in DEMO_CAMPAIGNS if c['id'] == campaign_id), None)
    if not match:
        return jsonify({'error': f'Campaign {campaign_id} not found'}), 404
    return jsonify(_enrich(match))


@campaigns_bp.route('/stats', methods=['GET'])
def campaign_stats():
    """Aggregate stats across all campaigns."""
    total_spend = sum(c['spend'] for c in DEMO_CAMPAIGNS)
    total_revenue = sum(c['revenue'] for c in DEMO_CAMPAIGNS)
    enriched = [_enrich(c) for c in DEMO_CAMPAIGNS]
    best = max(enriched, key=lambda c: c['roi'])
    worst = min(enriched, key=lambda c: c['roi'])

    spend_by_channel = {}
    for c in DEMO_CAMPAIGNS:
        spend_by_channel[c['channel']] = spend_by_channel.get(c['channel'], 0) + c['spend']

    return jsonify({
        'total_spend': total_spend,
        'total_revenue': total_revenue,
        'total_roi': round((total_revenue - total_spend) / total_spend * 100, 1),
        'best_campaign': {'name': best['name'], 'roi': best['roi']},
        'worst_campaign': {'name': worst['name'], 'roi': worst['roi']},
        'spend_by_channel': spend_by_channel,
    })


@campaigns_bp.route('/roi-comparison', methods=['GET'])
def roi_comparison():
    """All campaigns ranked by ROI — primary data source for RoiComparison.vue."""
    enriched = [_enrich(c) for c in DEMO_CAMPAIGNS]
    enriched.sort(key=lambda c: c['roi'], reverse=True)
    return jsonify({'campaigns': enriched})


@campaigns_bp.route('/budget-efficiency', methods=['GET'])
def budget_efficiency():
    """Spend efficiency metrics: CPL and CPA by channel."""
    by_channel = {}
    for c in DEMO_CAMPAIGNS:
        ch = c['channel']
        if ch not in by_channel:
            by_channel[ch] = {'spend': 0, 'leads': 0, 'acquisitions': 0}
        by_channel[ch]['spend'] += c['spend']
        by_channel[ch]['leads'] += c['leads']
        by_channel[ch]['acquisitions'] += c['acquisitions']

    efficiency = {}
    for ch, v in by_channel.items():
        efficiency[ch] = {
            'spend': v['spend'],
            'cpl': round(v['spend'] / v['leads'], 2) if v['leads'] else 0,
            'cpa': round(v['spend'] / v['acquisitions'], 2) if v['acquisitions'] else 0,
        }

    return jsonify({'efficiency': efficiency})


@campaigns_bp.route('/attribution/<model>', methods=['GET'])
def attribution(model):
    """Attribution analysis by model (first_touch, last_touch, linear)."""
    valid_models = ('first_touch', 'last_touch', 'linear')
    if model not in valid_models:
        return jsonify({'error': f'Invalid model. Choose from: {", ".join(valid_models)}'}), 400

    enriched = [_enrich(c) for c in DEMO_CAMPAIGNS]
    return jsonify({
        'model': model,
        'campaigns': enriched,
    })
