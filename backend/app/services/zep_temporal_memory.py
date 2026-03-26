"""
Zep Temporal Memory Service

Leverages Zep's temporal features (timestamped episodes, fact validity windows)
to enable "time travel" — reconstructing what an agent knew at any simulation round.
Falls back to an in-memory chronological store when Zep is unavailable.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_temporal_memory')


@dataclass
class TemporalFact:
    """A fact with temporal metadata."""
    fact: str
    entity: str
    source_node: str
    target_node: str
    valid_from: str  # ISO 8601
    invalid_at: Optional[str] = None  # ISO 8601, None = still valid
    episode_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact": self.fact,
            "entity": self.entity,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "valid_from": self.valid_from,
            "invalid_at": self.invalid_at,
            "episode_ids": self.episode_ids,
        }


@dataclass
class TemporalEpisode:
    """A timestamped conversation episode."""
    uuid: str
    content: str
    created_at: str  # ISO 8601
    source: Optional[str] = None
    processed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "content": self.content,
            "created_at": self.created_at,
            "source": self.source,
            "processed": self.processed,
        }


def _round_to_iso(round_num: int, base_time: Optional[str] = None) -> str:
    """Convert a simulation round number to an ISO 8601 timestamp.

    Each round maps to 10-minute intervals from the base time.
    """
    if base_time:
        try:
            base = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
        except ValueError:
            base = datetime.now(timezone.utc)
    else:
        base = datetime.now(timezone.utc)
    from datetime import timedelta
    ts = base + timedelta(minutes=round_num * 10)
    return ts.isoformat()


class TemporalMemory:
    """Temporal memory backed by Zep's graph API with in-memory fallback.

    When Zep is available:
    - Episodes are stored with ``created_at`` timestamps via ``graph.add()``
    - Facts/edges carry ``valid_at`` / ``invalid_at`` windows
    - Episode retrieval uses ``graph.episode.get_by_graph_id()``

    When Zep is unavailable:
    - Episodes and facts are stored in dictionaries keyed by session_id
    - Simple keyword search replaces semantic search
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        self._zep_client = None
        self._zep_available = False

        if self.api_key:
            try:
                from zep_cloud.client import Zep
                self._zep_client = Zep(api_key=self.api_key)
                self._zep_available = True
                logger.info("TemporalMemory: Zep client initialized")
            except Exception as e:
                logger.warning(f"TemporalMemory: Zep unavailable, using fallback — {e}")
        else:
            logger.info("TemporalMemory: No ZEP_API_KEY, using in-memory fallback")

        # In-memory fallback stores
        self._episodes: Dict[str, List[TemporalEpisode]] = defaultdict(list)
        self._facts: Dict[str, List[TemporalFact]] = defaultdict(list)

    @property
    def is_zep_available(self) -> bool:
        return self._zep_available

    # ------------------------------------------------------------------
    # 1) add_episode — store a timestamped conversation episode
    # ------------------------------------------------------------------

    def add_episode(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a timestamped conversation episode.

        Args:
            session_id: Graph/session ID (maps to Zep graph_id).
            messages: List of ``{"role": "...", "content": "..."}`` dicts.
            timestamp: ISO 8601 timestamp. Defaults to now.

        Returns:
            Episode metadata dict with ``uuid`` and ``created_at``.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        combined = "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages
        )

        if self._zep_available:
            return self._add_episode_zep(session_id, combined, ts)
        return self._add_episode_fallback(session_id, combined, ts)

    def _add_episode_zep(self, graph_id: str, text: str, ts: str) -> Dict[str, Any]:
        try:
            episode = self._zep_client.graph.add(
                graph_id=graph_id,
                type="text",
                data=text,
                created_at=ts,
            )
            uuid = getattr(episode, 'uuid_', None) or getattr(episode, 'uuid', '')
            created = getattr(episode, 'created_at', ts)
            logger.info(f"Added Zep episode {uuid} to graph {graph_id}")
            return {"uuid": uuid, "created_at": str(created), "source": "zep"}
        except Exception as e:
            logger.error(f"Zep add_episode failed, falling back: {e}")
            return self._add_episode_fallback(graph_id, text, ts)

    def _add_episode_fallback(self, session_id: str, text: str, ts: str) -> Dict[str, Any]:
        uid = hashlib.sha256(f"{session_id}:{ts}:{text[:64]}".encode()).hexdigest()[:16]
        ep = TemporalEpisode(uuid=uid, content=text, created_at=ts, source="local")
        self._episodes[session_id].append(ep)
        self._episodes[session_id].sort(key=lambda e: e.created_at)
        return {"uuid": uid, "created_at": ts, "source": "local"}

    # ------------------------------------------------------------------
    # 2) query_at_time — retrieve facts known before a given timestamp
    # ------------------------------------------------------------------

    def query_at_time(
        self,
        session_id: str,
        query: str,
        before_timestamp: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Retrieve facts and episodes known at a specific time.

        Args:
            session_id: Graph/session ID.
            query: Search query string.
            before_timestamp: Only return facts valid before this ISO timestamp.
            limit: Max results.

        Returns:
            Dict with ``episodes`` and ``facts`` lists filtered by time.
        """
        if self._zep_available:
            return self._query_at_time_zep(session_id, query, before_timestamp, limit)
        return self._query_at_time_fallback(session_id, query, before_timestamp, limit)

    def _query_at_time_zep(
        self, graph_id: str, query: str, before: str, limit: int
    ) -> Dict[str, Any]:
        try:
            from ..utils.zep_paging import fetch_all_edges

            ep_resp = self._zep_client.graph.episode.get_by_graph_id(
                graph_id, lastn=200
            )
            episodes_raw = getattr(ep_resp, 'episodes', None) or []

            time_filtered = []
            for ep in episodes_raw:
                ep_time = str(getattr(ep, 'created_at', ''))
                if ep_time and ep_time <= before:
                    time_filtered.append(ep)

            # Keyword relevance scoring
            query_lower = query.lower()
            scored = []
            for ep in time_filtered:
                content = str(getattr(ep, 'content', ''))
                score = sum(1 for word in query_lower.split() if word in content.lower())
                if score > 0:
                    scored.append((score, ep))
            scored.sort(key=lambda x: x[0], reverse=True)

            result_episodes = []
            for _, ep in scored[:limit]:
                result_episodes.append({
                    "uuid": getattr(ep, 'uuid_', '') or getattr(ep, 'uuid', ''),
                    "content": getattr(ep, 'content', ''),
                    "created_at": str(getattr(ep, 'created_at', '')),
                })

            # Get edges valid before the cutoff
            all_edges = fetch_all_edges(self._zep_client, graph_id)
            facts = []
            for edge in all_edges:
                valid_at = str(getattr(edge, 'valid_at', '') or getattr(edge, 'created_at', ''))
                invalid_at = getattr(edge, 'invalid_at', None)
                if valid_at and valid_at <= before:
                    if invalid_at and str(invalid_at) <= before:
                        continue  # Already invalidated before our cutoff
                    fact_text = getattr(edge, 'fact', '') or ''
                    if any(w in fact_text.lower() for w in query_lower.split()) or not query.strip():
                        facts.append({
                            "fact": fact_text,
                            "edge_name": getattr(edge, 'name', ''),
                            "valid_from": valid_at,
                            "invalid_at": str(invalid_at) if invalid_at else None,
                            "source_node": getattr(edge, 'source_node_uuid', ''),
                            "target_node": getattr(edge, 'target_node_uuid', ''),
                        })

            return {
                "episodes": result_episodes,
                "facts": facts[:limit],
                "before_timestamp": before,
                "source": "zep",
            }
        except Exception as e:
            logger.error(f"Zep query_at_time failed, falling back: {e}")
            return self._query_at_time_fallback(graph_id, query, before, limit)

    def _query_at_time_fallback(
        self, session_id: str, query: str, before: str, limit: int
    ) -> Dict[str, Any]:
        query_lower = query.lower()
        eps = self._episodes.get(session_id, [])
        matched = []
        for ep in eps:
            if ep.created_at > before:
                continue
            score = sum(1 for w in query_lower.split() if w in ep.content.lower())
            if score > 0 or not query.strip():
                matched.append(ep)

        facts = [
            f for f in self._facts.get(session_id, [])
            if f.valid_from <= before
            and (f.invalid_at is None or f.invalid_at > before)
        ]

        return {
            "episodes": [e.to_dict() for e in matched[:limit]],
            "facts": [f.to_dict() for f in facts[:limit]],
            "before_timestamp": before,
            "source": "local",
        }

    # ------------------------------------------------------------------
    # 3) get_memory_evolution — show how knowledge about an entity changed
    # ------------------------------------------------------------------

    def get_memory_evolution(
        self, session_id: str, entity: str
    ) -> Dict[str, Any]:
        """Show how knowledge about an entity changed over time.

        Returns a chronological list of facts mentioning the entity,
        including when each fact became valid and when it was invalidated.

        Args:
            session_id: Graph/session ID.
            entity: Entity name to track.

        Returns:
            Dict with ``entity``, ``timeline`` (list of facts), ``source``.
        """
        if self._zep_available:
            return self._get_evolution_zep(session_id, entity)
        return self._get_evolution_fallback(session_id, entity)

    def _get_evolution_zep(self, graph_id: str, entity: str) -> Dict[str, Any]:
        try:
            from ..utils.zep_paging import fetch_all_edges, fetch_all_nodes

            nodes = fetch_all_nodes(self._zep_client, graph_id)
            entity_lower = entity.lower()

            # Find node UUIDs matching the entity name
            entity_uuids = set()
            for node in nodes:
                name = (getattr(node, 'name', '') or '').lower()
                if entity_lower in name or name in entity_lower:
                    uuid = getattr(node, 'uuid_', None) or getattr(node, 'uuid', '')
                    entity_uuids.add(uuid)

            edges = fetch_all_edges(self._zep_client, graph_id)
            timeline = []
            for edge in edges:
                src = getattr(edge, 'source_node_uuid', '')
                tgt = getattr(edge, 'target_node_uuid', '')
                fact_text = (getattr(edge, 'fact', '') or '').lower()

                if src in entity_uuids or tgt in entity_uuids or entity_lower in fact_text:
                    valid_at = str(getattr(edge, 'valid_at', '') or getattr(edge, 'created_at', ''))
                    invalid_at = getattr(edge, 'invalid_at', None)
                    expired_at = getattr(edge, 'expired_at', None)
                    timeline.append({
                        "fact": getattr(edge, 'fact', ''),
                        "edge_name": getattr(edge, 'name', ''),
                        "valid_from": valid_at,
                        "invalid_at": str(invalid_at) if invalid_at else None,
                        "expired_at": str(expired_at) if expired_at else None,
                        "is_current": invalid_at is None and expired_at is None,
                        "source_node": src,
                        "target_node": tgt,
                    })

            timeline.sort(key=lambda x: x.get("valid_from", ""))

            return {
                "entity": entity,
                "timeline": timeline,
                "total_facts": len(timeline),
                "current_facts": sum(1 for t in timeline if t["is_current"]),
                "source": "zep",
            }
        except Exception as e:
            logger.error(f"Zep get_memory_evolution failed, falling back: {e}")
            return self._get_evolution_fallback(graph_id, entity)

    def _get_evolution_fallback(self, session_id: str, entity: str) -> Dict[str, Any]:
        entity_lower = entity.lower()
        facts = self._facts.get(session_id, [])
        timeline = [
            {
                **f.to_dict(),
                "is_current": f.invalid_at is None,
            }
            for f in facts
            if entity_lower in f.entity.lower()
            or entity_lower in f.fact.lower()
        ]
        timeline.sort(key=lambda x: x.get("valid_from", ""))

        return {
            "entity": entity,
            "timeline": timeline,
            "total_facts": len(timeline),
            "current_facts": sum(1 for t in timeline if t["is_current"]),
            "source": "local",
        }

    # ------------------------------------------------------------------
    # 4) get_contradictions — identify contradictory facts in memory
    # ------------------------------------------------------------------

    def get_contradictions(self, session_id: str) -> Dict[str, Any]:
        """Identify contradictory facts in memory.

        A contradiction occurs when two edges involving the same pair of
        nodes have overlapping validity windows with different facts, or
        when a fact has been explicitly invalidated (``invalid_at`` set).

        Args:
            session_id: Graph/session ID.

        Returns:
            Dict with ``contradictions`` list and summary counts.
        """
        if self._zep_available:
            return self._get_contradictions_zep(session_id)
        return self._get_contradictions_fallback(session_id)

    def _get_contradictions_zep(self, graph_id: str) -> Dict[str, Any]:
        try:
            from ..utils.zep_paging import fetch_all_edges

            edges = fetch_all_edges(self._zep_client, graph_id)
            return self._find_contradictions(edges, source="zep")
        except Exception as e:
            logger.error(f"Zep get_contradictions failed, falling back: {e}")
            return self._get_contradictions_fallback(graph_id)

    def _get_contradictions_fallback(self, session_id: str) -> Dict[str, Any]:
        facts = self._facts.get(session_id, [])
        # Build edge-like objects from stored facts
        edges = []
        for f in facts:
            edges.append(_MockEdge(
                source_node_uuid=f.source_node,
                target_node_uuid=f.target_node,
                name=f.entity,
                fact=f.fact,
                valid_at=f.valid_from,
                invalid_at=f.invalid_at,
                created_at=f.valid_from,
            ))
        return self._find_contradictions(edges, source="local")

    @staticmethod
    def _find_contradictions(edges, source: str = "zep") -> Dict[str, Any]:
        """Detect contradictions from a list of edges.

        Groups edges by node pair and looks for:
        - Superseded facts (same relationship name, one invalidated)
        - Conflicting facts (same node pair, overlapping validity windows)
        """
        # Group by (source, target, name) to find superseded facts
        groups: Dict[tuple, list] = defaultdict(list)
        invalidated = []

        for edge in edges:
            src = getattr(edge, 'source_node_uuid', '')
            tgt = getattr(edge, 'target_node_uuid', '')
            name = getattr(edge, 'name', '') or ''
            fact = getattr(edge, 'fact', '') or ''
            valid_at = str(getattr(edge, 'valid_at', '') or getattr(edge, 'created_at', ''))
            inv_at = getattr(edge, 'invalid_at', None)

            key = (src, tgt, name.lower())
            groups[key].append({
                "fact": fact,
                "edge_name": name,
                "valid_from": valid_at,
                "invalid_at": str(inv_at) if inv_at else None,
                "source_node": src,
                "target_node": tgt,
            })

            if inv_at:
                invalidated.append({
                    "fact": fact,
                    "edge_name": name,
                    "valid_from": valid_at,
                    "invalid_at": str(inv_at),
                    "source_node": src,
                    "target_node": tgt,
                })

        contradictions = []

        # Superseded: multiple facts for same relationship
        for key, group in groups.items():
            if len(group) < 2:
                continue
            group.sort(key=lambda x: x.get("valid_from", ""))
            for i in range(len(group) - 1):
                contradictions.append({
                    "type": "superseded",
                    "old_fact": group[i],
                    "new_fact": group[i + 1],
                    "relationship": key[2],
                })

        # Explicitly invalidated facts
        for inv in invalidated:
            contradictions.append({
                "type": "invalidated",
                "fact": inv,
                "relationship": inv["edge_name"],
            })

        return {
            "contradictions": contradictions,
            "total_contradictions": len(contradictions),
            "superseded_count": sum(1 for c in contradictions if c["type"] == "superseded"),
            "invalidated_count": sum(1 for c in contradictions if c["type"] == "invalidated"),
            "source": source,
        }


class _MockEdge:
    """Minimal edge-like object for fallback contradiction detection."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
