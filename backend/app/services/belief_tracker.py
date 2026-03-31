"""
Belief Tracker Service

Analyzes agent actions to extract and track belief dimensions over simulation rounds.
Beliefs are scored across dimensions: product_quality, pricing, brand_trust,
competitive_position, and adoption_intent.

Supports two modes:
  - LLM mode: uses the configured LLM to extract nuanced beliefs from content
  - Demo/mock mode: uses keyword-based heuristics when no LLM key is configured
"""

import json
import re
from typing import Dict, List, Any, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.belief_tracker')

BELIEF_DIMENSIONS = [
    'product_quality',
    'pricing',
    'brand_trust',
    'competitive_position',
    'adoption_intent',
]

# Keyword-based scoring for demo/mock mode
_DIMENSION_KEYWORDS = {
    'product_quality': {
        'positive': [
            'impressive', 'innovative', 'reliable', 'powerful', 'robust',
            'excellent', 'superior', 'cutting-edge', 'seamless', 'intuitive',
        ],
        'negative': [
            'buggy', 'unreliable', 'clunky', 'outdated', 'limited',
            'broken', 'slow', 'poor', 'lacking', 'unstable',
        ],
    },
    'pricing': {
        'positive': [
            'affordable', 'value', 'worth', 'reasonable', 'competitive',
            'fair', 'cost-effective', 'bargain', 'economical', 'savings',
        ],
        'negative': [
            'expensive', 'overpriced', 'costly', 'pricey', 'premium',
            'steep', 'unaffordable', 'gouging', 'markup', 'hidden fees',
        ],
    },
    'brand_trust': {
        'positive': [
            'trust', 'reliable', 'transparent', 'reputable', 'honest',
            'credible', 'dependable', 'consistent', 'respected', 'proven',
        ],
        'negative': [
            'skeptical', 'distrust', 'shady', 'misleading', 'questionable',
            'doubt', 'suspicious', 'unproven', 'risky', 'concerned',
        ],
    },
    'competitive_position': {
        'positive': [
            'leader', 'best', 'ahead', 'dominant', 'preferred',
            'winning', 'top', 'outperform', 'advantage', 'superior',
        ],
        'negative': [
            'behind', 'losing', 'inferior', 'weaker', 'lagging',
            'competitor', 'alternative', 'switch', 'replaced', 'outdone',
        ],
    },
    'adoption_intent': {
        'positive': [
            'adopt', 'implement', 'migrate', 'onboard', 'purchase',
            'subscribe', 'try', 'evaluate', 'interested', 'excited',
        ],
        'negative': [
            'abandon', 'cancel', 'churn', 'leave', 'reject',
            'pass', 'skip', 'avoid', 'defer', 'postpone',
        ],
    },
}


