"""
Sentiment analysis service for simulation actions.
Computes per-agent sentiment scores over rounds using keyword matching,
with optional LLM-powered analysis when an API key is configured.
"""

import math
from collections import defaultdict

POSITIVE_WORDS = [
    'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
    'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
    'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
    'exciting', 'confident', 'strong', 'pleased', 'significant', 'positive',
    'agree', 'support', 'approve', 'endorse', 'trust', 'optimistic',
]

NEGATIVE_WORDS = [
    'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
    'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
    'problem', 'unclear', 'confusing', 'frustrated', 'poor', 'slow',
    'lacks', 'overpriced', 'clunky', 'limited', 'negative', 'afraid',
    'disagree', 'oppose', 'reject', 'distrust', 'pessimistic', 'fail',
]

AGENT_COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#FFB800',
                '#E91E63', '#00BCD4', '#795548', '#607D8B', '#9C27B0']


def _score_content(content):
    if not content:
        return 0.0
    lower = content.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def _score_action(action):
    action_type = (action.get('action_type') or '').upper()
    content_score = _score_content(action.get('action_args', {}).get('content'))

    if 'LIKE' in action_type or 'UPVOTE' in action_type:
        return 0.3 + content_score * 0.2
    if 'REPOST' in action_type or 'RETWEET' in action_type or 'SHARE' in action_type:
        return 0.2 + content_score * 0.2
    if 'REPLY' in action_type or 'COMMENT' in action_type:
        return content_score * 0.8
    return content_score * 0.6


