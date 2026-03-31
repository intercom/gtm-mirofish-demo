"""
Campaign API Blueprint.
Endpoints for listing campaigns, ROI comparison, attribution analysis,
and budget efficiency metrics.
"""

from flask import Blueprint, jsonify, request

from ..services.campaign_generator import get_campaigns
from ..utils.logger import get_logger

logger = get_logger('mirofish.campaigns')

campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/api/v1/campaigns')


# ── Helpers ──────────────────────────────────────────────


def _find_campaign(campaign_id: str):
    """Find a campaign by ID, or None."""
    for c in get_campaigns():
        if c.id == campaign_id:
            return c
    return None


# ── Endpoints ────────────────────────────────────────────


@campaigns_bp.route('', methods=['GET'])
def list_campaigns():
    """
    GET /api/campaigns
    List campaigns with optional type and status filters.

    Query params:
        type   — paid | organic | event | email | partner
        status — active | completed | planned
    """
    campaigns = get_campaigns()

    filter_type = request.args.get('type')
    if filter_type:
        campaigns = [c for c in campaigns if c.type == filter_type]

    filter_status = request.args.get('status')
    if filter_status:
        campaigns = [c for c in campaigns if c.status == filter_status]

    return jsonify({
        'campaigns': [c.to_dict() for c in campaigns],
        'total': len(campaigns),
    })


@campaigns_bp.route('/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """
    GET /api/campaigns/<id>
    Campaign details with cost breakdown and attribution.
    """
    campaign = _find_campaign(campaign_id)
    if not campaign:
        return jsonify({'error': f'Campaign {campaign_id} not found'}), 404
    return jsonify(campaign.to_dict(include_details=True))


@campaigns_bp.route('/stats', methods=['GET'])
def campaign_stats():
    """
    GET /api/campaigns/stats
    Aggregate statistics: total spend, overall ROI, best/worst campaign,
    spend by channel.
    """
    campaigns = get_campaigns()
    if not campaigns:
        return jsonify({'error': 'No campaigns available'}), 404

    total_spend = sum(c.spend_to_date for c in campaigns)
    total_revenue = sum(c.closed_won_value for c in campaigns)
    overall_roi = round((total_revenue - total_spend) / total_spend * 100, 2) if total_spend else 0

    best = max(campaigns, key=lambda c: c.roi_percentage)
    worst = min(campaigns, key=lambda c: c.roi_percentage)

    spend_by_channel: dict[str, float] = {}
    for c in campaigns:
        spend_by_channel[c.channel] = spend_by_channel.get(c.channel, 0) + c.spend_to_date

    return jsonify({
        'total_spend': total_spend,
        'total_revenue': total_revenue,
        'overall_roi': overall_roi,
        'campaign_count': len(campaigns),
        'best_campaign': {'id': best.id, 'name': best.name, 'roi_percentage': best.roi_percentage},
        'worst_campaign': {'id': worst.id, 'name': worst.name, 'roi_percentage': worst.roi_percentage},
        'spend_by_channel': spend_by_channel,
    })


@campaigns_bp.route('/roi-comparison', methods=['GET'])
def roi_comparison():
    """
    GET /api/campaigns/roi-comparison
    All campaigns ranked by ROI percentage (descending).
    """
    campaigns = sorted(get_campaigns(), key=lambda c: c.roi_percentage, reverse=True)
    return jsonify({
        'campaigns': [
            {
                'id': c.id,
                'name': c.name,
                'type': c.type,
                'channel': c.channel,
                'spend': c.spend_to_date,
                'revenue': c.closed_won_value,
                'roi_percentage': c.roi_percentage,
                'leads_generated': c.leads_generated,
            }
            for c in campaigns
        ],
    })


@campaigns_bp.route('/attribution/<model>', methods=['GET'])
def attribution_analysis(model):
    """
    GET /api/campaigns/attribution/<model>
    Attribution analysis by model: first_touch, last_touch, linear, time_decay.
    Returns each campaign's attributed credit under the selected model.
    """
    valid_models = ('first_touch', 'last_touch', 'linear', 'time_decay')
    if model not in valid_models:
        return jsonify({
            'error': f'Invalid attribution model: {model}',
            'valid_models': list(valid_models),
        }), 400

    result = []
    for c in get_campaigns():
        model_attrs = [a for a in c.attributions if a.attribution_model == model]
        total_credit = sum(a.credit_percentage for a in model_attrs)
        opp_count = len(model_attrs)
        result.append({
            'campaign_id': c.id,
            'campaign_name': c.name,
            'channel': c.channel,
            'type': c.type,
            'opportunity_count': opp_count,
            'total_credit': round(total_credit, 1),
            'avg_credit': round(total_credit / opp_count, 1) if opp_count else 0,
        })

    result.sort(key=lambda x: x['total_credit'], reverse=True)
    return jsonify({'model': model, 'attributions': result})


@campaigns_bp.route('/budget-efficiency', methods=['GET'])
def budget_efficiency():
    """
    GET /api/campaigns/budget-efficiency
    Spend efficiency metrics: CPL and CPA grouped by channel.
    """
    by_channel: dict[str, dict] = {}
    for c in get_campaigns():
        ch = c.channel
        if ch not in by_channel:
            by_channel[ch] = {
                'channel': ch,
                'campaigns': 0,
                'total_spend': 0,
                'total_leads': 0,
                'total_opportunities': 0,
                'total_budget': 0,
            }
        bucket = by_channel[ch]
        bucket['campaigns'] += 1
        bucket['total_spend'] += c.spend_to_date
        bucket['total_leads'] += c.leads_generated
        bucket['total_opportunities'] += c.opportunities
        bucket['total_budget'] += c.budget

    channels = []
    for bucket in by_channel.values():
        spend = bucket['total_spend']
        leads = bucket['total_leads']
        opps = bucket['total_opportunities']
        budget = bucket['total_budget']
        channels.append({
            'channel': bucket['channel'],
            'campaigns': bucket['campaigns'],
            'total_spend': spend,
            'total_budget': budget,
            'budget_utilization': round(spend / budget * 100, 1) if budget else 0,
            'total_leads': leads,
            'total_opportunities': opps,
            'cpl': round(spend / leads, 2) if leads else 0,
            'cpa': round(spend / opps, 2) if opps else 0,
        })

    channels.sort(key=lambda x: x['cpl'])
    return jsonify({'channels': channels})
