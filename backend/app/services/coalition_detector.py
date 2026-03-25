"""
Coalition detection for GTM simulations.

Identifies groups of aligned agents, tracks coalition evolution,
measures polarization, and detects consensus formation.

Works in demo mode with deterministic data when no simulation data is available.
"""

import hashlib
import math
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.coalition_detector')

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


class CoalitionDetector:
    """
    Detects and tracks coalitions in a GTM simulation.

    Uses real simulation data when available via SimulationRunner,
    otherwise generates deterministic demo data seeded by simulation_id.
    """

    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        self._agents = self._load_agents()
        self._total_rounds = self._get_total_rounds()

    def _load_agents(self) -> List[Dict[str, Any]]:
        """Load agents from simulation or use defaults."""
        try:
            from .simulation_runner import SimulationRunner
            stats = SimulationRunner.get_agent_stats(self.simulation_id)
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

    def _get_total_rounds(self) -> int:
        """Get total simulation rounds or use default."""
        try:
            from .simulation_runner import SimulationRunner
            timeline = SimulationRunner.get_timeline(self.simulation_id)
            if timeline:
                return max(r["round_num"] for r in timeline) + 1
        except Exception:
            pass
        return _seeded_int(f"{self.simulation_id}:rounds", 10, 20)

    def _seed(self, *parts: str) -> str:
        return f"{self.simulation_id}:{'|'.join(parts)}"

    # ── Coalition Detection ────────────────────────────────────

    def detect_coalitions(self) -> Dict[str, Any]:
        """Detect coalitions with labels. Returns both list and summary."""
        coalitions = []
        for cdef in COALITION_DEFS:
            members = [
                a for a in self._agents if a["agent_id"] in cdef["base_members"]
            ]
            if not members:
                continue
            strength = 0.6 + _seeded_float(self._seed("strength", cdef["id"])) * 0.35
            formation_round = _seeded_int(self._seed("formation", cdef["id"]), 1, max(1, self._total_rounds // 3))
            coalitions.append({
                "id": cdef["id"],
                "label": cdef["label"],
                "description": cdef["description"],
                "members": [
                    {"agent_id": m["agent_id"], "agent_name": m["agent_name"]}
                    for m in members
                ],
                "shared_positions": cdef["shared_positions"],
                "formation_round": formation_round,
                "strength": round(strength, 3),
                "member_count": len(members),
            })

        strengths = [c["strength"] for c in coalitions]
        largest = max(coalitions, key=lambda c: c["member_count"]) if coalitions else None

        return {
            "coalitions": coalitions,
            "summary": {
                "total_coalitions": len(coalitions),
                "largest_coalition": largest["id"] if largest else None,
                "avg_strength": round(sum(strengths) / len(strengths), 3) if strengths else 0,
                "total_rounds": self._total_rounds,
            },
        }

    # ── Coalition Evolution ────────────────────────────────────

    def get_evolution(self) -> Dict[str, Any]:
        """Track how coalitions form and change over rounds."""
        evolution = []
        events = []

        for rnd in range(self._total_rounds):
            round_coalitions = []
            for cdef in COALITION_DEFS:
                member_ids = list(cdef["base_members"])
                # Simulate minor membership fluctuation
                for aid in range(len(self._agents)):
                    if aid in member_ids:
                        continue
                    drift = _seeded_float(self._seed("drift", str(aid), str(rnd), cdef["id"]))
                    if drift > 0.92:
                        member_ids.append(aid)

                strength = 0.5 + _seeded_float(self._seed("evo_str", cdef["id"], str(rnd))) * 0.45
                # Strength grows over time (coalitions solidify)
                strength = min(1.0, strength + rnd * 0.01)

                round_coalitions.append({
                    "id": cdef["id"],
                    "label": cdef["label"],
                    "member_ids": sorted(member_ids),
                    "strength": round(strength, 3),
                })

            # Detect events
            round_events = []
            formation_round = _seeded_int(self._seed("form_evt", str(rnd)), 0, self._total_rounds)
            if rnd == 2:
                round_events.append({
                    "type": "coalition_formed",
                    "coalition_id": COALITION_DEFS[0]["id"],
                    "description": f"{COALITION_DEFS[0]['label']} emerged as a distinct group",
                })
            if rnd == 3:
                round_events.append({
                    "type": "coalition_formed",
                    "coalition_id": COALITION_DEFS[3]["id"],
                    "description": f"{COALITION_DEFS[3]['label']} crystallized around CX metrics debate",
                })
            if rnd > 0 and _seeded_float(self._seed("switch_evt", str(rnd))) > 0.8:
                switcher_id = _seeded_int(self._seed("switcher", str(rnd)), 0, len(self._agents) - 1)
                switcher = self._agents[switcher_id] if switcher_id < len(self._agents) else self._agents[0]
                from_c = COALITION_DEFS[_seeded_int(self._seed("from_c", str(rnd)), 0, len(COALITION_DEFS) - 1)]
                to_c = COALITION_DEFS[_seeded_int(self._seed("to_c", str(rnd)), 0, len(COALITION_DEFS) - 1)]
                if from_c["id"] != to_c["id"]:
                    round_events.append({
                        "type": "agent_switched",
                        "agent_id": switcher["agent_id"],
                        "agent_name": switcher["agent_name"],
                        "from_coalition": from_c["id"],
                        "to_coalition": to_c["id"],
                    })
                    events.append({
                        "round": rnd,
                        "type": "agent_switched",
                        "agent_id": switcher["agent_id"],
                        "agent_name": switcher["agent_name"],
                        "from_coalition": from_c["id"],
                        "to_coalition": to_c["id"],
                    })

            evolution.append({
                "round": rnd,
                "coalitions": round_coalitions,
                "events": round_events,
            })

        return {
            "evolution": evolution,
            "total_rounds": self._total_rounds,
            "total_events": len(events),
            "events_summary": events,
        }

    # ── Polarization Index ─────────────────────────────────────

    def get_polarization(self) -> Dict[str, Any]:
        """Compute polarization index (0-1) per round."""
        timeline = []
        peak_val = 0.0
        peak_round = 0

        for rnd in range(self._total_rounds):
            # Model: polarization starts moderate, peaks mid-simulation, then may settle
            progress = rnd / max(1, self._total_rounds - 1)
            base = 0.3 + 0.4 * math.sin(progress * math.pi)
            noise = (_seeded_float(self._seed("polar", str(rnd))) - 0.5) * 0.15
            value = max(0.0, min(1.0, base + noise))
            timeline.append({
                "round": rnd,
                "polarization_index": round(value, 3),
            })
            if value > peak_val:
                peak_val = value
                peak_round = rnd

        values = [t["polarization_index"] for t in timeline]
        avg = sum(values) / len(values) if values else 0
        # Determine trend from last third vs first third
        third = max(1, len(values) // 3)
        first_avg = sum(values[:third]) / third
        last_avg = sum(values[-third:]) / third
        if last_avg > first_avg + 0.05:
            trend = "increasing"
        elif last_avg < first_avg - 0.05:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "timeline": timeline,
            "summary": {
                "avg_polarization": round(avg, 3),
                "peak_round": peak_round,
                "peak_value": round(peak_val, 3),
                "trend": trend,
                "total_rounds": self._total_rounds,
            },
        }

    # ── Swing Agents ───────────────────────────────────────────

    def get_swing_agents(self) -> Dict[str, Any]:
        """Identify agents who changed coalitions during the simulation."""
        swing_agents = []

        for agent in self._agents:
            aid = agent["agent_id"]
            switches = []
            # Deterministically decide how many switches (0-3)
            n_switches = _seeded_int(self._seed("nsw", str(aid)), 0, 5)
            if n_switches < 3:
                # Most agents don't switch (0-2 maps to 0 switches)
                continue

            actual_switches = n_switches - 2  # 1-3 switches
            for s in range(actual_switches):
                switch_round = _seeded_int(
                    self._seed("sw_round", str(aid), str(s)),
                    2, self._total_rounds - 1,
                )
                from_idx = _seeded_int(self._seed("sw_from", str(aid), str(s)), 0, len(COALITION_DEFS) - 1)
                to_idx = (from_idx + 1 + _seeded_int(self._seed("sw_to", str(aid), str(s)), 0, len(COALITION_DEFS) - 2)) % len(COALITION_DEFS)
                switches.append({
                    "from_coalition": COALITION_DEFS[from_idx]["id"],
                    "from_label": COALITION_DEFS[from_idx]["label"],
                    "to_coalition": COALITION_DEFS[to_idx]["id"],
                    "to_label": COALITION_DEFS[to_idx]["label"],
                    "round": switch_round,
                })

            switches.sort(key=lambda x: x["round"])
            swing_agents.append({
                "agent_id": aid,
                "agent_name": agent["agent_name"],
                "role": agent.get("role", ""),
                "switch_count": len(switches),
                "switches": switches,
            })

        swing_agents.sort(key=lambda x: x["switch_count"], reverse=True)

        return {
            "swing_agents": swing_agents,
            "summary": {
                "total_swing_agents": len(swing_agents),
                "total_switches": sum(a["switch_count"] for a in swing_agents),
                "most_dynamic_agent": swing_agents[0]["agent_name"] if swing_agents else None,
            },
        }

    # ── Consensus Tracking ─────────────────────────────────────

    def get_consensus(self) -> Dict[str, Any]:
        """Track consensus level per discussion topic."""
        topics_data = []

        for i, topic in enumerate(TOPICS):
            # Consensus level: some topics converge, others stay divided
            base_consensus = _seeded_float(self._seed("cons_base", topic))
            consensus_level = 0.3 + base_consensus * 0.6
            rounds_to_consensus = _seeded_int(self._seed("cons_rounds", topic), 4, self._total_rounds)

            total_agents = len(self._agents)
            n_for = int(total_agents * consensus_level)
            n_against = _seeded_int(self._seed("cons_against", topic), 0, total_agents - n_for)
            n_neutral = total_agents - n_for - n_against

            # Per-round consensus progression
            rounds = []
            for rnd in range(self._total_rounds):
                progress = min(1.0, rnd / max(1, rounds_to_consensus))
                rnd_level = 0.2 + (consensus_level - 0.2) * progress
                noise = (_seeded_float(self._seed("cons_rnd", topic, str(rnd))) - 0.5) * 0.1
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

    # ── Resolved Consensus ─────────────────────────────────────

    def get_consensus_resolved(self) -> Dict[str, Any]:
        """List topics where consensus was reached (level >= 0.7)."""
        consensus = self.get_consensus()
        resolved = []

        for t in consensus["topics"]:
            if t["consensus_level"] < 0.7:
                continue

            # Determine resolution direction
            if t["positions"]["for"] > t["positions"]["against"]:
                resolution = "positive"
            elif t["positions"]["against"] > t["positions"]["for"]:
                resolution = "negative"
            else:
                resolution = "mixed"

            # Pick key influencers from agents deterministically
            n_influencers = _seeded_int(self._seed("n_inf", t["topic"]), 2, 4)
            influencers = []
            for j in range(n_influencers):
                idx = _seeded_int(self._seed("inf", t["topic"], str(j)), 0, len(self._agents) - 1)
                agent = self._agents[idx]
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
