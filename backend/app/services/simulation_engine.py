"""
Simulation Execution Engine

In-memory, LLM-driven execution loop for GTM simulations.
Manages agent turns, sentiment tracking, consensus detection, and full history replay.

Unlike SimulationRunner (which spawns OASIS subprocesses), this engine runs
entirely in-process with direct LLM calls for each agent turn.
"""

import json
import random
import threading
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.simulation_engine')


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EngineStatus(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    MESSAGE = "message"
    DECISION = "decision"
    DATA_REQUEST = "data_request"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class AgentAction:
    """A single parsed action from an agent's LLM response."""
    action_type: ActionType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "content": self.content,
            "metadata": self.metadata,
        }


@dataclass
class AgentTurnResult:
    """Result of processing one agent's turn in a round."""
    agent_id: str
    agent_name: str
    round_num: int
    raw_response: str
    actions: List[AgentAction] = field(default_factory=list)
    sentiment_score: float = 0.0  # -1.0 to 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "round_num": self.round_num,
            "raw_response": self.raw_response,
            "actions": [a.to_dict() for a in self.actions],
            "sentiment_score": self.sentiment_score,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentState:
    """Persistent state for a single agent across rounds."""
    agent_id: str
    name: str
    role: str
    persona: str
    priorities: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    communication_style: str = ""
    memory: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    turns_taken: int = 0
    last_action: Optional[str] = None

    # Optional GTM-specific fields
    segment: str = ""
    contract_value: str = ""
    decision_authority: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "persona": self.persona,
            "priorities": self.priorities,
            "concerns": self.concerns,
            "communication_style": self.communication_style,
            "sentiment_score": self.sentiment_score,
            "turns_taken": self.turns_taken,
            "last_action": self.last_action,
            "segment": self.segment,
            "contract_value": self.contract_value,
            "decision_authority": self.decision_authority,
        }


@dataclass
class EnvironmentState:
    """Shared environment visible to all agents."""
    scenario_context: str = ""
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    global_sentiment: float = 0.0  # avg across agents
    consensus_score: float = 0.0  # 0..1, how aligned agents are
    hot_topics: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    round_num: int = 0
    max_recent_messages: int = 20

    def add_message(self, agent_id: str, agent_name: str, content: str):
        msg = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "content": content,
            "round": self.round_num,
        }
        self.recent_messages.insert(0, msg)
        if len(self.recent_messages) > self.max_recent_messages:
            self.recent_messages = self.recent_messages[:self.max_recent_messages]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_context": self.scenario_context,
            "recent_messages": self.recent_messages,
            "global_sentiment": self.global_sentiment,
            "consensus_score": self.consensus_score,
            "hot_topics": self.hot_topics,
            "events": self.events,
            "round_num": self.round_num,
        }


@dataclass
class RoundResult:
    """Aggregated result of one simulation round."""
    round_num: int
    turns: List[AgentTurnResult] = field(default_factory=list)
    active_agent_count: int = 0
    avg_sentiment: float = 0.0
    consensus_score: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "turns": [t.to_dict() for t in self.turns],
            "active_agent_count": self.active_agent_count,
            "avg_sentiment": self.avg_sentiment,
            "consensus_score": self.consensus_score,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


@dataclass
class ExecutionHistory:
    """Full simulation execution history for replay."""
    simulation_id: str
    rounds: List[RoundResult] = field(default_factory=list)
    total_rounds: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    final_sentiment: float = 0.0
    final_consensus: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "rounds": [r.to_dict() for r in self.rounds],
            "total_rounds": self.total_rounds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "final_sentiment": self.final_sentiment,
            "final_consensus": self.final_consensus,
        }


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are {name}, a {role} in a GTM simulation.

Persona: {persona}
Communication style: {communication_style}
Priorities: {priorities}
Concerns: {concerns}
{extra_context}

Respond to the scenario in character. Your response MUST be valid JSON with this structure:
{{
  "message": "Your in-character response to the situation",
  "sentiment": <float from -1.0 (very negative) to 1.0 (very positive)>,
  "decision": "<optional: buy/stay/churn/escalate/wait/null>",
  "data_request": "<optional: any data you'd want before deciding, or null>"
}}

Stay in character. Be concise."""

AGENT_TURN_PROMPT = """## Current Scenario
{scenario_context}

## Round {round_num}
{events}

## Recent Discussion
{recent_messages}

