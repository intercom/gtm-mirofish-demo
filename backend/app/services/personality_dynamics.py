"""
Personality Dynamics Service

Generates deterministic personality trait vectors and sentiment data for
simulation agents. Uses seeded randomness so the same (sim_id, agent_id)
always produces the same personality trajectory.

Personality is a vector of 5 traits (each 0-100):
    analytical, creative, assertive, empathetic, risk_tolerant

Sentiment is a float 1-10 (1=very negative, 10=very positive).
"""

import hashlib
import math
import random
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.personality_dynamics')

TRAITS = ['analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant']

PERSONA_TRAIT_PROFILES = {
    'VP': {'analytical': 65, 'creative': 50, 'assertive': 80, 'empathetic': 45, 'risk_tolerant': 60},
    'Director': {'analytical': 60, 'creative': 55, 'assertive': 70, 'empathetic': 55, 'risk_tolerant': 50},
    'Manager': {'analytical': 55, 'creative': 45, 'assertive': 50, 'empathetic': 70, 'risk_tolerant': 40},
    'CTO': {'analytical': 80, 'creative': 70, 'assertive': 65, 'empathetic': 35, 'risk_tolerant': 75},
    'Engineer': {'analytical': 85, 'creative': 60, 'assertive': 40, 'empathetic': 40, 'risk_tolerant': 55},
    'Analyst': {'analytical': 90, 'creative': 40, 'assertive': 35, 'empathetic': 50, 'risk_tolerant': 30},
    'default': {'analytical': 55, 'creative': 55, 'assertive': 55, 'empathetic': 55, 'risk_tolerant': 55},
}

SENTIMENT_LABELS = {
    (1, 3): 'frustrated',
    (3, 5): 'cautious',
    (5, 7): 'engaged',
    (7, 9): 'optimistic',
    (9, 11): 'enthusiastic',
}

DEFAULT_AGENTS = [
    {'agent_id': 0, 'name': 'Sarah Chen', 'role': 'VP'},
    {'agent_id': 1, 'name': 'Marcus Johnson', 'role': 'Director'},
    {'agent_id': 2, 'name': 'Elena Rodriguez', 'role': 'Manager'},
    {'agent_id': 3, 'name': 'David Kim', 'role': 'CTO'},
    {'agent_id': 4, 'name': 'Priya Patel', 'role': 'Analyst'},
    {'agent_id': 5, 'name': 'James Wilson', 'role': 'VP'},
    {'agent_id': 6, 'name': 'Aisha Mohammed', 'role': 'Director'},
    {'agent_id': 7, 'name': 'Tom O\'Brien', 'role': 'Engineer'},
    {'agent_id': 8, 'name': 'Lisa Wang', 'role': 'Manager'},
    {'agent_id': 9, 'name': 'Robert Taylor', 'role': 'Analyst'},
    {'agent_id': 10, 'name': 'Maria Garcia', 'role': 'Director'},
    {'agent_id': 11, 'name': 'Ahmed Hassan', 'role': 'Engineer'},
    {'agent_id': 12, 'name': 'Jennifer Lee', 'role': 'VP'},
    {'agent_id': 13, 'name': 'Carlos Mendez', 'role': 'Manager'},
    {'agent_id': 14, 'name': 'Nina Volkov', 'role': 'CTO'},
]

MAX_ROUNDS = 144


def _seed(sim_id: str, agent_id: int, extra: str = '') -> int:
    raw = f"{sim_id}:{agent_id}:{extra}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def _get_role(agent_id: int) -> str:
    if agent_id < len(DEFAULT_AGENTS):
        return DEFAULT_AGENTS[agent_id]['role']
    return 'default'


def _base_personality(agent_id: int, sim_id: str) -> Dict[str, int]:
    """Generate a base personality vector for an agent, with per-sim jitter."""
    role = _get_role(agent_id)
    base = PERSONA_TRAIT_PROFILES.get(role, PERSONA_TRAIT_PROFILES['default']).copy()
    rng = random.Random(_seed(sim_id, agent_id, 'base'))
    for trait in TRAITS:
        jitter = rng.randint(-8, 8)
        base[trait] = max(20, min(80, base[trait] + jitter))
    return base


def _personality_at_round(agent_id: int, sim_id: str, round_num: int) -> Dict[str, int]:
    """Personality evolves slightly per round via a smooth random walk."""
    base = _base_personality(agent_id, sim_id)
    rng = random.Random(_seed(sim_id, agent_id, 'evolution'))
    current = base.copy()
    for r in range(round_num):
        for trait in TRAITS:
            delta = rng.choice([-2, -1, -1, 0, 0, 0, 0, 1, 1, 2])
            current[trait] = max(20, min(80, current[trait] + delta))
    return current


