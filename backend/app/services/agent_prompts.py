"""
Agent Prompt Engineering Module
LLM prompt templates for OASIS simulation agents.

Provides structured prompts that produce parseable agent responses,
with provider-specific optimizations (XML tags for Claude, JSON mode for GPT/Gemini).

Also includes:
- Personality-aware prompt modification via PersonalityDynamics and SentimentDynamics
- Memory-augmented prompt building with token-budget-aware truncation
"""

import json
import re
import hashlib
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

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
# AgentPromptEngine — LLM prompt generation & parsing
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


# ---------------------------------------------------------------------------
# Personality-aware prompt modification
# ---------------------------------------------------------------------------

# Personality trait names (5-dimensional vector, each 0-100)
PERSONALITY_TRAITS = [
    'analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant',
]

# Threshold for "high" trait expression (at or above)
HIGH_THRESHOLD = 65
# Threshold for "low" trait expression (at or below)
LOW_THRESHOLD = 35

# Trait behavior descriptions injected into prompts
TRAIT_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    'analytical': {
        'high': 'You prefer data-driven arguments and ask for evidence.',
        'low': 'You rely on intuition and gut feelings rather than detailed analysis.',
    },
    'creative': {
        'high': 'You often suggest unconventional approaches and think outside the box.',
        'low': 'You prefer proven methods and established best practices.',
    },
    'assertive': {
        'high': 'You speak confidently and advocate strongly for your positions.',
        'low': 'You tend to defer to others and seek group consensus before voicing opinions.',
    },
    'empathetic': {
        'high': "You consider others' feelings and seek win-win outcomes.",
        'low': 'You focus on objective outcomes rather than interpersonal dynamics.',
    },
    'risk_tolerant': {
        'high': 'You are comfortable with uncertainty and favor bold moves.',
        'low': 'You prefer cautious, well-tested approaches and avoid unnecessary risk.',
    },
}

# Sentiment ranges mapped to mood descriptions
SENTIMENT_MOODS: List[Dict[str, Any]] = [
    {'min': 1, 'max': 3, 'label': 'frustrated/pessimistic',
     'prompt': 'Your current mood is frustrated and pessimistic. You are skeptical of optimistic claims and focus on potential problems.'},
    {'min': 4, 'max': 5, 'label': 'neutral/cautious',
     'prompt': 'Your current mood is neutral and cautious. You weigh options carefully without strong emotional bias.'},
    {'min': 6, 'max': 7, 'label': 'engaged/optimistic',
     'prompt': 'Your current mood is engaged and optimistic. You are receptive to new ideas and see opportunities.'},
    {'min': 8, 'max': 10, 'label': 'enthusiastic/confident',
     'prompt': 'Your current mood is enthusiastic and confident. You champion ideas energetically and inspire momentum.'},
]


@dataclass
class PersonalityVector:
    """5-dimensional personality trait vector. Each trait is 0-100."""
    analytical: int = 50
    creative: int = 50
    assertive: int = 50
    empathetic: int = 50
    risk_tolerant: int = 50

    def to_dict(self) -> Dict[str, int]:
        return {t: getattr(self, t) for t in PERSONALITY_TRAITS}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'PersonalityVector':
        return cls(**{t: data.get(t, 50) for t in PERSONALITY_TRAITS})


@dataclass
class AgentPromptContext:
    """All context needed to build a personality-aware prompt."""
    agent_id: int
    agent_name: str
    base_persona: str
    personality: PersonalityVector = field(default_factory=PersonalityVector)
    sentiment: float = 5.0  # 1-10 scale
    memories: Optional[List[str]] = None


