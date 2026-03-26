"""
<<<<<<< HEAD
Coalition detection algorithm for OASIS simulations.

Uses agglomerative clustering on an agent agreement matrix to identify
groups of agents that form alliances based on shared interaction patterns.
Also provides consensus tracking for GTM discussion topics.
"""

import hashlib
import math
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner, AgentAction

logger = get_logger('mirofish.coalition_detector')

# Interaction types that signal agreement/alignment
POSITIVE_INTERACTIONS = {'LIKE_POST', 'LIKE_COMMENT', 'REPOST', 'UPVOTE', 'FOLLOW'}
NEGATIVE_INTERACTIONS = {'DISLIKE_POST', 'DISLIKE_COMMENT', 'MUTE'}
CONTENT_INTERACTIONS = {'CREATE_POST', 'CREATE_COMMENT', 'REPLY', 'QUOTE_POST'}

AGREEMENT_THRESHOLD = 0.6

# GTM discussion topics used across coalition analysis
TOPICS = [
    "AI-powered customer support",
    "Vendor consolidation strategy",
    "ROI of automation tools",
    "Data privacy and compliance",
    "Integration complexity",
    "Customer satisfaction metrics",
]

# Default agent roster for demo mode (matches typical GTM simulation)
DEFAULT_AGENTS = [
    {"agent_id": 0, "agent_name": "Sarah Chen", "role": "VP of Support", "company": "TechCorp"},
    {"agent_id": 1, "agent_name": "Marcus Johnson", "role": "CX Director", "company": "RetailMax"},
    {"agent_id": 2, "agent_name": "Priya Patel", "role": "IT Leader", "company": "FinServe"},
    {"agent_id": 3, "agent_name": "David Kim", "role": "Operations Manager", "company": "HealthPlus"},
    {"agent_id": 4, "agent_name": "Rachel Torres", "role": "CFO", "company": "StartupAI"},
    {"agent_id": 5, "agent_name": "James Wright", "role": "VP of Support", "company": "MediaFlow"},
    {"agent_id": 6, "agent_name": "Aisha Mohammed", "role": "CX Director", "company": "EduTech"},
    {"agent_id": 7, "agent_name": "Tom Nakamura", "role": "CTO", "company": "CloudBase"},
    {"agent_id": 8, "agent_name": "Lisa Park", "role": "Support Manager", "company": "SaaSPro"},
    {"agent_id": 9, "agent_name": "Carlos Rivera", "role": "VP of Sales", "company": "GrowthCo"},
    {"agent_id": 10, "agent_name": "Emma Walsh", "role": "Product Director", "company": "InnovateLab"},
    {"agent_id": 11, "agent_name": "Robert Singh", "role": "IT Director", "company": "SecureNet"},
    {"agent_id": 12, "agent_name": "Nina Volkov", "role": "Operations VP", "company": "LogiTech"},
    {"agent_id": 13, "agent_name": "Michael Brown", "role": "Finance Director", "company": "BudgetWise"},
    {"agent_id": 14, "agent_name": "Yuki Tanaka", "role": "CX Manager", "company": "ServiceFirst"},
]

# Coalition definitions for demo mode
COALITION_DEFS = [
    {
        "id": "innovation_advocates",
        "label": "Innovation Advocates",
        "description": "Pro-AI adoption group favoring rapid technology investment and automation of customer-facing workflows.",
        "shared_positions": ["pro-AI adoption", "automation-first", "competitive differentiation"],
        "base_members": [0, 5, 7, 9, 10],
    },
    {
        "id": "risk_pragmatists",
        "label": "Risk-Conscious Pragmatists",
        "description": "Cautious group prioritizing security, compliance, and proven solutions over bleeding-edge adoption.",
        "shared_positions": ["security-first", "proven solutions", "phased rollout"],
        "base_members": [2, 3, 11, 12],
    },
    {
        "id": "cost_optimizers",
        "label": "Cost Optimizers",
        "description": "ROI-focused coalition advocating for vendor consolidation and measurable returns before investment.",
        "shared_positions": ["ROI-driven", "vendor consolidation", "budget discipline"],
        "base_members": [4, 13],
    },
    {
        "id": "cx_champions",
        "label": "Customer-First Champions",
        "description": "Group centered on customer satisfaction metrics and experience-led decision making.",
        "shared_positions": ["customer satisfaction", "experience-led", "quality over speed"],
        "base_members": [1, 6, 8, 14],
    },
]


