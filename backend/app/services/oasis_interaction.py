"""
OASIS Interaction Protocol

Defines how agents interact within OASIS simulations.

Interaction types:
1. DirectMessage  — one agent messages another (e.g. sales rep → customer)
2. GroupDiscussion — multiple agents discuss a topic (e.g. deal review meeting)
3. Broadcast      — one agent broadcasts to all (e.g. marketing campaign launch)
4. Reaction       — agents respond to an event (e.g. competitor price change)

Each interaction produces a structured InteractionResult with participants,
messages, sentiment scores, decisions, and next actions.
"""

import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('mirofish.oasis_interaction')


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InteractionType(str, Enum):
    DIRECT_MESSAGE = "direct_message"
    GROUP_DISCUSSION = "group_discussion"
    BROADCAST = "broadcast"
    REACTION = "reaction"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Message:
    sender_id: str
    sender_name: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Decision:
    agent_id: str
    agent_name: str
    decision: str
    confidence: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Action:
    agent_id: str
    agent_name: str
    action_type: str
    description: str
    target: Optional[str] = None
    priority: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InteractionResult:
    interaction_id: str
    interaction_type: InteractionType
    participants: List[Dict[str, Any]]
    messages: List[Message]
    sentiment_scores: Dict[str, float]
    decisions_made: List[Decision]
    next_actions: List[Action]
    token_usage: Dict[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "interaction_type": self.interaction_type.value,
            "participants": self.participants,
            "messages": [m.to_dict() for m in self.messages],
            "sentiment_scores": self.sentiment_scores,
            "decisions_made": [d.to_dict() for d in self.decisions_made],
            "next_actions": [a.to_dict() for a in self.next_actions],
            "token_usage": self.token_usage,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough token count (~4 chars per token for English text)."""
    return max(1, len(text) // 4)


def _build_agent_context(agent: Dict[str, Any]) -> str:
    """Build a persona description from an agent profile dict."""
    parts = [f"Name: {agent.get('name', 'Unknown')}"]
    if agent.get("profession"):
        parts.append(f"Role: {agent['profession']}")
    if agent.get("bio"):
        parts.append(f"Bio: {agent['bio']}")
    if agent.get("persona"):
        parts.append(f"Persona: {agent['persona']}")
    if agent.get("interested_topics"):
        topics = agent["interested_topics"]
        if isinstance(topics, list):
            topics = ", ".join(topics)
        parts.append(f"Interests: {topics}")
    return "\n".join(parts)


_JSON_RESPONSE_SCHEMA = """Respond in JSON with exactly these fields:
- "message": your message text (1-3 paragraphs, stay fully in character)
- "sentiment": a float from -1.0 (very negative) to 1.0 (very positive)
- "decisions": array of objects with "decision", "confidence" (0-1), "reasoning" — or empty array
- "next_actions": array of objects with "action_type", "description", "target" (optional), "priority" ("high"/"medium"/"low") — or empty array"""


# ---------------------------------------------------------------------------
# OasisInteractionProtocol
# ---------------------------------------------------------------------------

class OasisInteractionProtocol:
    """Orchestrates agent interactions within OASIS simulations."""

    def __init__(self):
        self._llm: Optional[LLMClient] = None

    @staticmethod
    def is_llm_available() -> bool:
        """Check whether an LLM client can be initialised."""
        return bool(Config.LLM_API_KEY)

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_interaction(
        self,
        agents: List[Dict[str, Any]],
        interaction_type: InteractionType,
        context: Dict[str, Any],
    ) -> InteractionResult:
        """
        Execute an interaction between agents.

        Args:
            agents: Agent profile dicts (matching OasisAgentProfile.to_dict()).
            interaction_type: One of the four InteractionType values.
            context: Dict with keys such as:
                topic       — what the interaction is about
                scenario    — broader scenario description (optional)
                constraints — list of behavioural rules (optional)
                max_rounds  — rounds for group discussions (default 2)
                event       — description for Reaction type (optional)

        Returns:
            InteractionResult
        """
        start_ms = time.monotonic_ns() // 1_000_000
        interaction_id = str(uuid.uuid4())

        handlers = {
            InteractionType.DIRECT_MESSAGE: self._run_direct_message,
            InteractionType.GROUP_DISCUSSION: self._run_group_discussion,
            InteractionType.BROADCAST: self._run_broadcast,
            InteractionType.REACTION: self._run_reaction,
        }

        handler = handlers[interaction_type]

        logger.info(
            "Running %s interaction with %d agents, id=%s",
            interaction_type.value, len(agents), interaction_id,
        )

        result = handler(interaction_id, agents, context)
        result.duration_ms = (time.monotonic_ns() // 1_000_000) - start_ms

        logger.info(
            "Interaction %s completed in %dms — messages=%d, tokens=%d",
            interaction_id, result.duration_ms,
            len(result.messages), result.token_usage["total_tokens"],
        )
        return result

    # ------------------------------------------------------------------
    # Interaction handlers
    # ------------------------------------------------------------------

    def _run_direct_message(
        self, interaction_id: str, agents: List[Dict], context: Dict,
    ) -> InteractionResult:
        """One agent messages another and receives a reply."""
        if len(agents) < 2:
            raise ValueError("DirectMessage requires at least 2 agents")

        sender, receiver = agents[0], agents[1]
        topic = context.get("topic", "general discussion")
        scenario = context.get("scenario", "")
        constraints = context.get("constraints", [])

        llm = self._get_llm()
        usage = _new_usage()
        messages: List[Message] = []
        decisions: List[Decision] = []
        actions: List[Action] = []
        sentiments: Dict[str, float] = {}

        # Sender composes message
        sender_sys = _dm_system(sender, receiver, topic, scenario, constraints, "sender")
        sender_resp = llm.chat_json(
            messages=[
                {"role": "system", "content": sender_sys},
                {"role": "user", "content": f"Compose your message to {receiver.get('name', 'the recipient')} about: {topic}"},
            ],
            temperature=0.7,
        )
        _accum_usage(usage, sender_sys, sender_resp)

        sender_msg = Message(
            sender_id=str(sender.get("user_id", "0")),
            sender_name=sender.get("name", "Unknown"),
            content=sender_resp.get("message", ""),
        )
        messages.append(sender_msg)
        sentiments[sender_msg.sender_id] = float(sender_resp.get("sentiment", 0.0))
        _collect_decisions(sender, sender_resp, decisions)
        _collect_actions(sender, sender_resp, actions)

        # Receiver responds
        recv_sys = _dm_system(receiver, sender, topic, scenario, constraints, "receiver")
        recv_resp = llm.chat_json(
            messages=[
                {"role": "system", "content": recv_sys},
                {"role": "user", "content": (
                    f"{sender.get('name', 'Someone')} sent you this message:\n\n"
                    f"\"{sender_msg.content}\"\n\nRespond in character."
                )},
            ],
            temperature=0.7,
        )
        _accum_usage(usage, recv_sys, recv_resp)

        recv_msg = Message(
            sender_id=str(receiver.get("user_id", "0")),
            sender_name=receiver.get("name", "Unknown"),
            content=recv_resp.get("message", ""),
        )
        messages.append(recv_msg)
        sentiments[recv_msg.sender_id] = float(recv_resp.get("sentiment", 0.0))
        _collect_decisions(receiver, recv_resp, decisions)
        _collect_actions(receiver, recv_resp, actions)

        return InteractionResult(
            interaction_id=interaction_id,
            interaction_type=InteractionType.DIRECT_MESSAGE,
            participants=[_agent_summary(a) for a in (sender, receiver)],
            messages=messages,
            sentiment_scores=sentiments,
            decisions_made=decisions,
            next_actions=actions,
            token_usage=usage,
        )

    def _run_group_discussion(
        self, interaction_id: str, agents: List[Dict], context: Dict,
    ) -> InteractionResult:
        """Multiple agents discuss a topic over several rounds."""
        if len(agents) < 2:
            raise ValueError("GroupDiscussion requires at least 2 agents")

        topic = context.get("topic", "general discussion")
        scenario = context.get("scenario", "")
        constraints = context.get("constraints", [])
        max_rounds = min(context.get("max_rounds", 2), 5)

        llm = self._get_llm()
        usage = _new_usage()
        messages: List[Message] = []
        decisions: List[Decision] = []
        actions: List[Action] = []
        sentiments: Dict[str, float] = {}
        conversation_log: List[Dict[str, str]] = []

        for round_num in range(max_rounds):
            for agent in agents:
                agent_id = str(agent.get("user_id", "0"))
                agent_name = agent.get("name", "Unknown")

                sys_prompt = _group_system(agent, agents, topic, scenario, constraints, round_num)

                user_content = f"Round {round_num + 1}: Share your perspective on '{topic}'."
                if conversation_log:
                    recent = conversation_log[-10:]
                    history = "\n".join(f"- {e['name']}: {e['content']}" for e in recent)
                    user_content += f"\n\nConversation so far:\n{history}"

                resp = llm.chat_json(
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.7,
                )
                _accum_usage(usage, sys_prompt + user_content, resp)

                msg_content = resp.get("message", "")
                messages.append(Message(
                    sender_id=agent_id,
                    sender_name=agent_name,
                    content=msg_content,
                    metadata={"round": round_num + 1},
                ))
                conversation_log.append({"name": agent_name, "content": msg_content})
                sentiments[agent_id] = float(resp.get("sentiment", 0.0))
                _collect_decisions(agent, resp, decisions)
                _collect_actions(agent, resp, actions)

        return InteractionResult(
            interaction_id=interaction_id,
            interaction_type=InteractionType.GROUP_DISCUSSION,
            participants=[_agent_summary(a) for a in agents],
            messages=messages,
            sentiment_scores=sentiments,
            decisions_made=decisions,
            next_actions=actions,
            token_usage=usage,
        )

    def _run_broadcast(
        self, interaction_id: str, agents: List[Dict], context: Dict,
    ) -> InteractionResult:
        """One agent broadcasts a message; the rest react."""
        if len(agents) < 2:
            raise ValueError("Broadcast requires at least 2 agents (1 broadcaster + recipients)")

        broadcaster = agents[0]
        recipients = agents[1:]
        topic = context.get("topic", "announcement")
        scenario = context.get("scenario", "")
        constraints = context.get("constraints", [])

        llm = self._get_llm()
        usage = _new_usage()
        messages: List[Message] = []
        decisions: List[Decision] = []
        actions: List[Action] = []
        sentiments: Dict[str, float] = {}

        # Broadcaster creates message
        bc_sys = _broadcast_system(broadcaster, topic, scenario, constraints)
        bc_resp = llm.chat_json(
            messages=[
                {"role": "system", "content": bc_sys},
                {"role": "user", "content": f"Create a broadcast message about: {topic}"},
            ],
            temperature=0.7,
        )
        _accum_usage(usage, bc_sys, bc_resp)

        bc_content = bc_resp.get("message", "")
        bc_id = str(broadcaster.get("user_id", "0"))
        messages.append(Message(
            sender_id=bc_id,
            sender_name=broadcaster.get("name", "Unknown"),
            content=bc_content,
            metadata={"is_broadcast": True},
        ))
        sentiments[bc_id] = float(bc_resp.get("sentiment", 0.0))
        _collect_decisions(broadcaster, bc_resp, decisions)
        _collect_actions(broadcaster, bc_resp, actions)

        # Each recipient reacts
        for recipient in recipients:
            r_id = str(recipient.get("user_id", "0"))
            r_sys = _broadcast_reaction_system(
                recipient, broadcaster, bc_content, topic, scenario, constraints,
            )
            r_resp = llm.chat_json(
                messages=[
                    {"role": "system", "content": r_sys},
                    {"role": "user", "content": (
                        f"React to this broadcast from {broadcaster.get('name', 'someone')}:"
                        f"\n\n\"{bc_content}\""
                    )},
                ],
                temperature=0.7,
            )
            _accum_usage(usage, r_sys, r_resp)

            messages.append(Message(
                sender_id=r_id,
                sender_name=recipient.get("name", "Unknown"),
                content=r_resp.get("message", ""),
                metadata={"is_reaction_to_broadcast": True},
            ))
            sentiments[r_id] = float(r_resp.get("sentiment", 0.0))
            _collect_decisions(recipient, r_resp, decisions)
            _collect_actions(recipient, r_resp, actions)

        return InteractionResult(
            interaction_id=interaction_id,
            interaction_type=InteractionType.BROADCAST,
            participants=[_agent_summary(a) for a in agents],
            messages=messages,
            sentiment_scores=sentiments,
            decisions_made=decisions,
            next_actions=actions,
            token_usage=usage,
        )

    def _run_reaction(
        self, interaction_id: str, agents: List[Dict], context: Dict,
    ) -> InteractionResult:
        """All agents independently react to an external event."""
        event = context.get("event", context.get("topic", "an unspecified event"))
        scenario = context.get("scenario", "")
        constraints = context.get("constraints", [])

        llm = self._get_llm()
        usage = _new_usage()
        messages: List[Message] = []
        decisions: List[Decision] = []
        actions: List[Action] = []
        sentiments: Dict[str, float] = {}

        for agent in agents:
            agent_id = str(agent.get("user_id", "0"))
            sys_prompt = _event_reaction_system(agent, event, scenario, constraints)
            resp = llm.chat_json(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"React to this event: {event}"},
                ],
                temperature=0.7,
            )
            _accum_usage(usage, sys_prompt, resp)

            messages.append(Message(
                sender_id=agent_id,
                sender_name=agent.get("name", "Unknown"),
                content=resp.get("message", ""),
                metadata={"event": event},
            ))
            sentiments[agent_id] = float(resp.get("sentiment", 0.0))
            _collect_decisions(agent, resp, decisions)
            _collect_actions(agent, resp, actions)

        return InteractionResult(
            interaction_id=interaction_id,
            interaction_type=InteractionType.REACTION,
            participants=[_agent_summary(a) for a in agents],
            messages=messages,
            sentiment_scores=sentiments,
            decisions_made=decisions,
            next_actions=actions,
            token_usage=usage,
        )


# ---------------------------------------------------------------------------
# Prompt builders (module-level for reuse / testability)
# ---------------------------------------------------------------------------

def _constraint_block(constraints: List[str]) -> str:
    if not constraints:
        return "None"
    return "\n".join(f"- {c}" for c in constraints)


def _dm_system(
    agent: Dict, other: Dict, topic: str, scenario: str,
    constraints: List[str], role: str,
) -> str:
    verb = "compose a message to" if role == "sender" else "respond to a message from"
    other_name = other.get("name", "the other person")
    scenario_line = f"\nSCENARIO: {scenario}" if scenario else ""
    return (
        f"You are simulating an agent in a GTM (Go-To-Market) simulation.\n"
        f"Stay fully in character and {verb} {other_name}.\n\n"
        f"YOUR PROFILE:\n{_build_agent_context(agent)}\n\n"
        f"TOPIC: {topic}{scenario_line}\n"
        f"CONSTRAINTS:\n{_constraint_block(constraints)}\n\n"
        f"{_JSON_RESPONSE_SCHEMA}"
    )


def _group_system(
    agent: Dict, all_agents: List[Dict], topic: str, scenario: str,
    constraints: List[str], round_num: int,
) -> str:
    others = [
        a.get("name", "Unknown")
        for a in all_agents
        if a.get("user_id") != agent.get("user_id")
    ]
    scenario_line = f"\nSCENARIO: {scenario}" if scenario else ""
    return (
        f"You are simulating an agent in a GTM group discussion (round {round_num + 1}).\n"
        f"Stay fully in character. Engage with other participants' ideas.\n\n"
        f"YOUR PROFILE:\n{_build_agent_context(agent)}\n\n"
        f"OTHER PARTICIPANTS: {', '.join(others)}\n"
        f"TOPIC: {topic}{scenario_line}\n"
        f"CONSTRAINTS:\n{_constraint_block(constraints)}\n\n"
        f"{_JSON_RESPONSE_SCHEMA}"
    )


def _broadcast_system(
    broadcaster: Dict, topic: str, scenario: str, constraints: List[str],
) -> str:
    scenario_line = f"\nSCENARIO: {scenario}" if scenario else ""
    return (
        f"You are simulating an agent broadcasting a message in a GTM simulation.\n"
        f"Stay fully in character. Create a compelling broadcast for your audience.\n\n"
        f"YOUR PROFILE:\n{_build_agent_context(broadcaster)}\n\n"
        f"TOPIC: {topic}{scenario_line}\n"
        f"CONSTRAINTS:\n{_constraint_block(constraints)}\n\n"
        f"{_JSON_RESPONSE_SCHEMA}"
    )


def _broadcast_reaction_system(
    recipient: Dict, broadcaster: Dict, broadcast_content: str,
    topic: str, scenario: str, constraints: List[str],
) -> str:
    scenario_line = f"\nSCENARIO: {scenario}" if scenario else ""
    return (
        f"You are simulating an agent reacting to a broadcast in a GTM simulation.\n"
        f"Stay fully in character. React naturally based on your role and perspective.\n\n"
        f"YOUR PROFILE:\n{_build_agent_context(recipient)}\n\n"
        f"BROADCAST FROM: {broadcaster.get('name', 'someone')}\n"
        f"TOPIC: {topic}{scenario_line}\n"
        f"CONSTRAINTS:\n{_constraint_block(constraints)}\n\n"
        f"{_JSON_RESPONSE_SCHEMA}"
    )


def _event_reaction_system(
    agent: Dict, event: str, scenario: str, constraints: List[str],
) -> str:
    scenario_line = f"\nSCENARIO: {scenario}" if scenario else ""
    return (
        f"You are simulating an agent reacting to an external event in a GTM simulation.\n"
        f"Stay fully in character. React based on how this event impacts your role and goals.\n\n"
        f"YOUR PROFILE:\n{_build_agent_context(agent)}\n\n"
        f"EVENT: {event}{scenario_line}\n"
        f"CONSTRAINTS:\n{_constraint_block(constraints)}\n\n"
        f"{_JSON_RESPONSE_SCHEMA}"
    )


# ---------------------------------------------------------------------------
# Collection helpers
# ---------------------------------------------------------------------------

def _new_usage() -> Dict[str, int]:
    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _accum_usage(usage: Dict[str, int], prompt_text: str, response: Any) -> None:
    p = _estimate_tokens(prompt_text)
    c = _estimate_tokens(str(response))
    usage["prompt_tokens"] += p
    usage["completion_tokens"] += c
    usage["total_tokens"] += p + c


def _agent_summary(agent: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": agent.get("user_id"),
        "name": agent.get("name", "Unknown"),
        "profession": agent.get("profession", ""),
    }


def _collect_decisions(
    agent: Dict, response: Dict, out: List[Decision],
) -> None:
    aid = str(agent.get("user_id", "0"))
    name = agent.get("name", "Unknown")
    for d in response.get("decisions", []):
        if isinstance(d, dict) and d.get("decision"):
            out.append(Decision(
                agent_id=aid,
                agent_name=name,
                decision=d["decision"],
                confidence=float(d.get("confidence", 0.5)),
                reasoning=d.get("reasoning", ""),
            ))


def _collect_actions(
    agent: Dict, response: Dict, out: List[Action],
) -> None:
    aid = str(agent.get("user_id", "0"))
    name = agent.get("name", "Unknown")
    for a in response.get("next_actions", []):
        if isinstance(a, dict) and a.get("action_type"):
            out.append(Action(
                agent_id=aid,
                agent_name=name,
                action_type=a["action_type"],
                description=a.get("description", ""),
                target=a.get("target"),
                priority=a.get("priority", "medium"),
            ))
