"""
Personality Dynamics Engine
Models gradual personality evolution during simulation based on interaction outcomes.

Personality is a 5-trait vector (each 0-100, clamped to 20-80):
  analytical, creative, assertive, empathetic, risk_tolerant

Changes are small (±1-3 per interaction) so personality evolves gradually.
"""

import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from copy import deepcopy

from ..utils.logger import get_logger

logger = get_logger('mirofish.personality_dynamics')

TRAITS = ['analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant']
TRAIT_MIN = 20
TRAIT_MAX = 80
DEFAULT_TRAIT_VALUE = 50


@dataclass
class PersonalityVector:
    """A 5-trait personality snapshot."""
    analytical: int = DEFAULT_TRAIT_VALUE
    creative: int = DEFAULT_TRAIT_VALUE
    assertive: int = DEFAULT_TRAIT_VALUE
    empathetic: int = DEFAULT_TRAIT_VALUE
    risk_tolerant: int = DEFAULT_TRAIT_VALUE

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)

    def clamp(self) -> 'PersonalityVector':
        for trait in TRAITS:
            val = getattr(self, trait)
            setattr(self, trait, max(TRAIT_MIN, min(TRAIT_MAX, val)))
        return self

    @classmethod
    def from_dict(cls, d: Dict[str, int]) -> 'PersonalityVector':
        return cls(**{t: d.get(t, DEFAULT_TRAIT_VALUE) for t in TRAITS})

    @classmethod
    def random_initial(cls) -> 'PersonalityVector':
        """Generate a random starting personality within bounds."""
        return cls(**{t: random.randint(35, 65) for t in TRAITS})


@dataclass
class PersonalitySnapshot:
    """Personality at a specific simulation round."""
    agent_id: str
    round_num: int
    vector: PersonalityVector
    trigger: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'round_num': self.round_num,
            'vector': self.vector.to_dict(),
            'trigger': self.trigger,
        }


# Maps interaction outcome types to trait deltas (trait_name, min_delta, max_delta)
OUTCOME_EFFECTS: Dict[str, List[tuple]] = {
    'positive_consensus': [
        ('empathetic', 1, 3),
        ('assertive', 0, 1),
    ],
    'rejected_idea': [
        ('assertive', -3, -1),
        ('analytical', 0, 2),
    ],
    'successful_risk': [
        ('risk_tolerant', 1, 3),
        ('creative', 0, 2),
    ],
    'failed_risk': [
        ('risk_tolerant', -3, -1),
        ('analytical', 1, 2),
    ],
    'failed_prediction': [
        ('analytical', 1, 3),
        ('assertive', -2, -1),
    ],
    'creative_breakthrough': [
        ('creative', 1, 3),
        ('risk_tolerant', 0, 2),
    ],
    'conflict_resolved': [
        ('empathetic', 1, 3),
        ('assertive', -1, 1),
    ],
    'led_group': [
        ('assertive', 1, 3),
        ('empathetic', 0, 1),
    ],
    'supported_others': [
        ('empathetic', 1, 3),
        ('assertive', -1, 0),
    ],
    'analytical_success': [
        ('analytical', 1, 3),
        ('creative', -1, 0),
    ],
}


