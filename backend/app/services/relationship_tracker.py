"""
Agent Relationship Tracker

Tracks pairwise relationships between agents based on their simulation interactions.
Computes affinity scores, detects alliances (agreement clusters), and conflicts.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ..utils.logger import get_logger

logger = get_logger('mirofish.relationship_tracker')


@dataclass
class Relationship:
    """Pairwise relationship between two agents."""
    agent_a_id: int
    agent_a_name: str
    agent_b_id: int
    agent_b_name: str
    affinity: float = 0.0  # -1 to 1
    agreements: int = 0
    disagreements: int = 0
    neutral_interactions: int = 0
    topics: List[str] = field(default_factory=list)
    last_round: int = 0

    @property
    def interaction_count(self) -> int:
        return self.agreements + self.disagreements + self.neutral_interactions

    @property
    def agreement_rate(self) -> float:
        if self.interaction_count == 0:
            return 0.0
        return self.agreements / self.interaction_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_a_id": self.agent_a_id,
            "agent_a_name": self.agent_a_name,
            "agent_b_id": self.agent_b_id,
            "agent_b_name": self.agent_b_name,
            "affinity": round(self.affinity, 3),
            "agreements": self.agreements,
            "disagreements": self.disagreements,
            "neutral_interactions": self.neutral_interactions,
            "interaction_count": self.interaction_count,
            "agreement_rate": round(self.agreement_rate, 3),
            "topics": self.topics[-10:],  # last 10 topics
            "last_round": self.last_round,
        }


# Interaction types inferred from action combinations
AGREEMENT_ACTIONS = {'LIKE_POST', 'UPVOTE', 'REPOST', 'RETWEET', 'SHARE', 'FOLLOW'}
DISAGREEMENT_KEYWORDS = [
    'disagree', 'wrong', 'incorrect', 'no way', 'terrible', 'bad take',
    'skeptical', 'doubt', 'opposed', 'against', 'reject', 'dismiss',
]
AGREEMENT_KEYWORDS = [
    'agree', 'exactly', 'great point', 'well said', 'correct', 'right',
    'support', 'endorse', 'seconded', 'same here', 'absolutely', 'true',
]


class RelationshipTracker:
    """
    Tracks and computes relationships between simulation agents.

    Relationships are derived from agent actions:
    - Like/repost/follow → agreement (+0.1 affinity)
    - Reply/comment with positive sentiment → agreement (+0.1)
    - Reply/comment with negative sentiment → disagreement (-0.1)
    - Other interactions → neutral (+0.05)
    - Decay: affinity *= 0.95 per round without interaction
    """

    AFFINITY_AGREE = 0.1
    AFFINITY_DISAGREE = -0.1
    AFFINITY_NEUTRAL = 0.05
    DECAY_FACTOR = 0.95

    def __init__(self):
        self._relationships: Dict[Tuple[int, int], Relationship] = {}
        self._agent_names: Dict[int, str] = {}

    def _key(self, agent_a: int, agent_b: int) -> Tuple[int, int]:
        return (min(agent_a, agent_b), max(agent_a, agent_b))

    def _get_or_create(self, agent_a_id: int, agent_b_id: int) -> Relationship:
        key = self._key(agent_a_id, agent_b_id)
        if key not in self._relationships:
            self._relationships[key] = Relationship(
                agent_a_id=key[0],
                agent_a_name=self._agent_names.get(key[0], f"Agent {key[0]}"),
                agent_b_id=key[1],
                agent_b_name=self._agent_names.get(key[1], f"Agent {key[1]}"),
            )
        return self._relationships[key]

    def update_relationship(self, agent_a_id: int, agent_b_id: int,
                            interaction_type: str, topic: str = "",
                            round_num: int = 0):
        """
        Update relationship based on an interaction.

        Args:
            agent_a_id: The agent performing the action
            agent_b_id: The agent being acted upon
            interaction_type: 'agreement', 'disagreement', or 'neutral'
            topic: Optional topic/content snippet
            round_num: The simulation round
        """
        if agent_a_id == agent_b_id:
            return

        rel = self._get_or_create(agent_a_id, agent_b_id)

        if interaction_type == 'agreement':
            rel.affinity = min(1.0, rel.affinity + self.AFFINITY_AGREE)
            rel.agreements += 1
        elif interaction_type == 'disagreement':
            rel.affinity = max(-1.0, rel.affinity + self.AFFINITY_DISAGREE)
            rel.disagreements += 1
        else:
            rel.affinity = min(1.0, rel.affinity + self.AFFINITY_NEUTRAL)
            rel.neutral_interactions += 1

        if topic and topic not in rel.topics:
            rel.topics.append(topic)

        rel.last_round = max(rel.last_round, round_num)

    def apply_decay(self, current_round: int):
        """Apply decay to relationships that had no interaction this round."""
        for rel in self._relationships.values():
            if rel.last_round < current_round:
                rel.affinity *= self.DECAY_FACTOR
                if abs(rel.affinity) < 0.001:
                    rel.affinity = 0.0

    def get_relationship(self, agent_a_id: int, agent_b_id: int) -> Optional[Dict[str, Any]]:
        key = self._key(agent_a_id, agent_b_id)
        rel = self._relationships.get(key)
        return rel.to_dict() if rel else None

    def get_agent_relationships(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get all relationships for a specific agent."""
        results = []
        for key, rel in self._relationships.items():
            if agent_id in key:
                results.append(rel.to_dict())
        return sorted(results, key=lambda r: abs(r['affinity']), reverse=True)

    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get the complete relationship graph."""
        return [rel.to_dict() for rel in self._relationships.values()
                if rel.interaction_count > 0]

    def get_alliances(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Detect groups of agents who consistently agree.
        Uses a simple connected-components approach on positive-affinity edges.
        """
        # Build adjacency list of positive relationships
        adj: Dict[int, set] = defaultdict(set)
        for rel in self._relationships.values():
            if rel.affinity >= threshold and rel.interaction_count >= 2:
                adj[rel.agent_a_id].add(rel.agent_b_id)
                adj[rel.agent_b_id].add(rel.agent_a_id)

        # Find connected components via BFS
        visited = set()
        alliances = []

        for agent_id in adj:
            if agent_id in visited:
                continue
            component = set()
            queue = [agent_id]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)

            if len(component) >= 2:
                members = sorted(component)
                avg_affinity = self._avg_affinity_in_group(members)
                alliances.append({
                    "members": [
                        {"id": m, "name": self._agent_names.get(m, f"Agent {m}")}
                        for m in members
                    ],
                    "size": len(members),
                    "avg_affinity": round(avg_affinity, 3),
                })

        return sorted(alliances, key=lambda a: a['size'], reverse=True)

    def get_conflicts(self, threshold: float = -0.2) -> List[Dict[str, Any]]:
        """Detect pairs of agents who consistently disagree."""
        conflicts = []
        for rel in self._relationships.values():
            if rel.affinity <= threshold and rel.interaction_count >= 2:
                conflicts.append({
                    "agent_a": {"id": rel.agent_a_id, "name": rel.agent_a_name},
                    "agent_b": {"id": rel.agent_b_id, "name": rel.agent_b_name},
                    "affinity": round(rel.affinity, 3),
                    "disagreements": rel.disagreements,
                    "interaction_count": rel.interaction_count,
                })
        return sorted(conflicts, key=lambda c: c['affinity'])

    def get_prompt_context(self, agent_id: int, top_n: int = 3) -> str:
        """
        Generate relationship context string for agent prompts.
        E.g. "You trust Agent X but disagree with Agent Y."
        """
        rels = self.get_agent_relationships(agent_id)
        if not rels:
            return ""

        trusted = []
        distrusted = []
        for r in rels[:top_n * 2]:
            other_name = r['agent_b_name'] if r['agent_a_id'] == agent_id else r['agent_a_name']
            if r['affinity'] > 0.2:
                trusted.append(other_name)
            elif r['affinity'] < -0.2:
                distrusted.append(other_name)

        parts = []
        if trusted[:top_n]:
            parts.append(f"You trust {', '.join(trusted[:top_n])}")
        if distrusted[:top_n]:
            parts.append(f"you disagree with {', '.join(distrusted[:top_n])}")

        if not parts:
            return ""
        return parts[0] + (" but " + parts[1] if len(parts) > 1 else "") + "."

    def _avg_affinity_in_group(self, members: List[int]) -> float:
        member_set = set(members)
        total = 0.0
        count = 0
        for key, rel in self._relationships.items():
            if key[0] in member_set and key[1] in member_set:
                total += rel.affinity
                count += 1
        return total / count if count else 0.0

    @classmethod
    def classify_interaction(cls, action_type: str, content: str = "") -> str:
        """
        Classify an action as agreement, disagreement, or neutral.

        Args:
            action_type: The action type (LIKE_POST, CREATE_COMMENT, etc.)
            content: Optional content text for sentiment analysis
        """
        upper_type = action_type.upper()

        # Direct agreement actions
        if any(a in upper_type for a in AGREEMENT_ACTIONS):
            return 'agreement'

        # For replies/comments, check content sentiment
        if 'REPLY' in upper_type or 'COMMENT' in upper_type:
            if content:
                lower = content.lower()
                disagree_score = sum(1 for kw in DISAGREEMENT_KEYWORDS if kw in lower)
                agree_score = sum(1 for kw in AGREEMENT_KEYWORDS if kw in lower)
                if disagree_score > agree_score:
                    return 'disagreement'
                if agree_score > disagree_score:
                    return 'agreement'
            return 'neutral'

        return 'neutral'

    @classmethod
    def build_from_actions(cls, actions: list) -> 'RelationshipTracker':
        """
        Build a RelationshipTracker from a list of AgentAction objects.

        This analyzes all actions to infer agent-to-agent relationships by
        detecting who interacted with whose content.
        """
        tracker = cls()

        # First pass: build agent name mapping and index posts by content/ID
        post_authors: Dict[str, int] = {}  # post content hash → agent_id

        for action in actions:
            tracker._agent_names[action.agent_id] = action.agent_name

            upper_type = action.action_type.upper()
            args = action.action_args or {}

            # Track post authorship
            if 'CREATE_POST' in upper_type or 'CREATE_THREAD' in upper_type:
                content = args.get('content', '')
                if content:
                    post_authors[content[:100]] = action.agent_id

        # Second pass: detect interactions
        for action in actions:
            upper_type = action.action_type.upper()
            args = action.action_args or {}

            target_agent_id = None
            content = args.get('content', '')

            # Try to find the target agent from action args
            if 'post_id' in args or 'parent_post_id' in args:
                # Look up who created the post being interacted with
                ref_content = args.get('original_content', args.get('post_content', ''))
                if ref_content:
                    target_agent_id = post_authors.get(ref_content[:100])

            if 'target_user_id' in args:
                target_agent_id = args['target_user_id']
            elif 'author_id' in args:
                target_agent_id = args['author_id']

            if target_agent_id is None or target_agent_id == action.agent_id:
                continue

            interaction_type = cls.classify_interaction(action.action_type, content)
            topic = content[:50] if content else ""

            tracker.update_relationship(
                agent_a_id=action.agent_id,
                agent_b_id=target_agent_id,
                interaction_type=interaction_type,
                topic=topic,
                round_num=action.round_num,
            )

        # Apply decay for the final round
        if actions:
            max_round = max(a.round_num for a in actions)
            tracker.apply_decay(max_round)

        return tracker

    @classmethod
    def build_from_simulation(cls, simulation_id: str) -> 'RelationshipTracker':
        """
        Build relationships from a simulation's saved action logs.

        Args:
            simulation_id: The simulation ID to analyze
        """
        from .simulation_runner import SimulationRunner

        actions = SimulationRunner.get_all_actions(simulation_id)
        if not actions:
            logger.info(f"No actions found for simulation {simulation_id}")
            return cls()

        logger.info(f"Building relationships from {len(actions)} actions for {simulation_id}")
        return cls.build_from_actions(actions)

    @classmethod
    def get_demo_data(cls) -> Dict[str, Any]:
        """Return mock relationship data for demo mode."""
        agents = [
            {"id": 0, "name": "Sarah Chen"},
            {"id": 1, "name": "Marcus Rivera"},
            {"id": 2, "name": "Priya Patel"},
            {"id": 3, "name": "James Morrison"},
            {"id": 4, "name": "Elena Volkov"},
            {"id": 5, "name": "David Kim"},
        ]

        relationships = [
            {"agent_a_id": 0, "agent_a_name": "Sarah Chen", "agent_b_id": 1, "agent_b_name": "Marcus Rivera",
             "affinity": 0.65, "agreements": 8, "disagreements": 1, "neutral_interactions": 3,
             "interaction_count": 12, "agreement_rate": 0.667, "topics": ["product strategy", "pricing"], "last_round": 10},
            {"agent_a_id": 0, "agent_a_name": "Sarah Chen", "agent_b_id": 2, "agent_b_name": "Priya Patel",
             "affinity": 0.42, "agreements": 5, "disagreements": 2, "neutral_interactions": 4,
             "interaction_count": 11, "agreement_rate": 0.455, "topics": ["engineering", "timeline"], "last_round": 10},
            {"agent_a_id": 1, "agent_a_name": "Marcus Rivera", "agent_b_id": 3, "agent_b_name": "James Morrison",
             "affinity": -0.35, "agreements": 2, "disagreements": 7, "neutral_interactions": 2,
             "interaction_count": 11, "agreement_rate": 0.182, "topics": ["budget", "hiring"], "last_round": 9},
            {"agent_a_id": 2, "agent_a_name": "Priya Patel", "agent_b_id": 4, "agent_b_name": "Elena Volkov",
             "affinity": 0.55, "agreements": 6, "disagreements": 1, "neutral_interactions": 2,
             "interaction_count": 9, "agreement_rate": 0.667, "topics": ["tech stack", "architecture"], "last_round": 10},
            {"agent_a_id": 3, "agent_a_name": "James Morrison", "agent_b_id": 5, "agent_b_name": "David Kim",
             "affinity": 0.30, "agreements": 4, "disagreements": 2, "neutral_interactions": 3,
             "interaction_count": 9, "agreement_rate": 0.444, "topics": ["marketing", "launch"], "last_round": 8},
            {"agent_a_id": 4, "agent_a_name": "Elena Volkov", "agent_b_id": 5, "agent_b_name": "David Kim",
             "affinity": -0.25, "agreements": 1, "disagreements": 4, "neutral_interactions": 2,
             "interaction_count": 7, "agreement_rate": 0.143, "topics": ["process", "tooling"], "last_round": 10},
            {"agent_a_id": 0, "agent_a_name": "Sarah Chen", "agent_b_id": 5, "agent_b_name": "David Kim",
             "affinity": 0.15, "agreements": 3, "disagreements": 2, "neutral_interactions": 3,
             "interaction_count": 8, "agreement_rate": 0.375, "topics": ["roadmap"], "last_round": 7},
            {"agent_a_id": 1, "agent_a_name": "Marcus Rivera", "agent_b_id": 4, "agent_b_name": "Elena Volkov",
             "affinity": 0.48, "agreements": 5, "disagreements": 1, "neutral_interactions": 2,
             "interaction_count": 8, "agreement_rate": 0.625, "topics": ["innovation", "strategy"], "last_round": 10},
        ]

        alliances = [
            {
                "members": [
                    {"id": 0, "name": "Sarah Chen"},
                    {"id": 1, "name": "Marcus Rivera"},
                    {"id": 4, "name": "Elena Volkov"},
                ],
                "size": 3,
                "avg_affinity": 0.52,
            },
            {
                "members": [
                    {"id": 2, "name": "Priya Patel"},
                    {"id": 4, "name": "Elena Volkov"},
                ],
                "size": 2,
                "avg_affinity": 0.55,
            },
        ]

        conflicts = [
            {
                "agent_a": {"id": 1, "name": "Marcus Rivera"},
                "agent_b": {"id": 3, "name": "James Morrison"},
                "affinity": -0.35,
                "disagreements": 7,
                "interaction_count": 11,
            },
            {
                "agent_a": {"id": 4, "name": "Elena Volkov"},
                "agent_b": {"id": 5, "name": "David Kim"},
                "affinity": -0.25,
                "disagreements": 4,
                "interaction_count": 7,
            },
        ]

        return {
            "agents": agents,
            "relationships": relationships,
            "alliances": alliances,
            "conflicts": conflicts,
        }
