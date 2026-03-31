"""
Agent memory abstraction layer.

Provides a unified interface for storing and retrieving agent memories,
with automatic fallback from Zep Cloud to an in-memory backend when
ZEP_API_KEY is not configured.

Memory is scoped per-agent, per-simulation (session). Agents don't share
memories unless explicitly transferred.
"""

import threading
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.agent_memory')


@dataclass
class MemoryMessage:
    """A single message stored in agent memory."""
    agent_id: str
    session_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class MemorySearchResult:
    """Result of a semantic/keyword memory search."""
    message: MemoryMessage
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message.to_dict(),
            "score": self.score,
        }


class _InMemoryBackend:
    """
    In-memory fallback when Zep is unavailable.

    Uses a nested dict keyed by (agent_id, session_id) and simple keyword
    matching for search.
    """

    def __init__(self):
        # {agent_id: {session_id: [MemoryMessage, ...]}}
        self._store: Dict[str, Dict[str, List[MemoryMessage]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._lock = threading.Lock()

    def store_message(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryMessage:
        msg = MemoryMessage(
            agent_id=agent_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        with self._lock:
            self._store[agent_id][session_id].append(msg)
        return msg

    def get_history(
        self, agent_id: str, session_id: str, last_n: int = 10
    ) -> List[MemoryMessage]:
        with self._lock:
            messages = self._store.get(agent_id, {}).get(session_id, [])
            return list(messages[-last_n:])

    def search_memory(
        self, agent_id: str, query: str, limit: int = 5
    ) -> List[MemorySearchResult]:
        query_terms = set(query.lower().split())
        if not query_terms:
            return []

        scored: List[MemorySearchResult] = []
        with self._lock:
            sessions = self._store.get(agent_id, {})
            for messages in sessions.values():
                for msg in messages:
                    content_lower = msg.content.lower()
                    hits = sum(1 for t in query_terms if t in content_lower)
                    if hits > 0:
                        score = hits / len(query_terms)
                        scored.append(MemorySearchResult(message=msg, score=score))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:limit]

    def get_facts(self, agent_id: str) -> List[Dict[str, Any]]:
        # No fact extraction in the in-memory backend — return empty list
        return []

    def clear_memory(
        self, agent_id: str, session_id: Optional[str] = None
    ) -> None:
        with self._lock:
            if session_id:
                if agent_id in self._store:
                    self._store[agent_id].pop(session_id, None)
            else:
                self._store.pop(agent_id, None)


class _ZepBackend:
    """
    Zep Cloud v3-backed memory backend.

    Maps agent_id → Zep user, (agent_id, session_id) → Zep thread.
    Uses Zep's graph search for semantic memory search and the thread API
    for conversation history.
    """

    def __init__(self, api_key: str):
        from zep_cloud.client import Zep

        self._client = Zep(api_key=api_key)
        self._ensured_users: set = set()
        self._ensured_threads: set = set()

    def _zep_user_id(self, agent_id: str) -> str:
        return f"agent_{agent_id}"

    def _zep_thread_id(self, agent_id: str, session_id: str) -> str:
        return f"sim_{session_id}_agent_{agent_id}"

    def _ensure_user(self, agent_id: str) -> None:
        user_id = self._zep_user_id(agent_id)
        if user_id in self._ensured_users:
            return
        try:
            self._client.user.get(user_id)
        except Exception:
            try:
                self._client.user.add(user_id=user_id)
            except Exception as exc:
                logger.debug(f"User creation may have raced: {exc}")
        self._ensured_users.add(user_id)

    def _ensure_thread(self, agent_id: str, session_id: str) -> None:
        thread_id = self._zep_thread_id(agent_id, session_id)
        if thread_id in self._ensured_threads:
            return
        self._ensure_user(agent_id)
        try:
            self._client.thread.get(thread_id)
        except Exception:
            try:
                self._client.thread.create(
                    thread_id=thread_id,
                    user_id=self._zep_user_id(agent_id),
                )
            except Exception as exc:
                logger.debug(f"Thread creation may have raced: {exc}")
        self._ensured_threads.add(thread_id)

    def store_message(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryMessage:
        from zep_cloud.types import Message

        self._ensure_thread(agent_id, session_id)
        thread_id = self._zep_thread_id(agent_id, session_id)

        msg = Message(role_type=role, role=role, content=content, metadata=metadata or {})
        self._client.thread.add_messages(thread_id, messages=[msg])

        return MemoryMessage(
            agent_id=agent_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )

    def get_history(
        self, agent_id: str, session_id: str, last_n: int = 10
    ) -> List[MemoryMessage]:
        self._ensure_thread(agent_id, session_id)
        thread_id = self._zep_thread_id(agent_id, session_id)

        response = self._client.thread.get(thread_id, lastn=last_n)
        results: List[MemoryMessage] = []
        for m in response.messages or []:
            results.append(
                MemoryMessage(
                    agent_id=agent_id,
                    session_id=session_id,
                    role=getattr(m, "role", "unknown"),
                    content=getattr(m, "content", ""),
                    metadata=getattr(m, "metadata", {}) or {},
                    timestamp=str(getattr(m, "created_at", "") or ""),
                )
            )
        return results

    def search_memory(
        self, agent_id: str, query: str, limit: int = 5
    ) -> List[MemorySearchResult]:
        user_id = self._zep_user_id(agent_id)
        self._ensure_user(agent_id)

        results = self._client.graph.search(
            query=query, user_id=user_id, limit=limit, scope="edges"
        )
        out: List[MemorySearchResult] = []
        for edge in results.edges or []:
            msg = MemoryMessage(
                agent_id=agent_id,
                session_id="",
                role="system",
                content=getattr(edge, "fact", "") or getattr(edge, "name", ""),
                metadata=getattr(edge, "attributes", {}) or {},
            )
            out.append(MemorySearchResult(message=msg, score=getattr(edge, "score", 0.0)))
        return out

    def get_facts(self, agent_id: str) -> List[Dict[str, Any]]:
        user_id = self._zep_user_id(agent_id)
        self._ensure_user(agent_id)

        try:
            node_resp = self._client.user.get_node(user_id)
            node_uuid = getattr(node_resp.node, "uuid_", None) or getattr(
                node_resp.node, "uuid", None
            )
            if not node_uuid:
                return []

            edges = self._client.graph.node.get_entity_edges(node_uuid=node_uuid)
            facts: List[Dict[str, Any]] = []
            for edge in edges or []:
                fact_text = getattr(edge, "fact", "")
                if fact_text:
                    facts.append(
                        {
                            "name": getattr(edge, "name", ""),
                            "fact": fact_text,
                            "created_at": str(getattr(edge, "created_at", "") or ""),
                        }
                    )
            return facts
        except Exception as exc:
            logger.warning(f"Failed to get facts for agent {agent_id}: {exc}")
            return []

    def clear_memory(
        self, agent_id: str, session_id: Optional[str] = None
    ) -> None:
        if session_id:
            thread_id = self._zep_thread_id(agent_id, session_id)
            try:
                self._client.thread.delete(thread_id)
            except Exception as exc:
                logger.warning(f"Failed to delete Zep thread {thread_id}: {exc}")
            self._ensured_threads.discard(thread_id)
        else:
            user_id = self._zep_user_id(agent_id)
            try:
                threads = self._client.user.get_threads(user_id)
                for t in threads or []:
                    tid = getattr(t, "thread_id", None)
                    if tid:
                        self._client.thread.delete(tid)
                        self._ensured_threads.discard(tid)
            except Exception as exc:
                logger.warning(f"Failed to clear Zep threads for {user_id}: {exc}")
            self._ensured_users.discard(user_id)


class AgentMemory:
    """
    Unified agent memory interface.

    Automatically uses Zep Cloud when ZEP_API_KEY is configured,
    otherwise falls back to a thread-safe in-memory store.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or Config.ZEP_API_KEY
        if key:
            try:
                self._backend = _ZepBackend(api_key=key)
                self._backend_type = "zep"
                logger.info("AgentMemory initialized with Zep backend")
            except Exception as exc:
                logger.warning(f"Zep init failed, falling back to in-memory: {exc}")
                self._backend = _InMemoryBackend()
                self._backend_type = "memory"
        else:
            self._backend = _InMemoryBackend()
            self._backend_type = "memory"
            logger.info("AgentMemory initialized with in-memory backend (no ZEP_API_KEY)")

    @property
    def backend_type(self) -> str:
        """Returns 'zep' or 'memory'."""
        return self._backend_type

    def store_message(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryMessage:
        """Store a message in agent memory."""
        return self._backend.store_message(
            agent_id=agent_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
        )

    def get_history(
        self, agent_id: str, session_id: str, last_n: int = 10
    ) -> List[MemoryMessage]:
        """Retrieve recent messages for an agent in a session."""
        return self._backend.get_history(
            agent_id=agent_id, session_id=session_id, last_n=last_n
        )

    def search_memory(
        self, agent_id: str, query: str, limit: int = 5
    ) -> List[MemorySearchResult]:
        """Semantic search (Zep) or keyword search (in-memory) over agent memory."""
        return self._backend.search_memory(
            agent_id=agent_id, query=query, limit=limit
        )

    def get_facts(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get extracted facts about an agent (Zep only; returns [] for in-memory)."""
        return self._backend.get_facts(agent_id=agent_id)

    def clear_memory(
        self, agent_id: str, session_id: Optional[str] = None
    ) -> None:
        """
        Clear agent memory.

        If session_id is provided, clears only that session.
        Otherwise clears all sessions for the agent.
        """
        self._backend.clear_memory(agent_id=agent_id, session_id=session_id)
