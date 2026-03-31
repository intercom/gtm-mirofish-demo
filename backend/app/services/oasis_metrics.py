"""
OASIS Metrics Collector — aggregates simulation statistics.

Provides a unified interface for both OasisOrchestrator and DemoSimulator
to report metrics. The API layer calls get_summary() to return metrics
to the frontend.
"""

from typing import Any, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.oasis_metrics')


class MetricsCollector:
    """
    Collects and aggregates metrics from a running or completed simulation.
    One instance per simulation, stored in the simulation registry.
    """

    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        self.total_rounds = 0
        self.completed_rounds = 0
        self.total_actions = 0
        self.twitter_actions = 0
        self.reddit_actions = 0
        self.active_agents = 0
        self.actions_by_type: Dict[str, int] = {}
        self.actions_by_agent: Dict[str, int] = {}

    def record_round(self, round_data: Dict[str, Any]):
        """Record metrics from a completed round."""
        self.completed_rounds += 1
        actions = round_data.get("actions", [])
        self.total_actions += len(actions)
        self.twitter_actions += round_data.get("twitter_actions", 0)
        self.reddit_actions += round_data.get("reddit_actions", 0)

        agents_seen = set()
        for action in actions:
            action_type = action.get("action_type", "UNKNOWN")
            self.actions_by_type[action_type] = self.actions_by_type.get(action_type, 0) + 1

            agent_name = action.get("agent_name", "unknown")
            self.actions_by_agent[agent_name] = self.actions_by_agent.get(agent_name, 0) + 1
            agents_seen.add(agent_name)

        self.active_agents = max(self.active_agents, len(agents_seen))

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary dict for the API response."""
        return {
            "simulation_id": self.simulation_id,
            "total_rounds": self.total_rounds,
            "completed_rounds": self.completed_rounds,
            "total_actions": self.total_actions,
            "twitter_actions": self.twitter_actions,
            "reddit_actions": self.reddit_actions,
            "active_agents": self.active_agents,
            "actions_by_type": self.actions_by_type,
            "actions_by_agent": self.actions_by_agent,
        }

    def ingest_from_orchestrator(self, orchestrator) -> None:
        """
        Bulk-ingest all rounds from an orchestrator (or demo simulator)
        that has already completed. Useful for demo mode where all rounds
        are generated synchronously.
        """
        for round_num in sorted(orchestrator.rounds.keys()):
            self.record_round(orchestrator.rounds[round_num])
        self.total_rounds = orchestrator.max_rounds
