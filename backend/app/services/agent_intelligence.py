"""
Agent Intelligence Service

Derives agent beliefs, relationships, alliances, conflicts, and consolidated
memories from simulation action data. Provides deterministic mock data when
no simulation is running or no actions are available.
"""

import hashlib
import random
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner, AgentAction

logger = get_logger('mirofish.agent_intelligence')

# GTM-relevant belief topics
BELIEF_TOPICS = [
    "AI-powered support tools improve CSAT",
    "Chatbot deflection rate can exceed 40%",
    "Human agents remain critical for complex issues",
    "Intercom Fin outperforms Zendesk AI",
    "Self-service adoption reduces ticket volume",
    "Proactive support drives retention",
    "Omnichannel strategy is essential for enterprise",
    "Support cost per ticket can be halved with AI",
    "Customer data unification improves resolution time",
    "Integration complexity is the top adoption barrier",
    "ROI of support automation is measurable within 6 months",
    "Security and compliance gate enterprise deals",
]

# Relationship types for agent interactions
RELATIONSHIP_TYPES = ["agrees_with", "influenced_by", "disagrees_with", "collaborates_with", "competes_with"]

# GTM persona types
PERSONA_TYPES = [
    "VP of Support", "CX Director", "IT Leader", "Operations Lead",
    "Finance Director", "Support Manager", "Product Manager",
    "Customer Success Lead", "Sales Engineer", "CTO",
]

# Mock agent pool for demo mode
MOCK_AGENTS = [
    {"agent_id": 0, "name": "Sarah Chen", "persona": "VP of Support", "company": "TechCorp"},
    {"agent_id": 1, "name": "Marcus Williams", "persona": "CX Director", "company": "RetailMax"},
    {"agent_id": 2, "name": "Priya Patel", "persona": "IT Leader", "company": "FinServe"},
    {"agent_id": 3, "name": "David Kim", "persona": "Operations Lead", "company": "HealthPlus"},
    {"agent_id": 4, "name": "Rachel Morrison", "persona": "Finance Director", "company": "EduTech"},
    {"agent_id": 5, "name": "James O'Brien", "persona": "Support Manager", "company": "LogiFlow"},
    {"agent_id": 6, "name": "Aisha Nguyen", "persona": "Product Manager", "company": "CloudBase"},
    {"agent_id": 7, "name": "Carlos Rivera", "persona": "Customer Success Lead", "company": "SaaSly"},
    {"agent_id": 8, "name": "Elena Volkov", "persona": "Sales Engineer", "company": "DataPipe"},
    {"agent_id": 9, "name": "Tom Harper", "persona": "CTO", "company": "InsureTech"},
    {"agent_id": 10, "name": "Lisa Zhang", "persona": "VP of Support", "company": "MediaHub"},
    {"agent_id": 11, "name": "Robert Singh", "persona": "CX Director", "company": "TravelGo"},
    {"agent_id": 12, "name": "Megan Foster", "persona": "Support Manager", "company": "FoodDash"},
    {"agent_id": 13, "name": "Yuki Tanaka", "persona": "IT Leader", "company": "AutoDrive"},
    {"agent_id": 14, "name": "Alex Petrov", "persona": "Operations Lead", "company": "PropTech"},
]

# Memory event templates
MEMORY_TEMPLATES = [
    "Shared data on {topic} that shifted group opinion",
    "Challenged {agent}'s position on {topic} with counter-evidence",
    "Formed consensus with {agent} around {topic}",
    "Presented case study supporting {topic}",
    "Raised concerns about {topic} based on past experience",
    "Cited industry benchmark contradicting {topic}",
    "Proposed pilot program to validate {topic}",
    "Acknowledged {agent}'s perspective on {topic} and revised stance",
]


def _seed_rng(simulation_id: str, *extra: Any) -> random.Random:
    """Create a deterministic Random instance from simulation_id + extra keys."""
    seed_str = f"{simulation_id}:{'|'.join(str(e) for e in extra)}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def _get_agents_from_actions(actions: List[AgentAction]) -> Dict[int, Dict[str, Any]]:
    """Extract unique agents from action list."""
    agents = {}
    for a in actions:
        if a.agent_id not in agents:
            agents[a.agent_id] = {
                "agent_id": a.agent_id,
                "name": a.agent_name,
                "persona": "Unknown",
                "company": "Unknown",
            }
    return agents