class AgentPromptModifier:
    """
    Builds personality-aware system prompts for simulation agents.

    Combines:
    - Base persona (role, background, priorities)
    - Personality vector (5 traits → behavioral instructions)
    - Sentiment (mood modifier → tone shift)
    - Recent memories (optional context)
    """

    @staticmethod
    def get_trait_modifiers(personality: PersonalityVector) -> List[str]:
        """Return behavioral instruction strings for traits that exceed thresholds."""
        modifiers = []
        for trait in PERSONALITY_TRAITS:
            value = getattr(personality, trait)
            if value >= HIGH_THRESHOLD:
                modifiers.append(TRAIT_DESCRIPTIONS[trait]['high'])
            elif value <= LOW_THRESHOLD:
                modifiers.append(TRAIT_DESCRIPTIONS[trait]['low'])
        return modifiers

    @staticmethod
    def get_mood_description(sentiment: float) -> str:
        """Map a sentiment score (1-10) to a mood prompt string."""
        clamped = max(1.0, min(10.0, sentiment))
        for mood in SENTIMENT_MOODS:
            if mood['min'] <= clamped <= mood['max']:
                return mood['prompt']
        return SENTIMENT_MOODS[1]['prompt']  # default neutral

    @staticmethod
    def build_system_prompt(ctx: AgentPromptContext) -> str:
        """
        Build a complete personality-aware system prompt.

        Layers:
        1. Base persona (who you are)
        2. Personality traits (how you think and act)
        3. Sentiment/mood (current emotional state)
        4. Memories (what you remember)
        """
        sections = []

        # 1. Base persona
        if ctx.base_persona:
            sections.append(ctx.base_persona)

        # 2. Personality traits
        trait_mods = AgentPromptModifier.get_trait_modifiers(ctx.personality)
        if trait_mods:
            sections.append(
                'Your behavioral tendencies:\n- ' + '\n- '.join(trait_mods)
            )

        # 3. Mood modifier
        mood = AgentPromptModifier.get_mood_description(ctx.sentiment)
        sections.append(mood)

        # 4. Memories
        if ctx.memories:
            recent = ctx.memories[:10]  # cap to avoid prompt bloat
            sections.append(
                'Your recent memories:\n- ' + '\n- '.join(recent)
            )

        return '\n\n'.join(sections)

    @staticmethod
    def modify_existing_prompt(
        original_prompt: str,
        personality: PersonalityVector,
        sentiment: float = 5.0,
        memories: Optional[List[str]] = None,
    ) -> str:
        """
        Append personality/sentiment modifiers to an existing system prompt.

        Use when you already have a base prompt and want to enrich it with
        personality dynamics without replacing it entirely.
        """
        additions = []

        trait_mods = AgentPromptModifier.get_trait_modifiers(personality)
        if trait_mods:
            additions.append(
                'Your behavioral tendencies:\n- ' + '\n- '.join(trait_mods)
            )

        mood = AgentPromptModifier.get_mood_description(sentiment)
        additions.append(mood)

        if memories:
            recent = memories[:10]
            additions.append(
                'Your recent memories:\n- ' + '\n- '.join(recent)
            )

        if not additions:
            return original_prompt

        return original_prompt.rstrip() + '\n\n' + '\n\n'.join(additions)

    @staticmethod
    def generate_default_personality(
        persona_template: Optional[Dict[str, Any]] = None,
    ) -> PersonalityVector:
        """
        Generate a plausible default personality vector.

        If a persona template (from persona_templates.json) is provided,
        bias traits to match the role archetype. Otherwise, use randomized
        mid-range values.
        """
        if persona_template:
            return _personality_from_template(persona_template)

        # Random mid-range values (30-70) for a balanced default
        return PersonalityVector(**{
            t: random.randint(30, 70) for t in PERSONALITY_TRAITS
        })

    @staticmethod
    def generate_default_sentiment() -> float:
        """Return a neutral-leaning default sentiment."""
        return round(random.uniform(4.5, 6.5), 1)


