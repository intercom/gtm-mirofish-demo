"""
Demo Simulator — generates synthetic simulation data without LLM calls.

Mimics the OasisOrchestrator interface so the API layer can treat both
identically. Used when no LLM_API_KEY is configured.
"""

import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.oasis_demo')


class DemoSimulator:
    """
    Generates fake but realistic-looking simulation rounds.
    Same interface as OasisOrchestrator so the registry / API can swap freely.
    """

    DEMO_ACTION_TYPES = [
        "CREATE_POST", "LIKE_POST", "REPOST", "FOLLOW",
        "DO_NOTHING", "CREATE_COMMENT", "LIKE_COMMENT",
    ]

    DEMO_AGENT_NAMES = [
        "Alex Chen", "Jordan Rivera", "Morgan Lee", "Casey Kim",
        "Taylor Brooks", "Avery Patel", "Quinn Santos", "Drew Anderson",
    ]

    def __init__(self, simulation_id: str, config: Dict[str, Any]):
        self.simulation_id = simulation_id
        self.config = config
        self.status = "idle"
        self.current_round = 0
        self.max_rounds = 0
        self.rounds: Dict[int, Dict[str, Any]] = {}
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None

    def start(self, max_rounds: Optional[int] = None) -> Dict[str, Any]:
        self.max_rounds = max_rounds or 10
        self.status = "running"
        self.started_at = datetime.now().isoformat()
        self._generate_all_rounds()
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        self.current_round = self.max_rounds
        logger.info(f"DemoSimulator completed: {self.simulation_id}, rounds={self.max_rounds}")
        return self.get_status()

    def _generate_all_rounds(self):
        """Pre-generate all rounds with synthetic data."""
        num_agents = min(len(self.DEMO_AGENT_NAMES), self.config.get("agent_count", 5))
        agents = self.DEMO_AGENT_NAMES[:num_agents]

        for r in range(1, self.max_rounds + 1):
            actions = []
            for i, name in enumerate(agents):
                action_type = random.choice(self.DEMO_ACTION_TYPES)
                actions.append({
                    "round_num": r,
                    "agent_id": i,
                    "agent_name": name,
                    "action_type": action_type,
                    "platform": random.choice(["twitter", "reddit"]),
                    "timestamp": datetime.now().isoformat(),
                })
            self.rounds[r] = {
                "round_num": r,
                "actions": actions,
                "twitter_actions": sum(1 for a in actions if a["platform"] == "twitter"),
                "reddit_actions": sum(1 for a in actions if a["platform"] == "reddit"),
                "active_agents": len(agents),
            }

    def pause(self) -> Dict[str, Any]:
        if self.status != "running":
            raise ValueError(f"Cannot pause demo simulation in state: {self.status}")
        self.status = "paused"
        return self.get_status()

    def resume(self) -> Dict[str, Any]:
        if self.status != "paused":
            raise ValueError(f"Cannot resume demo simulation in state: {self.status}")
        self.status = "running"
        return self.get_status()

    def stop(self) -> Dict[str, Any]:
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        return self.get_status()

    def get_round(self, round_num: int) -> Optional[Dict[str, Any]]:
        return self.rounds.get(round_num)

    def get_status(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "status": self.status,
            "mode": "demo",
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }
