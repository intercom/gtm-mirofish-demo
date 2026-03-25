"""
Agent behavior prediction service.
Predicts next actions, consensus timing, and outcomes using
frequency-based Bayesian analysis of past simulation rounds.
"""

import random
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from ..config import Config
from ..utils.logger import get_logger
from .simulation_manager import SimulationManager
from .simulation_runner import SimulationRunner

logger = get_logger('mirofish.behavior_predictor')

ACTION_CATEGORIES = [
    'agree', 'disagree', 'propose_new_idea',
    'ask_question', 'make_decision', 'stay_silent',
]

# Map raw OASIS action types to prediction categories
ACTION_TYPE_MAP = {
    'CREATE_POST': 'propose_new_idea',
    'CREATE_COMMENT': 'agree',
    'LIKE_POST': 'agree',
    'LIKE_COMMENT': 'agree',
    'DISLIKE_POST': 'disagree',
    'DISLIKE_COMMENT': 'disagree',
    'REPOST': 'agree',
    'QUOTE_POST': 'propose_new_idea',
    'FOLLOW': 'agree',
    'SEARCH_POSTS': 'ask_question',
    'SEARCH_USER': 'ask_question',
    'TREND': 'ask_question',
    'REFRESH': 'stay_silent',
    'DO_NOTHING': 'stay_silent',
    'MUTE': 'disagree',
}


