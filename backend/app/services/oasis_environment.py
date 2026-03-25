"""
OASIS Environment Manager
Manages simulation environment lifecycle: creation, agent placement,
constraint configuration, stepping, and state retrieval.

Wraps the low-level oasis library calls (oasis.make, env.reset, env.step)
into a service-layer abstraction used by SimulationRunner and the API layer.
"""

import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.environment')


# ---------------------------------------------------------------------------
# Try importing OASIS — gracefully degrade to demo mode if unavailable
# ---------------------------------------------------------------------------
try:
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_twitter_agent_graph,
        generate_reddit_agent_graph,
    )
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType

    OASIS_AVAILABLE = True
except ImportError:
    OASIS_AVAILABLE = False


class EnvironmentType(str, Enum):
    """Supported OASIS environment types, each with distinct interaction patterns."""
    PIPELINE_REVIEW = "pipeline_review"
    DEAL_NEGOTIATION = "deal_negotiation"
    MARKET_SIMULATION = "market_simulation"
    TEAM_STANDUP = "team_standup"
    QUARTERLY_REVIEW = "quarterly_review"


class EnvironmentStatus(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Default constraints per environment type
# ---------------------------------------------------------------------------
_DEFAULT_CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    EnvironmentType.PIPELINE_REVIEW: {
        "max_rounds": 20,
        "budget_limit": None,
        "competitive_pressure": 0.3,
        "interaction_style": "structured",
        "time_pressure": 0.5,
        "allowed_actions": Config.OASIS_TWITTER_ACTIONS,
    },
    EnvironmentType.DEAL_NEGOTIATION: {
        "max_rounds": 30,
        "budget_limit": 100_000,
        "competitive_pressure": 0.8,
        "interaction_style": "adversarial",
        "time_pressure": 0.7,
        "allowed_actions": Config.OASIS_TWITTER_ACTIONS,
    },
    EnvironmentType.MARKET_SIMULATION: {
        "max_rounds": 50,
        "budget_limit": None,
        "competitive_pressure": 0.6,
        "interaction_style": "organic",
        "time_pressure": 0.3,
        "allowed_actions": Config.OASIS_TWITTER_ACTIONS + Config.OASIS_REDDIT_ACTIONS,
    },
    EnvironmentType.TEAM_STANDUP: {
        "max_rounds": 10,
        "budget_limit": None,
        "competitive_pressure": 0.1,
        "interaction_style": "collaborative",
        "time_pressure": 0.8,
        "allowed_actions": Config.OASIS_TWITTER_ACTIONS,
    },
    EnvironmentType.QUARTERLY_REVIEW: {
        "max_rounds": 40,
        "budget_limit": 500_000,
        "competitive_pressure": 0.5,
        "interaction_style": "formal",
        "time_pressure": 0.4,
        "allowed_actions": Config.OASIS_TWITTER_ACTIONS,
    },
}


