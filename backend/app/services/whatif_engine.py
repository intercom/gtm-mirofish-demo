"""
What-If Analysis Engine — runs scenario variations and compares outcomes.

Supports creating modified scenario configs, running them (with deterministic
mock results for demo mode), comparing variants to a base, and parameter
sensitivity sweeps.
"""

import hashlib
import math
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from ..utils.logger import get_logger
    logger = get_logger('mirofish.whatif')
except (ImportError, ValueError):
    import logging
    logger = logging.getLogger('mirofish.whatif')


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class ModificationType(str, Enum):
    CHANGE_AGENT_COUNT = "change_agent_count"
    CHANGE_AGENT_PERSONALITY = "change_agent_personality"
    CHANGE_ENVIRONMENT = "change_environment"
    CHANGE_LLM_PROVIDER = "change_llm_provider"
    CHANGE_ROUNDS = "change_rounds"
    CHANGE_CONSTRAINTS = "change_constraints"


class ScenarioStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Default base scenario config — mirrors demo_app.py defaults
_DEFAULT_BASE_CONFIG = {
    "agent_count": 15,
    "total_rounds": 144,
    "total_hours": 72,
    "minutes_per_round": 30,
    "platform_mode": "parallel",
    "personality_mix": {
        "vp_support": 0.20,
        "cx_director": 0.20,
        "it_leader": 0.13,
        "operations": 0.20,
        "finance": 0.07,
        "support_manager": 0.07,
        "cto": 0.07,
        "customer_success": 0.06,
    },
    "environment": {
        "industry_focus": "mixed",
        "competitive_intensity": 0.6,
        "market_sentiment": 0.5,
        "budget_pressure": 0.5,
    },
    "constraints": {
        "max_posts_per_agent": 20,
        "reply_probability": 0.4,
        "like_probability": 0.3,
        "repost_probability": 0.1,
    },
    "llm_provider": "anthropic",
    "temperature": 0.7,
}

# Persona types used in the simulation
PERSONA_TYPES = [
    "vp_support", "cx_director", "it_leader", "operations",
    "finance", "support_manager", "cto", "customer_success",
]

# Outcome metric names
OUTCOME_METRICS = [
    "avg_sentiment",
    "consensus_reached",
    "decision_quality",
    "time_to_resolution",
    "total_engagement",
    "ai_resolution_advocacy",
    "competitive_displacement_score",
    "meeting_booking_rate",
]


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Modification:
    """A single modification to apply to a base scenario."""
    type: ModificationType
    parameter: str
    value: Any
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type.value if isinstance(self.type, ModificationType) else self.type,
            "parameter": self.parameter,
            "value": self.value,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Modification":
        return cls(
            type=ModificationType(d["type"]),
            parameter=d["parameter"],
            value=d["value"],
            label=d.get("label", ""),
        )


@dataclass
class ScenarioConfig:
    """Configuration for a what-if scenario (base or variant)."""
    scenario_id: str
    base_scenario_id: Optional[str]
    label: str
    config: Dict[str, Any]
    modifications: List[Modification] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "base_scenario_id": self.base_scenario_id,
            "label": self.label,
            "config": self.config,
            "modifications": [m.to_dict() for m in self.modifications],
            "created_at": self.created_at,
        }


@dataclass
class SimulationResults:
    """Outcome metrics from running a scenario."""
    scenario_id: str
    status: ScenarioStatus
    metrics: Dict[str, float] = field(default_factory=dict)
    agent_metrics: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    completed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "metrics": self.metrics,
            "agent_metrics": self.agent_metrics,
            "timeline": self.timeline,
            "duration_seconds": self.duration_seconds,
            "completed_at": self.completed_at,
        }


@dataclass
class ComparisonResult:
    """Structured comparison between base and variant scenarios."""
    base_id: str
    variant_id: str
    metric_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    summary: str = ""
    winner: str = ""

    def to_dict(self) -> dict:
        return {
            "base_id": self.base_id,
            "variant_id": self.variant_id,
            "metric_deltas": self.metric_deltas,
            "summary": self.summary,
            "winner": self.winner,
        }