def _sentiment_at_round(agent_id: int, sim_id: str, round_num: int) -> float:
    """Sentiment follows a slow sine wave + noise for natural-feeling arcs."""
    seed = _seed(sim_id, agent_id, 'sentiment')
    rng = random.Random(seed)
    phase = rng.uniform(0, 2 * math.pi)
    amplitude = rng.uniform(1.5, 3.0)
    base_mood = rng.uniform(4.5, 6.5)
    noise_rng = random.Random(_seed(sim_id, agent_id, f'noise_{round_num}'))
    noise = noise_rng.uniform(-0.5, 0.5)
    val = base_mood + amplitude * math.sin(phase + round_num * 0.08) + noise
    return round(max(1.0, min(10.0, val)), 2)


def _sentiment_label(score: float) -> str:
    for (lo, hi), label in SENTIMENT_LABELS.items():
        if lo <= score < hi:
            return label
    return 'neutral'


class PersonalityDynamicsService:

    @staticmethod
    def get_agents(sim_id: str) -> List[Dict[str, Any]]:
        """Return the agent roster for a simulation."""
        return [
            {
                'agent_id': a['agent_id'],
                'name': a['name'],
                'role': a['role'],
            }
            for a in DEFAULT_AGENTS
        ]

    @staticmethod
    def get_personality(sim_id: str, agent_id: int) -> Dict[str, Any]:
        """Current personality vector (latest round)."""
        personality = _personality_at_round(agent_id, sim_id, MAX_ROUNDS)
        return {
            'agent_id': agent_id,
            'round': MAX_ROUNDS,
            'traits': personality,
        }

    @staticmethod
    def get_personality_history(sim_id: str, agent_id: int) -> Dict[str, Any]:
        """Personality trait values at each round (sampled every 6 rounds)."""
        history = []
        step = 6
        for r in range(0, MAX_ROUNDS + 1, step):
            traits = _personality_at_round(agent_id, sim_id, r)
            history.append({'round': r, 'traits': traits})
        return {
            'agent_id': agent_id,
            'total_rounds': MAX_ROUNDS,
            'sample_step': step,
            'history': history,
        }

    @staticmethod
    def get_sentiment_history(sim_id: str, agent_id: int) -> Dict[str, Any]:
        """Per-round sentiment values."""
        history = []
        step = 6
        for r in range(0, MAX_ROUNDS + 1, step):
            score = _sentiment_at_round(agent_id, sim_id, r)
            history.append({
                'round': r,
                'score': score,
                'label': _sentiment_label(score),
            })
        overall = sum(h['score'] for h in history) / len(history)
        return {
            'agent_id': agent_id,
            'total_rounds': MAX_ROUNDS,
            'sample_step': step,
            'overall_sentiment': round(overall, 2),
            'history': history,
        }

    @staticmethod
    def get_personality_comparison(sim_id: str) -> Dict[str, Any]:
        """All agents' current personality vectors side-by-side."""
        agents = []
        for a in DEFAULT_AGENTS:
            aid = a['agent_id']
            initial = _base_personality(aid, sim_id)
            current = _personality_at_round(aid, sim_id, MAX_ROUNDS)
            deltas = {t: current[t] - initial[t] for t in TRAITS}
            agents.append({
                'agent_id': aid,
                'name': a['name'],
                'role': a['role'],
                'initial': initial,
                'current': current,
                'deltas': deltas,
            })
        return {
            'traits': TRAITS,
            'agents': agents,
        }

    @staticmethod
    def get_group_mood(sim_id: str) -> Dict[str, Any]:
        """Group mood overview — average sentiment + per-agent breakdown."""
        agent_moods = []
        for a in DEFAULT_AGENTS:
            aid = a['agent_id']
            score = _sentiment_at_round(aid, sim_id, MAX_ROUNDS)
            agent_moods.append({
                'agent_id': aid,
                'name': a['name'],
                'sentiment': score,
                'label': _sentiment_label(score),
            })
        avg = sum(m['sentiment'] for m in agent_moods) / len(agent_moods)
        return {
            'round': MAX_ROUNDS,
            'group_average': round(avg, 2),
            'group_label': _sentiment_label(avg),
            'agents': agent_moods,
        }

    @staticmethod
    def get_mood_swings(sim_id: str, threshold: float = 2.0) -> Dict[str, Any]:
        """Detect rounds where an agent's sentiment changed sharply."""
        swings = []
        step = 6
        for a in DEFAULT_AGENTS:
            aid = a['agent_id']
            prev_score: Optional[float] = None
            for r in range(0, MAX_ROUNDS + 1, step):
                score = _sentiment_at_round(aid, sim_id, r)
                if prev_score is not None:
                    delta = score - prev_score
                    if abs(delta) >= threshold:
                        swings.append({
                            'agent_id': aid,
                            'agent_name': a['name'],
                            'round': r,
                            'previous_score': prev_score,
                            'new_score': score,
                            'delta': round(delta, 2),
                            'direction': 'positive' if delta > 0 else 'negative',
                        })
                prev_score = score
        swings.sort(key=lambda s: abs(s['delta']), reverse=True)
        return {
            'threshold': threshold,
            'total_swings': len(swings),
            'swings': swings,
        }