@dataclass
class EnvironmentState:
    """Snapshot of environment state at a point in time."""
    env_id: str
    env_type: str
    status: str
    current_round: int
    total_rounds: int
    agent_count: int
    total_actions: int
    constraints: Dict[str, Any]
    agent_states: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "env_id": self.env_id,
            "env_type": self.env_type,
            "status": self.status,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "agent_count": self.agent_count,
            "total_actions": self.total_actions,
            "constraints": self.constraints,
            "agent_states": self.agent_states,
            "metrics": self.metrics,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class _ManagedEnvironment:
    """Internal container for a live OASIS environment and its metadata."""
    env_id: str
    env_type: EnvironmentType
    status: EnvironmentStatus
    platform: str  # "twitter" or "reddit"
    constraints: Dict[str, Any]
    current_round: int = 0
    total_actions: int = 0
    agent_ids: List[int] = field(default_factory=list)
    agent_names: Dict[int, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    # OASIS runtime objects (None in demo mode)
    oasis_env: Any = None
    agent_graph: Any = None
    model: Any = None
    db_path: Optional[str] = None


class EnvironmentManager:
    """
    Manages OASIS simulation environments.

    Provides a unified interface for creating environments, placing agents,
    setting behavioural constraints, stepping the simulation, and reading state.
    Falls back to deterministic demo mode when OASIS is not installed.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = data_dir or Config.OASIS_SIMULATION_DATA_DIR
        os.makedirs(self._data_dir, exist_ok=True)
        self._environments: Dict[str, _ManagedEnvironment] = {}

    # ------------------------------------------------------------------
    # 1. create_environment
    # ------------------------------------------------------------------
    def create_environment(
        self,
        env_type: str,
        config: Dict[str, Any],
    ) -> EnvironmentState:
        """
        Create and initialise a simulation environment.

        Args:
            env_type: One of EnvironmentType values.
            config: Dict with keys like simulation_id, platform, profile_path,
                    semaphore, and optional LLM overrides.

        Returns:
            EnvironmentState snapshot of the freshly created environment.
        """
        env_type_enum = EnvironmentType(env_type)
        sim_id: str = config.get("simulation_id", f"env_{os.urandom(6).hex()}")
        platform: str = config.get("platform", "twitter")
        profile_path: str = config.get("profile_path", "")
        semaphore: int = config.get("semaphore", 30)

        constraints = dict(_DEFAULT_CONSTRAINTS.get(env_type_enum, {}))

        env_dir = os.path.join(self._data_dir, sim_id)
        os.makedirs(env_dir, exist_ok=True)
        db_path = os.path.join(env_dir, f"{platform}_simulation.db")

        managed = _ManagedEnvironment(
            env_id=sim_id,
            env_type=env_type_enum,
            status=EnvironmentStatus.CREATED,
            platform=platform,
            constraints=constraints,
            db_path=db_path,
        )

        if OASIS_AVAILABLE and profile_path and os.path.exists(profile_path):
            managed.model = self._create_model(config)
            managed.status = EnvironmentStatus.INITIALIZED
        else:
            logger.info(
                f"OASIS not available or no profile — env {sim_id} uses demo mode"
            )
            managed.status = EnvironmentStatus.INITIALIZED

        self._environments[sim_id] = managed
        logger.info(
            f"Created environment: id={sim_id}, type={env_type}, platform={platform}"
        )
        return self.get_state(sim_id)

    # ------------------------------------------------------------------
    # 2. add_agents
    # ------------------------------------------------------------------
    async def add_agents(
        self,
        env_id: str,
        agents: List[Dict[str, Any]],
    ) -> EnvironmentState:
        """
        Generate an OASIS agent graph and place agents into the environment.

        Args:
            env_id: Environment identifier.
            agents: List of agent descriptors. Each must have at least
                    ``profile_path`` (str). Optional keys: ``agent_names``
                    (dict mapping int id → str name).

        Returns:
            Updated EnvironmentState.
        """
        managed = self._get_env(env_id)

        profile_path = (
            agents[0].get("profile_path", "") if agents else ""
        )
        agent_names: Dict[int, str] = {}
        for a in agents:
            agent_names.update(a.get("agent_names", {}))

        if OASIS_AVAILABLE and managed.model and profile_path:
            available_actions = self._resolve_actions(managed)
            if managed.platform == "twitter":
                managed.agent_graph = await generate_twitter_agent_graph(
                    profile_path=profile_path,
                    model=managed.model,
                    available_actions=available_actions,
                )
            else:
                managed.agent_graph = await generate_reddit_agent_graph(
                    profile_path=profile_path,
                    model=managed.model,
                    available_actions=available_actions,
                )

            # Collect agent IDs from the graph
            for agent_id, agent in managed.agent_graph.get_agents():
                managed.agent_ids.append(agent_id)
                if agent_id not in agent_names:
                    agent_names[agent_id] = getattr(agent, "name", f"Agent_{agent_id}")

            # Create the OASIS env object
            oasis_platform = (
                oasis.DefaultPlatformType.TWITTER
                if managed.platform == "twitter"
                else oasis.DefaultPlatformType.REDDIT
            )
            if os.path.exists(managed.db_path):
                os.remove(managed.db_path)

            managed.oasis_env = oasis.make(
                agent_graph=managed.agent_graph,
                platform=oasis_platform,
                database_path=managed.db_path,
                semaphore=managed.constraints.get("semaphore", 30),
            )
            await managed.oasis_env.reset()
            logger.info(f"OASIS env reset complete for {env_id}, agents={len(managed.agent_ids)}")
        else:
            # Demo mode: synthesize agent IDs from provided agent_names or count
            if agent_names:
                managed.agent_ids = list(agent_names.keys())
            else:
                count = len(agents) if agents else 5
                managed.agent_ids = list(range(count))
                agent_names = {i: f"Agent_{i}" for i in managed.agent_ids}

        managed.agent_names = agent_names
        managed.updated_at = datetime.now().isoformat()
        return self.get_state(env_id)

    # ------------------------------------------------------------------
    # 3. set_constraints
    # ------------------------------------------------------------------
    def set_constraints(
        self,
        env_id: str,
        rules: Dict[str, Any],
    ) -> EnvironmentState:
        """
        Merge behavioural constraints into an existing environment.

        Supported constraint keys:
            max_rounds, budget_limit, competitive_pressure,
            interaction_style, time_pressure, allowed_actions,
            market_conditions (dict), semaphore (int).

        Args:
            env_id: Environment identifier.
            rules: Constraint overrides to merge.

        Returns:
            Updated EnvironmentState.
        """
        managed = self._get_env(env_id)
        managed.constraints.update(rules)
        managed.updated_at = datetime.now().isoformat()
        logger.info(f"Updated constraints for {env_id}: {list(rules.keys())}")
        return self.get_state(env_id)

    # ------------------------------------------------------------------
    # 4. step
    # ------------------------------------------------------------------
    async def step(
        self,
        env_id: str,
        agent_actions: Optional[Dict[int, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Advance the environment by one time step.

        Args:
            env_id: Environment identifier.
            agent_actions: Optional mapping of agent_id → action override.
                           If None, active agents perform LLMAction.

        Returns:
            Dict with round_num, active_agents, actions_taken, and status.
        """
        managed = self._get_env(env_id)
        max_rounds = managed.constraints.get("max_rounds", 50)
        if managed.current_round >= max_rounds:
            managed.status = EnvironmentStatus.COMPLETED
            managed.updated_at = datetime.now().isoformat()
            return {
                "round_num": managed.current_round,
                "active_agents": 0,
                "actions_taken": 0,
                "status": managed.status.value,
            }

        managed.status = EnvironmentStatus.RUNNING
        managed.current_round += 1
        round_num = managed.current_round

        if OASIS_AVAILABLE and managed.oasis_env and managed.agent_graph:
            actions = self._build_actions(managed, agent_actions)
            await managed.oasis_env.step(actions)
            active_count = len(actions)
        else:
            # Demo mode: simulate deterministic activity
            active_count = self._demo_step(managed)

        managed.total_actions += active_count
        managed.updated_at = datetime.now().isoformat()

        if managed.current_round >= max_rounds:
            managed.status = EnvironmentStatus.COMPLETED

        return {
            "round_num": round_num,
            "active_agents": active_count,
            "actions_taken": active_count,
            "status": managed.status.value,
        }

    # ------------------------------------------------------------------
    # 5. get_state
    # ------------------------------------------------------------------
    def get_state(self, env_id: str) -> EnvironmentState:
        """
        Return a snapshot of the current environment state.

        Args:
            env_id: Environment identifier.

        Returns:
            EnvironmentState dataclass.
        """
        managed = self._get_env(env_id)
        agent_states = [
            {
                "agent_id": aid,
                "name": managed.agent_names.get(aid, f"Agent_{aid}"),
            }
            for aid in managed.agent_ids
        ]
        max_rounds = managed.constraints.get("max_rounds", 50)
        progress = (
            managed.current_round / max_rounds if max_rounds > 0 else 0.0
        )
        metrics = {
            "progress": round(progress, 4),
            "avg_actions_per_round": (
                round(managed.total_actions / managed.current_round, 2)
                if managed.current_round > 0
                else 0.0
            ),
        }
        return EnvironmentState(
            env_id=managed.env_id,
            env_type=managed.env_type.value,
            status=managed.status.value,
            current_round=managed.current_round,
            total_rounds=max_rounds,
            agent_count=len(managed.agent_ids),
            total_actions=managed.total_actions,
            constraints=managed.constraints,
            agent_states=agent_states,
            metrics=metrics,
            created_at=managed.created_at,
            updated_at=managed.updated_at,
        )

    # ------------------------------------------------------------------
    # Convenience: list / remove
    # ------------------------------------------------------------------
    def list_environments(self) -> List[EnvironmentState]:
        return [self.get_state(eid) for eid in self._environments]

    def remove_environment(self, env_id: str) -> None:
        """Tear down and remove a managed environment."""
        if env_id in self._environments:
            managed = self._environments.pop(env_id)
            if managed.oasis_env and hasattr(managed.oasis_env, "close"):
                try:
                    managed.oasis_env.close()
                except Exception:
                    pass
            logger.info(f"Removed environment: {env_id}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_env(self, env_id: str) -> _ManagedEnvironment:
        if env_id not in self._environments:
            raise ValueError(f"Environment not found: {env_id}")
        return self._environments[env_id]

    @staticmethod
    def _create_model(config: Dict[str, Any]):
        """Create a camel ModelFactory model from env vars / config overrides."""
        api_key = os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get("LLM_BASE_URL", "")
        model_name = os.environ.get("LLM_MODEL_NAME", "") or config.get(
            "llm_model", "gpt-4o-mini"
        )

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        if base_url:
            os.environ["OPENAI_API_BASE_URL"] = base_url

        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=model_name,
        )

    @staticmethod
    def _resolve_actions(managed: _ManagedEnvironment) -> list:
        """Map string action names from constraints to ActionType enums."""
        action_names = managed.constraints.get("allowed_actions", [])
        actions = []
        for name in action_names:
            try:
                actions.append(ActionType[name] if isinstance(name, str) else name)
            except KeyError:
                continue
        if not actions:
            return (
                [ActionType.CREATE_POST, ActionType.LIKE_POST, ActionType.REPOST,
                 ActionType.FOLLOW, ActionType.DO_NOTHING, ActionType.QUOTE_POST]
                if managed.platform == "twitter"
                else [ActionType.CREATE_POST, ActionType.LIKE_POST,
                      ActionType.DISLIKE_POST, ActionType.CREATE_COMMENT,
                      ActionType.DO_NOTHING]
            )
        return actions

    @staticmethod
    def _build_actions(
        managed: _ManagedEnvironment,
        overrides: Optional[Dict[int, Any]],
    ) -> dict:
        """Build the {agent_obj: action} dict for oasis env.step()."""
        actions = {}
        for aid in managed.agent_ids:
            try:
                agent = managed.agent_graph.get_agent(aid)
            except Exception:
                continue

            if overrides and aid in overrides:
                override = overrides[aid]
                if isinstance(override, dict):
                    action_type = ActionType[override["action_type"]]
                    actions[agent] = ManualAction(
                        action_type=action_type,
                        action_args=override.get("action_args", {}),
                    )
                else:
                    actions[agent] = override
            else:
                actions[agent] = LLMAction()
        return actions

    @staticmethod
    def _demo_step(managed: _ManagedEnvironment) -> int:
        """Deterministic demo-mode step — no LLM or OASIS required."""
        rng = random.Random(hash(managed.env_id) + managed.current_round)
        base_active = max(1, len(managed.agent_ids) // 3)
        jitter = rng.randint(0, max(1, len(managed.agent_ids) // 5))
        return min(base_active + jitter, len(managed.agent_ids))