@dataclass
class SensitivityResult:
    """Results from a parameter sensitivity sweep."""
    base_id: str
    parameter: str
    variants: List[Dict[str, Any]] = field(default_factory=list)
    sensitivity_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "base_id": self.base_id,
            "parameter": self.parameter,
            "variants": self.variants,
            "sensitivity_scores": self.sensitivity_scores,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class WhatIfEngine:
    """Runs scenario variations for what-if analysis.

    All state is held in-memory. In demo mode (no LLM key), results are
    generated deterministically from seeded random so they're reproducible
    across calls.
    """

    def __init__(self):
        self._scenarios: Dict[str, ScenarioConfig] = {}
        self._results: Dict[str, SimulationResults] = {}
        self._variant_links: Dict[str, List[str]] = {}  # base_id -> [variant_ids]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_scenario(
        self,
        base_scenario_id: Optional[str],
        modifications: List[Dict[str, Any]],
        label: str = "",
    ) -> ScenarioConfig:
        """Create a modified scenario config from a base.

        If base_scenario_id is None, uses the default base config.
        Returns the new ScenarioConfig with modifications applied.
        """
        base_config = self._resolve_base_config(base_scenario_id)
        mods = [Modification.from_dict(m) for m in modifications]

        new_config = self._apply_modifications(dict(base_config), mods)
        scenario_id = f"whatif-{uuid.uuid4().hex[:8]}"

        if not label:
            label = self._auto_label(mods)

        scenario = ScenarioConfig(
            scenario_id=scenario_id,
            base_scenario_id=base_scenario_id,
            label=label,
            config=new_config,
            modifications=mods,
        )

        self._scenarios[scenario_id] = scenario

        # Link variant to base
        effective_base = base_scenario_id or "__default__"
        self._variant_links.setdefault(effective_base, []).append(scenario_id)

        logger.info("Created scenario %s from base %s with %d modifications",
                     scenario_id, effective_base, len(mods))
        return scenario

    def run_scenario(self, scenario_id: str) -> SimulationResults:
        """Run a scenario and return results with outcome metrics.

        In demo mode, generates deterministic mock results derived from the
        scenario config using seeded randomness.
        """
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        start = time.time()
        results = self._generate_mock_results(scenario)
        results.duration_seconds = round(time.time() - start, 3)
        results.completed_at = datetime.utcnow().isoformat()
        results.status = ScenarioStatus.COMPLETED

        self._results[scenario_id] = results
        logger.info("Completed scenario %s in %.3fs", scenario_id, results.duration_seconds)
        return results

    def compare_to_base(self, base_id: str, variant_id: str) -> ComparisonResult:
        """Compare a variant's results to the base scenario.

        Both scenarios must have been run first.
        """
        base_results = self._get_results(base_id)
        variant_results = self._get_results(variant_id)

        metric_deltas = {}
        improvements = 0
        regressions = 0

        for metric in OUTCOME_METRICS:
            base_val = base_results.metrics.get(metric, 0.0)
            variant_val = variant_results.metrics.get(metric, 0.0)
            delta = variant_val - base_val
            pct_change = (delta / base_val * 100) if base_val != 0 else 0.0

            metric_deltas[metric] = {
                "base_value": round(base_val, 4),
                "variant_value": round(variant_val, 4),
                "delta": round(delta, 4),
                "percent_change": round(pct_change, 2),
            }

            if delta > 0.001:
                improvements += 1
            elif delta < -0.001:
                regressions += 1

        winner = "variant" if improvements > regressions else "base" if regressions > improvements else "tie"

        variant_scenario = self._scenarios.get(variant_id)
        mod_desc = variant_scenario.label if variant_scenario else "variant"

        summary = (
            f"Variant '{mod_desc}' shows {improvements} improved metrics "
            f"and {regressions} regressed metrics vs base. "
            f"Overall winner: {winner}."
        )

        return ComparisonResult(
            base_id=base_id,
            variant_id=variant_id,
            metric_deltas=metric_deltas,
            summary=summary,
            winner=winner,
        )

    def run_sensitivity(
        self,
        base_id: Optional[str],
        parameter: str,
        value_range: List[Any],
    ) -> SensitivityResult:
        """Run multiple variations of one parameter (batch sweep).

        Creates and runs up to len(value_range) scenarios, then computes
        sensitivity scores showing how much each outcome metric changes
        per unit change in the parameter.
        """
        base_config = self._resolve_base_config(base_id)

        # Ensure a base result exists
        effective_base = base_id or "__default__"
        if effective_base not in self._results:
            base_scenario = self._ensure_base_scenario(base_id)
            self.run_scenario(base_scenario.scenario_id)
            effective_base = base_scenario.scenario_id

        base_results = self._results[effective_base]
        variants_data = []

        mod_type = self._infer_modification_type(parameter)

        for val in value_range:
            mod = {
                "type": mod_type.value,
                "parameter": parameter,
                "value": val,
                "label": f"{parameter}={val}",
            }
            scenario = self.create_scenario(base_id, [mod], label=f"{parameter}={val}")
            results = self.run_scenario(scenario.scenario_id)

            variants_data.append({
                "scenario_id": scenario.scenario_id,
                "parameter_value": val,
                "metrics": results.metrics,
            })

        # Compute sensitivity scores: for each metric, compute how much it
        # changes on average per unit change in the parameter (when numeric)
        sensitivity_scores = self._compute_sensitivity_scores(
            parameter, value_range, base_results.metrics, variants_data
        )

        return SensitivityResult(
            base_id=effective_base,
            parameter=parameter,
            variants=variants_data,
            sensitivity_scores=sensitivity_scores,
        )

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        return self._scenarios.get(scenario_id)

    def get_results(self, scenario_id: str) -> Optional[SimulationResults]:
        return self._results.get(scenario_id)

    def get_variants(self, base_id: str) -> List[ScenarioConfig]:
        """Get all variant scenarios linked to a base."""
        effective_base = base_id or "__default__"
        variant_ids = self._variant_links.get(effective_base, [])
        return [self._scenarios[vid] for vid in variant_ids if vid in self._scenarios]

    def list_scenarios(self) -> List[ScenarioConfig]:
        return list(self._scenarios.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_base_config(self, base_scenario_id: Optional[str]) -> Dict[str, Any]:
        """Return the config dict for the given base scenario, or default."""
        if base_scenario_id and base_scenario_id in self._scenarios:
            return dict(self._scenarios[base_scenario_id].config)
        return dict(_DEFAULT_BASE_CONFIG)

    def _ensure_base_scenario(self, base_id: Optional[str]) -> ScenarioConfig:
        """Ensure there's a stored scenario for the base (creates one if needed)."""
        if base_id and base_id in self._scenarios:
            return self._scenarios[base_id]

        scenario_id = base_id or f"whatif-base-{uuid.uuid4().hex[:8]}"
        scenario = ScenarioConfig(
            scenario_id=scenario_id,
            base_scenario_id=None,
            label="Base scenario",
            config=dict(_DEFAULT_BASE_CONFIG),
        )
        self._scenarios[scenario_id] = scenario
        return scenario

    def _apply_modifications(
        self, config: Dict[str, Any], mods: List[Modification]
    ) -> Dict[str, Any]:
        """Apply a list of modifications to a config dict."""
        for mod in mods:
            if mod.type == ModificationType.CHANGE_AGENT_COUNT:
                config["agent_count"] = int(mod.value)

            elif mod.type == ModificationType.CHANGE_ROUNDS:
                config["total_rounds"] = int(mod.value)
                config["total_hours"] = int(mod.value) * config.get("minutes_per_round", 30) / 60

            elif mod.type == ModificationType.CHANGE_AGENT_PERSONALITY:
                # value can be a dict of persona_type -> weight
                if isinstance(mod.value, dict):
                    config["personality_mix"] = {**config.get("personality_mix", {}), **mod.value}
                elif mod.parameter in PERSONA_TYPES:
                    config.setdefault("personality_mix", {})[mod.parameter] = float(mod.value)

            elif mod.type == ModificationType.CHANGE_ENVIRONMENT:
                if isinstance(mod.value, dict):
                    config["environment"] = {**config.get("environment", {}), **mod.value}
                elif mod.parameter:
                    config.setdefault("environment", {})[mod.parameter] = mod.value

            elif mod.type == ModificationType.CHANGE_LLM_PROVIDER:
                config["llm_provider"] = str(mod.value)
                if mod.parameter == "temperature":
                    config["temperature"] = float(mod.value)

            elif mod.type == ModificationType.CHANGE_CONSTRAINTS:
                if isinstance(mod.value, dict):
                    config["constraints"] = {**config.get("constraints", {}), **mod.value}
                elif mod.parameter:
                    config.setdefault("constraints", {})[mod.parameter] = mod.value

        return config

    def _auto_label(self, mods: List[Modification]) -> str:
        """Generate a human-readable label from modifications."""
        if not mods:
            return "Unmodified variant"
        parts = []
        for m in mods[:3]:
            parts.append(m.label or f"{m.parameter}={m.value}")
        label = ", ".join(parts)
        if len(mods) > 3:
            label += f" (+{len(mods) - 3} more)"
        return label

    def _get_results(self, scenario_id: str) -> SimulationResults:
        """Get results or raise if not found."""
        results = self._results.get(scenario_id)
        if not results:
            raise ValueError(
                f"No results for scenario {scenario_id}. Run it first."
            )
        return results

    def _infer_modification_type(self, parameter: str) -> ModificationType:
        """Infer the modification type from a parameter name."""
        mapping = {
            "agent_count": ModificationType.CHANGE_AGENT_COUNT,
            "total_rounds": ModificationType.CHANGE_ROUNDS,
            "round_count": ModificationType.CHANGE_ROUNDS,
            "temperature": ModificationType.CHANGE_LLM_PROVIDER,
            "llm_provider": ModificationType.CHANGE_LLM_PROVIDER,
            "competitive_intensity": ModificationType.CHANGE_ENVIRONMENT,
            "market_sentiment": ModificationType.CHANGE_ENVIRONMENT,
            "budget_pressure": ModificationType.CHANGE_ENVIRONMENT,
            "industry_focus": ModificationType.CHANGE_ENVIRONMENT,
            "max_posts_per_agent": ModificationType.CHANGE_CONSTRAINTS,
            "reply_probability": ModificationType.CHANGE_CONSTRAINTS,
            "like_probability": ModificationType.CHANGE_CONSTRAINTS,
            "repost_probability": ModificationType.CHANGE_CONSTRAINTS,
        }
        for key in PERSONA_TYPES:
            mapping[key] = ModificationType.CHANGE_AGENT_PERSONALITY
        return mapping.get(parameter, ModificationType.CHANGE_ENVIRONMENT)

    # ------------------------------------------------------------------
    # Deterministic mock result generation
    # ------------------------------------------------------------------

    def _config_seed(self, config: Dict[str, Any]) -> int:
        """Derive a deterministic seed from a config dict."""
        raw = str(sorted(self._flatten(config).items()))
        return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)

    def _flatten(self, d: dict, prefix: str = "") -> dict:
        """Flatten nested dict for hashing."""
        items = {}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.update(self._flatten(v, key))
            else:
                items[key] = v
        return items

    def _generate_mock_results(self, scenario: ScenarioConfig) -> SimulationResults:
        """Generate deterministic mock simulation results from config."""
        config = scenario.config
        seed = self._config_seed(config)
        rng = random.Random(seed)

        agent_count = config.get("agent_count", 15)
        total_rounds = config.get("total_rounds", 144)
        env = config.get("environment", {})
        constraints = config.get("constraints", {})
        personality_mix = config.get("personality_mix", {})

        # Environment factors influence outcomes
        competitive_intensity = env.get("competitive_intensity", 0.6)
        market_sentiment = env.get("market_sentiment", 0.5)
        budget_pressure = env.get("budget_pressure", 0.5)

        # Scale factor from agent count (diminishing returns past 15)
        agent_scale = math.log(agent_count + 1) / math.log(16)

        # Round scale (more rounds = more convergence, diminishing returns)
        round_scale = math.log(total_rounds + 1) / math.log(145)

        # Personality influence: heavy vp_support + cx_director = higher sentiment
        vp_weight = personality_mix.get("vp_support", 0.2)
        cx_weight = personality_mix.get("cx_director", 0.2)
        leadership_factor = (vp_weight + cx_weight) / 0.4  # normalized around 1.0

        # Reply probability affects engagement
        reply_prob = constraints.get("reply_probability", 0.4)

        # Compute outcome metrics with config-sensitive noise
        base_sentiment = 0.62 * market_sentiment / 0.5 * leadership_factor
        avg_sentiment = max(-1.0, min(1.0,
            base_sentiment + rng.gauss(0, 0.05) * round_scale
        ))

        consensus_raw = (
            0.7 * round_scale
            + 0.15 * agent_scale
            + 0.1 * leadership_factor
            + 0.05 * market_sentiment
            + rng.gauss(0, 0.03)
        )
        consensus_reached = 1.0 if consensus_raw > 0.75 else 0.0

        decision_quality = max(0.0, min(1.0,
            0.55
            + 0.15 * agent_scale
            + 0.12 * round_scale
            + 0.08 * leadership_factor
            - 0.05 * budget_pressure
            + rng.gauss(0, 0.04)
        ))

        # Time to resolution (in rounds) — more agents/rounds = faster
        base_ttr = total_rounds * 0.6
        ttr_factor = (
            1.0
            - 0.15 * (agent_scale - 0.5)
            - 0.1 * (competitive_intensity - 0.5)
            + 0.1 * (budget_pressure - 0.5)
        )
        time_to_resolution = max(10, int(base_ttr * ttr_factor + rng.gauss(0, 5)))

        total_engagement = int(
            agent_count * total_rounds * 0.6
            * (0.8 + 0.4 * reply_prob)
            * agent_scale
            + rng.gauss(0, 20)
        )

        ai_advocacy = max(0.0, min(1.0,
            0.58
            + 0.12 * round_scale
            + 0.1 * (1.0 - budget_pressure)
            + 0.05 * leadership_factor
            + rng.gauss(0, 0.04)
        ))

        displacement_score = max(0.0, min(1.0,
            0.45
            + 0.2 * competitive_intensity
            + 0.1 * agent_scale
            + 0.05 * market_sentiment
            + rng.gauss(0, 0.05)
        ))

        meeting_rate = max(0.0, min(1.0,
            0.12
            + 0.08 * leadership_factor
            + 0.05 * round_scale
            - 0.03 * budget_pressure
            + 0.04 * competitive_intensity
            + rng.gauss(0, 0.02)
        ))

        metrics = {
            "avg_sentiment": round(avg_sentiment, 4),
            "consensus_reached": consensus_reached,
            "decision_quality": round(decision_quality, 4),
            "time_to_resolution": time_to_resolution,
            "total_engagement": max(0, total_engagement),
            "ai_resolution_advocacy": round(ai_advocacy, 4),
            "competitive_displacement_score": round(displacement_score, 4),
            "meeting_booking_rate": round(meeting_rate, 4),
        }

        # Per-agent metrics
        agent_metrics = self._generate_agent_metrics(config, rng)

        # Timeline buckets (6-round buckets)
        timeline = self._generate_timeline(config, rng)

        return SimulationResults(
            scenario_id=scenario.scenario_id,
            status=ScenarioStatus.RUNNING,  # will be set to COMPLETED by caller
            metrics=metrics,
            agent_metrics=agent_metrics,
            timeline=timeline,
        )

    def _generate_agent_metrics(
        self, config: Dict[str, Any], rng: random.Random
    ) -> List[Dict[str, Any]]:
        """Generate per-agent outcome data."""
        agents = [
            ("Sarah Chen", "VP Support", "Acme SaaS"),
            ("Marcus Johnson", "CX Director", "MedFirst Health"),
            ("Priya Patel", "Head of Ops", "PayStream Financial"),
            ("David Kim", "IT Leader", "ShopNova"),
            ("Rachel Torres", "VP Support", "CloudOps Inc"),
            ("James Wright", "CX Director", "Retail Plus"),
            ("Anika Sharma", "Support Eng Lead", "DevStack"),
            ("Tom O'Brien", "VP CS", "GrowthLoop"),
            ("Elena Vasquez", "Dir Digital", "HealthBridge"),
            ("Michael Chang", "Head of Ops", "FinEdge"),
            ("Lisa Park", "VP CX", "TravelNow"),
            ("Sofia Martinez", "Support Mgr", "QuickShip"),
            ("Nathan Lee", "CTO", "DataPulse"),
            ("Catherine Hayes", "CFO", "ScaleUp Corp"),
            ("Robert Williams", "IT Director", "EduSpark"),
        ]

        agent_count = min(config.get("agent_count", 15), len(agents))
        total_rounds = config.get("total_rounds", 144)
        env = config.get("environment", {})
        market_sentiment = env.get("market_sentiment", 0.5)

        result = []
        for i in range(agent_count):
            name, role, company = agents[i]
            base_sentiment = 0.5 + 0.3 * market_sentiment + rng.gauss(0, 0.15)
            posts = max(1, int(total_rounds * (0.4 + rng.uniform(0, 0.3))))
            engagement = max(0, int(posts * (1.5 + rng.uniform(0, 1.0))))

            result.append({
                "agent_name": name,
                "agent_role": role,
                "company": company,
                "posts": posts,
                "engagement_score": round(engagement / max(1, total_rounds), 4),
                "avg_sentiment": round(max(-1, min(1, base_sentiment)), 4),
                "decision_stage": rng.choice([
                    "Awareness", "Interest", "Consideration",
                    "Intent", "Evaluation", "Decision",
                ]),
            })

        return result

    def _generate_timeline(
        self, config: Dict[str, Any], rng: random.Random
    ) -> List[Dict[str, Any]]:
        """Generate timeline data in 6-round buckets."""
        total_rounds = config.get("total_rounds", 144)
        agent_count = config.get("agent_count", 15)
        bucket_size = 6
        buckets = max(1, total_rounds // bucket_size)

        timeline = []
        for b in range(buckets):
            round_start = b * bucket_size + 1
            base_activity = agent_count * 0.4 * math.log(b + 2)
            actions = max(1, int(base_activity + rng.gauss(0, 2)))
            sentiment = 0.4 + 0.3 * (b / max(1, buckets)) + rng.gauss(0, 0.08)

            timeline.append({
                "bucket": b,
                "round_start": round_start,
                "round_end": min(total_rounds, round_start + bucket_size - 1),
                "actions": actions,
                "avg_sentiment": round(max(-1, min(1, sentiment)), 4),
            })

        return timeline

    def _compute_sensitivity_scores(
        self,
        parameter: str,
        value_range: List[Any],
        base_metrics: Dict[str, float],
        variants_data: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Compute how much each metric changes per unit of parameter change."""
        scores = {}

        # Only compute slope-style sensitivity for numeric parameters
        numeric_values = []
        for v in value_range:
            try:
                numeric_values.append(float(v))
            except (TypeError, ValueError):
                numeric_values = []
                break

        if not numeric_values or len(numeric_values) < 2:
            # Non-numeric: compute max spread as sensitivity
            for metric in OUTCOME_METRICS:
                values = [vd["metrics"].get(metric, 0.0) for vd in variants_data]
                if values:
                    scores[metric] = round(max(values) - min(values), 4)
                else:
                    scores[metric] = 0.0
            return scores

        param_range = max(numeric_values) - min(numeric_values)
        if param_range == 0:
            return {m: 0.0 for m in OUTCOME_METRICS}

        for metric in OUTCOME_METRICS:
            metric_values = [vd["metrics"].get(metric, 0.0) for vd in variants_data]
            metric_range = max(metric_values) - min(metric_values)
            # Sensitivity = metric change per unit parameter change (normalized)
            scores[metric] = round(metric_range / param_range, 6)

        return scores