## Your Memory
{memory}

Given the above, respond in character as {name}."""


# ---------------------------------------------------------------------------
# Mock responses for demo mode
# ---------------------------------------------------------------------------

MOCK_RESPONSES = [
    {
        "message": "I need to see concrete ROI data before making any commitments. Our board meets next quarter and I need hard numbers.",
        "sentiment": -0.2,
        "decision": "wait",
        "data_request": "Can you share case studies from similar-sized companies?"
    },
    {
        "message": "This pricing restructure actually addresses some pain points we've had. The usage-based model aligns better with our seasonal patterns.",
        "sentiment": 0.6,
        "decision": "stay",
        "data_request": None
    },
    {
        "message": "I'm concerned about the migration timeline. We can't afford downtime during our peak support season.",
        "sentiment": -0.4,
        "decision": "wait",
        "data_request": "What's the typical migration timeline for enterprise accounts?"
    },
    {
        "message": "We've already started evaluating alternatives. Unless there's a compelling reason to stay, we're leaning toward switching.",
        "sentiment": -0.7,
        "decision": "churn",
        "data_request": None
    },
    {
        "message": "The new features in the upgraded tier are exactly what our team needs. Happy to move forward with the transition.",
        "sentiment": 0.8,
        "decision": "buy",
        "data_request": None
    },
    {
        "message": "I want to bring my team lead into this conversation. The technical implications need deeper review.",
        "sentiment": 0.0,
        "decision": "escalate",
        "data_request": "Can we schedule a technical deep-dive session?"
    },
    {
        "message": "Our budget is locked for this fiscal year. Any price increase would need to go through a new approval cycle.",
        "sentiment": -0.3,
        "decision": "wait",
        "data_request": "Is there a grace period or grandfathering option?"
    },
    {
        "message": "Honestly, the integration stability has been great. We'd rather not rock the boat by switching vendors.",
        "sentiment": 0.5,
        "decision": "stay",
        "data_request": None
    },
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SimulationEngine:
    """
    Core simulation execution engine.

    Runs an in-memory, LLM-driven simulation where agents take turns
    responding to a GTM scenario. Tracks sentiment, consensus, and
    stores full execution history for replay.

    Thread-safe: all mutable state access is guarded by a lock.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._status: EngineStatus = EngineStatus.IDLE
        self._simulation_id: str = ""
        self._agents: Dict[str, AgentState] = {}
        self._environment: EnvironmentState = EnvironmentState()
        self._history: Optional[ExecutionHistory] = None
        self._total_rounds: int = 10
        self._current_round: int = 0
        self._llm_client = None
        self._demo_mode: bool = False
        self._stop_requested: bool = False
        self._on_round_complete: Optional[Callable] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def status(self) -> EngineStatus:
        with self._lock:
            return self._status

    @property
    def simulation_id(self) -> str:
        return self._simulation_id

    @property
    def current_round(self) -> int:
        with self._lock:
            return self._current_round

    @property
    def progress_percent(self) -> float:
        with self._lock:
            if self._total_rounds == 0:
                return 0.0
            return round(self._current_round / self._total_rounds * 100, 1)

    # ------------------------------------------------------------------
    # prepare()
    # ------------------------------------------------------------------

    def prepare(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure agents and environment from a template or custom config.

        Args:
            config: Either a GTM scenario template dict or custom config with:
                - scenario_context (str): The situation being simulated
                - agents (list): Agent definitions with name/role/persona/etc.
                - total_rounds (int, optional): Number of rounds (default 10)
                - hot_topics (list, optional): Topics to seed the discussion
                - events (list, optional): Scheduled events

        Returns:
            Summary dict with agent_count, total_rounds, simulation_id, demo_mode.
        """
        with self._lock:
            if self._status in (EngineStatus.RUNNING,):
                raise RuntimeError("Cannot prepare while simulation is running")

            self._status = EngineStatus.PREPARING

        try:
            sim_id = f"engine_{uuid.uuid4().hex[:12]}"

            # Detect demo mode
            demo_mode = not Config.LLM_API_KEY
            llm_client = None
            if not demo_mode:
                try:
                    from ..utils.llm_client import LLMClient
                    llm_client = LLMClient()
                except Exception as e:
                    logger.warning(f"LLM client init failed, falling back to demo mode: {e}")
                    demo_mode = True

            # Parse config — support both GTM scenario template format and custom format
            scenario_context = config.get("seed_text") or config.get("scenario_context", "")
            total_rounds = (
                config.get("simulation_config", {}).get("total_rounds")
                or config.get("total_rounds")
                or 10
            )
            hot_topics = config.get("hot_topics", [])
            events = config.get("events", [])

            # Build agents
            agents: Dict[str, AgentState] = {}
            agent_defs = config.get("agents", [])

            # If using GTM template format with agent_config, generate agents from templates
            if not agent_defs and "agent_config" in config:
                agent_defs = self._agents_from_template(config["agent_config"])

            for i, agent_def in enumerate(agent_defs):
                agent_id = agent_def.get("agent_id", f"agent_{i:03d}")
                agents[agent_id] = AgentState(
                    agent_id=agent_id,
                    name=agent_def.get("name", f"Agent {i+1}"),
                    role=agent_def.get("role", "Stakeholder"),
                    persona=agent_def.get("persona", ""),
                    priorities=agent_def.get("priorities", []),
                    concerns=agent_def.get("concerns", []),
                    communication_style=agent_def.get("communication_style", "professional"),
                    segment=agent_def.get("segment", ""),
                    contract_value=agent_def.get("contract_value", ""),
                    decision_authority=agent_def.get("decision_authority", ""),
                )

            # If still no agents, create a small default set for demo
            if not agents:
                agents = self._default_demo_agents()

            # Build environment
            environment = EnvironmentState(
                scenario_context=scenario_context,
                hot_topics=hot_topics,
                events=events,
            )

            history = ExecutionHistory(simulation_id=sim_id, total_rounds=total_rounds)

            # Commit state under lock
            with self._lock:
                self._simulation_id = sim_id
                self._agents = agents
                self._environment = environment
                self._history = history
                self._total_rounds = total_rounds
                self._current_round = 0
                self._llm_client = llm_client
                self._demo_mode = demo_mode
                self._stop_requested = False
                self._status = EngineStatus.READY

            summary = {
                "simulation_id": sim_id,
                "agent_count": len(agents),
                "total_rounds": total_rounds,
                "demo_mode": demo_mode,
                "agents": [a.to_dict() for a in agents.values()],
            }
            logger.info(f"Engine prepared: {sim_id}, {len(agents)} agents, {total_rounds} rounds, demo={demo_mode}")
            return summary

        except Exception as e:
            with self._lock:
                self._status = EngineStatus.FAILED
            logger.error(f"Engine prepare failed: {e}")
            raise

    # ------------------------------------------------------------------
    # execute_round()
    # ------------------------------------------------------------------

    def execute_round(self, round_num: int) -> RoundResult:
        """
        Execute a single simulation round.

        1. Determine agent order (shuffled for fairness)
        2. For each agent: build context → call LLM → parse actions → update state
        3. Between-round: update sentiment, consensus, check stopping conditions

        Args:
            round_num: 1-based round number.

        Returns:
            RoundResult with all agent turns and metrics.
        """
        with self._lock:
            if self._status not in (EngineStatus.READY, EngineStatus.RUNNING):
                raise RuntimeError(f"Cannot execute round in state: {self._status.value}")
            self._status = EngineStatus.RUNNING
            self._current_round = round_num
            self._environment.round_num = round_num

        round_result = RoundResult(round_num=round_num)

        # Determine agent order — shuffle for fairness
        with self._lock:
            agent_ids = list(self._agents.keys())
        random.shuffle(agent_ids)

        round_result.active_agent_count = len(agent_ids)

        # Process each agent's turn
        for agent_id in agent_ids:
            with self._lock:
                if self._stop_requested:
                    break
                agent = deepcopy(self._agents[agent_id])
                env_snapshot = deepcopy(self._environment)

            turn_result = self._process_agent_turn(agent, env_snapshot, round_num)

            # Apply turn results back to shared state
            with self._lock:
                self._agents[agent_id].sentiment_score = turn_result.sentiment_score
                self._agents[agent_id].turns_taken += 1
                if turn_result.actions:
                    self._agents[agent_id].last_action = turn_result.actions[0].content[:100]

                # Add messages to agent's memory (keep last 5)
                self._agents[agent_id].memory.append(
                    f"Round {round_num}: {turn_result.raw_response[:200]}"
                )
                if len(self._agents[agent_id].memory) > 5:
                    self._agents[agent_id].memory = self._agents[agent_id].memory[-5:]

                # Add message actions to environment
                for action in turn_result.actions:
                    if action.action_type == ActionType.MESSAGE:
                        self._environment.add_message(agent_id, agent.name, action.content)

            round_result.turns.append(turn_result)

        # Between-round updates
        with self._lock:
            self._update_sentiment_scores()
            self._update_consensus_score()
            round_result.avg_sentiment = self._environment.global_sentiment
            round_result.consensus_score = self._environment.consensus_score
            round_result.ended_at = datetime.now().isoformat()

            if self._history:
                self._history.rounds.append(round_result)

        return round_result

    # ------------------------------------------------------------------
    # execute_all()
    # ------------------------------------------------------------------

    def execute_all(
        self,
        on_round_complete: Optional[Callable[[RoundResult], None]] = None,
    ) -> Generator[RoundResult, None, None]:
        """
        Execute all rounds, yielding each RoundResult for streaming.

        Args:
            on_round_complete: Optional callback invoked after each round.

        Yields:
            RoundResult for each completed round.
        """
        with self._lock:
            if self._status not in (EngineStatus.READY,):
                raise RuntimeError(f"Cannot start execution in state: {self._status.value}")
            total = self._total_rounds
            self._stop_requested = False
            if self._history:
                self._history.started_at = datetime.now().isoformat()

        logger.info(f"Engine executing all {total} rounds for {self._simulation_id}")

        for round_num in range(1, total + 1):
            # Check stop / pause
            with self._lock:
                if self._stop_requested:
                    logger.info(f"Stop requested at round {round_num}")
                    break

            round_result = self.execute_round(round_num)

            if on_round_complete:
                on_round_complete(round_result)

            yield round_result

            # Check stopping conditions
            if self._should_stop_early():
                logger.info(f"Early stop triggered at round {round_num}")
                break

        # Finalize
        with self._lock:
            self._status = EngineStatus.COMPLETED
            if self._history:
                self._history.completed_at = datetime.now().isoformat()
                self._history.final_sentiment = self._environment.global_sentiment
                self._history.final_consensus = self._environment.consensus_score
                self._history.total_rounds = self._current_round

        logger.info(f"Engine completed: {self._simulation_id}, {self._current_round} rounds")

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------

    def pause(self):
        with self._lock:
            if self._status == EngineStatus.RUNNING:
                self._status = EngineStatus.PAUSED
                self._stop_requested = True

    def resume(self):
        with self._lock:
            if self._status == EngineStatus.PAUSED:
                self._status = EngineStatus.READY
                self._stop_requested = False

    def stop(self):
        with self._lock:
            self._stop_requested = True
            if self._status in (EngineStatus.RUNNING, EngineStatus.PAUSED):
                self._status = EngineStatus.COMPLETED

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        """Full engine state snapshot."""
        with self._lock:
            return {
                "simulation_id": self._simulation_id,
                "status": self._status.value,
                "current_round": self._current_round,
                "total_rounds": self._total_rounds,
                "progress_percent": round(self._current_round / max(self._total_rounds, 1) * 100, 1),
                "demo_mode": self._demo_mode,
                "agent_count": len(self._agents),
                "global_sentiment": self._environment.global_sentiment,
                "consensus_score": self._environment.consensus_score,
                "agents": {aid: a.to_dict() for aid, a in self._agents.items()},
                "environment": self._environment.to_dict(),
            }

    def get_history(self) -> Dict[str, Any]:
        """Full execution history for replay."""
        with self._lock:
            if self._history:
                return self._history.to_dict()
            return {"simulation_id": self._simulation_id, "rounds": [], "total_rounds": 0}

    def get_agent_stats(self) -> List[Dict[str, Any]]:
        """Per-agent statistics."""
        with self._lock:
            return [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "role": a.role,
                    "sentiment_score": a.sentiment_score,
                    "turns_taken": a.turns_taken,
                    "last_action": a.last_action,
                    "segment": a.segment,
                    "decision_authority": a.decision_authority,
                }
                for a in self._agents.values()
            ]

    # ------------------------------------------------------------------
    # Internal: agent turn processing
    # ------------------------------------------------------------------

    def _process_agent_turn(
        self, agent: AgentState, env: EnvironmentState, round_num: int
    ) -> AgentTurnResult:
        """Process a single agent's turn — get LLM response and parse actions."""
        if self._demo_mode:
            return self._mock_agent_turn(agent, round_num)

        # Build prompts
        extra_context_parts = []
        if agent.segment:
            extra_context_parts.append(f"Segment: {agent.segment}")
        if agent.contract_value:
            extra_context_parts.append(f"Contract value: {agent.contract_value}")
        if agent.decision_authority:
            extra_context_parts.append(f"Decision authority: {agent.decision_authority}")
        extra_context = "\n".join(extra_context_parts)

        system_msg = AGENT_SYSTEM_PROMPT.format(
            name=agent.name,
            role=agent.role,
            persona=agent.persona,
            communication_style=agent.communication_style,
            priorities=", ".join(agent.priorities) if agent.priorities else "general business goals",
            concerns=", ".join(agent.concerns) if agent.concerns else "typical business concerns",
            extra_context=extra_context,
        )

        recent_msgs_text = ""
        for msg in env.recent_messages[:10]:
            recent_msgs_text += f"- {msg['agent_name']}: {msg['content']}\n"
        if not recent_msgs_text:
            recent_msgs_text = "(No messages yet — you're among the first to respond.)"

        events_text = ""
        for evt in env.events:
            events_text += f"- {evt.get('description', str(evt))}\n"
        if not events_text:
            events_text = "(No special events this round.)"

        memory_text = "\n".join(agent.memory[-3:]) if agent.memory else "(First round — no prior memory.)"

        user_msg = AGENT_TURN_PROMPT.format(
            scenario_context=env.scenario_context,
            round_num=round_num,
            events=events_text,
            recent_messages=recent_msgs_text,
            memory=memory_text,
            name=agent.name,
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        try:
            response_data = self._llm_client.chat_json(
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )
            raw_response = json.dumps(response_data, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"LLM call failed for {agent.name}, using fallback: {e}")
            return self._mock_agent_turn(agent, round_num)

        return self._parse_turn_response(agent, round_num, raw_response, response_data)

    def _parse_turn_response(
        self, agent: AgentState, round_num: int,
        raw_response: str, data: Dict[str, Any],
    ) -> AgentTurnResult:
        """Parse a JSON response into an AgentTurnResult with actions."""
        actions: List[AgentAction] = []
        sentiment = float(data.get("sentiment", 0.0))
        sentiment = max(-1.0, min(1.0, sentiment))

        message = data.get("message", "")
        if message:
            actions.append(AgentAction(
                action_type=ActionType.MESSAGE,
                content=message,
            ))

        decision = data.get("decision")
        if decision and decision != "null":
            actions.append(AgentAction(
                action_type=ActionType.DECISION,
                content=str(decision),
                metadata={"agent_role": agent.role, "agent_segment": agent.segment},
            ))

        data_request = data.get("data_request")
        if data_request and data_request != "null":
            actions.append(AgentAction(
                action_type=ActionType.DATA_REQUEST,
                content=str(data_request),
            ))

        return AgentTurnResult(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            round_num=round_num,
            raw_response=raw_response,
            actions=actions,
            sentiment_score=sentiment,
        )

    def _mock_agent_turn(self, agent: AgentState, round_num: int) -> AgentTurnResult:
        """Generate a plausible mock response for demo mode."""
        mock = random.choice(MOCK_RESPONSES)

        # Add persona-flavored variation
        sentiment = mock["sentiment"] + random.uniform(-0.15, 0.15)
        sentiment = max(-1.0, min(1.0, sentiment))

        data = {
            "message": mock["message"],
            "sentiment": sentiment,
            "decision": mock["decision"],
            "data_request": mock["data_request"],
        }

        return self._parse_turn_response(
            agent, round_num, json.dumps(data, ensure_ascii=False), data
        )

    # ------------------------------------------------------------------
    # Internal: between-round updates
    # ------------------------------------------------------------------

    def _update_sentiment_scores(self):
        """Update global sentiment as average of all agent sentiments."""
        if not self._agents:
            return
        total = sum(a.sentiment_score for a in self._agents.values())
        self._environment.global_sentiment = round(total / len(self._agents), 3)

    def _update_consensus_score(self):
        """
        Consensus = 1 - normalized standard deviation of agent sentiments.
        High consensus means agents are aligned (all positive or all negative).
        """
        if len(self._agents) < 2:
            self._environment.consensus_score = 1.0
            return

        scores = [a.sentiment_score for a in self._agents.values()]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        # Normalize: max possible std_dev for [-1,1] range is 1.0
        self._environment.consensus_score = round(max(0.0, 1.0 - std_dev), 3)

    def _should_stop_early(self) -> bool:
        """Check stopping conditions between rounds."""
        with self._lock:
            # Stop if consensus is very high (agents converged)
            if self._environment.consensus_score >= 0.95 and self._current_round >= 3:
                logger.info("Early stop: high consensus reached")
                return True

            # Stop if all agents have made firm decisions
            firm_decisions = {"buy", "churn", "stay"}
            decided = 0
            for agent in self._agents.values():
                if agent.last_action and agent.last_action.lower() in firm_decisions:
                    decided += 1
            if decided == len(self._agents) and len(self._agents) > 0:
                logger.info("Early stop: all agents decided")
                return True

        return False

    # ------------------------------------------------------------------
    # Internal: agent generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _agents_from_template(agent_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate agent definitions from a GTM template's agent_config block."""
        count = min(agent_config.get("count", 10), 50)  # cap at 50 for in-memory engine
        persona_types = agent_config.get("persona_types", ["Stakeholder"])
        firmographic = agent_config.get("firmographic_mix", {})
        segments = firmographic.get("segments", ["Mid-Market"])
        contract_values = firmographic.get("contract_values", ["$2000-10000/mo"])

        agents = []
        for i in range(count):
            role = persona_types[i % len(persona_types)]
            segment = segments[i % len(segments)]
            contract = contract_values[i % len(contract_values)]
            agents.append({
                "agent_id": f"agent_{i:03d}",
                "name": f"{role} #{i+1}",
                "role": role,
                "persona": f"A {segment} {role} evaluating the proposal.",
                "communication_style": "professional",
                "segment": segment,
                "contract_value": contract,
                "decision_authority": "influencer" if "Manager" in role else "decision_maker",
            })

        return agents

    @staticmethod
    def _default_demo_agents() -> Dict[str, AgentState]:
        """Create a small default agent set for demo mode."""
        defaults = [
            ("VP of Support", "executive", "strategic, data-driven", ["cost reduction", "team efficiency"], ["vendor lock-in", "migration risk"]),
            ("CX Director", "director", "detail-oriented, quality-focused", ["customer experience", "omnichannel"], ["feature parity", "training"]),
            ("IT Leader", "director", "technical, risk-aware", ["security", "integration stability"], ["data privacy", "API limits"]),
            ("Head of Ops", "director", "pragmatic, metrics-driven", ["automation", "scalability"], ["implementation complexity", "ROI"]),
        ]
        agents = {}
        for i, (role, seniority, style, priorities, concerns) in enumerate(defaults):
            aid = f"agent_{i:03d}"
            agents[aid] = AgentState(
                agent_id=aid,
                name=f"{role} (Demo)",
                role=role,
                persona=f"A {seniority}-level {role} evaluating a pricing change.",
                communication_style=style,
                priorities=priorities,
                concerns=concerns,
                decision_authority="final_approver" if seniority == "executive" else "influencer",
            )
        return agents


# ---------------------------------------------------------------------------
# Module-level registry for concurrent access to multiple engines
# ---------------------------------------------------------------------------

_engines: Dict[str, SimulationEngine] = {}
_registry_lock = threading.Lock()


def get_engine(simulation_id: str) -> Optional[SimulationEngine]:
    """Retrieve an engine by simulation ID."""
    with _registry_lock:
        return _engines.get(simulation_id)


def create_engine() -> SimulationEngine:
    """Create and register a new engine instance."""
    engine = SimulationEngine()
    return engine


def register_engine(engine: SimulationEngine):
    """Register an engine after prepare() has been called."""
    with _registry_lock:
        _engines[engine.simulation_id] = engine


def remove_engine(simulation_id: str):
    """Remove an engine from the registry."""
    with _registry_lock:
        _engines.pop(simulation_id, None)


def list_engines() -> List[Dict[str, Any]]:
    """List all registered engines with summary info."""
    with _registry_lock:
        return [
            {
                "simulation_id": sid,
                "status": eng.status.value,
                "current_round": eng.current_round,
                "progress_percent": eng.progress_percent,
            }
            for sid, eng in _engines.items()
        ]