def _score_content_keyword(content: str, dimension: str) -> float:
    """Score content for a belief dimension using keyword matching. Returns -1 to 1."""
    if not content:
        return 0.0
    lower = content.lower()
    kw = _DIMENSION_KEYWORDS.get(dimension, {})
    pos = sum(1 for w in kw.get('positive', []) if w in lower)
    neg = sum(1 for w in kw.get('negative', []) if w in lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _weight_by_action_type(action_type: str) -> float:
    """Weight belief signal strength by action type."""
    t = (action_type or '').upper()
    if 'POST' in t or 'CREATE' in t:
        return 1.0
    if 'REPLY' in t or 'COMMENT' in t:
        return 0.8
    if 'REPOST' in t or 'RETWEET' in t or 'SHARE' in t:
        return 0.5
    if 'LIKE' in t or 'UPVOTE' in t:
        return 0.3
    return 0.4


def extract_beliefs_from_actions(actions: List[Dict[str, Any]]) -> Dict[int, Dict]:
    """
    Analyze simulation actions to extract belief scores per round (keyword mode).

    Returns:
        Dict keyed by round number, each containing:
          - dimensions: { dimension_name: avg_score (-1..1) }
          - agent_count: number of unique agents
          - action_count: number of actions analyzed
    """
    round_data: Dict[int, Dict] = {}

    for action in actions:
        round_num = action.get('round_num')
        if round_num is None:
            continue

        content = (action.get('action_args') or {}).get('content', '')
        action_type = action.get('action_type', '')
        agent_id = action.get('agent_name') or action.get('agent_id', '')
        weight = _weight_by_action_type(action_type)

        if round_num not in round_data:
            round_data[round_num] = {
                'scores': {d: [] for d in BELIEF_DIMENSIONS},
                'agents': set(),
            }

        entry = round_data[round_num]
        entry['agents'].add(agent_id)

        for dim in BELIEF_DIMENSIONS:
            raw = _score_content_keyword(content, dim)
            entry['scores'][dim].append(raw * weight)

    result = {}
    for round_num in sorted(round_data.keys()):
        entry = round_data[round_num]
        dimensions = {}
        for dim in BELIEF_DIMENSIONS:
            scores = entry['scores'][dim]
            dimensions[dim] = round(sum(scores) / len(scores), 3) if scores else 0.0
        result[round_num] = {
            'dimensions': dimensions,
            'agent_count': len(entry['agents']),
            'action_count': sum(len(s) for s in entry['scores'].values()) // len(BELIEF_DIMENSIONS),
        }

    return result


def extract_beliefs_llm(actions: List[Dict[str, Any]], llm_client) -> Dict[int, Dict]:
    """
    Use LLM to extract nuanced beliefs from agent actions.
    Falls back to keyword extraction on failure.
    """
    # Group actions by round, take a sample per round to keep token usage reasonable
    rounds: Dict[int, List[str]] = {}
    round_agents: Dict[int, set] = {}
    round_counts: Dict[int, int] = {}

    for action in actions:
        rn = action.get('round_num')
        if rn is None:
            continue
        content = (action.get('action_args') or {}).get('content', '')
        agent_id = action.get('agent_name') or action.get('agent_id', '')
        if rn not in rounds:
            rounds[rn] = []
            round_agents[rn] = set()
            round_counts[rn] = 0
        round_counts[rn] += 1
        round_agents[rn].add(agent_id)
        if len(rounds[rn]) < 15 and content:
            rounds[rn].append(content)

    if not rounds:
        return {}

    sample_text = ""
    for rn in sorted(rounds.keys()):
        sample_text += f"\n--- Round {rn} ({round_counts[rn]} actions) ---\n"
        sample_text += "\n".join(f"- {c[:200]}" for c in rounds[rn])

    prompt = f"""Analyze these GTM simulation agent posts/comments and score each round's collective beliefs.

Dimensions to score (each from -1.0 to 1.0):
- product_quality: perception of product quality/features
- pricing: perception of pricing/value
- brand_trust: trust and credibility of the brand
- competitive_position: perceived market position vs competitors
- adoption_intent: willingness to adopt/purchase

Agent content by round:
{sample_text}

Return JSON object with round numbers as keys:
{{"1": {{"product_quality": 0.3, "pricing": -0.1, "brand_trust": 0.5, "competitive_position": 0.2, "adoption_intent": 0.4}}, ...}}

Only return the JSON, no explanation."""

    try:
        result = llm_client.chat_json([
            {"role": "system", "content": "You are a GTM simulation analyst. Score belief dimensions from agent content."},
            {"role": "user", "content": prompt},
        ], temperature=0.2, max_tokens=2048)

        output = {}
        for rn_str, dims in result.items():
            try:
                rn = int(rn_str)
            except (ValueError, TypeError):
                continue
            dimensions = {}
            for dim in BELIEF_DIMENSIONS:
                val = dims.get(dim, 0)
                dimensions[dim] = max(-1.0, min(1.0, round(float(val), 3)))
            output[rn] = {
                'dimensions': dimensions,
                'agent_count': len(round_agents.get(rn, set())),
                'action_count': round_counts.get(rn, 0),
            }
        return output
    except Exception as e:
        logger.warning(f"LLM belief extraction failed, falling back to keywords: {e}")
        return extract_beliefs_from_actions(actions)


def generate_demo_beliefs(num_rounds: int = 10) -> Dict[int, Dict]:
    """Generate realistic demo belief data for when no simulation is running."""
    import random
    random.seed(42)

    result = {}
    prev = {d: random.uniform(-0.1, 0.3) for d in BELIEF_DIMENSIONS}

    for rn in range(1, num_rounds + 1):
        dimensions = {}
        for dim in BELIEF_DIMENSIONS:
            drift = random.uniform(-0.08, 0.12)
            noise = random.gauss(0, 0.03)
            val = prev[dim] + drift + noise
            val = max(-1.0, min(1.0, val))
            dimensions[dim] = round(val, 3)
            prev[dim] = val

        result[rn] = {
            'dimensions': dimensions,
            'agent_count': random.randint(15, 50),
            'action_count': random.randint(30, 120),
        }

    return result
