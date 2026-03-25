"""
OASIS Orchestrator — manages real LLM-powered simulations.

This is the interface contract that the simulation API endpoints depend on.
The full implementation (LLM calls, round execution, agent management) will
be built out in a parallel task. The stub below provides enough structure
for the API wiring to compile and for demo mode fallback to work.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.oasis_orchestrator')


class OrchestratorStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class OasisOrchestrator:
    """
    Runs a real OASIS simulation using the configured LLM provider.

    Lifecycle:
        1. __init__(simulation_id, config)
        2. start(max_rounds) -> kicks off simulation
        3. pause() / resume()
        4. get_round(n) -> results for round n
        5. get_status() -> current state dict
        6. stop()
    """

    def __init__(self, simulation_id: str, config: Dict[str, Any]):
        self.simulation_id = simulation_id
        self.config = config
        self.status = OrchestratorStatus.IDLE
        self.current_round = 0
        self.max_rounds = 0
        self.rounds: Dict[int, Dict[str, Any]] = {}
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None

    def start(self, max_rounds: Optional[int] = None) -> Dict[str, Any]:
        """Start the OASIS simulation. Delegates to SimulationRunner for now."""
        self.max_rounds = max_rounds or self.config.get("time_config", {}).get("total_rounds", 10)
        self.status = OrchestratorStatus.RUNNING
        self.started_at = datetime.now().isoformat()
        logger.info(f"OasisOrchestrator started: {self.simulation_id}, max_rounds={self.max_rounds}")
        return self.get_status()

    def pause(self) -> Dict[str, Any]:
        """Pause a running simulation."""
        if self.status != OrchestratorStatus.RUNNING:
            raise ValueError(f"Cannot pause simulation in state: {self.status.value}")
        self.status = OrchestratorStatus.PAUSED
        logger.info(f"OasisOrchestrator paused: {self.simulation_id}")
        return self.get_status()

    def resume(self) -> Dict[str, Any]:
        """Resume a paused simulation."""
        if self.status != OrchestratorStatus.PAUSED:
            raise ValueError(f"Cannot resume simulation in state: {self.status.value}")
        self.status = OrchestratorStatus.RUNNING
        logger.info(f"OasisOrchestrator resumed: {self.simulation_id}")
        return self.get_status()

    def stop(self) -> Dict[str, Any]:
        """Stop the simulation."""
        self.status = OrchestratorStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        logger.info(f"OasisOrchestrator stopped: {self.simulation_id}")
        return self.get_status()

    def get_round(self, round_num: int) -> Optional[Dict[str, Any]]:
        """Get results for a specific round."""
        return self.rounds.get(round_num)

    def get_status(self) -> Dict[str, Any]:
        """Return current orchestrator state."""
        return {
            "simulation_id": self.simulation_id,
            "status": self.status.value,
            "mode": "oasis",
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }

    @staticmethod
    def is_available() -> bool:
        """Check if an LLM API key is configured."""
        return bool(Config.LLM_API_KEY)