def _personality_from_template(template: Dict[str, Any]) -> PersonalityVector:
    """
    Derive personality traits from a GTM persona template.

    Maps role archetypes and communication styles to trait biases.
    """
    style = (template.get('communication_style') or '').lower()
    role = (template.get('role') or '').lower()
    authority = (template.get('decision_authority') or '').lower()

    analytical = 50
    creative = 50
    assertive = 50
    empathetic = 50
    risk_tolerant = 50

    # Communication style signals
    if 'data-driven' in style or 'technical' in style or 'metrics' in style:
        analytical += 15
    if 'collaborative' in style or 'quality' in style:
        empathetic += 10
        creative += 5
    if 'strategic' in style:
        analytical += 10
        risk_tolerant += 5
    if 'pragmatic' in style or 'efficiency' in style:
        analytical += 5
        risk_tolerant -= 5
    if 'risk-aware' in style or 'process-oriented' in style:
        risk_tolerant -= 10
        analytical += 5

    # Decision authority signals
    if authority == 'final_approver':
        assertive += 15
        risk_tolerant += 5
    elif authority == 'technical_veto':
        analytical += 10
        assertive += 10
        risk_tolerant -= 10
    elif authority == 'influencer':
        empathetic += 10
        creative += 5

    # Role-based bias
    if 'vp' in role or 'head' in role:
        assertive += 5
    if 'it' in role or 'technical' in role:
        analytical += 5
    if 'cx' in role or 'experience' in role:
        empathetic += 10

    # Clamp to valid range (20-80 per PRD spec)
    return PersonalityVector(
        analytical=max(20, min(80, analytical)),
        creative=max(20, min(80, creative)),
        assertive=max(20, min(80, assertive)),
        empathetic=max(20, min(80, empathetic)),
        risk_tolerant=max(20, min(80, risk_tolerant)),
    )


# ---------------------------------------------------------------------------
# Memory-augmented prompt building
# ---------------------------------------------------------------------------

# Default token budget: 30% of context window for memory injection
DEFAULT_MEMORY_BUDGET_RATIO = 0.30
DEFAULT_CONTEXT_WINDOW = 8192
DEFAULT_TOP_K = 10
# Approximate chars-per-token for budget estimation
CHARS_PER_TOKEN = 4


@dataclass
class Memory:
    """A single agent memory entry."""
    content: str
    round_created: int
    importance: float = 5.0  # 0-10 scale
    category: str = "observation"  # decision, fact, opinion, observation
    source: Optional[str] = None

    # Importance weights by category
    CATEGORY_WEIGHTS = {
        "decision": 10,
        "fact": 7,
        "opinion": 5,
        "observation": 3,
    }

    def effective_importance(self, current_round: int) -> float:
        """Score with recency decay: importance *= 0.9^(rounds_since_created)."""
        base = self.CATEGORY_WEIGHTS.get(self.category, self.importance)
        rounds_elapsed = max(0, current_round - self.round_created)
        return base * (0.9 ** rounds_elapsed)


@dataclass
class AgentContext:
    """Structured context about an agent for prompt building."""
    agent_id: str
    agent_name: str
    persona: str = ""
    beliefs: Dict[str, str] = field(default_factory=dict)
    facts: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    memories: List[Memory] = field(default_factory=list)
    current_round: int = 0


