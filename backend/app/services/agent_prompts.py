"""
Agent Prompt Engineering Module
LLM prompt templates for OASIS simulation agents.

Provides structured prompts that produce parseable agent responses,
with provider-specific optimizations (XML tags for Claude, JSON mode for GPT/Gemini).
"""

import json
import re
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.agent_prompts')


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AgentTurnResponse:
    """Parsed structured response from an agent's turn."""
    thought: str = ""
    message: str = ""
    decision: str = "NONE"
    sentiment: int = 5
    raw: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought": self.thought,
            "message": self.message,
            "decision": self.decision,
            "sentiment": self.sentiment,
        }


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def _detect_provider() -> str:
    """Detect LLM provider from config base URL."""
    base_url = Config.LLM_BASE_URL or ""
    if "anthropic" in base_url:
        return "anthropic"
    if "generativelanguage.googleapis" in base_url:
        return "gemini"
    return "openai"


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = (
    "You are {name}, a {role} at Intercom. "
    "{personality}. {expertise}. "
    "You are in a {scenario_type} meeting. "
    "{constraints}. "
    "Respond in character — stay consistent with your persona throughout the conversation."
)

# Claude (Anthropic) works best with XML-tagged output
TURN_PROMPT_XML = """\
Current discussion:
{recent_messages}

Environment: {state}
Your memory: {memories}

What do you say or decide? Respond using EXACTLY these XML tags:

<thought>Your internal reasoning — not shared with others</thought>
<message>What you say to the group</message>
<decision>Any decision you make, or NONE</decision>
<sentiment>A number from 1 (very negative) to 10 (very positive)</sentiment>"""

# OpenAI / Gemini work best with explicit JSON instructions
TURN_PROMPT_JSON = """\
Current discussion:
{recent_messages}

Environment: {state}
Your memory: {memories}

What do you say or decide? Respond with ONLY a JSON object (no markdown fences):

{{
  "thought": "(internal reasoning — not shared with others)",
  "message": "(what you say to the group)",
  "decision": "(any decision you make, or NONE)",
  "sentiment": (a number from 1 to 10)
}}"""


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------

def _parse_xml_response(text: str) -> AgentTurnResponse:
    """Extract structured fields from XML-tagged LLM output."""
    resp = AgentTurnResponse(raw=text)

    for tag in ("thought", "message", "decision"):
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        if match:
            setattr(resp, tag, match.group(1).strip())

    sentiment_match = re.search(r"<sentiment>\s*(\d+)\s*</sentiment>", text)
    if sentiment_match:
        resp.sentiment = max(1, min(10, int(sentiment_match.group(1))))

    return resp


def _parse_json_response(text: str) -> AgentTurnResponse:
    """Extract structured fields from JSON LLM output."""
    resp = AgentTurnResponse(raw=text)

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON agent response, falling back to regex")
        return _parse_labelled_response(text)

    resp.thought = str(data.get("thought", ""))
    resp.message = str(data.get("message", ""))
    resp.decision = str(data.get("decision", "NONE")) or "NONE"

    raw_sentiment = data.get("sentiment", 5)
    try:
        resp.sentiment = max(1, min(10, int(raw_sentiment)))
    except (ValueError, TypeError):
        resp.sentiment = 5

    return resp


def _parse_labelled_response(text: str) -> AgentTurnResponse:
    """
    Last-resort parser for label-style output like:
      THOUGHT: ...
      MESSAGE: ...
      DECISION: ...
      SENTIMENT: ...
    """
    resp = AgentTurnResponse(raw=text)

    for label in ("THOUGHT", "MESSAGE", "DECISION"):
        pattern = rf"{label}:\s*(.+?)(?=\n(?:THOUGHT|MESSAGE|DECISION|SENTIMENT):|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            setattr(resp, label.lower(), match.group(1).strip())

    sentiment_match = re.search(r"SENTIMENT:\s*(\d+)", text, re.IGNORECASE)
    if sentiment_match:
        resp.sentiment = max(1, min(10, int(sentiment_match.group(1))))

    return resp


# ---------------------------------------------------------------------------
# Main service class
# ---------------------------------------------------------------------------