def _moving_average(values, window=3):
    result = []
    for i in range(len(values)):
        start = max(0, i - window // 2)
        end = min(len(values), i + window // 2 + 1)
        result.append(sum(values[start:end]) / (end - start))
    return result


def analyze_sentiment(actions):
    """
    Compute per-agent sentiment arcs from a list of simulation actions.

    Returns dict with:
      - agents: list of {id, name, color, scores: [{round, raw, smoothed}]}
      - group_average: [{round, raw, smoothed}]
      - events: [{round, type, label}]  (conflicts, consensus, decisions)
      - story_arc: [{round, value}]  (narrative reference curve)
      - rounds: [int]
    """
    if not actions:
        return _empty_result()

    # Group scores by agent and round
    agent_rounds = defaultdict(lambda: defaultdict(list))
    agent_names = {}
    all_rounds = set()

    for action in actions:
        round_num = action.get('round_num')
        if round_num is None:
            continue
        agent_id = action.get('agent_id') or action.get('agent_name', 'unknown')
        agent_name = action.get('agent_name') or agent_id
        agent_names[agent_id] = agent_name
        score = _score_action(action)
        agent_rounds[agent_id][round_num].append(score)
        all_rounds.add(round_num)

    if not all_rounds:
        return _empty_result()

    rounds = sorted(all_rounds)

    # Build per-agent score arrays
    agent_ids = sorted(agent_rounds.keys(), key=lambda a: agent_names.get(a, a))
    agents = []
    group_scores_by_round = defaultdict(list)

    for idx, agent_id in enumerate(agent_ids):
        raw_scores = []
        for r in rounds:
            scores = agent_rounds[agent_id].get(r, [])
            if scores:
                avg = sum(scores) / len(scores)
            else:
                avg = None
            raw_scores.append(avg)
            if avg is not None:
                group_scores_by_round[r].append(avg)

        # Interpolate None gaps (agent inactive for a round)
        filled = _interpolate(raw_scores)
        smoothed = _moving_average(filled, window=3)

        agents.append({
            'id': agent_id,
            'name': agent_names.get(agent_id, agent_id),
            'color': AGENT_COLORS[idx % len(AGENT_COLORS)],
            'scores': [
                {'round': r, 'raw': round(filled[i], 3), 'smoothed': round(smoothed[i], 3)}
                for i, r in enumerate(rounds)
            ],
        })

    # Group average
    group_raw = []
    for r in rounds:
        vals = group_scores_by_round.get(r, [0])
        group_raw.append(sum(vals) / len(vals))
    group_smoothed = _moving_average(group_raw, window=3)

    group_average = [
        {'round': r, 'raw': round(group_raw[i], 3), 'smoothed': round(group_smoothed[i], 3)}
        for i, r in enumerate(rounds)
    ]

    # Detect events
    events = _detect_events(group_raw, rounds, agent_rounds, rounds)

    # Story arc reference (setup → tension → climax → resolution)
    story_arc = _generate_story_arc(rounds)

    return {
        'agents': agents,
        'group_average': group_average,
        'events': events,
        'story_arc': story_arc,
        'rounds': rounds,
    }


def _interpolate(values):
    """Fill None values with linear interpolation."""
    result = list(values)
    for i, v in enumerate(result):
        if v is None:
            # Find nearest non-None neighbors
            prev_val = next((result[j] for j in range(i - 1, -1, -1) if result[j] is not None), 0.0)
            next_val = next((result[j] for j in range(i + 1, len(result)) if result[j] is not None), prev_val)
            result[i] = (prev_val + next_val) / 2
    return result


def _detect_events(group_raw, rounds, agent_rounds, sorted_rounds):
    """Detect notable events: consensus, conflict, mood swings."""
    events = []
    for i, r in enumerate(rounds):
        all_scores = []
        for agent_id in agent_rounds:
            scores = agent_rounds[agent_id].get(r, [])
            if scores:
                all_scores.append(sum(scores) / len(scores))

        if len(all_scores) < 2:
            continue

        avg = sum(all_scores) / len(all_scores)
        spread = max(all_scores) - min(all_scores)

        # Consensus: low spread + high agreement
        if spread < 0.15 and len(all_scores) >= 2:
            events.append({'round': r, 'type': 'consensus', 'label': 'Consensus'})
        # Conflict: high spread
        elif spread > 0.5:
            events.append({'round': r, 'type': 'conflict', 'label': 'Divergence'})

        # Mood swing: large change from previous round
        if i > 0:
            delta = abs(group_raw[i] - group_raw[i - 1])
            if delta > 0.25:
                direction = 'surge' if group_raw[i] > group_raw[i - 1] else 'drop'
                events.append({'round': r, 'type': 'swing', 'label': f'Mood {direction}'})

    return events


def _generate_story_arc(rounds):
    """Generate a narrative arc reference curve: setup → rising tension → climax → resolution."""
    if len(rounds) < 2:
        return [{'round': r, 'value': 0} for r in rounds]

    n = len(rounds)
    arc = []
    for i, r in enumerate(rounds):
        t = i / (n - 1)  # 0 to 1
        # Bell-curve-like arc peaking at ~60% through
        value = math.sin(t * math.pi * 0.9) * 0.4
        arc.append({'round': r, 'value': round(value, 3)})
    return arc


def _empty_result():
    return {
        'agents': [],
        'group_average': [],
        'events': [],
        'story_arc': [],
        'rounds': [],
    }


def generate_demo_sentiment(num_rounds=10, num_agents=4):
    """Generate realistic demo sentiment data when no real simulation is available."""
    import random
    random.seed(42)

    agent_personas = [
        ('vp_sales', 'VP of Sales'),
        ('cx_director', 'CX Director'),
        ('it_leader', 'IT Leader'),
        ('ops_manager', 'Operations Manager'),
        ('cfo', 'CFO'),
    ]

    rounds = list(range(1, num_rounds + 1))
    agents = []

    # Each agent follows a slightly different sentiment arc
    arc_patterns = [
        lambda t: -0.1 + 0.5 * t,                        # Skeptic → believer
        lambda t: 0.3 - 0.2 * math.sin(t * math.pi),     # Cautiously positive
        lambda t: -0.3 + 0.6 * t - 0.2 * t * t,          # Slow warm-up
        lambda t: 0.4 * math.sin(t * math.pi * 1.5),      # Oscillating
        lambda t: 0.1 - 0.1 * t + 0.3 * t * t,           # Late convert
    ]

    group_scores_by_round = defaultdict(list)

    for idx in range(min(num_agents, len(agent_personas))):
        agent_id, agent_name = agent_personas[idx]
        pattern = arc_patterns[idx]
        scores = []
        for i, r in enumerate(rounds):
            t = i / max(1, num_rounds - 1)
            raw = max(-0.6, min(0.6, pattern(t) + random.gauss(0, 0.05)))
            scores.append(raw)
            group_scores_by_round[r].append(raw)

        smoothed = _moving_average(scores, window=3)
        agents.append({
            'id': agent_id,
            'name': agent_name,
            'color': AGENT_COLORS[idx % len(AGENT_COLORS)],
            'scores': [
                {'round': r, 'raw': round(scores[i], 3), 'smoothed': round(smoothed[i], 3)}
                for i, r in enumerate(rounds)
            ],
        })

    group_raw = [sum(group_scores_by_round[r]) / len(group_scores_by_round[r]) for r in rounds]
    group_smoothed = _moving_average(group_raw, window=3)

    return {
        'agents': agents,
        'group_average': [
            {'round': r, 'raw': round(group_raw[i], 3), 'smoothed': round(group_smoothed[i], 3)}
            for i, r in enumerate(rounds)
        ],
        'events': [
            {'round': 3, 'type': 'conflict', 'label': 'Divergence'},
            {'round': 5, 'type': 'swing', 'label': 'Mood surge'},
            {'round': 7, 'type': 'consensus', 'label': 'Consensus'},
        ],
        'story_arc': _generate_story_arc(rounds),
        'rounds': rounds,
    }
