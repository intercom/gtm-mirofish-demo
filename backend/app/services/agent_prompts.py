"""
Memory-augmented agent prompt builder.

Injects long-term memory (consolidated memories, beliefs, relationships)
into agent prompts with token-budget-aware truncation.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.agent_prompts')

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