def _seeded_float(seed_str: str) -> float:
    """Deterministic float [0, 1) from a seed string."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    return (h % 10000) / 10000.0


def _seeded_int(seed_str: str, lo: int, hi: int) -> int:
    """Deterministic int in [lo, hi] from a seed string."""
    return lo + int(_seeded_float(seed_str) * (hi - lo + 1))


@dataclass
class Coalition:
    """A detected coalition of agents."""
    coalition_id: int
    members: List[Dict[str, Any]]
    shared_positions: List[str]
    formation_round: int
    strength: float
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coalition_id": self.coalition_id,
            "members": self.members,
            "shared_positions": self.shared_positions,
            "formation_round": self.formation_round,
            "strength": round(self.strength, 3),
            "label": self.label,
            "size": len(self.members),
        }


@dataclass
class CoalitionEvolution:
    """Coalition state at a given round."""
    round_num: int
    coalitions: List[Coalition]
    polarization_index: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "coalitions": [c.to_dict() for c in self.coalitions],
            "polarization_index": round(self.polarization_index, 3),
        }


@dataclass
class SwingAgent:
    """An agent that switched coalitions during the simulation."""
    agent_id: int
    agent_name: str
    transitions: List[Dict[str, Any]]
    influence_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "transitions": self.transitions,
            "influence_score": round(self.influence_score, 3),
            "transition_count": len(self.transitions),
        }


class CoalitionDetector:
    """
    Detects coalitions in simulation data using agglomerative clustering
    on an NxN agent agreement matrix.
    """

    def __init__(self, threshold: float = AGREEMENT_THRESHOLD):
        self.threshold = threshold

    def detect_coalitions(self, simulation_id: str) -> List[Coalition]:
        """
        Detect coalitions from simulation action data.

        Algorithm:
        1. Build NxN agreement matrix from agent interactions
        2. Apply agglomerative clustering with threshold
        3. Extract coalition metadata (shared positions, strength)
        """
        actions = SimulationRunner.get_all_actions(simulation_id)
        if not actions:
            return self._generate_demo_coalitions(simulation_id)

        agents = self._extract_agents(actions)
        if len(agents) < 2:
            return []

        agreement_matrix = self._build_agreement_matrix(actions, agents)
        clusters = self._agglomerative_cluster(agents, agreement_matrix)
        coalitions = self._build_coalitions(clusters, actions, agreement_matrix)
        return coalitions

    def track_coalition_evolution(self, simulation_id: str) -> List[CoalitionEvolution]:
        """Track how coalitions form and change across rounds."""
        actions = SimulationRunner.get_all_actions(simulation_id)
        if not actions:
            return self._generate_demo_evolution(simulation_id)

        agents = self._extract_agents(actions)
        if len(agents) < 2:
            return []

        rounds = sorted(set(a.round_num for a in actions))
        evolution = []

        for round_num in rounds:
            round_actions = [a for a in actions if a.round_num <= round_num]
            matrix = self._build_agreement_matrix(round_actions, agents)
            clusters = self._agglomerative_cluster(agents, matrix)
            coalitions = self._build_coalitions(clusters, round_actions, matrix)
            polarization = self._compute_polarization(matrix, agents)
            evolution.append(CoalitionEvolution(
                round_num=round_num,
                coalitions=coalitions,
                polarization_index=polarization,
            ))

        return evolution

    def identify_swing_agents(self, simulation_id: str) -> List[SwingAgent]:
        """Find agents who changed coalitions during the simulation."""
        evolution = self.track_coalition_evolution(simulation_id)
        if len(evolution) < 2:
            return []

        agent_coalition_history: Dict[int, List[Tuple[int, int]]] = defaultdict(list)

        for evo in evolution:
            for coalition in evo.coalitions:
                for member in coalition.members:
                    agent_coalition_history[member["agent_id"]].append(
                        (evo.round_num, coalition.coalition_id)
                    )

        swing_agents = []
        for agent_id, history in agent_coalition_history.items():
            transitions = []
            for i in range(1, len(history)):
                prev_round, prev_coalition = history[i - 1]
                curr_round, curr_coalition = history[i]
                if prev_coalition != curr_coalition:
                    transitions.append({
                        "from_coalition": prev_coalition,
                        "to_coalition": curr_coalition,
                        "at_round": curr_round,
                    })

            if transitions:
                agent_name = self._find_agent_name(agent_id, evolution)
                influence = len(transitions) / len(history)
                swing_agents.append(SwingAgent(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    transitions=transitions,
                    influence_score=min(1.0, influence * 2),
                ))

        swing_agents.sort(key=lambda s: s.influence_score, reverse=True)
        return swing_agents

    def compute_polarization_index(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Compute polarization index over time (0 = consensus, 1 = fully polarized)."""
        actions = SimulationRunner.get_all_actions(simulation_id)
        if not actions:
            return self._generate_demo_polarization()

        agents = self._extract_agents(actions)
        if len(agents) < 2:
            return []

        rounds = sorted(set(a.round_num for a in actions))
        timeline = []

        for round_num in rounds:
            round_actions = [a for a in actions if a.round_num <= round_num]
            matrix = self._build_agreement_matrix(round_actions, agents)
            polarization = self._compute_polarization(matrix, agents)
            timeline.append({
                "round_num": round_num,
                "polarization_index": round(polarization, 3),
            })

        return timeline

    # ── Consensus Tracking ─────────────────────────────────────

    def _load_agents_for_consensus(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Load agents from simulation or use defaults for consensus tracking."""
        try:
            stats = SimulationRunner.get_agent_stats(simulation_id)
            if stats:
                return [
                    {
                        "agent_id": s["agent_id"],
                        "agent_name": s["agent_name"],
                        "role": "Participant",
                        "company": "",
                    }
                    for s in stats
                ]
        except Exception:
            pass
        return list(DEFAULT_AGENTS)

    def _get_total_rounds_for_consensus(self, simulation_id: str) -> int:
        """Get total simulation rounds or use default for consensus tracking."""
        try:
            timeline = SimulationRunner.get_timeline(simulation_id)
            if timeline:
                return max(r["round_num"] for r in timeline) + 1
        except Exception:
            pass
        return _seeded_int(f"{simulation_id}:rounds", 10, 20)

    @staticmethod
    def _seed(simulation_id: str, *parts: str) -> str:
        return f"{simulation_id}:{'|'.join(parts)}"

    def get_consensus(self, simulation_id: str) -> Dict[str, Any]:
        """Track consensus level per discussion topic."""
        agents = self._load_agents_for_consensus(simulation_id)
        total_rounds = self._get_total_rounds_for_consensus(simulation_id)
        topics_data = []

        for i, topic in enumerate(TOPICS):
            base_consensus = _seeded_float(self._seed(simulation_id, "cons_base", topic))
            consensus_level = 0.3 + base_consensus * 0.6
            rounds_to_consensus = _seeded_int(self._seed(simulation_id, "cons_rounds", topic), 4, total_rounds)

            total_agents = len(agents)
            n_for = int(total_agents * consensus_level)
            n_against = _seeded_int(self._seed(simulation_id, "cons_against", topic), 0, total_agents - n_for)
            n_neutral = total_agents - n_for - n_against

            rounds = []
            for rnd in range(total_rounds):
                progress = min(1.0, rnd / max(1, rounds_to_consensus))
                rnd_level = 0.2 + (consensus_level - 0.2) * progress
                noise = (_seeded_float(self._seed(simulation_id, "cons_rnd", topic, str(rnd))) - 0.5) * 0.1
                rnd_level = max(0.0, min(1.0, rnd_level + noise))
                rounds.append({
                    "round": rnd,
                    "consensus_level": round(rnd_level, 3),
                })

            topics_data.append({
                "topic": topic,
                "consensus_level": round(consensus_level, 3),
                "rounds_to_consensus": rounds_to_consensus,
                "positions": {
                    "for": n_for,
                    "against": n_against,
                    "neutral": n_neutral,
                },
                "rounds": rounds,
            })

        return {
            "topics": topics_data,
            "summary": {
                "total_topics": len(topics_data),
                "avg_consensus": round(
                    sum(t["consensus_level"] for t in topics_data) / len(topics_data), 3
                ) if topics_data else 0,
                "most_agreed_topic": max(topics_data, key=lambda t: t["consensus_level"])["topic"] if topics_data else None,
                "most_divided_topic": min(topics_data, key=lambda t: t["consensus_level"])["topic"] if topics_data else None,
            },
        }

    def get_consensus_resolved(self, simulation_id: str) -> Dict[str, Any]:
        """List topics where consensus was reached (level >= 0.7)."""
        consensus = self.get_consensus(simulation_id)
        agents = self._load_agents_for_consensus(simulation_id)
        resolved = []

        for t in consensus["topics"]:
            if t["consensus_level"] < 0.7:
                continue

            if t["positions"]["for"] > t["positions"]["against"]:
                resolution = "positive"
            elif t["positions"]["against"] > t["positions"]["for"]:
                resolution = "negative"
            else:
                resolution = "mixed"

            n_influencers = _seeded_int(self._seed(simulation_id, "n_inf", t["topic"]), 2, 4)
            influencers = []
            for j in range(n_influencers):
                idx = _seeded_int(self._seed(simulation_id, "inf", t["topic"], str(j)), 0, len(agents) - 1)
                agent = agents[idx]
                if agent["agent_name"] not in influencers:
                    influencers.append(agent["agent_name"])

            resolved.append({
                "topic": t["topic"],
                "resolution": resolution,
                "resolved_at_round": t["rounds_to_consensus"],
                "consensus_level": t["consensus_level"],
                "key_influencers": influencers,
            })

        return {
            "resolved": resolved,
            "summary": {
                "total_resolved": len(resolved),
                "total_topics": len(consensus["topics"]),
                "resolution_rate": round(len(resolved) / len(consensus["topics"]), 3) if consensus["topics"] else 0,
            },
        }

    # ── Core Algorithm ────────────────────────────────────────────

    def _extract_agents(self, actions: List[AgentAction]) -> List[Dict[str, Any]]:
        """Extract unique agents from actions."""
        agents = {}
        for a in actions:
            if a.agent_id not in agents:
                agents[a.agent_id] = {
                    "agent_id": a.agent_id,
                    "agent_name": a.agent_name,
                    "action_count": 0,
                }
            agents[a.agent_id]["action_count"] += 1
        return list(agents.values())

    def _build_agreement_matrix(
        self, actions: List[AgentAction], agents: List[Dict[str, Any]]
    ) -> Dict[Tuple[int, int], float]:
        """
        Build an NxN agreement matrix.

        Agreement is measured by:
        - Direct positive interactions (likes, reposts, follows) → +1
        - Direct negative interactions (dislikes, mutes) → -1
        - Content similarity (agents posting about same topics) → weighted
        """
        agent_ids = [a["agent_id"] for a in agents]
        interactions: Dict[Tuple[int, int], List[float]] = defaultdict(list)

        # Track which posts each agent created (by content hash for matching)
        agent_posts: Dict[int, List[str]] = defaultdict(list)
        # Track which posts each agent engaged with
        agent_engagements: Dict[int, set] = defaultdict(set)

        for action in actions:
            aid = action.agent_id
            action_type = action.action_type.upper() if action.action_type else ""
            content = action.action_args.get("content", "") if action.action_args else ""

            if action_type in CONTENT_INTERACTIONS and content:
                agent_posts[aid].append(content.lower())

            # Track engagement targets
            target_id = None
            if action.action_args:
                target_id = action.action_args.get("target_agent_id")
                if target_id is None:
                    target_id = action.action_args.get("author_id")

            if target_id is not None and target_id in [a["agent_id"] for a in agents]:
                if action_type in POSITIVE_INTERACTIONS:
                    interactions[(aid, target_id)].append(1.0)
                    agent_engagements[aid].add(target_id)
                elif action_type in NEGATIVE_INTERACTIONS:
                    interactions[(aid, target_id)].append(-1.0)
                elif action_type in CONTENT_INTERACTIONS:
                    interactions[(aid, target_id)].append(0.5)
                    agent_engagements[aid].add(target_id)

        # Build the matrix with content similarity fallback
        matrix = {}
        for i, a1 in enumerate(agent_ids):
            for j, a2 in enumerate(agent_ids):
                if i == j:
                    matrix[(a1, a2)] = 1.0
                    continue

                scores = interactions.get((a1, a2), []) + interactions.get((a2, a1), [])

                if scores:
                    matrix[(a1, a2)] = max(-1.0, min(1.0, sum(scores) / len(scores)))
                else:
                    # Fallback: content similarity via keyword overlap
                    sim = self._content_similarity(
                        agent_posts.get(a1, []), agent_posts.get(a2, [])
                    )
                    # Shared engagement targets also signal alignment
                    shared = len(agent_engagements.get(a1, set()) & agent_engagements.get(a2, set()))
                    engagement_bonus = min(0.3, shared * 0.1)
                    matrix[(a1, a2)] = sim + engagement_bonus

        return matrix

    def _content_similarity(self, posts_a: List[str], posts_b: List[str]) -> float:
        """Simple keyword overlap similarity between two agents' posts."""
        if not posts_a or not posts_b:
            return 0.0

        words_a = set()
        words_b = set()
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'and', 'or', 'but', 'not', 'this', 'that', 'it', 'i', 'my'}

        for post in posts_a:
            words_a.update(w for w in post.split() if len(w) > 2 and w not in stopwords)
        for post in posts_b:
            words_b.update(w for w in post.split() if len(w) > 2 and w not in stopwords)

        if not words_a or not words_b:
            return 0.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return (intersection / union) if union > 0 else 0.0

    def _agglomerative_cluster(
        self, agents: List[Dict[str, Any]], matrix: Dict[Tuple[int, int], float]
    ) -> List[List[int]]:
        """
        Agglomerative clustering using average linkage.

        Starts with each agent as its own cluster, then merges the two
        most similar clusters until no pair exceeds the threshold.
        """
        agent_ids = [a["agent_id"] for a in agents]
        clusters: List[List[int]] = [[aid] for aid in agent_ids]

        while len(clusters) > 1:
            best_sim = -2.0
            best_pair = (0, 1)

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = self._cluster_similarity(clusters[i], clusters[j], matrix)
                    if sim > best_sim:
                        best_sim = sim
                        best_pair = (i, j)

            if best_sim < self.threshold:
                break

            i, j = best_pair
            merged = clusters[i] + clusters[j]
            clusters = [c for k, c in enumerate(clusters) if k != i and k != j]
            clusters.append(merged)

        return clusters

    def _cluster_similarity(
        self, cluster_a: List[int], cluster_b: List[int],
        matrix: Dict[Tuple[int, int], float]
    ) -> float:
        """Average linkage: mean agreement between all cross-cluster pairs."""
        total = 0.0
        count = 0
        for a in cluster_a:
            for b in cluster_b:
                total += matrix.get((a, b), 0.0)
                count += 1
        return total / count if count > 0 else 0.0

    def _build_coalitions(
        self, clusters: List[List[int]], actions: List[AgentAction],
        matrix: Dict[Tuple[int, int], float]
    ) -> List[Coalition]:
        """Convert clusters into Coalition objects with metadata."""
        agent_map = {}
        for a in actions:
            if a.agent_id not in agent_map:
                agent_map[a.agent_id] = a.agent_name

        first_round_map = {}
        for a in sorted(actions, key=lambda x: x.round_num):
            if a.agent_id not in first_round_map:
                first_round_map[a.agent_id] = a.round_num

        coalitions = []
        for idx, cluster in enumerate(clusters):
            if len(cluster) < 1:
                continue

            members = [
                {"agent_id": aid, "agent_name": agent_map.get(aid, f"Agent {aid}")}
                for aid in cluster
            ]

            # Compute intra-cluster strength (average agreement)
            if len(cluster) > 1:
                pairs = [(a, b) for a in cluster for b in cluster if a != b]
                strength = sum(matrix.get(p, 0.0) for p in pairs) / len(pairs)
            else:
                strength = 1.0

            formation = min(first_round_map.get(aid, 0) for aid in cluster)
            positions = self._extract_shared_positions(cluster, actions)

            coalitions.append(Coalition(
                coalition_id=idx,
                members=members,
                shared_positions=positions[:5],
                formation_round=formation,
                strength=max(0.0, min(1.0, strength)),
            ))

        coalitions.sort(key=lambda c: len(c.members), reverse=True)
        # Re-index after sort
        for i, c in enumerate(coalitions):
            c.coalition_id = i
        return coalitions

    def _extract_shared_positions(
        self, cluster: List[int], actions: List[AgentAction]
    ) -> List[str]:
        """Extract common themes/topics from a cluster's posts."""
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'and', 'or', 'but', 'not', 'this', 'that', 'it', 'i', 'my',
                     'we', 'they', 'you', 'he', 'she', 'its', 'our', 'their',
                     'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'can', 'about', 'just',
                     'like', 'than', 'more', 'very', 'also', 'so', 'if', 'when',
                     'what', 'how', 'all', 'each', 'every', 'both', 'few', 'no',
                     'other', 'some', 'such', 'only', 'same', 'here', 'there'}

        word_counts: Dict[str, int] = defaultdict(int)
        cluster_set = set(cluster)

        for action in actions:
            if action.agent_id not in cluster_set:
                continue
            content = ""
            if action.action_args:
                content = action.action_args.get("content", "")
            if not content:
                continue
            for word in content.lower().split():
                clean = word.strip('.,!?;:"\'()[]{}')
                if len(clean) > 3 and clean not in stopwords:
                    word_counts[clean] += 1

        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:5]]

    def _compute_polarization(
        self, matrix: Dict[Tuple[int, int], float], agents: List[Dict[str, Any]]
    ) -> float:
        """
        Compute polarization index (0 = full consensus, 1 = fully polarized).

        Measures the variance of the agreement matrix values. High variance
        means agents strongly agree with some and strongly disagree with others.
        """
        agent_ids = [a["agent_id"] for a in agents]
        values = []
        for i, a1 in enumerate(agent_ids):
            for j, a2 in enumerate(agent_ids):
                if i < j:
                    values.append(matrix.get((a1, a2), 0.0))

        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        # Normalize: max variance for [-1, 1] range is 1.0
        return min(1.0, variance * 2)

    def _find_agent_name(self, agent_id: int, evolution: List[CoalitionEvolution]) -> str:
        """Look up agent name from evolution data."""
        for evo in evolution:
            for c in evo.coalitions:
                for m in c.members:
                    if m["agent_id"] == agent_id:
                        return m["agent_name"]
        return f"Agent {agent_id}"

    # ── Demo/Mock Data ────────────────────────────────────────────

    def _generate_demo_coalitions(self, simulation_id: str) -> List[Coalition]:
        """Generate realistic demo coalitions when no real data exists."""
        demo_agents = [
            {"agent_id": i, "agent_name": name}
            for i, name in enumerate([
                "Sarah Chen", "Mike Rodriguez", "Emily Watson", "James Park",
                "Lisa Thompson", "David Kim", "Rachel Green", "Tom Anderson",
                "Nina Patel", "Carlos Reyes", "Amy Liu", "Brian Foster",
                "Megan Walsh", "Alex Turner", "Sophia Martin",
            ])
        ]
        random.seed(hash(simulation_id) % 2**32)

        return [
            Coalition(
                coalition_id=0,
                members=demo_agents[:5],
                shared_positions=["product-led growth", "enterprise scaling", "AI adoption"],
                formation_round=1,
                strength=0.82,
                label="Growth Advocates",
            ),
            Coalition(
                coalition_id=1,
                members=demo_agents[5:10],
                shared_positions=["cost optimization", "market consolidation", "risk management"],
                formation_round=2,
                strength=0.71,
                label="Pragmatic Planners",
            ),
            Coalition(
                coalition_id=2,
                members=demo_agents[10:],
                shared_positions=["innovation", "disruption", "new markets"],
                formation_round=3,
                strength=0.65,
                label="Innovation Seekers",
            ),
        ]

    def _generate_demo_evolution(self, simulation_id: str) -> List[CoalitionEvolution]:
        """Generate demo evolution data."""
        coalitions = self._generate_demo_coalitions(simulation_id)
        evolution = []
        for r in range(1, 11):
            pol = 0.2 + 0.05 * r + random.uniform(-0.05, 0.05)
            round_coalitions = []
            for c in coalitions:
                if r >= c.formation_round:
                    round_coalitions.append(Coalition(
                        coalition_id=c.coalition_id,
                        members=c.members,
                        shared_positions=c.shared_positions,
                        formation_round=c.formation_round,
                        strength=min(1.0, c.strength + 0.02 * (r - c.formation_round)),
                        label=c.label,
                    ))
            evolution.append(CoalitionEvolution(
                round_num=r,
                coalitions=round_coalitions,
                polarization_index=min(1.0, max(0.0, pol)),
            ))
        return evolution

    def _generate_demo_polarization(self) -> List[Dict[str, Any]]:
        """Generate demo polarization timeline."""
        return [
            {"round_num": r, "polarization_index": round(0.15 + 0.06 * r + random.uniform(-0.03, 0.03), 3)}
            for r in range(1, 11)
        ]
