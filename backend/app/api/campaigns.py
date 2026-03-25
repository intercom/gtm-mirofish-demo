"""
Campaign Analytics API
Provides attribution model comparison and campaign performance data.
Works in demo/mock mode when no real campaign data is available.
"""

from flask import Blueprint, jsonify

from ..utils.logger import get_logger

logger = get_logger('mirofish.campaigns')

campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/api/campaigns')

ATTRIBUTION_MODELS = ['first_touch', 'last_touch', 'linear', 'time_decay', 'position_based']

MODEL_DESCRIPTIONS = {
    'first_touch': 'Credits the campaign that first generated the lead.',
    'last_touch': 'Credits the final campaign before conversion.',
    'linear': 'Splits credit equally across all touchpoints.',
    'time_decay': 'Weights recent touchpoints more heavily.',
    'position_based': '40% to first touch, 40% to last touch, 20% split among middle.',
}

MOCK_CAMPAIGNS = [
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


@campaigns_bp.route('/attribution', methods=['GET'])
def get_attribution_comparison():
    """Return attribution credit percentages across all models for each campaign."""
    campaigns = MOCK_CAMPAIGNS
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