class AgentPromptEngine:
    """
    Generates and parses LLM prompts for OASIS simulation agents.

    Adapts prompt format based on the configured LLM provider:
    - Anthropic (Claude): XML-tagged output for reliable extraction
    - OpenAI / Gemini: JSON-mode output

    Falls back to deterministic mock responses when no LLM key is configured.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or _detect_provider()
        self._has_llm_key = bool(Config.LLM_API_KEY)

    # ----- prompt builders -----

    def build_system_prompt(
        self,
        name: str,
        role: str,
        personality: str,
        expertise: str,
        scenario_type: str,
        constraints: str = "Keep responses concise and actionable",
    ) -> str:
        """Build a system prompt that establishes the agent's persona."""
        return SYSTEM_PROMPT_TEMPLATE.format(
            name=name,
            role=role,
            personality=personality,
            expertise=expertise,
            scenario_type=scenario_type,
            constraints=constraints,
        )

    def build_turn_prompt(
        self,
        recent_messages: str,
        state: str = "",
        memories: str = "",
    ) -> str:
        """Build a turn prompt with the right format for the current provider."""
        template = TURN_PROMPT_XML if self.provider == "anthropic" else TURN_PROMPT_JSON
        return template.format(
            recent_messages=recent_messages or "(no messages yet)",
            state=state or "(no specific environment context)",
            memories=memories or "(no prior memories)",
        )

    def build_messages(
        self,
        system_prompt: str,
        turn_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Assemble a full messages list ready for LLMClient.chat().

        Returns the standard OpenAI-format messages array:
        [system, ...history, user(turn_prompt)]
        """
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": turn_prompt})
        return messages

    # ----- response parsing -----

    def parse_response(self, text: str) -> AgentTurnResponse:
        """
        Parse an LLM response into structured AgentTurnResponse.

        Tries the provider-preferred format first, then falls back through
        alternative parsers so the simulation doesn't crash on malformed output.
        """
        if not text or not text.strip():
            logger.warning("Empty agent response received")
            return AgentTurnResponse(
                message="(no response)",
                raw=text or "",
            )

        if self.provider == "anthropic":
            resp = _parse_xml_response(text)
        else:
            resp = _parse_json_response(text)

        if not resp.message and not resp.thought:
            logger.info("Primary parser found no content, trying labelled fallback")
            resp = _parse_labelled_response(text)

        if not resp.message:
            logger.warning("All parsers failed to extract message, using raw text")
            resp.message = text.strip()[:500]

        return resp

    # ----- demo / mock mode -----

    def mock_response(
        self,
        agent_name: str,
        role: str,
        scenario_type: str,
        round_num: int = 1,
    ) -> AgentTurnResponse:
        """
        Generate a deterministic mock response for demo mode
        (when no LLM API key is configured).

        Uses a hash-based seed so the same agent + round always
        produces the same output — making demos reproducible.
        """
        seed = int(hashlib.md5(
            f"{agent_name}:{round_num}".encode()
        ).hexdigest()[:8], 16)

        thoughts = [
            f"I need to consider how {scenario_type} impacts our Q3 pipeline.",
            f"The competitive landscape is shifting — we should act before Zendesk does.",
            f"Our ICP data suggests mid-market is under-served right now.",
            f"I've seen this pattern before — early engagement wins the deal.",
            f"We need better alignment between sales and product on this.",
        ]
        messages = [
            f"Based on my experience in {role}, I think we should focus on mid-market accounts that show high product-qualified signals.",
            f"I've been tracking Freshdesk's moves in this segment — we have a window to capture share if we act in the next quarter.",
            f"The data shows our conversion rate drops 40% when we don't engage within 48 hours. Speed matters here.",
            f"I'd recommend we pilot a dedicated {scenario_type} play with 10 accounts before scaling.",
            f"Let me share what's worked for my team: a 3-touch sequence combining product signals with intent data.",
        ]
        decisions = [
            "NONE",
            f"Propose a pilot program for {scenario_type}",
            "NONE",
            "Request cross-functional alignment meeting",
            "NONE",
        ]

        idx = seed % len(messages)
        sentiment = 5 + (seed % 5)

        return AgentTurnResponse(
            thought=thoughts[idx],
            message=messages[idx],
            decision=decisions[idx],
            sentiment=sentiment,
            raw=f"[MOCK] {messages[idx]}",
        )
