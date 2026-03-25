"""
Branch insights API — generates AI-powered or template-based recommendations
from simulation branch comparison data.
"""

import hashlib
import json
from flask import Blueprint, request, jsonify

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.branches')

branches_bp = Blueprint('branches', __name__, url_prefix='/api/v1/branches')


# ---------------------------------------------------------------------------
# Template-based insight generation (demo / no-LLM fallback)
# ---------------------------------------------------------------------------

def _hash_seed(text):
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def _find_best_branch(branches, metric):
    best = None
    for b in branches:
        val = b.get('metrics', {}).get(metric)
        if val is not None and (best is None or val > best.get('metrics', {}).get(metric, 0)):
            best = b
    return best


def _find_worst_branch(branches, metric):
    worst = None
    for b in branches:
        val = b.get('metrics', {}).get(metric)
        if val is not None and (worst is None or val < worst.get('metrics', {}).get(metric, float('inf'))):
            worst = b
    return worst


def _pct_diff(a, b):
    if b == 0:
        return 0
    return round(((a - b) / abs(b)) * 100, 1)


def _generate_template_insights(branches):
    """Deterministic template-based insights when no LLM is configured."""
    if not branches or len(branches) < 2:
        return []

    insights = []
    n = len(branches)

    # --- 1. Most impactful branch (by engagement) ---
    best_eng = _find_best_branch(branches, 'engagement_rate')
    worst_eng = _find_worst_branch(branches, 'engagement_rate')
    if best_eng and worst_eng and best_eng['branch_id'] != worst_eng['branch_id']:
        best_val = best_eng['metrics']['engagement_rate']
        worst_val = worst_eng['metrics']['engagement_rate']
        diff = _pct_diff(best_val, worst_val)
        insights.append({
            'id': 'impact-engagement',
            'type': 'impact',
            'title': 'Most Impactful Modification',
            'description': (
                f'Based on {n} branches, "{best_eng.get("label", best_eng["branch_id"])}" '
                f'achieved the highest engagement rate ({best_val:.0%}), '
                f'outperforming the lowest branch by {abs(diff)}%.'
            ),
            'confidence': min(0.65 + (n * 0.05), 0.95),
            'evidence': [
                {'branch_id': best_eng['branch_id'], 'metric': 'engagement_rate', 'value': best_val},
                {'branch_id': worst_eng['branch_id'], 'metric': 'engagement_rate', 'value': worst_val},
            ],
        })

    # --- 2. Optimal configuration recommendation ---
    best_sent = _find_best_branch(branches, 'avg_sentiment')
    if best_sent:
        label = best_sent.get('label', best_sent['branch_id'])
        mod = best_sent.get('modification', 'current configuration')
        sentiment = best_sent['metrics'].get('avg_sentiment', 0)
        insights.append({
            'id': 'recommendation-config',
            'type': 'recommendation',
            'title': 'Recommended Configuration',
            'description': (
                f'The optimal configuration appears to be "{label}" '
                f'(modification: {mod}), which achieved the best average '
                f'sentiment score of {sentiment:.2f}.'
            ),
            'confidence': min(0.60 + (n * 0.04), 0.90),
            'evidence': [
                {'branch_id': best_sent['branch_id'], 'metric': 'avg_sentiment', 'value': sentiment},
            ],
        })

    # --- 3. Decision-maker conversion insight ---
    best_dm = _find_best_branch(branches, 'decision_makers')
    if best_dm and best_dm['metrics'].get('decision_makers', 0) > 0:
        dm_count = best_dm['metrics']['decision_makers']
        total = best_dm['metrics'].get('total_agents', dm_count * 3)
        insights.append({
            'id': 'observation-decisions',
            'type': 'observation',
            'title': 'Decision-Maker Conversion',
            'description': (
                f'Branch "{best_dm.get("label", best_dm["branch_id"])}" '
                f'converted {dm_count} agents to the Decision stage '
                f'out of {total} total agents — the highest across all branches.'
            ),
            'confidence': 0.80,
            'evidence': [
                {'branch_id': best_dm['branch_id'], 'metric': 'decision_makers', 'value': dm_count},
            ],
        })

    # --- 4. Diminishing returns warning ---
    sorted_by_actions = sorted(
        [b for b in branches if b.get('metrics', {}).get('total_actions')],
        key=lambda b: b['metrics']['total_actions'],
    )
    if len(sorted_by_actions) >= 3:
        mid = len(sorted_by_actions) // 2
        low_half_avg = sum(
            b['metrics'].get('engagement_rate', 0) for b in sorted_by_actions[:mid]
        ) / mid
        high_half_avg = sum(
            b['metrics'].get('engagement_rate', 0) for b in sorted_by_actions[mid:]
        ) / (len(sorted_by_actions) - mid)
        if high_half_avg > 0 and low_half_avg / high_half_avg > 0.85:
            insights.append({
                'id': 'warning-diminishing',
                'type': 'warning',
                'title': 'Diminishing Returns Detected',
                'description': (
                    f'Diminishing returns observed: branches with higher action '
                    f'counts show only marginally better engagement rates '
                    f'({high_half_avg:.0%} vs {low_half_avg:.0%}). '
                    f'Consider optimizing agent quality over quantity.'
                ),
                'confidence': 0.55,
                'evidence': [
                    {'branch_id': b['branch_id'], 'metric': 'total_actions',
                     'value': b['metrics']['total_actions']}
                    for b in sorted_by_actions
                ],
            })

    # --- 5. Top topic convergence ---
    topics = {}
    for b in branches:
        topic = b.get('metrics', {}).get('top_topic')
        if topic:
            topics.setdefault(topic, []).append(b['branch_id'])
    dominant = max(topics.items(), key=lambda t: len(t[1]), default=None)
    if dominant and len(dominant[1]) >= 2:
        insights.append({
            'id': 'observation-topic',
            'type': 'observation',
            'title': 'Topic Convergence',
            'description': (
                f'"{dominant[0]}" emerged as the dominant topic in '
                f'{len(dominant[1])} of {n} branches, suggesting strong '
                f'organic interest regardless of scenario modifications.'
            ),
            'confidence': 0.70,
            'evidence': [
                {'branch_id': bid, 'metric': 'top_topic', 'value': dominant[0]}
                for bid in dominant[1]
            ],
        })

    return insights


