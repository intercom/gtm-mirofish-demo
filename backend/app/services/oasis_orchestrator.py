"""
OASIS Simulation Orchestrator
Coordinates the simulation loop: initializes environments, runs rounds,
tracks progress, and manages pause/resume lifecycle.

This is the service-layer abstraction of the execution logic found in
backend/scripts/run_parallel_simulation.py, designed to be callable from
Flask API endpoints and the CLI script alike.
"""

import asyncio
import json
import os
import random
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.oasis_orchestrator')

# Maximum retry attempts for transient LLM errors during a round
MAX_LLM_RETRIES = 3
# Base delay (seconds) for exponential backoff
BACKOFF_BASE = 1.0


class OrchestratorState(str, Enum):
    """Orchestrator lifecycle states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# Alias for compatibility with the simulation registry API layer
OrchestratorStatus = OrchestratorState


@dataclass
class RoundResult:
    """Outcome of a single simulation round."""
    round_number: int
    simulated_hour: int
    simulated_day: int
    active_agent_count: int
    actions: List[Dict[str, Any]] = field(default_factory=list)
    twitter_action_count: int = 0
    reddit_action_count: int = 0
    started_at: str = ""
    finished_at: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "simulated_hour": self.simulated_hour,
            "simulated_day": self.simulated_day,
            "active_agent_count": self.active_agent_count,
            "twitter_action_count": self.twitter_action_count,
            "reddit_action_count": self.reddit_action_count,
            "actions_count": len(self.actions),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }


@dataclass
class OrchestratorResults:
    """Aggregated results from a full simulation run."""
    simulation_id: str
    state: str
    total_rounds: int
    completed_rounds: int
    total_twitter_actions: int = 0
    total_reddit_actions: int = 0
    rounds: List[RoundResult] = field(default_factory=list)
    agent_states: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "state": self.state,
            "total_rounds": self.total_rounds,
            "completed_rounds": self.completed_rounds,
            "total_twitter_actions": self.total_twitter_actions,
            "total_reddit_actions": self.total_reddit_actions,
            "total_actions": self.total_twitter_actions + self.total_reddit_actions,
            "rounds_summary": [r.to_dict() for r in self.rounds],
            "agent_states": self.agent_states,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


def _get_active_agents_for_round(
    agent_graph,
    config: Dict[str, Any],
    current_hour: int,
    round_num: int,
) -> List[Tuple[int, Any]]:
    """Select which agents are active this round based on time-of-day and activity config.

    Mirrors the logic in backend/scripts/run_parallel_simulation.py so that
    the orchestrator produces identical scheduling behaviour.
    """
    time_config = config.get("time_config", {})
    agent_configs = config.get("agent_configs", [])

    base_min = time_config.get("agents_per_hour_min", 5)
    base_max = time_config.get("agents_per_hour_max", 20)

    peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
    off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])

    if current_hour in peak_hours:
        multiplier = time_config.get("peak_activity_multiplier", 1.5)
    elif current_hour in off_peak_hours:
        multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
    else:
        multiplier = 1.0

    target_count = int(random.uniform(base_min, base_max) * multiplier)

    candidates: List[int] = []
    for cfg in agent_configs:
        agent_id = cfg.get("agent_id", 0)
        active_hours = cfg.get("active_hours", list(range(8, 23)))
        activity_level = cfg.get("activity_level", 0.5)

        if current_hour not in active_hours:
            continue
        if random.random() < activity_level:
            candidates.append(agent_id)

    selected_ids = (
        random.sample(candidates, min(target_count, len(candidates)))
        if candidates
        else []
    )

    active_agents: List[Tuple[int, Any]] = []
    for agent_id in selected_ids:
        try:
            agent = agent_graph.get_agent(agent_id)
            active_agents.append((agent_id, agent))
        except Exception:
            pass

    return active_agents


def _get_agent_names(config: Dict[str, Any]) -> Dict[int, str]:
    """Build agent_id -> entity_name mapping from simulation config."""
    names: Dict[int, str] = {}
    for ac in config.get("agent_configs", []):
        aid = ac.get("agent_id")
        if aid is not None:
            names[aid] = ac.get("entity_name", f"Agent_{aid}")
    return names


class OasisOrchestrator:
    """
    Main simulation loop coordinator.

    Manages the lifecycle of an OASIS simulation:
      initialize  →  run_round / run_full  →  get_results
                      pause / resume

    Works with the real OASIS library when available, and degrades gracefully
    when it is not installed (demo mode returns immediately with empty results).
    """

    def __init__(self, simulation_id: str, config=None):
        self.simulation_id = simulation_id

        # Accept either a config dict (from SimulationRegistry) or a
        # simulation_dir string (from direct / CLI usage).
        if isinstance(config, dict):
            self._config = config
            self.simulation_dir = config.get('simulation_dir', '')
        elif isinstance(config, str):
            self._config = {}
            self.simulation_dir = config
        else:
            self._config = {}
            self.simulation_dir = ''

        self.state = OrchestratorState.IDLE
        self._agent_names: Dict[int, str] = {}

        # Platform environments & graphs (populated during initialize)
        self._twitter_env = None
        self._twitter_graph = None
        self._reddit_env = None
        self._reddit_graph = None

        # Round tracking
        self._total_rounds: int = 0
        self._minutes_per_round: int = 30
        self._current_round: int = 0
        self._round_results: List[RoundResult] = []

        # Action counters
        self._twitter_actions: int = 0
        self._reddit_actions: int = 0

        # Pause / resume / stop
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused initially
        self._stop_requested = False

        # Timestamps
        self._started_at: Optional[str] = None
        self._completed_at: Optional[str] = None
        self._error: Optional[str] = None

        # Progress callback: (round_number, total_rounds, message) -> None
        self._progress_callback: Optional[Callable] = None

        # JSONL log file handles (opened lazily)
        if self.simulation_dir:
            self._twitter_log_path = os.path.join(self.simulation_dir, "twitter", "actions.jsonl")
            self._reddit_log_path = os.path.join(self.simulation_dir, "reddit", "actions.jsonl")
        else:
            self._twitter_log_path = ""
            self._reddit_log_path = ""

        # OASIS library availability flag
        self._oasis_available = False

    # ------------------------------------------------------------------
    # Lightweight start (called by the API / registry layer)
    # ------------------------------------------------------------------

    def start(self, max_rounds: Optional[int] = None) -> Dict[str, Any]:
        """Mark the orchestrator as running.

        The API layer calls this after creating the orchestrator via the
        SimulationRegistry.  The actual round execution is handled either
        by ``run_full`` (async) or by the SimulationRunner subprocess.
        """
        self._total_rounds = max_rounds or self._config.get("time_config", {}).get("total_rounds", 10)
        self.state = OrchestratorState.RUNNING
        self._started_at = datetime.now().isoformat()
        logger.info(f"OasisOrchestrator started: {self.simulation_id}, max_rounds={self._total_rounds}")
        return self.get_status()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    async def initialize(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> None:
        """Set up OASIS environments, agent graphs, and initial state.

        Args:
            config: Simulation config dict.  If ``None``, loaded from
                ``simulation_config.json`` in *simulation_dir*.
            enable_twitter: Whether to create a Twitter environment.
            enable_reddit: Whether to create a Reddit environment.
        """
        self.state = OrchestratorState.INITIALIZING
        logger.info(f"Initializing orchestrator: {self.simulation_id}")

        # Load config
        if config is None:
            config_path = os.path.join(self.simulation_dir, "simulation_config.json")
            if not os.path.exists(config_path):
                self.state = OrchestratorState.FAILED
                self._error = f"Config not found: {config_path}"
                raise FileNotFoundError(self._error)
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

        self._config = config
        self._agent_names = _get_agent_names(config)

        time_config = config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        self._minutes_per_round = time_config.get("minutes_per_round", 30)
        self._total_rounds = (total_hours * 60) // self._minutes_per_round

        # Attempt to import OASIS dependencies
        try:
            import oasis  # noqa: F811
            from oasis import (
                ActionType,
                LLMAction,
                ManualAction,
                generate_twitter_agent_graph,
                generate_reddit_agent_graph,
            )
            from camel.models import ModelFactory
            from camel.types import ModelPlatformType

            self._oasis_available = True
        except ImportError:
            logger.warning("OASIS library not installed — orchestrator will operate in stub mode")
            self._oasis_available = False
            self.state = OrchestratorState.READY
            return

        # Build LLM model
        model = self._create_model(config)

        # Ensure log directories exist
        os.makedirs(os.path.dirname(self._twitter_log_path), exist_ok=True)
        os.makedirs(os.path.dirname(self._reddit_log_path), exist_ok=True)

        # --- Twitter ---
        if enable_twitter:
            profile_path = os.path.join(self.simulation_dir, "twitter_profiles.csv")
            if os.path.exists(profile_path):
                twitter_actions = [
                    ActionType.CREATE_POST,
                    ActionType.LIKE_POST,
                    ActionType.REPOST,
                    ActionType.FOLLOW,
                    ActionType.DO_NOTHING,
                    ActionType.QUOTE_POST,
                ]
                self._twitter_graph = await generate_twitter_agent_graph(
                    profile_path=profile_path,
                    model=model,
                    available_actions=twitter_actions,
                )
                db_path = os.path.join(self.simulation_dir, "twitter_simulation.db")
                if os.path.exists(db_path):
                    os.remove(db_path)
                self._twitter_env = oasis.make(
                    agent_graph=self._twitter_graph,
                    platform=oasis.DefaultPlatformType.TWITTER,
                    database_path=db_path,
                    semaphore=30,
                )
                await self._twitter_env.reset()
                logger.info(f"[{self.simulation_id}] Twitter environment ready")

        # --- Reddit ---
        if enable_reddit:
            profile_path = os.path.join(self.simulation_dir, "reddit_profiles.json")
            if os.path.exists(profile_path):
                reddit_actions = [
                    ActionType.LIKE_POST,
                    ActionType.DISLIKE_POST,
                    ActionType.CREATE_POST,
                    ActionType.CREATE_COMMENT,
                    ActionType.LIKE_COMMENT,
                    ActionType.DISLIKE_COMMENT,
                    ActionType.SEARCH_POSTS,
                    ActionType.SEARCH_USER,
                    ActionType.TREND,
                    ActionType.REFRESH,
                    ActionType.DO_NOTHING,
                    ActionType.FOLLOW,
                    ActionType.MUTE,
                ]
                boost_model = self._create_model(config, use_boost=True)
                self._reddit_graph = await generate_reddit_agent_graph(
                    profile_path=profile_path,
                    model=boost_model,
                    available_actions=reddit_actions,
                )
                db_path = os.path.join(self.simulation_dir, "reddit_simulation.db")
                if os.path.exists(db_path):
                    os.remove(db_path)
                self._reddit_env = oasis.make(
                    agent_graph=self._reddit_graph,
                    platform=oasis.DefaultPlatformType.REDDIT,
                    database_path=db_path,
                    semaphore=30,
                )
                await self._reddit_env.reset()
                logger.info(f"[{self.simulation_id}] Reddit environment ready")

        self.state = OrchestratorState.READY
        logger.info(
            f"[{self.simulation_id}] Initialization complete — "
            f"total_rounds={self._total_rounds}, "
            f"twitter={'yes' if self._twitter_env else 'no'}, "
            f"reddit={'yes' if self._reddit_env else 'no'}"
        )

    # ------------------------------------------------------------------
    # Running rounds
    # ------------------------------------------------------------------

    async def run_round(self, round_number: int) -> RoundResult:
        """Execute a single simulation round.

        Each agent that is active this round makes an LLM-driven decision.
        Actions are logged to the per-platform ``actions.jsonl`` files.

        Retries with exponential backoff on transient LLM errors.
        """
        if self.state not in (OrchestratorState.RUNNING, OrchestratorState.READY):
            raise RuntimeError(f"Cannot run round in state {self.state.value}")

        simulated_minutes = round_number * self._minutes_per_round
        simulated_hour = (simulated_minutes // 60) % 24
        simulated_day = simulated_minutes // (60 * 24) + 1

        result = RoundResult(
            round_number=round_number,
            simulated_hour=simulated_hour,
            simulated_day=simulated_day,
            active_agent_count=0,
            started_at=datetime.now().isoformat(),
        )

        # If OASIS isn't available, return an empty round
        if not self._oasis_available:
            result.finished_at = datetime.now().isoformat()
            self._round_results.append(result)
            return result

        from oasis import LLMAction  # deferred import

        # --- Execute on each platform with retry ---
        for platform, env, graph, log_path in self._platform_iter():
            if env is None:
                continue

            active_agents = _get_active_agents_for_round(
                graph, self._config, simulated_hour, round_number
            )

            # Log round_start event
            self._write_log(log_path, {
                "round": round_number,
                "timestamp": datetime.now().isoformat(),
                "event_type": "round_start",
                "simulated_hour": simulated_hour,
            })

            round_action_count = 0

            if active_agents:
                result.active_agent_count += len(active_agents)
                actions = {agent: LLMAction() for _, agent in active_agents}

                # Retry with exponential backoff on LLM errors
                last_err = None
                for attempt in range(MAX_LLM_RETRIES):
                    try:
                        await env.step(actions)
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        if attempt < MAX_LLM_RETRIES - 1:
                            delay = BACKOFF_BASE * (2 ** attempt)
                            logger.warning(
                                f"[{self.simulation_id}] LLM error on {platform} "
                                f"round {round_number}, attempt {attempt + 1}: {e}. "
                                f"Retrying in {delay:.1f}s..."
                            )
                            await asyncio.sleep(delay)

                if last_err is not None:
                    err_msg = f"{platform} round {round_number} failed after {MAX_LLM_RETRIES} attempts: {last_err}"
                    logger.error(f"[{self.simulation_id}] {err_msg}")
                    result.error = err_msg
                else:
                    # Log each agent's action
                    for agent_id, _ in active_agents:
                        entry = {
                            "round": round_number,
                            "timestamp": datetime.now().isoformat(),
                            "agent_id": agent_id,
                            "agent_name": self._agent_names.get(agent_id, f"Agent_{agent_id}"),
                            "action_type": "LLM_ACTION",
                            "action_args": {},
                            "success": True,
                        }
                        self._write_log(log_path, entry)
                        result.actions.append(entry)
                        round_action_count += 1

            # Log round_end event
            self._write_log(log_path, {
                "round": round_number,
                "timestamp": datetime.now().isoformat(),
                "event_type": "round_end",
                "actions_count": round_action_count,
            })

            if platform == "twitter":
                result.twitter_action_count = round_action_count
                self._twitter_actions += round_action_count
            else:
                result.reddit_action_count = round_action_count
                self._reddit_actions += round_action_count

        result.finished_at = datetime.now().isoformat()
        self._round_results.append(result)
        self._current_round = round_number
        return result

    async def run_full(
        self,
        max_rounds: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
    ) -> OrchestratorResults:
        """Run the complete simulation with progress tracking.

        Args:
            max_rounds: Cap the number of rounds (``None`` uses config value).
            progress_callback: ``(round_num, total, message) -> None`` called
                after each round completes.

        Returns:
            Structured results covering all rounds.
        """
        if self.state not in (OrchestratorState.READY, OrchestratorState.PAUSED):
            raise RuntimeError(f"Cannot start run in state {self.state.value}")

        self.state = OrchestratorState.RUNNING
        self._progress_callback = progress_callback
        self._started_at = datetime.now().isoformat()
        self._stop_requested = False

        effective_rounds = self._total_rounds
        if max_rounds is not None and max_rounds > 0:
            effective_rounds = min(effective_rounds, max_rounds)

        logger.info(
            f"[{self.simulation_id}] Starting full run: "
            f"{effective_rounds} rounds"
        )

        # Execute initial event posts (round 0)
        await self._execute_initial_events()

        try:
            for rn in range(effective_rounds):
                # Check for stop request
                if self._stop_requested:
                    logger.info(f"[{self.simulation_id}] Stop requested at round {rn}")
                    break

                # Honour pause — blocks until resumed
                self._pause_event.wait()

                round_result = await self.run_round(rn + 1)

                # Emit progress
                if self._progress_callback:
                    pct = round((rn + 1) / effective_rounds * 100, 1)
                    self._progress_callback(
                        rn + 1,
                        effective_rounds,
                        f"Round {rn + 1}/{effective_rounds} ({pct}%) — "
                        f"day {round_result.simulated_day}, "
                        f"{round_result.simulated_hour:02d}:00",
                    )

            self.state = OrchestratorState.COMPLETED
            self._completed_at = datetime.now().isoformat()
            logger.info(
                f"[{self.simulation_id}] Simulation complete — "
                f"twitter={self._twitter_actions}, reddit={self._reddit_actions}"
            )

        except Exception as exc:
            self.state = OrchestratorState.FAILED
            self._error = str(exc)
            logger.error(f"[{self.simulation_id}] Simulation failed: {exc}")
            raise

        return self.get_results()

    # ------------------------------------------------------------------
    # Pause / Resume / Stop
    # ------------------------------------------------------------------

    def pause(self) -> None:
        """Pause simulation after the current round finishes."""
        if self.state != OrchestratorState.RUNNING:
            return
        self._pause_event.clear()
        self.state = OrchestratorState.PAUSED
        logger.info(f"[{self.simulation_id}] Paused at round {self._current_round}")

    def resume(self) -> None:
        """Resume a paused simulation."""
        if self.state != OrchestratorState.PAUSED:
            return
        self.state = OrchestratorState.RUNNING
        self._pause_event.set()
        logger.info(f"[{self.simulation_id}] Resumed from round {self._current_round}")

    def stop(self) -> None:
        """Request a graceful stop after the current round."""
        self._stop_requested = True
        # Also unblock pause so the loop can exit
        self._pause_event.set()
        logger.info(f"[{self.simulation_id}] Stop requested")

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def get_results(self) -> OrchestratorResults:
        """Return structured simulation results."""
        return OrchestratorResults(
            simulation_id=self.simulation_id,
            state=self.state.value,
            total_rounds=self._total_rounds,
            completed_rounds=self._current_round,
            total_twitter_actions=self._twitter_actions,
            total_reddit_actions=self._reddit_actions,
            rounds=list(self._round_results),
            agent_states=self._build_agent_states(),
            started_at=self._started_at,
            completed_at=self._completed_at,
            error=self._error,
        )

    def get_status(self) -> Dict[str, Any]:
        """Lightweight status snapshot for polling."""
        return {
            "simulation_id": self.simulation_id,
            "state": self.state.value,
            "status": self.state.value,
            "mode": "oasis",
            "current_round": self._current_round,
            "total_rounds": self._total_rounds,
            "max_rounds": self._total_rounds,
            "progress_percent": round(
                self._current_round / max(self._total_rounds, 1) * 100, 1
            ),
            "twitter_actions": self._twitter_actions,
            "reddit_actions": self._reddit_actions,
            "total_actions": self._twitter_actions + self._reddit_actions,
            "started_at": self._started_at,
            "completed_at": self._completed_at,
            "error": self._error,
        }

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close OASIS environments and release resources."""
        if self._twitter_env:
            try:
                await self._twitter_env.close()
            except Exception as e:
                logger.warning(f"Error closing Twitter env: {e}")
            self._twitter_env = None

        if self._reddit_env:
            try:
                await self._reddit_env.close()
            except Exception as e:
                logger.warning(f"Error closing Reddit env: {e}")
            self._reddit_env = None

        logger.info(f"[{self.simulation_id}] Environments closed")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _platform_iter(self):
        """Yield (platform_name, env, graph, log_path) for active platforms."""
        if self._twitter_env is not None:
            yield "twitter", self._twitter_env, self._twitter_graph, self._twitter_log_path
        if self._reddit_env is not None:
            yield "reddit", self._reddit_env, self._reddit_graph, self._reddit_log_path

    def _write_log(self, log_path: str, entry: Dict[str, Any]) -> None:
        """Append a JSON line to a platform log file."""
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def _execute_initial_events(self) -> None:
        """Post seed content (round 0) before the main loop starts."""
        if not self._oasis_available:
            return

        from oasis import ActionType, ManualAction

        event_config = self._config.get("event_config", {})
        initial_posts = event_config.get("initial_posts", [])
        if not initial_posts:
            return

        for platform, env, graph, log_path in self._platform_iter():
            self._write_log(log_path, {
                "round": 0,
                "timestamp": datetime.now().isoformat(),
                "event_type": "round_start",
                "simulated_hour": 0,
            })

            initial_actions = {}
            count = 0
            for post in initial_posts:
                agent_id = post.get("poster_agent_id", 0)
                content = post.get("content", "")
                try:
                    agent = graph.get_agent(agent_id)
                    initial_actions[agent] = ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content},
                    )
                    self._write_log(log_path, {
                        "round": 0,
                        "timestamp": datetime.now().isoformat(),
                        "agent_id": agent_id,
                        "agent_name": self._agent_names.get(agent_id, f"Agent_{agent_id}"),
                        "action_type": "CREATE_POST",
                        "action_args": {"content": content},
                        "success": True,
                    })
                    count += 1
                except Exception:
                    pass

            if initial_actions:
                await env.step(initial_actions)

            self._write_log(log_path, {
                "round": 0,
                "timestamp": datetime.now().isoformat(),
                "event_type": "round_end",
                "actions_count": count,
            })

            if platform == "twitter":
                self._twitter_actions += count
            else:
                self._reddit_actions += count

            logger.info(
                f"[{self.simulation_id}] {platform}: posted {count} initial events"
            )

    def _build_agent_states(self) -> Dict[int, Dict[str, Any]]:
        """Aggregate per-agent statistics from round results."""
        agent_stats: Dict[int, Dict[str, Any]] = {}
        for rr in self._round_results:
            for action in rr.actions:
                aid = action.get("agent_id")
                if aid is None:
                    continue
                if aid not in agent_stats:
                    agent_stats[aid] = {
                        "agent_id": aid,
                        "agent_name": action.get("agent_name", f"Agent_{aid}"),
                        "total_actions": 0,
                        "rounds_active": 0,
                    }
                agent_stats[aid]["total_actions"] += 1
            # Track unique rounds per agent
            seen_in_round: set = set()
            for action in rr.actions:
                aid = action.get("agent_id")
                if aid is not None and aid not in seen_in_round:
                    seen_in_round.add(aid)
                    if aid in agent_stats:
                        agent_stats[aid]["rounds_active"] += 1
        return agent_stats

    @staticmethod
    def _create_model(config: Dict[str, Any], use_boost: bool = False):
        """Create a camel-ai ModelFactory model from environment config.

        Mirrors ``create_model()`` in run_parallel_simulation.py.
        """
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        boost_api_key = os.environ.get("LLM_BOOST_API_KEY", "")
        boost_base_url = os.environ.get("LLM_BOOST_BASE_URL", "")
        boost_model = os.environ.get("LLM_BOOST_MODEL_NAME", "")

        if use_boost and boost_api_key:
            llm_api_key = boost_api_key
            llm_base_url = boost_base_url
            llm_model = boost_model or os.environ.get("LLM_MODEL_NAME", "")
        else:
            llm_api_key = os.environ.get("LLM_API_KEY", "")
            llm_base_url = os.environ.get("LLM_BASE_URL", "")
            llm_model = os.environ.get("LLM_MODEL_NAME", "")

        if not llm_model:
            llm_model = config.get("llm_model", "gpt-4o-mini")

        if llm_api_key:
            os.environ["OPENAI_API_KEY"] = llm_api_key
        if llm_base_url:
            os.environ["OPENAI_API_BASE_URL"] = llm_base_url

        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=llm_model,
        )

    @staticmethod
    def is_available() -> bool:
        """Check if an LLM API key is configured."""
        return bool(Config.LLM_API_KEY)
