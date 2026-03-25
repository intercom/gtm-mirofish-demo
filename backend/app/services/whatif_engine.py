"""
What-If Analysis Engine

Runs scenario variations by modifying simulation parameters and comparing outcomes.
Uses deterministic mock data when no real simulation backend is available.
"""

import hashlib
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.whatif')

# In-memory stores
_whatif_scenarios: Dict[str, Dict[str, Any]] = {}
_whatif_variants: Dict[str, List[str]] = {}  # base_sim_id -> [variant_ids]

SUPPORTED_PARAMETERS = {
    'agent_count': {'type': 'int', 'min': 2, 'max': 20, 'default': 8},
    'round_count': {'type': 'int', 'min': 10, 'max': 200, 'default': 50},
    'temperature': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.7},
    'personality_mix': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.5},
    'initial_sentiment': {'type': 'float', 'min': -1.0, 'max': 1.0, 'default': 0.0},
    'interaction_rate': {'type': 'float', 'min': 0.1, 'max': 1.0, 'default': 0.5},
}

OUTCOME_METRICS = [
    'avg_sentiment',
    'consensus_score',
    'decision_quality',
    'time_to_resolution',
    'engagement_rate',
    'competitive_mention_rate',
]


def _seed_rng(base_id: str, *extra: Any) -> random.Random:
    """Create a deterministic RNG seeded by base_id + extra values."""
    seed_str = f"{base_id}:{'|'.join(str(e) for e in extra)}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:12], 16)
    return random.Random(seed)


def _compute_mock_outcomes(rng: random.Random, modifications: List[Dict]) -> Dict[str, float]:
    """Generate realistic-looking outcome metrics influenced by modifications."""
    base = {
        'avg_sentiment': rng.uniform(0.1, 0.6),
        'consensus_score': rng.uniform(0.3, 0.7),
        'decision_quality': rng.uniform(0.4, 0.8),
        'time_to_resolution': rng.uniform(20, 80),
        'engagement_rate': rng.uniform(0.3, 0.8),
        'competitive_mention_rate': rng.uniform(0.05, 0.3),
    }

    for mod in modifications:
        param = mod.get('parameter', '')
        value = mod.get('value', 0)
        if param == 'agent_count':
            factor = value / SUPPORTED_PARAMETERS['agent_count']['default']
            base['engagement_rate'] *= min(factor, 1.5)
            base['time_to_resolution'] *= max(0.6, 1.0 / factor)
        elif param == 'temperature':
            diff = value - SUPPORTED_PARAMETERS['temperature']['default']
            base['consensus_score'] -= diff * 0.3
            base['decision_quality'] -= abs(diff) * 0.15
        elif param == 'round_count':
            factor = value / SUPPORTED_PARAMETERS['round_count']['default']
            base['consensus_score'] *= min(factor ** 0.3, 1.4)
            base['time_to_resolution'] = value * rng.uniform(0.6, 0.9)
        elif param == 'personality_mix':
            base['avg_sentiment'] += (value - 0.5) * 0.3
            base['consensus_score'] -= abs(value - 0.5) * 0.2
        elif param == 'initial_sentiment':
            base['avg_sentiment'] = (base['avg_sentiment'] + value) / 2
        elif param == 'interaction_rate':
            base['engagement_rate'] = min(1.0, value * rng.uniform(0.8, 1.2))
            base['competitive_mention_rate'] *= value / 0.5

    for k in base:
        if k != 'time_to_resolution':
            base[k] = max(0.0, min(1.0, base[k]))
        else:
            base[k] = max(5.0, min(200.0, base[k]))
        base[k] = round(base[k], 4)

    return base


class WhatIfEngine:
    """Runs what-if scenario variations for simulation analysis."""

    @staticmethod
    def create_scenario(
        base_simulation_id: str,
        modifications: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create and 'run' a what-if scenario variant.

        Returns a scenario result with deterministic mock outcomes.
        """
        rng = _seed_rng(base_simulation_id, *[
            f"{m.get('parameter')}={m.get('value')}" for m in modifications
        ])

        variant_id = f"whatif_{base_simulation_id}_{rng.randint(100000, 999999)}"
        outcomes = _compute_mock_outcomes(rng, modifications)

        base_outcomes = _compute_mock_outcomes(
            _seed_rng(base_simulation_id, 'base'), []
        )

        deltas = {}
        for metric in OUTCOME_METRICS:
            base_val = base_outcomes[metric]
            variant_val = outcomes[metric]
            if base_val != 0:
                deltas[metric] = round((variant_val - base_val) / abs(base_val) * 100, 2)
            else:
                deltas[metric] = 0.0

        scenario = {
            'variant_id': variant_id,
            'base_simulation_id': base_simulation_id,
            'modifications': modifications,
            'status': 'completed',
            'outcomes': outcomes,
            'base_outcomes': base_outcomes,
            'deltas': deltas,
            'created_at': datetime.now().isoformat(),
        }

        _whatif_scenarios[variant_id] = scenario
        _whatif_variants.setdefault(base_simulation_id, []).append(variant_id)

        logger.info(f"Created what-if variant {variant_id} for base {base_simulation_id}")
        return scenario

    @staticmethod
    def get_variants(base_simulation_id: str) -> List[Dict[str, Any]]:
        """List all what-if variants for a base simulation."""
        variant_ids = _whatif_variants.get(base_simulation_id, [])
        return [_whatif_scenarios[vid] for vid in variant_ids if vid in _whatif_scenarios]

    @staticmethod
    def get_variant(variant_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific variant by ID."""
        return _whatif_scenarios.get(variant_id)

    @staticmethod
    def get_supported_parameters() -> Dict[str, Any]:
        """Return the list of tunable parameters with their constraints."""
        return SUPPORTED_PARAMETERS
