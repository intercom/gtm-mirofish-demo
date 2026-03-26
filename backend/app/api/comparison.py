"""
Comparison API — comparative chart overlay data for multiple simulation runs.

Returns time-series and summary metrics for side-by-side run analysis.
Always works in demo/mock mode when no real simulation data is available.
"""

import random
from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.api.comparison')

comparison_bp = Blueprint('comparison', __name__, url_prefix='/api/v1/comparison')


def _generate_demo_series(run_id, num_rounds, seed):
    """Generate plausible demo time-series data for one run."""
    rng = random.Random(seed)
    actions_per_round = []
    sentiment_per_round = []
    engagement_per_round = []

    cumulative_actions = 0
    base_actions = rng.randint(8, 18)
    base_sentiment = rng.uniform(-0.1, 0.2)
    base_engagement = rng.uniform(15, 35)

    for r in range(1, num_rounds + 1):
        growth = 1 + (r / num_rounds) * rng.uniform(0.3, 0.8)
        round_actions = max(1, int(base_actions * growth + rng.gauss(0, 2)))
        cumulative_actions += round_actions

        sentiment_drift = rng.gauss(0, 0.05)
        base_sentiment = max(-0.6, min(0.6, base_sentiment + sentiment_drift))

        eng_drift = rng.gauss(0, 1.5)
        base_engagement = max(5, min(60, base_engagement + eng_drift))

        actions_per_round.append({
            'round': r,
            'actions': round_actions,
            'cumulative': cumulative_actions,
        })
        sentiment_per_round.append({
            'round': r,
            'sentiment': round(base_sentiment, 3),
        })
        engagement_per_round.append({
            'round': r,
            'engagement_rate': round(base_engagement, 1),
        })

    return {
        'run_id': run_id,
        'rounds': num_rounds,
        'actions_timeline': actions_per_round,
        'sentiment_timeline': sentiment_per_round,
        'engagement_timeline': engagement_per_round,
        'summary': {
            'total_actions': cumulative_actions,
            'avg_sentiment': round(
                sum(s['sentiment'] for s in sentiment_per_round) / num_rounds, 3
            ),
            'avg_engagement': round(
                sum(e['engagement_rate'] for e in engagement_per_round) / num_rounds, 1
            ),
            'peak_actions_round': max(
                actions_per_round, key=lambda x: x['actions']
            )['round'],
        },
    }


DEMO_RUNS = {
    'demo-aggressive': {
        'id': 'demo-aggressive',
        'name': 'Aggressive Pricing',
        'scenario': 'Zendesk Displacement',
        'agent_count': 25,
        'rounds': 20,
    },
    'demo-conservative': {
        'id': 'demo-conservative',
        'name': 'Conservative Approach',
        'scenario': 'Zendesk Displacement',
        'agent_count': 25,
        'rounds': 20,
    },
    'demo-product-led': {
        'id': 'demo-product-led',
        'name': 'Product-Led Growth',
        'scenario': 'AI Agent Launch',
        'agent_count': 30,
        'rounds': 20,
    },
}


@comparison_bp.route('/runs', methods=['GET'])
def list_comparable_runs():
    """List runs available for comparison (demo data when no real runs)."""
    runs = list(DEMO_RUNS.values())
    return jsonify({'success': True, 'data': {'runs': runs}})


@comparison_bp.route('/data', methods=['POST'])
def get_comparison_data():
    """
    Return overlay-ready time-series data for selected runs.

    Request JSON:
        {
            "run_ids": ["demo-aggressive", "demo-conservative"],
            "metric": "actions" | "sentiment" | "engagement"  (optional, default all)
        }

    Response:
        {
            "success": true,
            "data": {
                "runs": [ { run_id, name, actions_timeline, sentiment_timeline, ... } ],
                "metrics": ["actions", "sentiment", "engagement"]
            }
        }
    """
    body = request.get_json() or {}
    run_ids = body.get('run_ids', [])

    if not run_ids or not isinstance(run_ids, list):
        return jsonify({
            'success': False,
            'error': 'Provide run_ids as a non-empty array',
        }), 400

    if len(run_ids) > 5:
        return jsonify({
            'success': False,
            'error': 'Maximum 5 runs can be compared at once',
        }), 400

    requested_metric = body.get('metric')
    valid_metrics = {'actions', 'sentiment', 'engagement'}
    metrics = [requested_metric] if requested_metric in valid_metrics else sorted(valid_metrics)

    results = []
    for i, run_id in enumerate(run_ids):
        meta = DEMO_RUNS.get(run_id)
        if meta:
            name = meta['name']
            num_rounds = meta['rounds']
        else:
            name = f'Run {run_id[:8]}'
            num_rounds = 20

        seed = hash(run_id) & 0xFFFFFFFF
        series = _generate_demo_series(run_id, num_rounds, seed)
        series['name'] = name

        results.append(series)

    return jsonify({
        'success': True,
        'data': {
            'runs': results,
            'metrics': metrics,
        },
    })