class PersonalityDynamics:
    """
    Manages personality evolution for all agents in a simulation.

    Usage:
        engine = PersonalityDynamics()
        engine.initialize_agent('agent_1')
        engine.update_personality('agent_1', 'positive_consensus', round_num=3)
        snapshot = engine.get_personality_snapshot('agent_1', round=3)
        trajectory = engine.get_personality_trajectory('agent_1')
    """

    def __init__(self):
        # agent_id -> current PersonalityVector
        self._current: Dict[str, PersonalityVector] = {}
        # agent_id -> list of PersonalitySnapshot (chronological)
        self._history: Dict[str, List[PersonalitySnapshot]] = {}

    def initialize_agent(
        self,
        agent_id: str,
        initial_vector: Optional[Dict[str, int]] = None,
    ) -> PersonalityVector:
        """Set up an agent with an initial personality vector."""
        if initial_vector:
            vec = PersonalityVector.from_dict(initial_vector).clamp()
        else:
            vec = PersonalityVector.random_initial()

        self._current[agent_id] = vec
        self._history[agent_id] = [
            PersonalitySnapshot(agent_id=agent_id, round_num=0, vector=deepcopy(vec), trigger='initial')
        ]
        logger.info(f"Initialized personality for agent {agent_id}: {vec.to_dict()}")
        return vec

    def update_personality(
        self,
        agent_id: str,
        interaction_outcome: str,
        round_num: int = 0,
    ) -> PersonalityVector:
        """
        Apply subtle personality shifts based on an interaction outcome.

        Args:
            agent_id: The agent whose personality to update.
            interaction_outcome: One of the keys in OUTCOME_EFFECTS.
            round_num: Current simulation round.

        Returns:
            Updated PersonalityVector (clamped to 20-80).
        """
        if agent_id not in self._current:
            logger.warning(f"Agent {agent_id} not initialized, auto-initializing")
            self.initialize_agent(agent_id)

        effects = OUTCOME_EFFECTS.get(interaction_outcome)
        if not effects:
            logger.warning(f"Unknown interaction outcome: {interaction_outcome}")
            return self._current[agent_id]

        vec = self._current[agent_id]
        for trait, lo, hi in effects:
            delta = random.randint(min(lo, hi), max(lo, hi))
            old_val = getattr(vec, trait)
            setattr(vec, trait, old_val + delta)

        vec.clamp()
        self._current[agent_id] = vec

        snapshot = PersonalitySnapshot(
            agent_id=agent_id,
            round_num=round_num,
            vector=deepcopy(vec),
            trigger=interaction_outcome,
        )
        self._history[agent_id].append(snapshot)

        logger.debug(
            f"Agent {agent_id} personality updated (trigger={interaction_outcome}, round={round_num}): "
            f"{vec.to_dict()}"
        )
        return vec

    def get_personality_snapshot(
        self,
        agent_id: str,
        round_num: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get personality vector at a specific round (or latest if round is None).

        Returns dict with agent_id, round_num, vector, trigger — or None if not found.
        """
        history = self._history.get(agent_id)
        if not history:
            return None

        if round_num is None:
            return history[-1].to_dict()

        # Find the last snapshot at or before the requested round
        result = None
        for snap in history:
            if snap.round_num <= round_num:
                result = snap
            else:
                break
        return result.to_dict() if result else None

    def get_personality_trajectory(self, agent_id: str) -> List[Dict[str, Any]]:
        """Return full personality evolution timeline for an agent."""
        history = self._history.get(agent_id, [])
        return [snap.to_dict() for snap in history]

    def get_all_agents(self) -> Dict[str, Dict[str, int]]:
        """Return current personality vectors for all agents."""
        return {aid: vec.to_dict() for aid, vec in self._current.items()}

    def get_agent_ids(self) -> List[str]:
        """Return list of all tracked agent IDs."""
        return list(self._current.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize full engine state."""
        return {
            'agents': {
                aid: {
                    'current': vec.to_dict(),
                    'history': [s.to_dict() for s in self._history.get(aid, [])],
                }
                for aid, vec in self._current.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityDynamics':
        """Restore engine from serialized state."""
        engine = cls()
        for aid, agent_data in data.get('agents', {}).items():
            engine._current[aid] = PersonalityVector.from_dict(agent_data['current'])
            engine._history[aid] = [
                PersonalitySnapshot(
                    agent_id=aid,
                    round_num=s['round_num'],
                    vector=PersonalityVector.from_dict(s['vector']),
                    trigger=s.get('trigger'),
                )
                for s in agent_data.get('history', [])
            ]
        return engine


# Singleton for in-process use across simulation rounds
_engines: Dict[str, PersonalityDynamics] = {}


def get_engine(simulation_id: str) -> PersonalityDynamics:
    """Get or create a PersonalityDynamics engine for a simulation."""
    if simulation_id not in _engines:
        _engines[simulation_id] = PersonalityDynamics()
        logger.info(f"Created personality engine for simulation {simulation_id}")
    return _engines[simulation_id]


def remove_engine(simulation_id: str) -> None:
    """Clean up engine when simulation ends."""
    _engines.pop(simulation_id, None)
