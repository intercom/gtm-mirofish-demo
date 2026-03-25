"""
Branch Comparison API
Provides branch comparison data for simulation branching scenarios.
Returns mock/demo data when no real branching backend is configured.
"""

import math
import random

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.branches')

branches_bp = Blueprint('branches', __name__, url_prefix='/api/v1/branches')


def _generate_mock_timeline(num_rounds, branch_point, modification, seed):
    """Generate a realistic mock timeline for a branch."""
    rng = random.Random(seed)

    timeline = []
    base_sentiment = 0.1
    base_engagement = 0.4

    for r in range(1, num_rounds + 1):
        noise = rng.gauss(0, 0.04)

        if r <= branch_point:
            sentiment = base_sentiment + 0.02 * r + noise
            engagement = base_engagement + 0.01 * r + noise * 0.5
            actions = int(12 + r * 1.5 + rng.randint(-2, 2))
        else:
            offset = r - branch_point
            if modification == 'add_agent':
                sentiment = base_sentiment + 0.03 * r + 0.02 * offset + noise
                engagement = base_engagement + 0.02 * r + 0.03 * offset + noise * 0.5
                actions = int(15 + r * 2.0 + offset * 1.5 + rng.randint(-2, 3))
            elif modification == 'inject_event':
                spike = 0.15 * math.exp(-0.3 * offset)
                sentiment = base_sentiment + 0.02 * r + spike + noise
                engagement = base_engagement + 0.015 * r + spike * 0.8 + noise * 0.5
                actions = int(14 + r * 1.8 + rng.randint(-2, 4))
            elif modification == 'change_personality':
                sentiment = base_sentiment + 0.01 * r - 0.01 * offset + noise
                engagement = base_engagement + 0.012 * r + 0.005 * offset + noise * 0.5
                actions = int(13 + r * 1.6 + rng.randint(-2, 2))
            elif modification == 'remove_agent':
                sentiment = base_sentiment + 0.025 * r - 0.005 * offset + noise
                engagement = base_engagement + 0.008 * r - 0.01 * offset + noise * 0.5
                actions = int(10 + r * 1.2 - offset * 0.5 + rng.randint(-2, 2))
            else:
                sentiment = base_sentiment + 0.02 * r + noise
                engagement = base_engagement + 0.01 * r + noise * 0.5
                actions = int(12 + r * 1.5 + rng.randint(-2, 2))

        sentiment = max(-1.0, min(1.0, sentiment))
        engagement = max(0.0, min(1.0, engagement))
        actions = max(1, actions)

        timeline.append({
            'round': r,
            'sentiment': round(sentiment, 3),
            'engagement': round(engagement, 3),
            'actions': actions,
        })

    return timeline


def _compute_metrics(timeline, branch_point):
    """Compute summary metrics from a branch timeline."""
    if not timeline:
        return {}

    post_branch = [t for t in timeline if t['round'] > branch_point]
    all_sentiments = [t['sentiment'] for t in timeline]
    all_engagements = [t['engagement'] for t in timeline]
    total_actions = sum(t['actions'] for t in timeline)

    post_sentiments = [t['sentiment'] for t in post_branch] if post_branch else all_sentiments
    post_engagements = [t['engagement'] for t in post_branch] if post_branch else all_engagements

    return {
        'finalSentiment': round(all_sentiments[-1], 3),
        'avgSentiment': round(sum(post_sentiments) / len(post_sentiments), 3),
        'finalEngagement': round(all_engagements[-1], 3),
        'avgEngagement': round(sum(post_engagements) / len(post_engagements), 3),
        'totalActions': total_actions,
        'peakSentiment': round(max(all_sentiments), 3),
    }


MOCK_BRANCHES = [
    {
        'id': 'branch-original',
        'label': 'Original Run',
        'modification': None,
        'modificationLabel': 'Baseline (no changes)',
        'color': '#2068FF',
    },
    {
        'id': 'branch-add-agent',
        'label': 'Added Industry Analyst',
        'modification': 'add_agent',
        'modificationLabel': 'Add agent: Industry Analyst',
        'color': '#009900',
    },
    {
        'id': 'branch-inject-event',
        'label': 'Market Disruption Event',
        'modification': 'inject_event',
        'modificationLabel': 'Inject event: Market disruption',
        'color': '#ff5600',
    },
    {
        'id': 'branch-personality',
        'label': 'Skeptical CTO',
        'modification': 'change_personality',
        'modificationLabel': 'Change personality: CTO → Skeptical',
        'color': '#AA00FF',
    },
]


@branches_bp.route('/comparison/<simulation_id>', methods=['GET'])
def get_comparison(simulation_id):
    """Get branch comparison data for a simulation.

    Query params:
        branch_ids: comma-separated branch IDs to compare (optional, defaults to all)
    """
    branch_ids_param = request.args.get('branch_ids', '')
    requested_ids = [b.strip() for b in branch_ids_param.split(',') if b.strip()]

    num_rounds = 12
    branch_point = 4

    branches = []
    for i, branch_def in enumerate(MOCK_BRANCHES):
        if requested_ids and branch_def['id'] not in requested_ids:
            continue

        mod = branch_def['modification']
        seed = hash(f"{simulation_id}-{branch_def['id']}")
        timeline = _generate_mock_timeline(num_rounds, branch_point, mod, seed)
        metrics = _compute_metrics(timeline, branch_point)

        branches.append({
            **branch_def,
            'branchPoint': 0 if mod is None else branch_point,
            'timeline': timeline,
            'metrics': metrics,
        })

    # Shared timeline is the portion before the branch point
    shared_timeline = []
    if branches:
        baseline = next((b for b in branches if b['modification'] is None), branches[0])
        shared_timeline = [t for t in baseline['timeline'] if t['round'] <= branch_point]

    # Determine winners for each metric
    metric_keys = ['finalSentiment', 'avgSentiment', 'finalEngagement', 'avgEngagement', 'totalActions', 'peakSentiment']
    winners = {}
    for key in metric_keys:
        best = max(branches, key=lambda b: b['metrics'].get(key, 0)) if branches else None
        winners[key] = best['id'] if best else None

    return jsonify({
        'simulationId': simulation_id,
        'branchPoint': branch_point,
        'totalRounds': num_rounds,
        'sharedTimeline': shared_timeline,
        'branches': branches,
        'winners': winners,
        'availableBranches': [
            {'id': b['id'], 'label': b['label'], 'color': b['color']}
            for b in MOCK_BRANCHES
        ],
    })


@branches_bp.route('/list/<simulation_id>', methods=['GET'])
def list_branches(simulation_id):
    """List available branches for a simulation."""
    return jsonify({
        'simulationId': simulation_id,
        'branches': [
            {
                'id': b['id'],
                'label': b['label'],
                'modification': b['modification'],
                'modificationLabel': b['modificationLabel'],
                'color': b['color'],
            }
            for b in MOCK_BRANCHES
        ],
    })
