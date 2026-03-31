"""
Scenario Aggregation Service
Aggregates results across multiple simulation runs for cross-scenario comparison.
"""

import math
import hashlib
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner, RunnerStatus
from .simulation_manager import SimulationManager, SimulationStatus

logger = get_logger('mirofish.aggregator')

# Sentiment word lists (shared with existing sentiment endpoint pattern)
POSITIVE_WORDS = {
    'impressive', 'excellent', 'resolved', 'improved', 'saved',
    'great', 'innovative', 'effective', 'successful', 'strong',
    'positive', 'growth', 'opportunity', 'advantage', 'recommend',
    'love', 'excited', 'amazing', 'perfect', 'solved',
}
NEGATIVE_WORDS = {
    'frustrated', 'failed', 'struggled', 'concerned', 'risk',
    'difficult', 'poor', 'expensive', 'slow', 'broken',
    'disappointed', 'confused', 'complex', 'problem', 'issue',
    'worried', 'terrible', 'worse', 'lost', 'angry',
}


def _score_sentiment(text: str) -> float:
    """Score sentiment of text from -1.0 to 1.0."""
    if not text:
        return 0.0
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


class ScenarioAggregator:
    """Aggregates metrics and outcomes across multiple simulation runs."""

    def __init__(self):
        self._manager = SimulationManager()

    def _load_sim_data(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Load run state and actions for a single simulation."""
        run_state = SimulationRunner.get_run_state(simulation_id)
        if not run_state:
            return None

        sim_state = self._manager._load_simulation_state(simulation_id)
        config = self._manager.get_simulation_config(simulation_id)

        actions = SimulationRunner.get_all_actions(simulation_id)
        timeline = SimulationRunner.get_timeline(simulation_id)
        agent_stats = SimulationRunner.get_agent_stats(simulation_id)

        return {
            "simulation_id": simulation_id,
            "run_state": run_state,
            "sim_state": sim_state,
            "config": config,
            "actions": actions,
            "timeline": timeline,
            "agent_stats": agent_stats,
        }

    def _extract_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from a single simulation's data."""
        rs = data["run_state"]
        actions = data["actions"]

        total_actions = rs.twitter_actions_count + rs.reddit_actions_count
        unique_agents = len({a.agent_id for a in actions})

        # Compute sentiment from action content
        sentiments = []
        for a in actions:
            content = a.action_args.get("content", "")
            if content:
                sentiments.append(_score_sentiment(content))

        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        # Action type distribution
        type_counts = Counter(a.action_type for a in actions)

        # Per-round activity
        rounds_active = len(data["timeline"])

        return {
            "simulation_id": data["simulation_id"],
            "status": rs.runner_status.value,
            "total_actions": total_actions,
            "twitter_actions": rs.twitter_actions_count,
            "reddit_actions": rs.reddit_actions_count,
            "unique_agents": unique_agents,
            "total_rounds": rs.total_rounds,
            "current_round": rs.current_round,
            "rounds_active": rounds_active,
            "avg_sentiment": round(avg_sentiment, 4),
            "action_types": dict(type_counts),
            "agents_count": len(data["agent_stats"]),
        }

    def aggregate_metrics(self, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        Compute averaged metrics across multiple simulations.

        Returns per-simulation metrics plus aggregated averages.
        """
        per_sim = []
        failed_ids = []

        for sim_id in simulation_ids:
            data = self._load_sim_data(sim_id)
            if data is None:
                failed_ids.append(sim_id)
                continue
            per_sim.append(self._extract_metrics(data))

        if not per_sim:
            return {
                "simulations": [],
                "aggregated": None,
                "failed_ids": failed_ids,
                "count": 0,
            }

        # Compute averages for numeric fields
        numeric_keys = [
            "total_actions", "twitter_actions", "reddit_actions",
            "unique_agents", "total_rounds", "current_round",
            "rounds_active", "avg_sentiment", "agents_count",
        ]
        n = len(per_sim)
        averages = {}
        for key in numeric_keys:
            values = [s[key] for s in per_sim]
            avg = sum(values) / n
            averages[key] = round(avg, 4)

        # Aggregate action_types across all sims
        combined_types = Counter()
        for s in per_sim:
            combined_types.update(s["action_types"])

        return {
            "simulations": per_sim,
            "aggregated": {
                **averages,
                "action_types": dict(combined_types),
            },
            "failed_ids": failed_ids,
            "count": n,
        }

    def find_common_outcomes(self, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        Find action types / agent behaviors that occurred in >50% of simulations.
        """
        all_data = []
        for sim_id in simulation_ids:
            data = self._load_sim_data(sim_id)
            if data:
                all_data.append(data)

        n = len(all_data)
        if n == 0:
            return {"common_action_types": [], "common_agents": [], "threshold": 0.5, "count": 0}

        threshold = n * 0.5

        # Action types that appear in >50% of sims
        type_presence = Counter()
        for data in all_data:
            types_in_sim = {a.action_type for a in data["actions"]}
            type_presence.update(types_in_sim)

        common_types = [
            {"action_type": t, "occurrence_count": c, "occurrence_rate": round(c / n, 4)}
            for t, c in type_presence.items() if c > threshold
        ]

        # Agents (by name pattern) that appear in >50% of sims
        agent_presence = Counter()
        for data in all_data:
            agent_names = {a.agent_name for a in data["actions"]}
            agent_presence.update(agent_names)

        common_agents = [
            {"agent_name": name, "occurrence_count": c, "occurrence_rate": round(c / n, 4)}
            for name, c in agent_presence.items() if c > threshold
        ]

        # Sentiment direction (positive/negative/neutral) appearing >50%
        sentiment_directions = Counter()
        for data in all_data:
            sentiments = [_score_sentiment(a.action_args.get("content", "")) for a in data["actions"] if a.action_args.get("content")]
            if sentiments:
                avg = sum(sentiments) / len(sentiments)
                direction = "positive" if avg > 0.05 else ("negative" if avg < -0.05 else "neutral")
                sentiment_directions[direction] += 1

        common_sentiments = [
            {"direction": d, "occurrence_count": c, "occurrence_rate": round(c / n, 4)}
            for d, c in sentiment_directions.items() if c > threshold
        ]

        return {
            "common_action_types": sorted(common_types, key=lambda x: x["occurrence_count"], reverse=True),
            "common_agents": sorted(common_agents, key=lambda x: x["occurrence_count"], reverse=True)[:20],
            "common_sentiments": common_sentiments,
            "threshold": 0.5,
            "count": n,
        }

    def find_rare_events(self, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        Find events that occurred in <10% of simulations.
        """
        all_data = []
        for sim_id in simulation_ids:
            data = self._load_sim_data(sim_id)
            if data:
                all_data.append(data)

        n = len(all_data)
        if n == 0:
            return {"rare_action_types": [], "rare_agents": [], "threshold": 0.1, "count": 0}

        threshold = max(n * 0.1, 1)

        # Action types that appear in <10% of sims
        type_presence = Counter()
        for data in all_data:
            types_in_sim = {a.action_type for a in data["actions"]}
            type_presence.update(types_in_sim)

        rare_types = [
            {"action_type": t, "occurrence_count": c, "occurrence_rate": round(c / n, 4)}
            for t, c in type_presence.items() if c < threshold
        ]

        # Agents appearing in <10% of sims
        agent_presence = Counter()
        for data in all_data:
            agent_names = {a.agent_name for a in data["actions"]}
            agent_presence.update(agent_names)

        rare_agents = [
            {"agent_name": name, "occurrence_count": c, "occurrence_rate": round(c / n, 4)}
            for name, c in agent_presence.items() if c < threshold
        ]

        return {
            "rare_action_types": sorted(rare_types, key=lambda x: x["occurrence_count"]),
            "rare_agents": sorted(rare_agents, key=lambda x: x["occurrence_count"])[:20],
            "threshold": 0.1,
            "count": n,
        }

    def compute_confidence_intervals(
        self, simulation_ids: List[str], metric: str = "total_actions"
    ) -> Dict[str, Any]:
        """
        Compute 95% confidence interval for a metric across simulation runs.

        Supported metrics: total_actions, twitter_actions, reddit_actions,
        unique_agents, avg_sentiment, rounds_active, agents_count.
        """
        valid_metrics = {
            "total_actions", "twitter_actions", "reddit_actions",
            "unique_agents", "avg_sentiment", "rounds_active", "agents_count",
        }
        if metric not in valid_metrics:
            return {"error": f"Unknown metric: {metric}. Valid: {sorted(valid_metrics)}"}

        values = []
        for sim_id in simulation_ids:
            data = self._load_sim_data(sim_id)
            if data:
                m = self._extract_metrics(data)
                values.append(m[metric])

        n = len(values)
        if n < 2:
            return {
                "metric": metric,
                "values": values,
                "count": n,
                "error": "Need at least 2 simulations for confidence intervals",
            }

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        std_dev = math.sqrt(variance)
        std_error = std_dev / math.sqrt(n)

        # 95% CI using z=1.96 (good approximation for n >= 30, reasonable for smaller n)
        z = 1.96
        ci_lower = mean - z * std_error
        ci_upper = mean + z * std_error

        return {
            "metric": metric,
            "count": n,
            "mean": round(mean, 4),
            "std_dev": round(std_dev, 4),
            "std_error": round(std_error, 4),
            "ci_95_lower": round(ci_lower, 4),
            "ci_95_upper": round(ci_upper, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "values": [round(v, 4) for v in values],
        }

    def cluster_simulations(self, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        Group similar simulation outcomes using simple k-means-style clustering
        on normalized metrics. Uses 2-3 clusters depending on data spread.

        No external dependencies — implements distance-based clustering manually.
        """
        all_metrics = []
        for sim_id in simulation_ids:
            data = self._load_sim_data(sim_id)
            if data:
                all_metrics.append(self._extract_metrics(data))

        n = len(all_metrics)
        if n < 2:
            return {
                "clusters": [{"label": "all", "simulation_ids": [m["simulation_id"] for m in all_metrics]}] if all_metrics else [],
                "count": n,
            }

        # Feature vector: total_actions, avg_sentiment, unique_agents, rounds_active
        feature_keys = ["total_actions", "avg_sentiment", "unique_agents", "rounds_active"]
        raw_vectors = []
        for m in all_metrics:
            raw_vectors.append([float(m[k]) for k in feature_keys])

        # Normalize each feature to 0-1
        mins = [min(v[i] for v in raw_vectors) for i in range(len(feature_keys))]
        maxs = [max(v[i] for v in raw_vectors) for i in range(len(feature_keys))]
        ranges = [maxs[i] - mins[i] if maxs[i] != mins[i] else 1.0 for i in range(len(feature_keys))]

        normalized = [
            [(v[i] - mins[i]) / ranges[i] for i in range(len(feature_keys))]
            for v in raw_vectors
        ]

        # Determine cluster count: 2 for < 6 sims, 3 otherwise
        k = min(2 if n < 6 else 3, n)

        # Deterministic seed selection for centroids
        seed = int(hashlib.md5(",".join(simulation_ids).encode()).hexdigest()[:8], 16)
        indices = list(range(n))
        indices.sort(key=lambda i: (seed + i * 7) % (n + 3))
        centroids = [normalized[indices[i]][:] for i in range(k)]

        # Simple k-means, 20 iterations max
        assignments = [0] * n
        for _ in range(20):
            # Assign each point to nearest centroid
            changed = False
            for i, vec in enumerate(normalized):
                dists = [sum((vec[d] - c[d]) ** 2 for d in range(len(feature_keys))) for c in centroids]
                nearest = dists.index(min(dists))
                if assignments[i] != nearest:
                    changed = True
                    assignments[i] = nearest

            if not changed:
                break

            # Recompute centroids
            for ci in range(k):
                members = [normalized[i] for i in range(n) if assignments[i] == ci]
                if members:
                    centroids[ci] = [
                        sum(m[d] for m in members) / len(members)
                        for d in range(len(feature_keys))
                    ]

        # Build cluster output
        cluster_map = defaultdict(list)
        for i, ci in enumerate(assignments):
            cluster_map[ci].append(all_metrics[i])

        labels = ["high_engagement", "moderate_engagement", "low_engagement"]
        clusters = []
        for ci in sorted(cluster_map.keys()):
            members = cluster_map[ci]
            avg_actions = sum(m["total_actions"] for m in members) / len(members)
            clusters.append({
                "label": labels[ci] if ci < len(labels) else f"cluster_{ci}",
                "simulation_ids": [m["simulation_id"] for m in members],
                "size": len(members),
                "avg_total_actions": round(avg_actions, 2),
                "avg_sentiment": round(sum(m["avg_sentiment"] for m in members) / len(members), 4),
            })

        # Sort clusters by avg_total_actions descending for consistent labeling
        clusters.sort(key=lambda c: c["avg_total_actions"], reverse=True)
        for i, c in enumerate(clusters):
            c["label"] = labels[i] if i < len(labels) else f"cluster_{i}"

        return {
            "clusters": clusters,
            "feature_keys": feature_keys,
            "count": n,
            "k": k,
        }
