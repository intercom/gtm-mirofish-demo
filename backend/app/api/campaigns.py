"""
Campaigns API
Serves campaign performance data, ROI comparison, efficiency metrics,
and attribution model comparison.
Works in demo mode with built-in mock data when no external data source is configured.
"""

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.campaigns')

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

ATTRIBUTION_MODELS = ['first_touch', 'last_touch', 'linear', 'time_decay', 'position_based']

MODEL_DESCRIPTIONS = {
    'first_touch': 'Credits the campaign that first generated the lead.',
    'last_touch': 'Credits the final campaign before conversion.',
    'linear': 'Splits credit equally across all touchpoints.',
    'time_decay': 'Weights recent touchpoints more heavily.',
    'position_based': '40% to first touch, 40% to last touch, 20% split among middle.',
}

MOCK_ATTRIBUTION_CAMPAIGNS = [
    {'id': 'camp-1', 'name': 'Google Ads — Brand Terms', 'type': 'paid', 'channel': 'search', 'total_revenue': 284000},
    {'id': 'camp-2', 'name': 'Webinar Series Q1', 'type': 'event', 'channel': 'webinar', 'total_revenue': 196000},
    {'id': 'camp-3', 'name': 'LinkedIn ABM Campaign', 'type': 'paid', 'channel': 'social', 'total_revenue': 152000},
    {'id': 'camp-4', 'name': 'Email Nurture Sequence', 'type': 'email', 'channel': 'email', 'total_revenue': 118000},
    {'id': 'camp-5', 'name': 'Content Syndication', 'type': 'organic', 'channel': 'content', 'total_revenue': 87000},
    {'id': 'camp-6', 'name': 'Partner Co-Marketing', 'type': 'partner', 'channel': 'partner', 'total_revenue': 63000},
]

MOCK_ATTRIBUTION = {
    'camp-1': {'first_touch': 38.2, 'last_touch': 22.1, 'linear': 28.5, 'time_decay': 24.8, 'position_based': 30.1},
    'camp-2': {'first_touch': 12.4, 'last_touch': 28.7, 'linear': 20.3, 'time_decay': 25.6, 'position_based': 20.5},
    'camp-3': {'first_touch': 21.6, 'last_touch': 14.3, 'linear': 18.2, 'time_decay': 16.1, 'position_based': 17.9},
    'camp-4': {'first_touch': 8.1, 'last_touch': 19.8, 'linear': 14.6, 'time_decay': 17.2, 'position_based': 13.9},
    'camp-5': {'first_touch': 15.3, 'last_touch': 6.2, 'linear': 10.8, 'time_decay': 8.4, 'position_based': 10.7},
    'camp-6': {'first_touch': 4.4, 'last_touch': 8.9, 'linear': 7.6, 'time_decay': 7.9, 'position_based': 6.9},
}


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


def _compute_recommendation(attribution_data, campaigns):
    """Determine which model is most appropriate based on data patterns."""
    max_variance = 0
    max_variance_campaign = None
    for camp in campaigns:
        credits = attribution_data[camp['id']]
        values = list(credits.values())
        variance = max(values) - min(values)
        if variance > max_variance:
            max_variance = variance
            max_variance_campaign = camp['name']

    if max_variance > 25:
        return {
            'model': 'position_based',
            'reason': (
                f'High attribution variance detected ({max_variance:.1f}pp spread on '
                f'"{max_variance_campaign}"). Position-based balances first and last '
                'touch while acknowledging middle interactions.'
            ),
        }
    elif max_variance > 15:
        return {
            'model': 'time_decay',
            'reason': (
                'Moderate variance across models suggests a multi-touch journey. '
                'Time-decay rewards recency while crediting earlier touchpoints.'
            ),
        }
    else:
        return {
            'model': 'linear',
            'reason': (
                'Low variance across models indicates evenly distributed touchpoints. '
                'Linear attribution fairly represents all campaign contributions.'
            ),
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


@campaigns_bp.route('/attribution', methods=['GET'])
def get_attribution_comparison():
    """Return attribution credit percentages across all models for each campaign."""
    campaigns = MOCK_ATTRIBUTION_CAMPAIGNS
    attribution = MOCK_ATTRIBUTION
    recommendation = _compute_recommendation(attribution, campaigns)

    return jsonify({
        'success': True,
        'data': {
            'campaigns': campaigns,
            'models': ATTRIBUTION_MODELS,
            'model_descriptions': MODEL_DESCRIPTIONS,
            'attribution': attribution,
            'recommendation': recommendation,
        },
    })


@campaigns_bp.route('/attribution/<model>', methods=['GET'])
def attribution_by_model(model):
    """Attribution analysis by model (first_touch, last_touch, linear, time_decay, position_based)."""
    if model not in ATTRIBUTION_MODELS:
        return jsonify({'error': f'Invalid model. Choose from: {", ".join(ATTRIBUTION_MODELS)}'}), 400

    enriched = [_enrich(c) for c in DEMO_CAMPAIGNS]
    return jsonify({
        'model': model,
        'campaigns': enriched,
    })