# ---------------------------------------------------------------------------
# LLM-powered insight generation
# ---------------------------------------------------------------------------

def _generate_llm_insights(branches):
    """Use the configured LLM to produce richer insights."""
    from ..utils.llm_client import LLMClient

    branch_summary = json.dumps([
        {
            'branch_id': b['branch_id'],
            'label': b.get('label', b['branch_id']),
            'modification': b.get('modification', 'unknown'),
            'metrics': b.get('metrics', {}),
        }
        for b in branches
    ], indent=2)

    messages = [
        {
            'role': 'system',
            'content': (
                'You are a GTM simulation analyst. Given branch comparison data '
                'from a multi-agent simulation, generate actionable insights. '
                'Return a JSON object with an "insights" array. Each insight has: '
                'id (string), type (one of: impact, recommendation, warning, observation), '
                'title (short heading), description (1-2 sentences with specific numbers), '
                'confidence (float 0-1). Focus on: which modification had the most impact, '
                'optimal configuration recommendations, diminishing returns, and '
                'unexpected patterns.'
            ),
        },
        {
            'role': 'user',
            'content': f'Analyze these simulation branches and generate insights:\n\n{branch_summary}',
        },
    ]

    client = LLMClient()
    result = client.chat_json(messages=messages, temperature=0.3, max_tokens=2048)
    raw_insights = result.get('insights', [])

    # Normalise and validate each insight
    valid = []
    for ins in raw_insights:
        if not isinstance(ins, dict):
            continue
        if ins.get('type') not in ('impact', 'recommendation', 'warning', 'observation'):
            ins['type'] = 'observation'
        ins.setdefault('confidence', 0.7)
        ins.setdefault('evidence', [])
        ins.setdefault('id', f'llm-{len(valid)}')
        valid.append(ins)

    return valid


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@branches_bp.route('/insights', methods=['POST'])
def branch_insights():
    """
    Generate insights from branch comparison data.

    Body JSON:
        simulation_id (str, optional): parent simulation id
        branches (list): each with branch_id, label, modification, metrics
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request body required'}), 400

    branches = data.get('branches', [])
    if not isinstance(branches, list) or len(branches) < 2:
        return jsonify({
            'success': False,
            'error': 'At least 2 branches are required for insight generation',
        }), 422

    for i, b in enumerate(branches):
        if not b.get('branch_id'):
            return jsonify({
                'success': False,
                'error': f'Branch at index {i} missing required field "branch_id"',
            }), 422

    use_llm = bool(Config.LLM_API_KEY)
    insights = []

    if use_llm:
        try:
            insights = _generate_llm_insights(branches)
            logger.info(f"Generated {len(insights)} LLM insights for {len(branches)} branches")
        except Exception as e:
            logger.warning(f"LLM insight generation failed, falling back to templates: {e}")
            insights = _generate_template_insights(branches)
    else:
        insights = _generate_template_insights(branches)
        logger.info(f"Generated {len(insights)} template insights for {len(branches)} branches")

    return jsonify({
        'success': True,
        'data': {
            'insights': insights,
            'branch_count': len(branches),
            'source': 'llm' if use_llm and insights else 'template',
        },
    })