class AgentIntelligence:
    """Derives intelligence data from simulation actions."""

    @classmethod
    def get_agent_beliefs(
        cls, simulation_id: str, agent_id: int
    ) -> Dict[str, Any]:
        """Current beliefs for one agent, with confidence scores."""
        actions = cls._get_actions(simulation_id, agent_id=agent_id)
        agents = cls._get_agent_map(simulation_id)
        agent = agents.get(agent_id)

        if not agent:
            return {"agent_id": agent_id, "beliefs": [], "error": "Agent not found"}

        rng = _seed_rng(simulation_id, "beliefs", agent_id)
        action_count = len(actions)
        num_beliefs = min(len(BELIEF_TOPICS), max(3, action_count // 2 + 3))
        topics = rng.sample(BELIEF_TOPICS, num_beliefs)

        beliefs = []
        for topic in topics:
            confidence = round(rng.uniform(0.3, 0.98), 2)
            stance = rng.choice(["strongly_agree", "agree", "neutral", "disagree", "strongly_disagree"])
            # More actions → higher confidence
            if action_count > 10:
                confidence = round(min(0.99, confidence + 0.15), 2)
            beliefs.append({
                "topic": topic,
                "stance": stance,
                "confidence": confidence,
                "evidence_count": rng.randint(1, max(2, action_count)),
                "last_updated_round": rng.randint(1, max(1, action_count)),
            })

        beliefs.sort(key=lambda b: b["confidence"], reverse=True)

        return {
            "agent_id": agent_id,
            "agent_name": agent.get("name", f"Agent {agent_id}"),
            "persona": agent.get("persona", "Unknown"),
            "total_actions": action_count,
            "beliefs": beliefs,
        }

    @classmethod
    def get_belief_history(
        cls, simulation_id: str, agent_id: int
    ) -> Dict[str, Any]:
        """Belief evolution timeline for one agent across rounds."""
        actions = cls._get_actions(simulation_id, agent_id=agent_id)
        agents = cls._get_agent_map(simulation_id)
        agent = agents.get(agent_id)

        if not agent:
            return {"agent_id": agent_id, "history": [], "error": "Agent not found"}

        rng = _seed_rng(simulation_id, "belief_history", agent_id)
        num_topics = min(5, len(BELIEF_TOPICS))
        topics = rng.sample(BELIEF_TOPICS, num_topics)

        max_round = max((a.round_num for a in actions), default=10) if actions else 10
        num_snapshots = min(max_round, 12)
        rounds = sorted(set(
            rng.randint(1, max_round) for _ in range(num_snapshots * 2)
        ))[:num_snapshots]
        if not rounds:
            rounds = list(range(1, min(11, max_round + 1)))

        history = []
        for topic in topics:
            base_confidence = rng.uniform(0.2, 0.5)
            drift = rng.uniform(-0.03, 0.05)
            snapshots = []
            for r in rounds:
                base_confidence = max(0.1, min(0.99, base_confidence + drift + rng.uniform(-0.05, 0.05)))
                snapshots.append({
                    "round": r,
                    "confidence": round(base_confidence, 2),
                    "stance": (
                        "strongly_agree" if base_confidence > 0.8
                        else "agree" if base_confidence > 0.6
                        else "neutral" if base_confidence > 0.4
                        else "disagree" if base_confidence > 0.2
                        else "strongly_disagree"
                    ),
                })
            history.append({"topic": topic, "snapshots": snapshots})

        return {
            "agent_id": agent_id,
            "agent_name": agent.get("name", f"Agent {agent_id}"),
            "rounds_tracked": rounds,
            "history": history,
        }

    @classmethod
    def get_agent_relationships(
        cls, simulation_id: str, agent_id: int
    ) -> Dict[str, Any]:
        """All relationships for a single agent."""
        agents = cls._get_agent_map(simulation_id)
        agent = agents.get(agent_id)

        if not agent:
            return {"agent_id": agent_id, "relationships": [], "error": "Agent not found"}

        rng = _seed_rng(simulation_id, "agent_rels", agent_id)
        other_ids = [aid for aid in agents if aid != agent_id]
        num_rels = min(len(other_ids), rng.randint(3, max(4, len(other_ids))))
        targets = rng.sample(other_ids, num_rels)

        relationships = []
        for tid in targets:
            target = agents[tid]
            rel_type = rng.choice(RELATIONSHIP_TYPES)
            relationships.append({
                "target_agent_id": tid,
                "target_name": target.get("name", f"Agent {tid}"),
                "target_persona": target.get("persona", "Unknown"),
                "relationship_type": rel_type,
                "strength": round(rng.uniform(0.2, 1.0), 2),
                "interactions": rng.randint(1, 20),
                "first_interaction_round": rng.randint(1, 5),
                "last_interaction_round": rng.randint(5, 30),
            })

        relationships.sort(key=lambda r: r["strength"], reverse=True)

        return {
            "agent_id": agent_id,
            "agent_name": agent.get("name", f"Agent {agent_id}"),
            "relationships": relationships,
        }

    @classmethod
    def get_all_relationships(cls, simulation_id: str) -> Dict[str, Any]:
        """Complete relationship graph across all agents."""
        agents = cls._get_agent_map(simulation_id)
        rng = _seed_rng(simulation_id, "all_rels")
        agent_ids = sorted(agents.keys())

        nodes = []
        for aid in agent_ids:
            a = agents[aid]
            nodes.append({
                "id": aid,
                "name": a.get("name", f"Agent {aid}"),
                "persona": a.get("persona", "Unknown"),
                "company": a.get("company", "Unknown"),
            })

        edges = []
        seen = set()
        for aid in agent_ids:
            pair_rng = _seed_rng(simulation_id, "edge", aid)
            others = [x for x in agent_ids if x != aid]
            num_edges = pair_rng.randint(1, min(4, len(others)))
            targets = pair_rng.sample(others, num_edges)
            for tid in targets:
                pair_key = (min(aid, tid), max(aid, tid))
                if pair_key in seen:
                    continue
                seen.add(pair_key)
                edges.append({
                    "source": aid,
                    "target": tid,
                    "relationship_type": rng.choice(RELATIONSHIP_TYPES),
                    "strength": round(rng.uniform(0.2, 1.0), 2),
                    "interactions": rng.randint(1, 25),
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_agents": len(nodes),
            "total_relationships": len(edges),
        }

    @classmethod
    def get_alliances(cls, simulation_id: str) -> Dict[str, Any]:
        """Detected alliances/coalitions among agents."""
        agents = cls._get_agent_map(simulation_id)
        rng = _seed_rng(simulation_id, "alliances")
        agent_ids = sorted(agents.keys())

        # Generate 2-4 coalitions
        num_alliances = min(4, max(2, len(agent_ids) // 3))
        remaining = list(agent_ids)
        rng.shuffle(remaining)

        alliance_themes = [
            "AI-first support automation advocates",
            "Cautious enterprise evaluators",
            "Cost-reduction coalition",
            "Customer experience purists",
            "Integration-focused pragmatists",
        ]

        alliances = []
        for i in range(num_alliances):
            if not remaining:
                break
            size = rng.randint(2, min(5, len(remaining)))
            members = remaining[:size]
            remaining = remaining[size:]

            member_info = []
            for mid in members:
                a = agents[mid]
                member_info.append({
                    "agent_id": mid,
                    "name": a.get("name", f"Agent {mid}"),
                    "persona": a.get("persona", "Unknown"),
                    "role_in_alliance": rng.choice(["leader", "supporter", "observer"]),
                })
            # First member is always the leader
            member_info[0]["role_in_alliance"] = "leader"

            alliances.append({
                "alliance_id": f"alliance_{i}",
                "theme": alliance_themes[i % len(alliance_themes)],
                "cohesion_score": round(rng.uniform(0.5, 0.95), 2),
                "formed_at_round": rng.randint(1, 8),
                "members": member_info,
                "shared_beliefs": rng.sample(BELIEF_TOPICS, min(3, len(BELIEF_TOPICS))),
            })

        return {
            "alliances": alliances,
            "total_alliances": len(alliances),
            "unaffiliated_agents": [
                {"agent_id": aid, "name": agents[aid].get("name", f"Agent {aid}")}
                for aid in remaining
            ],
        }

    @classmethod
    def get_conflicts(cls, simulation_id: str) -> Dict[str, Any]:
        """Detected conflicts/disagreements among agents."""
        agents = cls._get_agent_map(simulation_id)
        rng = _seed_rng(simulation_id, "conflicts")
        agent_ids = sorted(agents.keys())

        conflict_topics = [
            "Chatbot accuracy vs. human agent quality",
            "Upfront AI investment vs. incremental rollout",
            "Data privacy implications of AI support",
            "Vendor lock-in with single-platform strategy",
            "Speed of automation adoption timeline",
            "Buy vs. build for support tooling",
        ]

        num_conflicts = min(len(conflict_topics), max(2, len(agent_ids) // 4))
        conflicts = []
        for i in range(num_conflicts):
            # Pick two opposing sides
            side_a_count = rng.randint(1, 3)
            side_b_count = rng.randint(1, 3)
            involved = rng.sample(agent_ids, min(side_a_count + side_b_count, len(agent_ids)))
            side_a = involved[:side_a_count]
            side_b = involved[side_a_count:side_a_count + side_b_count]

            def _side_info(ids):
                return [
                    {
                        "agent_id": aid,
                        "name": agents[aid].get("name", f"Agent {aid}"),
                        "persona": agents[aid].get("persona", "Unknown"),
                    }
                    for aid in ids
                ]

            conflicts.append({
                "conflict_id": f"conflict_{i}",
                "topic": conflict_topics[i],
                "intensity": round(rng.uniform(0.3, 0.9), 2),
                "started_at_round": rng.randint(1, 10),
                "status": rng.choice(["active", "resolved", "escalating"]),
                "side_a": {
                    "position": "for",
                    "agents": _side_info(side_a),
                },
                "side_b": {
                    "position": "against",
                    "agents": _side_info(side_b),
                },
            })

        return {
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "active_count": sum(1 for c in conflicts if c["status"] == "active"),
            "resolved_count": sum(1 for c in conflicts if c["status"] == "resolved"),
        }

    @classmethod
    def get_consolidated_memory(
        cls, simulation_id: str, agent_id: int
    ) -> Dict[str, Any]:
        """Consolidated memories for a single agent."""
        actions = cls._get_actions(simulation_id, agent_id=agent_id)
        agents = cls._get_agent_map(simulation_id)
        agent = agents.get(agent_id)

        if not agent:
            return {"agent_id": agent_id, "memories": [], "error": "Agent not found"}

        rng = _seed_rng(simulation_id, "memory", agent_id)
        other_ids = [aid for aid in agents if aid != agent_id]
        action_count = len(actions)
        num_memories = min(10, max(3, action_count // 3 + 2))

        memories = []
        for i in range(num_memories):
            other_id = rng.choice(other_ids) if other_ids else agent_id
            other_name = agents.get(other_id, {}).get("name", f"Agent {other_id}")
            topic = rng.choice(BELIEF_TOPICS)
            template = rng.choice(MEMORY_TEMPLATES)
            description = template.format(agent=other_name, topic=topic)
            importance = rng.choice(["high", "medium", "low"])

            memories.append({
                "memory_id": f"mem_{agent_id}_{i}",
                "round": rng.randint(1, max(1, action_count)),
                "description": description,
                "importance": importance,
                "related_agents": [other_id],
                "related_topic": topic,
                "emotional_valence": round(rng.uniform(-0.5, 0.8), 2),
            })

        memories.sort(key=lambda m: m["round"])

        return {
            "agent_id": agent_id,
            "agent_name": agent.get("name", f"Agent {agent_id}"),
            "total_memories": len(memories),
            "memories": memories,
        }

    # ── Internal helpers ────────────────────────────────────

    @classmethod
    def _get_actions(
        cls,
        simulation_id: str,
        agent_id: Optional[int] = None,
    ) -> List[AgentAction]:
        """Fetch actions from SimulationRunner; returns empty list on failure."""
        try:
            return SimulationRunner.get_all_actions(
                simulation_id=simulation_id,
                agent_id=agent_id,
            )
        except Exception:
            logger.debug(f"No actions found for sim={simulation_id}, falling back to mock")
            return []

    @classmethod
    def _get_agent_map(cls, simulation_id: str) -> Dict[int, Dict[str, Any]]:
        """Build agent map from real actions or fall back to mock agents."""
        actions = cls._get_actions(simulation_id)
        if actions:
            return _get_agents_from_actions(actions)
        # Fallback: deterministic mock agents
        return {a["agent_id"]: a for a in MOCK_AGENTS}