class BehaviorPredictor:
    """Predicts agent behavior using frequency-based Bayesian analysis."""

    def __init__(self):
        self.manager = SimulationManager()

    def predict_next_action(
        self, simulation_id: str, agent_id: int, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Predict the next action for a specific agent.

        Returns predicted action with confidence and probability distribution.
        """
        actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id, agent_id=agent_id
        )

        if not actions:
            return self._mock_agent_prediction(agent_id)

        category_counts = Counter()
        for a in actions:
            cat = ACTION_TYPE_MAP.get(a.action_type, 'propose_new_idea')
            category_counts[cat] += 1

        total = sum(category_counts.values())
        probabilities = {
            cat: category_counts.get(cat, 0) / total for cat in ACTION_CATEGORIES
        }

        predicted = max(probabilities, key=probabilities.get)
        confidence = probabilities[predicted]

        return {
            'agent_id': agent_id,
            'predicted_action': predicted,
            'confidence': round(confidence, 3),
            'probabilities': {k: round(v, 3) for k, v in probabilities.items()},
            'based_on_actions': total,
        }

    def predict_all_agents(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Predict next actions for all agents in a simulation."""
        state = self.manager.get_simulation(simulation_id)
        if not state:
            return self._mock_all_predictions()

        all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
        if not all_actions:
            return self._mock_all_predictions()

        agent_ids = {a.agent_id for a in all_actions}
        return [
            self.predict_next_action(simulation_id, aid) for aid in sorted(agent_ids)
        ]

    def predict_consensus_round(self, simulation_id: str) -> Dict[str, Any]:
        """Estimate the round when the group reaches consensus."""
        all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
        if not all_actions:
            return self._mock_consensus()

        rounds = defaultdict(lambda: Counter())
        for a in all_actions:
            cat = ACTION_TYPE_MAP.get(a.action_type, 'propose_new_idea')
            rounds[a.round_num][cat] += 1

        agreement_ratios = []
        for rnd in sorted(rounds.keys()):
            total = sum(rounds[rnd].values())
            agree_count = rounds[rnd].get('agree', 0)
            agreement_ratios.append(agree_count / total if total > 0 else 0)

        current_round = max(rounds.keys()) if rounds else 0

        if len(agreement_ratios) >= 2:
            trend = agreement_ratios[-1] - agreement_ratios[0]
            if trend > 0 and agreement_ratios[-1] < 1.0:
                remaining = (1.0 - agreement_ratios[-1]) / max(
                    trend / len(agreement_ratios), 0.01
                )
                estimated_round = current_round + int(remaining) + 1
            else:
                estimated_round = current_round + 5
        else:
            estimated_round = current_round + 5

        return {
            'current_round': current_round,
            'estimated_consensus_round': estimated_round,
            'current_agreement_ratio': round(
                agreement_ratios[-1] if agreement_ratios else 0, 3
            ),
            'trend': 'increasing'
            if len(agreement_ratios) >= 2
            and agreement_ratios[-1] > agreement_ratios[0]
            else 'stable',
            'confidence': round(
                min(0.9, 0.3 + len(agreement_ratios) * 0.1), 3
            ),
        }

    def predict_outcome(self, simulation_id: str) -> Dict[str, Any]:
        """Predict the final state of the simulation."""
        all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
        if not all_actions:
            return self._mock_outcome()

        agent_stats = defaultdict(lambda: Counter())
        for a in all_actions:
            cat = ACTION_TYPE_MAP.get(a.action_type, 'propose_new_idea')
            agent_stats[a.agent_id][cat] += 1

        agent_influence = {}
        for aid, counts in agent_stats.items():
            total = sum(counts.values())
            influence = (
                counts.get('propose_new_idea', 0) * 2
                + counts.get('make_decision', 0) * 3
                + counts.get('agree', 0)
                - counts.get('stay_silent', 0)
            )
            agent_influence[aid] = influence

        if agent_influence:
            dominant_agent = max(agent_influence, key=agent_influence.get)
        else:
            dominant_agent = None

        total_actions = len(all_actions)
        agree_count = sum(
            1
            for a in all_actions
            if ACTION_TYPE_MAP.get(a.action_type) == 'agree'
        )
        disagree_count = sum(
            1
            for a in all_actions
            if ACTION_TYPE_MAP.get(a.action_type) == 'disagree'
        )

        sentiment = round(
            (agree_count - disagree_count) / max(total_actions, 1) * 10, 2
        )

        return {
            'predicted_sentiment': max(-10, min(10, sentiment)),
            'dominant_agent_id': dominant_agent,
            'predicted_outcome': 'consensus'
            if agree_count > disagree_count * 2
            else 'divided',
            'agent_influence_scores': {
                str(k): round(v, 2) for k, v in agent_influence.items()
            },
            'confidence': round(
                min(0.85, 0.2 + total_actions * 0.005), 3
            ),
            'total_actions_analyzed': total_actions,
        }

    def predict_what_if(
        self,
        simulation_id: str,
        modifications: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run a what-if prediction with modified agent traits.

        modifications: [{agent_id, trait, new_value}]
        """
        base_outcome = self.predict_outcome(simulation_id)

        adjusted_sentiment = base_outcome.get('predicted_sentiment', 0)
        for mod in modifications:
            trait = mod.get('trait', '')
            new_value = mod.get('new_value', 0.5)
            if trait in ('assertive', 'risk_tolerant'):
                adjusted_sentiment += (new_value - 0.5) * 2
            elif trait == 'empathetic':
                adjusted_sentiment += (new_value - 0.5) * 1.5
            elif trait == 'analytical':
                adjusted_sentiment += (new_value - 0.5) * 0.5

        adjusted_sentiment = max(-10, min(10, round(adjusted_sentiment, 2)))

        return {
            'baseline_outcome': base_outcome,
            'modifications_applied': modifications,
            'predicted_outcome': {
                'predicted_sentiment': adjusted_sentiment,
                'predicted_result': 'consensus'
                if adjusted_sentiment > 2
                else 'divided',
                'confidence': round(
                    max(0.1, base_outcome.get('confidence', 0.5) - 0.15), 3
                ),
            },
            'delta': {
                'sentiment_change': round(
                    adjusted_sentiment
                    - base_outcome.get('predicted_sentiment', 0),
                    2,
                ),
            },
        }

    # -- Mock data generators for demo mode --

    def _mock_agent_prediction(self, agent_id: int) -> Dict[str, Any]:
        rng = random.Random(agent_id)
        probs = {cat: rng.random() for cat in ACTION_CATEGORIES}
        total = sum(probs.values())
        probs = {k: round(v / total, 3) for k, v in probs.items()}
        predicted = max(probs, key=probs.get)
        return {
            'agent_id': agent_id,
            'predicted_action': predicted,
            'confidence': probs[predicted],
            'probabilities': probs,
            'based_on_actions': 0,
            'demo': True,
        }

    def _mock_all_predictions(self) -> List[Dict[str, Any]]:
        return [self._mock_agent_prediction(i) for i in range(1, 9)]

    def _mock_consensus(self) -> Dict[str, Any]:
        return {
            'current_round': 3,
            'estimated_consensus_round': 8,
            'current_agreement_ratio': 0.45,
            'trend': 'increasing',
            'confidence': 0.55,
            'demo': True,
        }

    def _mock_outcome(self) -> Dict[str, Any]:
        return {
            'predicted_sentiment': 3.2,
            'dominant_agent_id': 2,
            'predicted_outcome': 'consensus',
            'agent_influence_scores': {
                '1': 12.0, '2': 18.5, '3': 8.0, '4': 15.2,
                '5': 6.0, '6': 11.0, '7': 9.5, '8': 7.0,
            },
            'confidence': 0.62,
            'total_actions_analyzed': 0,
            'demo': True,
        }
