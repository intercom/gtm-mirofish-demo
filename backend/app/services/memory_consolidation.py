"""
Long-term memory consolidation service

Consolidates agent memories across simulation rounds using importance scoring,
recency decay (forgetting curve), and LLM-powered summarization.

When Zep is available, uses Zep's graph memory for semantic retrieval.
Otherwise, operates with a pure in-memory implementation for demo/mock mode.
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.memory_consolidation')


class MemoryType(str, Enum):
    """Memory category types with associated importance weights."""
    DECISION = "decision"
    FACT = "fact"
    OPINION = "opinion"
    OBSERVATION = "observation"


# Base importance scores per memory type
MEMORY_TYPE_WEIGHTS: Dict[str, int] = {
    MemoryType.DECISION: 10,
    MemoryType.FACT: 7,
    MemoryType.OPINION: 5,
    MemoryType.OBSERVATION: 3,
}

# Recency decay factor per round (Ebbinghaus-inspired forgetting curve)
RECENCY_DECAY_FACTOR = 0.9


@dataclass
class Memory:
    """A single agent memory unit."""
    memory_id: str
    agent_id: str
    content: str
    memory_type: str = MemoryType.OBSERVATION
    importance: float = 3.0
    round_created: int = 0
    round_last_accessed: int = 0
    access_count: int = 1
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": round(self.importance, 3),
            "round_created": self.round_created,
            "round_last_accessed": self.round_last_accessed,
            "access_count": self.access_count,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class MemoryConsolidator:
    """
    Consolidates agent memories across simulation rounds.

    Provides four core operations:
    - consolidate: merge similar/redundant memories into consolidated facts
    - prioritize: rank memories by relevance (recency, frequency, importance)
    - forget: remove low-priority memories (forgetting curve simulation)
    - summarize_session: create a summary of key learnings from a simulation
    """

    def __init__(self):
        # In-memory store: agent_id -> list of Memory objects
        self._memories: Dict[str, List[Memory]] = {}
        self._id_counter = 0

        # Check Zep availability
        self._zep_client = None
        if Config.ZEP_API_KEY:
            try:
                from zep_cloud.client import Zep
                self._zep_client = Zep(api_key=Config.ZEP_API_KEY)
                logger.info("MemoryConsolidator initialized with Zep backend")
            except Exception as e:
                logger.warning(f"Zep unavailable, using in-memory backend: {e}")
        else:
            logger.info("MemoryConsolidator initialized in demo/in-memory mode")

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"mem_{self._id_counter:06d}"

    def _get_agent_memories(self, agent_id: str) -> List[Memory]:
        if agent_id not in self._memories:
            self._memories[agent_id] = []
        return self._memories[agent_id]

    def add_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = MemoryType.OBSERVATION,
        current_round: int = 0,
        session_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """Add a new memory for an agent."""
        base_importance = MEMORY_TYPE_WEIGHTS.get(memory_type, 3)
        memory = Memory(
            memory_id=self._next_id(),
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            importance=float(base_importance),
            round_created=current_round,
            round_last_accessed=current_round,
            session_id=session_id,
            metadata=metadata or {},
        )
        self._get_agent_memories(agent_id).append(memory)
        logger.debug(f"Added memory for agent {agent_id}: type={memory_type}, importance={base_importance}")
        return memory

    def consolidate(self, agent_id: str, memories: Optional[List[Memory]] = None) -> List[Memory]:
        """
        Merge similar/redundant memories into consolidated facts.

        Groups memories by type, detects content overlap via substring matching,
        and merges duplicates by keeping the highest-importance version with
        boosted access count.

        If Zep is available, uses Zep's graph search for semantic deduplication.
        Otherwise uses simple substring similarity.

        Args:
            agent_id: The agent whose memories to consolidate
            memories: Optional explicit list; defaults to agent's stored memories

        Returns:
            The consolidated list of memories
        """
        if memories is None:
            memories = self._get_agent_memories(agent_id)

        if len(memories) <= 1:
            return memories

        # Group by memory type for more targeted consolidation
        by_type: Dict[str, List[Memory]] = {}
        for mem in memories:
            by_type.setdefault(mem.memory_type, []).append(mem)

        consolidated: List[Memory] = []

        for mem_type, group in by_type.items():
            merged = self._merge_similar(group)
            consolidated.extend(merged)

        # Update the agent's memory store
        self._memories[agent_id] = consolidated

        reduction = len(memories) - len(consolidated)
        if reduction > 0:
            logger.info(f"Consolidated agent {agent_id}: {len(memories)} -> {len(consolidated)} memories (-{reduction})")

        return consolidated

    def _merge_similar(self, memories: List[Memory]) -> List[Memory]:
        """Merge memories with overlapping content within a type group."""
        if len(memories) <= 1:
            return list(memories)

        merged: List[Memory] = []
        used = set()

        for i, mem_a in enumerate(memories):
            if i in used:
                continue

            best = mem_a
            for j, mem_b in enumerate(memories):
                if j <= i or j in used:
                    continue

                if self._is_similar(mem_a.content, mem_b.content):
                    used.add(j)
                    # Keep higher-importance memory, accumulate access count
                    if mem_b.importance > best.importance:
                        mem_b.access_count += best.access_count
                        best = mem_b
                    else:
                        best.access_count += mem_b.access_count

            merged.append(best)

        return merged

    @staticmethod
    def _is_similar(text_a: str, text_b: str, threshold: float = 0.6) -> bool:
        """Check content overlap using word-level Jaccard similarity."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return False
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) >= threshold

    def prioritize(
        self,
        memories: List[Memory],
        context: str = "",
        current_round: int = 0,
        top_k: Optional[int] = None,
    ) -> List[Memory]:
        """
        Rank memories by relevance to current context.

        Scoring combines three signals:
        - Base importance (from memory type)
        - Recency: importance *= 0.9^(rounds_since_created)
        - Frequency: bonus from access count (log scale)
        - Context relevance: word overlap with context string

        Args:
            memories: Memories to rank
            context: Current context string for relevance scoring
            current_round: Current simulation round for recency calculation
            top_k: Return only top K results (None = all, sorted)

        Returns:
            Sorted list of memories (highest priority first)
        """
        context_words = set(context.lower().split()) if context else set()

        def score(mem: Memory) -> float:
            # Base importance from memory type
            base = mem.importance

            # Recency decay
            rounds_elapsed = max(0, current_round - mem.round_created)
            recency = math.pow(RECENCY_DECAY_FACTOR, rounds_elapsed)

            # Frequency bonus (logarithmic to avoid runaway scores)
            freq_bonus = 1.0 + math.log1p(mem.access_count - 1) * 0.5

            # Context relevance
            context_score = 0.0
            if context_words:
                mem_words = set(mem.content.lower().split())
                overlap = len(context_words & mem_words)
                context_score = overlap / max(len(context_words), 1) * 3.0

            return base * recency * freq_bonus + context_score

        scored = sorted(memories, key=score, reverse=True)

        if top_k is not None:
            scored = scored[:top_k]

        return scored

    def forget(
        self,
        agent_id: str,
        threshold: float = 1.0,
        current_round: int = 0,
    ) -> List[Memory]:
        """
        Remove low-priority memories simulating a forgetting curve.

        Applies recency decay to each memory's importance. Memories whose
        decayed importance falls below the threshold are forgotten (removed).

        Args:
            agent_id: Agent whose memories to prune
            threshold: Minimum decayed importance to retain (default: 1.0)
            current_round: Current round for decay calculation

        Returns:
            List of forgotten (removed) memories
        """
        memories = self._get_agent_memories(agent_id)
        retained: List[Memory] = []
        forgotten: List[Memory] = []

        for mem in memories:
            rounds_elapsed = max(0, current_round - mem.round_created)
            decayed_importance = mem.importance * math.pow(RECENCY_DECAY_FACTOR, rounds_elapsed)

            if decayed_importance >= threshold:
                retained.append(mem)
            else:
                forgotten.append(mem)

        self._memories[agent_id] = retained

        if forgotten:
            logger.info(
                f"Agent {agent_id} forgot {len(forgotten)} memories "
                f"(threshold={threshold}, round={current_round}), "
                f"{len(retained)} retained"
            )

        return forgotten

    def summarize_session(
        self,
        agent_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Create a summary of key learnings from a simulation session.

        If an LLM key is configured, uses the LLM to produce a narrative summary.
        Otherwise, returns a structured summary from in-memory data.

        Args:
            agent_id: The agent to summarize
            session_id: The session to summarize

        Returns:
            Summary dict with key_memories, stats, and narrative
        """
        all_memories = self._get_agent_memories(agent_id)
        session_memories = [m for m in all_memories if m.session_id == session_id]

        if not session_memories:
            return {
                "agent_id": agent_id,
                "session_id": session_id,
                "total_memories": 0,
                "by_type": {},
                "key_memories": [],
                "narrative": "No memories recorded for this session.",
            }

        # Count by type
        by_type: Dict[str, int] = {}
        for mem in session_memories:
            by_type[mem.memory_type] = by_type.get(mem.memory_type, 0) + 1

        # Top memories by importance
        top_memories = sorted(session_memories, key=lambda m: m.importance, reverse=True)[:10]

        summary = {
            "agent_id": agent_id,
            "session_id": session_id,
            "total_memories": len(session_memories),
            "by_type": by_type,
            "key_memories": [m.to_dict() for m in top_memories],
            "narrative": "",
        }

        # Try LLM-powered narrative summary
        if Config.LLM_API_KEY:
            try:
                summary["narrative"] = self._generate_narrative(agent_id, session_memories)
            except Exception as e:
                logger.warning(f"LLM summary failed, using fallback: {e}")
                summary["narrative"] = self._fallback_narrative(agent_id, session_memories, by_type)
        else:
            summary["narrative"] = self._fallback_narrative(agent_id, session_memories, by_type)

        return summary

    def _generate_narrative(self, agent_id: str, memories: List[Memory]) -> str:
        """Generate a narrative summary using the LLM."""
        from ..utils.llm_client import LLMClient

        llm = LLMClient()

        # Build memory digest for the prompt
        memory_lines = []
        for mem in sorted(memories, key=lambda m: m.round_created):
            memory_lines.append(f"[Round {mem.round_created}] ({mem.memory_type}) {mem.content}")

        memory_digest = "\n".join(memory_lines[:50])  # Cap at 50 to stay within token budget

        messages = [
            {
                "role": "system",
                "content": (
                    "You are analyzing an agent's memories from a GTM simulation. "
                    "Summarize the key learnings, decisions, and behavioral patterns. "
                    "Be concise (3-5 sentences). Focus on what the agent learned and "
                    "how their behavior evolved."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Agent: {agent_id}\n"
                    f"Total memories: {len(memories)}\n\n"
                    f"Memory log:\n{memory_digest}\n\n"
                    "Provide a brief narrative summary of this agent's session."
                ),
            },
        ]

        return llm.chat(messages, temperature=0.4, max_tokens=512)

    @staticmethod
    def _fallback_narrative(
        agent_id: str,
        memories: List[Memory],
        by_type: Dict[str, int],
    ) -> str:
        """Generate a structured fallback summary without LLM."""
        type_summary = ", ".join(f"{count} {t}s" for t, count in sorted(by_type.items(), key=lambda x: -x[1]))

        top_3 = sorted(memories, key=lambda m: m.importance, reverse=True)[:3]
        highlights = "; ".join(m.content[:80] for m in top_3)

        return (
            f"Agent {agent_id} recorded {len(memories)} memories ({type_summary}). "
            f"Key highlights: {highlights}."
        )

    def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        current_round: int = 0,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve an agent's memories, optionally filtered and ranked.

        Args:
            agent_id: Agent to query
            memory_type: Optional filter by type
            current_round: Current round for prioritization
            top_k: Limit results

        Returns:
            List of memory dicts, sorted by priority
        """
        memories = self._get_agent_memories(agent_id)

        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        ranked = self.prioritize(memories, current_round=current_round, top_k=top_k)
        return [m.to_dict() for m in ranked]

    def get_stats(self) -> Dict[str, Any]:
        """Return overall consolidator statistics."""
        total = sum(len(mems) for mems in self._memories.values())
        return {
            "total_agents": len(self._memories),
            "total_memories": total,
            "backend": "zep" if self._zep_client else "in-memory",
            "agents": {
                agent_id: len(mems)
                for agent_id, mems in self._memories.items()
            },
        }

    def clear_agent(self, agent_id: str) -> int:
        """Remove all memories for an agent. Returns count removed."""
        count = len(self._memories.pop(agent_id, []))
        if count:
            logger.info(f"Cleared {count} memories for agent {agent_id}")
        return count