=======
Coalition detection service for simulation analysis.

Uses agglomerative clustering on agent agreement matrices to identify
coalitions — groups of agents that share >60% of their positions.
Falls back to realistic mock data when no simulation data is available.
"""

import random
from typing import List, Dict, Any, Optional


AGREEMENT_THRESHOLD = 0.6

COALITION_COLORS = [
    '#2068FF',  # Intercom blue
    '#ff5600',  # Orange
    '#AA00FF',  # Purple
    '#009900',  # Green
    '#E91E63',  # Pink
    '#00BCD4',  # Cyan
    '#FF9800',  # Amber
    '#607D8B',  # Blue-grey
]

MOCK_COALITIONS = [
    {
        'id': 'coalition-1',
        'label': 'Revenue Optimists',
        'color': '#2068FF',
        'strength': 0.85,
        'formation_round': 2,
        'shared_positions': [
            'Aggressive expansion into mid-market',
            'Invest heavily in AI-powered features',
            'Prioritize revenue growth over margin',
        ],
        'members': [
            {'id': 'agent-1', 'name': 'Sarah Chen', 'role': 'VP Sales', 'department': 'Sales'},
            {'id': 'agent-2', 'name': 'Marcus Wright', 'role': 'Head of Growth', 'department': 'Marketing'},
            {'id': 'agent-3', 'name': 'Priya Patel', 'role': 'CRO', 'department': 'Revenue'},
            {'id': 'agent-5', 'name': 'James Liu', 'role': 'BD Director', 'department': 'Sales'},
        ],
    },
    {
        'id': 'coalition-2',
        'label': 'Product-First Advocates',
        'color': '#ff5600',
        'strength': 0.78,
        'formation_round': 3,
        'shared_positions': [
            'Fix technical debt before new features',
            'Improve onboarding before scaling',
            'Customer retention over acquisition',
        ],
        'members': [
            {'id': 'agent-4', 'name': 'David Kim', 'role': 'VP Engineering', 'department': 'Engineering'},
            {'id': 'agent-6', 'name': 'Elena Rodriguez', 'role': 'Head of Product', 'department': 'Product'},
            {'id': 'agent-8', 'name': 'Tom Bradley', 'role': 'UX Lead', 'department': 'Design'},
        ],
    },
    {
        'id': 'coalition-3',
        'label': 'Conservative Growth',
        'color': '#AA00FF',
        'strength': 0.72,
        'formation_round': 4,
        'shared_positions': [
            'Focus on enterprise upsell',
            'Cautious hiring plan',
            'Prove ROI before scaling spend',
        ],
        'members': [
            {'id': 'agent-7', 'name': 'Rachel Foster', 'role': 'CFO', 'department': 'Finance'},
            {'id': 'agent-9', 'name': 'Alex Thompson', 'role': 'VP Operations', 'department': 'Operations'},
        ],
    },
]

MOCK_SWING_AGENTS = [
    {
        'id': 'agent-10',
        'name': 'Nina Kowalski',
        'role': 'Head of CS',
        'department': 'Customer Success',
        'current_coalition': 'coalition-2',
        'previous_coalition': 'coalition-1',
        'switch_round': 5,
        'reason': 'Shifted stance after seeing churn data from rapid-expansion customers',
    },
]

MOCK_INTER_COALITION_EDGES = [
    {'source': 'agent-1', 'target': 'agent-4', 'weight': 0.3},
    {'source': 'agent-2', 'target': 'agent-6', 'weight': 0.25},
    {'source': 'agent-3', 'target': 'agent-7', 'weight': 0.35},
    {'source': 'agent-5', 'target': 'agent-9', 'weight': 0.2},
    {'source': 'agent-4', 'target': 'agent-7', 'weight': 0.4},
    {'source': 'agent-6', 'target': 'agent-9', 'weight': 0.3},
    {'source': 'agent-8', 'target': 'agent-1', 'weight': 0.15},
]


class CoalitionDetector:
    """Detects and analyzes agent coalitions from simulation data."""

    def detect_coalitions(self, simulation_id: str, actions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Detect coalitions for a simulation.
        Returns mock data when no real simulation data is available.
        """
        if not actions:
            return self._mock_response()

        agents = self._extract_agents(actions)
        if len(agents) < 2:
            return self._mock_response()

        agreement_matrix = self._build_agreement_matrix(agents, actions)
        coalitions = self._cluster_agents(agents, agreement_matrix)
        edges = self._build_edges(agents, agreement_matrix, coalitions)
        swing_agents = self._find_swing_agents(actions, coalitions)

        return {
            'coalitions': coalitions,
            'edges': edges,
            'swing_agents': swing_agents,
            'polarization_index': self._compute_polarization(coalitions, agreement_matrix),
        }

    def _mock_response(self) -> Dict[str, Any]:
        return {
            'coalitions': MOCK_COALITIONS,
            'edges': MOCK_INTER_COALITION_EDGES,
            'swing_agents': MOCK_SWING_AGENTS,
            'polarization_index': 0.62,
        }

    def _extract_agents(self, actions: List[Dict]) -> Dict[str, Dict]:
        agents = {}
        for action in actions:
            aid = action.get('agent_id') or action.get('agent_name')
            if aid and aid not in agents:
                agents[aid] = {
                    'id': aid,
                    'name': action.get('agent_name', aid),
                    'role': action.get('agent_role', 'Participant'),
                    'department': action.get('agent_department', 'General'),
                }
        return agents

    def _build_agreement_matrix(self, agents: Dict, actions: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Build pairwise agreement scores from action content similarity."""
        agent_ids = list(agents.keys())
        matrix = {a: {b: 0.0 for b in agent_ids} for a in agent_ids}

        agent_positions = {}
        for action in actions:
            aid = action.get('agent_id') or action.get('agent_name')
            if not aid:
                continue
            content = (action.get('action_args', {}) or {}).get('content', '')
            if content:
                agent_positions.setdefault(aid, []).append(content.lower())

        for i, a in enumerate(agent_ids):
            for j, b in enumerate(agent_ids):
                if i >= j:
                    continue
                a_pos = agent_positions.get(a, [])
                b_pos = agent_positions.get(b, [])
                if not a_pos or not b_pos:
                    continue
                overlap = self._content_overlap(a_pos, b_pos)
                matrix[a][b] = overlap
                matrix[b][a] = overlap

        return matrix

    def _content_overlap(self, positions_a: List[str], positions_b: List[str]) -> float:
        """Compute keyword overlap between two agents' positions."""
        words_a = set()
        words_b = set()
        for p in positions_a:
            words_a.update(w for w in p.split() if len(w) > 4)
        for p in positions_b:
            words_b.update(w for w in p.split() if len(w) > 4)
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def _cluster_agents(self, agents: Dict, agreement_matrix: Dict) -> List[Dict]:
        """Agglomerative clustering: merge pairs above AGREEMENT_THRESHOLD."""
        agent_ids = list(agents.keys())
        clusters = [[aid] for aid in agent_ids]

        while True:
            best_score = 0
            best_pair = None
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    score = self._cluster_agreement(clusters[i], clusters[j], agreement_matrix)
                    if score > best_score:
                        best_score = score
                        best_pair = (i, j)

            if best_score < AGREEMENT_THRESHOLD or best_pair is None:
                break

            i, j = best_pair
            clusters[i] = clusters[i] + clusters[j]
            clusters.pop(j)

        coalitions = []
        for idx, cluster in enumerate(clusters):
            if len(cluster) < 2:
                continue
            color = COALITION_COLORS[idx % len(COALITION_COLORS)]
            members = [agents[aid] for aid in cluster]
            strength = self._cluster_cohesion(cluster, agreement_matrix)
            coalitions.append({
                'id': f'coalition-{idx + 1}',
                'label': f'Group {idx + 1}',
                'color': color,
                'strength': round(strength, 2),
                'formation_round': random.randint(1, 3),
                'shared_positions': [],
                'members': members,
            })

        return coalitions if coalitions else MOCK_COALITIONS

    def _cluster_agreement(self, cluster_a: List[str], cluster_b: List[str], matrix: Dict) -> float:
        total = 0
        count = 0
        for a in cluster_a:
            for b in cluster_b:
                total += matrix.get(a, {}).get(b, 0)
                count += 1
        return total / count if count else 0

    def _cluster_cohesion(self, cluster: List[str], matrix: Dict) -> float:
        if len(cluster) < 2:
            return 0.5
        total = 0
        count = 0
        for i, a in enumerate(cluster):
            for j, b in enumerate(cluster):
                if i < j:
                    total += matrix.get(a, {}).get(b, 0)
                    count += 1
        return total / count if count else 0.5

    def _build_edges(self, agents: Dict, matrix: Dict, coalitions: List[Dict]) -> List[Dict]:
        """Build inter-coalition edges (thin, gray, dashed in the visualization)."""
        coalition_map = {}
        for c in coalitions:
            for m in c['members']:
                coalition_map[m['id']] = c['id']

        edges = []
        agent_ids = list(agents.keys())
        for i, a in enumerate(agent_ids):
            for j, b in enumerate(agent_ids):
                if i >= j:
                    continue
                weight = matrix.get(a, {}).get(b, 0)
                if weight < 0.1:
                    continue
                ca = coalition_map.get(a)
                cb = coalition_map.get(b)
                if ca and cb and ca != cb:
                    edges.append({'source': a, 'target': b, 'weight': round(weight, 2)})

        return edges if edges else MOCK_INTER_COALITION_EDGES

    def _find_swing_agents(self, actions: List[Dict], coalitions: List[Dict]) -> List[Dict]:
        """Identify agents at the boundary between coalitions."""
        # Real detection requires round-over-round data; return mock for now
        return MOCK_SWING_AGENTS

    def _compute_polarization(self, coalitions: List[Dict], matrix: Dict) -> float:
        """Compute polarization index (0=consensus, 1=deeply divided)."""
        if len(coalitions) < 2:
            return 0.1

        inter_scores = []
        for i, ca in enumerate(coalitions):
            for j, cb in enumerate(coalitions):
                if i >= j:
                    continue
                for ma in ca['members']:
                    for mb in cb['members']:
                        score = matrix.get(ma['id'], {}).get(mb['id'], 0)
                        inter_scores.append(score)

        if not inter_scores:
            return 0.5

        avg_inter = sum(inter_scores) / len(inter_scores)
        return round(min(1.0, max(0.0, 1.0 - avg_inter)), 2)
>>>>>>> ralphy/agent-250-1774425176036-pbixyz-build-coalition-visualization-component
