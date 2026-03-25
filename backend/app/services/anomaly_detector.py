"""
Behavior anomaly detection service.
Detects unexpected agent behaviors using Z-score analysis
of action frequency patterns across simulation rounds.
"""

import math
import random
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
from datetime import datetime

from ..config import Config
from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner
from .simulation_manager import SimulationManager
from .behavior_predictor import ACTION_TYPE_MAP

logger = get_logger('mirofish.anomaly_detector')

ANOMALY_TYPES = [
    'sentiment_reversal',
    'unexpected_agreement',
    'leadership_emergence',
    'topic_hijacking',
    'sudden_silence',
    'activity_spike',
]


class AnomalyDetector:
    """Detects unexpected agent behaviors via Z-score outlier analysis."""

    def __init__(self):
        self.manager = SimulationManager()

    def detect_anomalies(
        self,
        simulation_id: str,
        target_round: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in a simulation, optionally for a specific round.

        Uses Z-score of per-agent action counts across rounds to find outliers.
        """
        all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
        if not all_actions:
            return self._mock_anomalies()

        # Build per-agent per-round action counts
        agent_round_counts: Dict[int, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        agent_round_categories: Dict[int, Dict[int, Counter]] = defaultdict(
            lambda: defaultdict(Counter)
        )
        for a in all_actions:
            agent_round_counts[a.agent_id][a.round_num] += 1
            cat = ACTION_TYPE_MAP.get(a.action_type, 'propose_new_idea')
            agent_round_categories[a.agent_id][a.round_num][cat] += 1

        anomalies = []
        for agent_id, round_counts in agent_round_counts.items():
            counts = list(round_counts.values())
            if len(counts) < 2:
                continue

            mean = sum(counts) / len(counts)
            variance = sum((c - mean) ** 2 for c in counts) / len(counts)
            std = math.sqrt(variance) if variance > 0 else 1.0

            for rnd, count in round_counts.items():
                if target_round is not None and rnd != target_round:
                    continue

                z_score = (count - mean) / std if std > 0 else 0

                if abs(z_score) >= 1.5:
                    anomaly = self._classify_anomaly(
                        agent_id, rnd, z_score, count, mean,
                        agent_round_categories[agent_id],
                    )
                    anomalies.append(anomaly)

        anomalies.sort(key=lambda a: a['surprise_score'], reverse=True)
        return anomalies

    def score_surprise(self, event: Dict[str, Any]) -> float:
        """Score how surprising an event is (0-1)."""
        z = abs(event.get('z_score', 0))
        # Sigmoid-like mapping: z=1.5 → ~0.4, z=3 → ~0.8, z=5 → ~0.95
        return round(min(1.0, 1.0 - 1.0 / (1.0 + z * 0.4)), 3)

    def explain_anomaly(self, anomaly: Dict[str, Any]) -> str:
        """Generate a human-readable explanation for an anomaly."""
        atype = anomaly.get('anomaly_type', 'unknown')
        agent = anomaly.get('agent_id', '?')
        rnd = anomaly.get('round', '?')
        score = anomaly.get('surprise_score', 0)

        explanations = {
            'activity_spike': (
                f"Agent {agent} had an unusual surge of activity in round {rnd}, "
                f"far exceeding their typical behavior pattern."
            ),
            'sudden_silence': (
                f"Agent {agent} went unexpectedly quiet in round {rnd}, "
                f"dropping well below their usual activity level."
            ),
            'sentiment_reversal': (
                f"Agent {agent} reversed their sentiment direction in round {rnd}, "
                f"switching from predominantly agreeing to disagreeing or vice versa."
            ),
            'unexpected_agreement': (
                f"Agent {agent} showed unexpected agreement in round {rnd}, "
                f"despite a history of disagreement."
            ),
            'leadership_emergence': (
                f"Agent {agent} emerged as a leader in round {rnd}, "
                f"suddenly proposing ideas and making decisions after being passive."
            ),
            'topic_hijacking': (
                f"Agent {agent} shifted the conversation direction significantly "
                f"in round {rnd}."
            ),
        }
        return explanations.get(atype, f"Unusual behavior by agent {agent} in round {rnd} (surprise: {score}).")

    def get_influence_graph(self, simulation_id: str) -> Dict[str, Any]:
        """
        Build an influence flow graph from agent interaction data.

        Returns nodes (agents) and edges (interaction frequency).
        """
        all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
        if not all_actions:
            return self._mock_influence_graph()

        agent_names: Dict[int, str] = {}
        agent_action_counts: Counter = Counter()
        interaction_pairs: Counter = Counter()

        for a in all_actions:
            agent_names[a.agent_id] = a.agent_name
            agent_action_counts[a.agent_id] += 1

        # Build interaction edges based on sequential actions within same round/platform
        actions_by_round = defaultdict(list)
        for a in all_actions:
            actions_by_round[(a.round_num, a.platform)].append(a)

        for key, round_actions in actions_by_round.items():
            round_actions.sort(key=lambda x: x.timestamp)
            for i in range(len(round_actions) - 1):
                src = round_actions[i].agent_id
                tgt = round_actions[i + 1].agent_id
                if src != tgt:
                    interaction_pairs[(src, tgt)] += 1

        nodes = [
            {
                'id': aid,
                'name': agent_names.get(aid, f'Agent {aid}'),
                'action_count': agent_action_counts[aid],
                'influence_score': round(
                    agent_action_counts[aid]
                    / max(sum(agent_action_counts.values()), 1)
                    * 100,
                    1,
                ),
            }
            for aid in sorted(agent_names.keys())
        ]

        edges = [
            {'source': src, 'target': tgt, 'weight': weight}
            for (src, tgt), weight in interaction_pairs.most_common(50)
        ]

        return {'nodes': nodes, 'edges': edges}

    def get_patterns(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Detect recurring behavior patterns across agents."""
        all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
        if not all_actions:
            return self._mock_patterns()

        agent_sequences: Dict[int, List[str]] = defaultdict(list)
        agent_names: Dict[int, str] = {}
        for a in sorted(all_actions, key=lambda x: (x.round_num, x.timestamp)):
            cat = ACTION_TYPE_MAP.get(a.action_type, 'propose_new_idea')
            agent_sequences[a.agent_id].append(cat)
            agent_names[a.agent_id] = a.agent_name

        patterns = []
        for aid, seq in agent_sequences.items():
            if len(seq) < 3:
                continue

            # Detect repeated bigrams
            bigrams = [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
            bigram_counts = Counter(bigrams)
            for (a, b), count in bigram_counts.most_common(3):
                if count < 2:
                    continue
                freq = count / len(bigrams)
                patterns.append({
                    'agent_id': aid,
                    'agent_name': agent_names.get(aid, f'Agent {aid}'),
                    'pattern': f'{a} → {b}',
                    'description': f'{agent_names.get(aid, f"Agent {aid}")} tends to {b} after {a}',
                    'frequency': count,
                    'consistency': round(freq, 3),
                })

        patterns.sort(key=lambda p: p['frequency'], reverse=True)
        return patterns[:20]

    # -- Internal helpers --

    def _classify_anomaly(
        self,
        agent_id: int,
        round_num: int,
        z_score: float,
        actual_count: int,
        mean_count: float,
        round_categories: Dict[int, Counter],
    ) -> Dict[str, Any]:
        """Classify an anomaly based on the z-score direction and action categories."""
        if z_score > 2.0:
            cats = round_categories.get(round_num, Counter())
            if cats.get('propose_new_idea', 0) > cats.get('agree', 0):
                atype = 'leadership_emergence'
            else:
                atype = 'activity_spike'
        elif z_score < -2.0:
            atype = 'sudden_silence'
        else:
            # Check for category shifts
            current_cats = round_categories.get(round_num, Counter())
            prev_rounds = [
                r for r in round_categories if r < round_num
            ]
            if prev_rounds:
                prev_cat = Counter()
                for r in prev_rounds:
                    prev_cat.update(round_categories[r])
                prev_dominant = prev_cat.most_common(1)[0][0] if prev_cat else None
                curr_dominant = (
                    current_cats.most_common(1)[0][0] if current_cats else None
                )
                if prev_dominant == 'disagree' and curr_dominant == 'agree':
                    atype = 'unexpected_agreement'
                elif prev_dominant == 'agree' and curr_dominant == 'disagree':
                    atype = 'sentiment_reversal'
                else:
                    atype = 'topic_hijacking'
            else:
                atype = 'activity_spike' if z_score > 0 else 'sudden_silence'

        surprise = self.score_surprise({'z_score': z_score})
        anomaly = {
            'agent_id': agent_id,
            'round': round_num,
            'anomaly_type': atype,
            'surprise_score': surprise,
            'z_score': round(z_score, 3),
            'actual_actions': actual_count,
            'expected_actions': round(mean_count, 1),
            'explanation': '',
        }
        anomaly['explanation'] = self.explain_anomaly(anomaly)
        return anomaly

    # -- Mock data for demo mode --

    def _mock_anomalies(self) -> List[Dict[str, Any]]:
        rng = random.Random(42)
        mock = []
        for i in range(5):
            atype = rng.choice(ANOMALY_TYPES)
            z = rng.uniform(1.5, 4.0)
            anomaly = {
                'agent_id': rng.randint(1, 8),
                'round': rng.randint(1, 10),
                'anomaly_type': atype,
                'surprise_score': self.score_surprise({'z_score': z}),
                'z_score': round(z, 3),
                'actual_actions': rng.randint(8, 20),
                'expected_actions': round(rng.uniform(3, 7), 1),
                'explanation': '',
                'demo': True,
            }
            anomaly['explanation'] = self.explain_anomaly(anomaly)
            mock.append(anomaly)
        mock.sort(key=lambda a: a['surprise_score'], reverse=True)
        return mock

    def _mock_influence_graph(self) -> Dict[str, Any]:
        rng = random.Random(42)
        nodes = [
            {'id': i, 'name': f'Agent {i}', 'action_count': rng.randint(5, 30),
             'influence_score': round(rng.uniform(5, 25), 1)}
            for i in range(1, 9)
        ]
        edges = []
        for i in range(1, 9):
            for j in range(1, 9):
                if i != j and rng.random() > 0.6:
                    edges.append({'source': i, 'target': j, 'weight': rng.randint(1, 8)})
        return {'nodes': nodes, 'edges': edges, 'demo': True}

    def _mock_patterns(self) -> List[Dict[str, Any]]:
        rng = random.Random(42)
        templates = [
            ('agree → propose_new_idea', 'tends to propose new ideas after agreeing'),
            ('disagree → ask_question', 'asks questions after disagreeing'),
            ('stay_silent → agree', 'tends to agree after periods of silence'),
            ('propose_new_idea → agree', 'gets agreement after proposing ideas'),
            ('ask_question → make_decision', 'makes decisions after asking questions'),
        ]
        patterns = []
        for i, (pattern, desc_suffix) in enumerate(templates):
            aid = rng.randint(1, 8)
            patterns.append({
                'agent_id': aid,
                'agent_name': f'Agent {aid}',
                'pattern': pattern,
                'description': f'Agent {aid} {desc_suffix}',
                'frequency': rng.randint(3, 12),
                'consistency': round(rng.uniform(0.15, 0.6), 3),
                'demo': True,
            })
        return patterns
