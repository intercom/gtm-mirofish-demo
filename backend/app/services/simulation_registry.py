"""
Simulation Registry — manages concurrent simulation orchestrators.

Maps simulation_id -> (orchestrator_or_demo, metrics_collector).
The API layer uses this to look up the active orchestrator for any
simulation, regardless of whether it's running in real OASIS mode
or demo mode.
"""

from typing import Any, Dict, Optional, Tuple, Union

from ..config import Config
from ..utils.logger import get_logger
from .oasis_orchestrator import OasisOrchestrator
from .oasis_demo import DemoSimulator
from .oasis_metrics import MetricsCollector

logger = get_logger('mirofish.simulation_registry')

Orchestrator = Union[OasisOrchestrator, DemoSimulator]


class SimulationRegistry:
    """Thread-safe registry of active simulation orchestrators."""

    _instances: Dict[str, Orchestrator] = {}
    _metrics: Dict[str, MetricsCollector] = {}

    @classmethod
    def resolve_mode(cls) -> str:
        """Determine whether to use 'oasis' or 'demo' based on LLM key availability."""
        return "oasis" if OasisOrchestrator.is_available() else "demo"

    @classmethod
    def create(cls, simulation_id: str, config: Dict[str, Any]) -> Tuple[Orchestrator, MetricsCollector]:
        """
        Create and register an orchestrator + metrics collector.

        Automatically picks OasisOrchestrator vs DemoSimulator based on
        whether an LLM API key is configured.
        """
        mode = cls.resolve_mode()

        if mode == "oasis":
            orchestrator = OasisOrchestrator(simulation_id, config)
        else:
            orchestrator = DemoSimulator(simulation_id, config)

        metrics = MetricsCollector(simulation_id)
        metrics.total_rounds = config.get("time_config", {}).get("total_rounds", 10)

        cls._instances[simulation_id] = orchestrator
        cls._metrics[simulation_id] = metrics

        logger.info(f"Registered simulation {simulation_id} in '{mode}' mode")
        return orchestrator, metrics

    @classmethod
    def get(cls, simulation_id: str) -> Optional[Orchestrator]:
        """Look up an orchestrator by simulation ID."""
        return cls._instances.get(simulation_id)

    @classmethod
    def get_metrics(cls, simulation_id: str) -> Optional[MetricsCollector]:
        """Look up a metrics collector by simulation ID."""
        return cls._metrics.get(simulation_id)

    @classmethod
    def remove(cls, simulation_id: str) -> None:
        """Unregister a simulation (after completion / cleanup)."""
        cls._instances.pop(simulation_id, None)
        cls._metrics.pop(simulation_id, None)
        logger.info(f"Unregistered simulation {simulation_id}")

    @classmethod
    def list_active(cls) -> Dict[str, Dict[str, Any]]:
        """Return status dicts for all registered simulations."""
        return {
            sid: orch.get_status()
            for sid, orch in cls._instances.items()
        }

    @classmethod
    def get_mode(cls, simulation_id: str) -> Optional[str]:
        """Return 'oasis' or 'demo' for a registered simulation."""
        orch = cls._instances.get(simulation_id)
        if orch is None:
            return None
        return "oasis" if isinstance(orch, OasisOrchestrator) else "demo"
