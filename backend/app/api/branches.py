"""
Branch Management & Comparison API

Branch Management:
    Endpoints for forking simulations at specific rounds, listing branches,
    viewing branch trees, comparing branches, and deleting branches.
    All management routes are registered on simulation_bp (prefix /api/simulation).

Branch Comparison:
    Provides branch comparison data for simulation branching scenarios.
    Returns mock/demo data when no real branching backend is configured.
    Comparison routes are on branches_bp (prefix /api/v1/branches).
"""

import math
import random
import traceback

from flask import Blueprint, request, jsonify

from . import simulation_bp
from ..services.branch_manager import BranchManager
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.branches')

branches_bp = Blueprint('branches', __name__, url_prefix='/api/v1/branches')


# ============== Branch Management (simulation_bp) ==============

@simulation_bp.route('/<simulation_id>/branch', methods=['POST'])
def create_branch(simulation_id: str):
    """
    Fork a simulation at a specific round.

    Request (JSON):
        {
            "at_round": 50,
            "label": "Higher engagement scenario",
            "modifications": [
                {"type": "engagement_boost", "value": 1.5},
                {"type": "add_competitor", "value": "Drift"}
            ],
            "parent_branch_id": null  // optional, for nested branches
        }

    Returns:
        {
            "success": true,
            "data": { branch object }
        }
    """
    try:
        data = request.get_json() or {}

        at_round = data.get('at_round')
        if at_round is None or not isinstance(at_round, int) or at_round < 0:
            return jsonify({
                "success": False,
                "error": "at_round is required and must be a non-negative integer"
            }), 400

        label = data.get('label', '').strip()
        if not label:
            return jsonify({
                "success": False,
                "error": "label is required"
            }), 400

        modifications = data.get('modifications', [])
        if not isinstance(modifications, list):
            return jsonify({
                "success": False,
                "error": "modifications must be a list"
            }), 400

        parent_branch_id = data.get('parent_branch_id')

        manager = BranchManager()
        branch = manager.create_branch(
            simulation_id=simulation_id,
            at_round=at_round,
            label=label,
            modifications=modifications,
            parent_branch_id=parent_branch_id,
        )

        return jsonify({
            "success": True,
            "data": branch.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Failed to create branch: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/branches', methods=['GET'])
def list_branches(simulation_id: str):
    """
    List all branches for a simulation.

    Returns:
        {
            "success": true,
            "data": [ branch objects ],
            "count": 3
        }
    """
    try:
        manager = BranchManager()
        branches = manager.list_branches(simulation_id)

        return jsonify({
            "success": True,
            "data": [b.to_dict() for b in branches],
            "count": len(branches)
        })

    except Exception as e:
        logger.error(f"Failed to list branches: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/branch-tree', methods=['GET'])
def get_branch_tree(simulation_id: str):
    """
    Get the full branch tree structure for a simulation.

    Returns a nested tree with the simulation as root and branches as children.

    Returns:
        {
            "success": true,
            "data": {
                "id": "sim_abc123",
                "type": "simulation",
                "label": "Main simulation",
                "at_round": 0,
                "children": [
                    {
                        "id": "br_xxx",
                        "type": "branch",
                        "label": "...",
                        "at_round": 50,
                        "children": [...]
                    }
                ]
            }
        }
    """
    try:
        manager = BranchManager()
        tree = manager.get_branch_tree(simulation_id)

        return jsonify({
            "success": True,
            "data": tree
        })

    except Exception as e:
        logger.error(f"Failed to get branch tree: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/compare-branches', methods=['GET'])
def compare_branches():
    """
    Compare multiple branches across simulations.

    Query params:
        ids: comma-separated branch IDs (e.g. ?ids=br_aaa,br_bbb,br_ccc)
        simulation_id: the simulation these branches belong to

    Returns:
        {
            "success": true,
            "data": {
                "branches": [...],
                "metrics": [...],
                "summary": { per-metric winners }
            }
        }
    """
    try:
        ids_str = request.args.get('ids', '')
        simulation_id = request.args.get('simulation_id', '')

        if not ids_str:
            return jsonify({
                "success": False,
                "error": "ids query parameter is required"
            }), 400

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id query parameter is required"
            }), 400

        branch_ids = [bid.strip() for bid in ids_str.split(',') if bid.strip()]
        if len(branch_ids) < 2:
            return jsonify({
                "success": False,
                "error": "At least 2 branch IDs are required for comparison"
            }), 400

        manager = BranchManager()
        result = manager.compare_branches(simulation_id, branch_ids)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Failed to compare branches: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/branch', methods=['DELETE'])
def delete_branch(simulation_id: str):
    """
    Delete a branch (and optionally its descendants).

    Query params:
        branch_id: the branch to delete (required)
        cascade: "true" to also delete child branches (default: false)

    Returns:
        {"success": true}
    """
    try:
        branch_id = request.args.get('branch_id', '').strip()
        if not branch_id:
            return jsonify({
                "success": False,
                "error": "branch_id query parameter is required"
            }), 400

        cascade = request.args.get('cascade', 'false').lower() == 'true'

        manager = BranchManager()
        deleted = manager.delete_branch(simulation_id, branch_id, cascade=cascade)

        if not deleted:
            return jsonify({
                "success": False,
                "error": f"Branch {branch_id} not found"
            }), 404

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Failed to delete branch: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Branch Comparison Mock Data (branches_bp) ==============

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
def list_comparison_branches(simulation_id):
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