def _estimate_tokens(text: str) -> int:
    """Rough token estimate based on character count."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def _keyword_overlap(text_a: str, text_b: str) -> float:
    """Simple keyword similarity between two strings (Jaccard on words)."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def rank_memories(
    memories: List[Memory],
    current_round: int,
    discussion_context: str = "",
    top_k: int = DEFAULT_TOP_K,
) -> List[Memory]:
    """
    Rank memories by composite score: recency-decayed importance + context similarity.

    Score = effective_importance + 5 * keyword_overlap(memory, discussion)
    """
    scored = []
    for mem in memories:
        importance = mem.effective_importance(current_round)
        similarity = _keyword_overlap(mem.content, discussion_context) if discussion_context else 0.0
        score = importance + 5.0 * similarity
        scored.append((score, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mem for _, mem in scored[:top_k]]


def _truncate_to_budget(texts: List[str], token_budget: int) -> List[str]:
    """Keep as many texts as fit within the token budget, in order."""
    result = []
    used = 0
    for text in texts:
        cost = _estimate_tokens(text)
        if used + cost > token_budget:
            remaining = token_budget - used
            if remaining > 20:
                # Truncate the last item to fit
                chars_allowed = remaining * CHARS_PER_TOKEN
                result.append(text[:chars_allowed] + "...")
            break
        result.append(text)
        used += cost
    return result


def build_memory_section(
    context: AgentContext,
    discussion_context: str = "",
    top_k: int = DEFAULT_TOP_K,
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    budget_ratio: float = DEFAULT_MEMORY_BUDGET_RATIO,
) -> str:
    """
    Build the memory-injection section of an agent prompt.

    Returns a formatted string containing consolidated memories,
    beliefs, facts, and relationships — all within the token budget.
    """
    token_budget = int(context_window * budget_ratio)
    sections = []
    budget_remaining = token_budget

    # 1. Memory reflection (beliefs, facts, relationships)
    reflection = _build_reflection(context)
    if reflection:
        reflection_tokens = _estimate_tokens(reflection)
        # Reserve at least 40% of memory budget for raw memories
        max_reflection_tokens = int(token_budget * 0.6)
        if reflection_tokens > max_reflection_tokens:
            reflection = reflection[: max_reflection_tokens * CHARS_PER_TOKEN] + "..."
            reflection_tokens = max_reflection_tokens
        sections.append(reflection)
        budget_remaining -= reflection_tokens

    # 2. Consolidated memories (ranked by relevance)
    if context.memories and budget_remaining > 50:
        ranked = rank_memories(
            context.memories,
            context.current_round,
            discussion_context,
            top_k,
        )
        memory_lines = [
            f"- [Round {m.round_created}, {m.category}] {m.content}"
            for m in ranked
        ]
        truncated = _truncate_to_budget(memory_lines, budget_remaining)
        if truncated:
            memories_block = (
                "Your memories from previous rounds:\n" + "\n".join(truncated)
            )
            sections.append(memories_block)

    return "\n\n".join(sections)


def _build_reflection(context: AgentContext) -> str:
    """Build the memory-reflection block from beliefs, facts, relationships."""
    parts = []

    if context.beliefs:
        belief_lines = [f"  - {k}: {v}" for k, v in context.beliefs.items()]
        parts.append(
            "Based on your memories, your current beliefs are:\n"
            + "\n".join(belief_lines)
        )

    if context.facts:
        fact_lines = [f"  - {f}" for f in context.facts]
        parts.append("Your key knowledge is:\n" + "\n".join(fact_lines))

    if context.relationships:
        rel_lines = [f"  - {name}: {desc}" for name, desc in context.relationships.items()]
        parts.append("Your relationships:\n" + "\n".join(rel_lines))

    return "\n\n".join(parts)


def build_augmented_prompt(
    context: AgentContext,
    base_system_prompt: str = "",
    discussion_context: str = "",
    top_k: int = DEFAULT_TOP_K,
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    budget_ratio: float = DEFAULT_MEMORY_BUDGET_RATIO,
) -> str:
    """
    Build a complete memory-augmented system prompt for an agent.

    Combines the base prompt (persona, instructions) with a memory section
    that injects consolidated memories, beliefs, facts, and relationships.
    """
    memory_section = build_memory_section(
        context,
        discussion_context=discussion_context,
        top_k=top_k,
        context_window=context_window,
        budget_ratio=budget_ratio,
    )

    parts = []
    if base_system_prompt:
        parts.append(base_system_prompt)
    if context.persona:
        parts.append(f"Your persona:\n{context.persona}")
    if memory_section:
        parts.append(memory_section)

    return "\n\n".join(parts)


# ── Demo / mock data ──

def _demo_memories(agent_name: str, num_rounds: int = 6) -> List[Memory]:
    """Generate deterministic demo memories when no real data is available."""
    seed = int(hashlib.md5(agent_name.encode()).hexdigest()[:8], 16)
    templates = [
        ("Pipeline numbers are tracking ahead of Q3 forecast", "fact", 8),
        ("Sales team alignment meeting was productive", "observation", 4),
        ("Decided to prioritize enterprise accounts this quarter", "decision", 9),
        ("Competitor launched a similar feature last week", "fact", 7),
        ("Team morale seems lower after the reorg announcement", "opinion", 5),
        ("Key stakeholder expressed concern about timeline", "observation", 6),
        ("Agreed to shift resources to the APAC expansion", "decision", 10),
        ("Customer churn rate ticked up in mid-market segment", "fact", 8),
        ("Marketing campaign ROI exceeded expectations", "fact", 7),
        ("Need to revisit pricing strategy for SMB tier", "opinion", 6),
    ]
    memories = []
    for i, (content, category, importance) in enumerate(templates):
        round_num = (seed + i * 3) % max(1, num_rounds)
        memories.append(Memory(
            content=content,
            round_created=round_num,
            importance=importance,
            category=category,
            source="demo",
        ))
    return memories


def _demo_beliefs(agent_name: str) -> Dict[str, str]:
    """Generate deterministic demo beliefs."""
    seed = int(hashlib.md5(agent_name.encode()).hexdigest()[:8], 16)
    all_beliefs = {
        "pipeline_outlook": ["optimistic", "cautious", "concerned"],
        "competitor_threat": ["low", "moderate", "high"],
        "team_readiness": ["strong", "developing", "needs improvement"],
        "market_timing": ["favorable", "neutral", "challenging"],
    }
    beliefs = {}
    for key, options in all_beliefs.items():
        beliefs[key] = options[seed % len(options)]
        seed = seed * 31 + 7
    return beliefs


def _demo_relationships(agent_name: str) -> Dict[str, str]:
    """Generate deterministic demo relationships."""
    agent_pool = [
        "Sarah Chen, VP Sales",
        "Marcus Johnson, IT Director",
        "Lisa Park, Operations Lead",
        "David Kim, Product Manager",
        "Emily Watson, CFO",
    ]
    seed = int(hashlib.md5(agent_name.encode()).hexdigest()[:8], 16)
    sentiments = ["trusted ally", "frequent collaborator", "occasional disagreements", "neutral"]
    relationships = {}
    for i, other in enumerate(agent_pool):
        if other.split(",")[0].strip() == agent_name:
            continue
        relationships[other] = sentiments[(seed + i) % len(sentiments)]
        if len(relationships) >= 3:
            break
    return relationships


def build_demo_prompt(
    agent_id: str,
    agent_name: str,
    persona: str = "",
    discussion_context: str = "",
    current_round: int = 5,
    top_k: int = DEFAULT_TOP_K,
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    budget_ratio: float = DEFAULT_MEMORY_BUDGET_RATIO,
) -> Dict[str, Any]:
    """
    Build a memory-augmented prompt using demo data.

    Used when no real simulation/Zep data is available (demo mode).
    Returns the full prompt plus metadata about what was injected.
    """
    memories = _demo_memories(agent_name, num_rounds=current_round)
    beliefs = _demo_beliefs(agent_name)
    relationships = _demo_relationships(agent_name)
    facts = [
        "Q3 pipeline is at 85% of target",
        "Enterprise win rate improved 12% this quarter",
        "APAC expansion launched 3 weeks ago",
    ]

    context = AgentContext(
        agent_id=agent_id,
        agent_name=agent_name,
        persona=persona or f"{agent_name} is a GTM simulation agent.",
        beliefs=beliefs,
        facts=facts,
        relationships=relationships,
        memories=memories,
        current_round=current_round,
    )

    ranked = rank_memories(memories, current_round, discussion_context, top_k)
    prompt = build_augmented_prompt(
        context,
        discussion_context=discussion_context,
        top_k=top_k,
        context_window=context_window,
        budget_ratio=budget_ratio,
    )

    return {
        "prompt": prompt,
        "metadata": {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "memories_injected": len(ranked),
            "beliefs_count": len(beliefs),
            "facts_count": len(facts),
            "relationships_count": len(relationships),
            "current_round": current_round,
            "token_budget": int(context_window * budget_ratio),
            "estimated_tokens": _estimate_tokens(prompt),
        },
    }
