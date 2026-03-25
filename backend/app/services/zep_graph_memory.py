"""
Zep graph memory service — builds and queries the knowledge graph.

Wraps Zep Cloud APIs for episode ingestion, graph search, entity
relationships, community summaries, and temporal fact retrieval.
Falls back to mock data when ZEP_API_KEY is not configured.
"""

import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_graph_memory')


def _is_zep_available() -> bool:
    return bool(Config.ZEP_API_KEY)


def _get_zep_client():
    """Lazy-import and create a Zep client only when ZEP_API_KEY is set."""
    from zep_cloud.client import Zep
    return Zep(api_key=Config.ZEP_API_KEY)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GraphEpisode:
    """A single episode added to the Zep graph."""
    episode_id: str
    session_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphQueryResult:
    """Result from a graph query."""
    facts: List[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    query: str
    total_count: int
    source: str  # 'zep' or 'mock'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts": self.facts,
            "nodes": self.nodes,
            "edges": self.edges,
            "query": self.query,
            "total_count": self.total_count,
            "source": self.source,
        }


@dataclass
class EntityRelationship:
    """An entity and its relationships."""
    entity_name: str
    entity_type: str
    summary: str
    relationships: List[Dict[str, Any]]
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "summary": self.summary,
            "relationships": self.relationships,
            "source": self.source,
        }


@dataclass
class CommunitySummary:
    """Community detection summary."""
    session_id: str
    communities: List[Dict[str, Any]]
    total_entities: int
    total_communities: int
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "communities": self.communities,
            "total_entities": self.total_entities,
            "total_communities": self.total_communities,
            "source": self.source,
        }


@dataclass
class TemporalFact:
    """A fact with time-range metadata."""
    fact: str
    valid_at: Optional[str]
    invalid_at: Optional[str]
    expired_at: Optional[str]
    created_at: Optional[str]
    source_entity: str
    target_entity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact": self.fact,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "expired_at": self.expired_at,
            "created_at": self.created_at,
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class GraphMemoryService:
    """
    Unified service for Zep graph memory operations.

    Maps simulation rounds to Zep episodes. Each agent message becomes
    a memory entry. When Zep is unavailable, returns mock graph data
    with pre-built entity relationships.
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds, doubles each retry

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or Config.ZEP_API_KEY
        self._client = None

    @property
    def client(self):
        if self._client is None and self._api_key:
            from zep_cloud.client import Zep
            self._client = Zep(api_key=self._api_key)
        return self._client

    @property
    def available(self) -> bool:
        return self._api_key is not None and self.client is not None

    # ------------------------------------------------------------------
    # Retry helper (matches codebase pattern)
    # ------------------------------------------------------------------

    def _call_with_retry(self, func, operation_name: str):
        last_exception = None
        delay = self.RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Zep {operation_name} attempt {attempt + 1} failed: "
                        f"{str(e)[:120]}, retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(
                        f"Zep {operation_name} failed after {self.MAX_RETRIES} "
                        f"attempts: {str(e)}"
                    )
        raise last_exception

    # ------------------------------------------------------------------
    # 1) add_episode
    # ------------------------------------------------------------------

    def add_episode(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        round_num: Optional[int] = None,
    ) -> GraphEpisode:
        """
        Add simulation conversation to Zep memory as a graph episode.

        Each message dict should have 'role' and 'content' keys.
        Messages are concatenated into a single text blob that Zep will
        parse for entity extraction.

        Args:
            session_id: The Zep graph ID (maps to a simulation).
            messages: List of message dicts with role/content.
            round_num: Optional simulation round number for metadata.

        Returns:
            GraphEpisode with the episode details.
        """
        content = "\n".join(
            f"{m.get('role', 'agent')}: {m.get('content', '')}"
            for m in messages
        )
        metadata = {"round_num": round_num} if round_num is not None else {}

        if not self.available:
            logger.info("Zep unavailable — episode stored locally only")
            ep_id = hashlib.md5(content[:200].encode()).hexdigest()[:12]
            return GraphEpisode(
                episode_id=ep_id,
                session_id=session_id,
                content=content,
                metadata=metadata,
            )

        result = self._call_with_retry(
            func=lambda: self.client.graph.add(
                graph_id=session_id,
                type="text",
                data=content,
            ),
            operation_name=f"add_episode(graph={session_id})",
        )

        ep_id = getattr(result, "uuid_", None) or getattr(result, "uuid", "") or ""
        logger.info(f"Episode added: graph={session_id}, episode={ep_id}")

        return GraphEpisode(
            episode_id=str(ep_id),
            session_id=session_id,
            content=content,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # 2) build_graph
    # ------------------------------------------------------------------

    def build_graph(self, session_id: str) -> Dict[str, Any]:
        """
        Trigger Zep's graph construction from episodes.

        Zep builds the graph asynchronously after episodes are added.
        This method returns the current graph stats, polling is left to
        the caller.

        Args:
            session_id: The Zep graph ID.

        Returns:
            Graph statistics dict.
        """
        if not self.available:
            return _mock_graph_stats(session_id)

        from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

        nodes = fetch_all_nodes(self.client, session_id)
        edges = fetch_all_edges(self.client, session_id)

        entity_types: Dict[str, int] = {}
        for node in nodes:
            for label in getattr(node, "labels", []) or []:
                if label not in ("Entity", "Node"):
                    entity_types[label] = entity_types.get(label, 0) + 1

        return {
            "graph_id": session_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "entity_types": entity_types,
            "source": "zep",
        }

    # ------------------------------------------------------------------
    # 3) query_graph
    # ------------------------------------------------------------------

    def query_graph(
        self,
        graph_id: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> GraphQueryResult:
        """
        Search the knowledge graph with natural language.

        Uses Zep's hybrid search (semantic + BM25) with cross-encoder
        reranking. Falls back to mock data when Zep is unavailable.

        Args:
            graph_id: The Zep graph ID.
            query: Natural language search query.
            filters: Optional filters (currently unused by Zep Cloud).
            limit: Maximum results to return.

        Returns:
            GraphQueryResult with facts, nodes, edges.
        """
        if not self.available:
            return _mock_query_result(query)

        try:
            search_results = self._call_with_retry(
                func=lambda: self.client.graph.search(
                    graph_id=graph_id,
                    query=query,
                    limit=limit,
                    scope="edges",
                    reranker="cross_encoder",
                ),
                operation_name=f"query_graph(graph={graph_id})",
            )

            facts = []
            edges = []
            nodes = []

            if hasattr(search_results, "edges") and search_results.edges:
                for edge in search_results.edges:
                    fact = getattr(edge, "fact", "")
                    if fact:
                        facts.append(fact)
                    edges.append({
                        "uuid": getattr(edge, "uuid_", None) or getattr(edge, "uuid", ""),
                        "name": getattr(edge, "name", ""),
                        "fact": fact,
                        "source_node_uuid": getattr(edge, "source_node_uuid", ""),
                        "target_node_uuid": getattr(edge, "target_node_uuid", ""),
                    })

            if hasattr(search_results, "nodes") and search_results.nodes:
                for node in search_results.nodes:
                    nodes.append({
                        "uuid": getattr(node, "uuid_", None) or getattr(node, "uuid", ""),
                        "name": getattr(node, "name", ""),
                        "labels": getattr(node, "labels", []),
                        "summary": getattr(node, "summary", ""),
                    })
                    summary = getattr(node, "summary", "")
                    if summary:
                        facts.append(f"[{node.name}]: {summary}")

            return GraphQueryResult(
                facts=facts,
                nodes=nodes,
                edges=edges,
                query=query,
                total_count=len(facts),
                source="zep",
            )

        except Exception as e:
            logger.warning(f"query_graph failed, returning mock data: {e}")
            return _mock_query_result(query)

    # ------------------------------------------------------------------
    # 4) get_entity_relationships
    # ------------------------------------------------------------------

    def get_entity_relationships(
        self,
        graph_id: str,
        entity_name: str,
    ) -> EntityRelationship:
        """
        Return all relationships for a named entity.

        Args:
            graph_id: The Zep graph ID.
            entity_name: The entity to look up.

        Returns:
            EntityRelationship with the entity info and its edges.
        """
        if not self.available:
            return _mock_entity_relationships(entity_name)

        from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

        all_nodes = fetch_all_nodes(self.client, graph_id)
        target_node = None
        for node in all_nodes:
            if (getattr(node, "name", "") or "").lower() == entity_name.lower():
                target_node = node
                break

        if target_node is None:
            return EntityRelationship(
                entity_name=entity_name,
                entity_type="Unknown",
                summary="Entity not found in graph",
                relationships=[],
                source="zep",
            )

        node_uuid = getattr(target_node, "uuid_", None) or getattr(target_node, "uuid", "")
        node_labels = getattr(target_node, "labels", []) or []
        entity_type = next((l for l in node_labels if l not in ("Entity", "Node")), "Entity")
        summary = getattr(target_node, "summary", "") or ""

        # Build a uuid→name lookup for readable relationship output
        uuid_to_name: Dict[str, str] = {}
        for n in all_nodes:
            n_uuid = getattr(n, "uuid_", None) or getattr(n, "uuid", "")
            uuid_to_name[str(n_uuid)] = getattr(n, "name", "") or ""

        all_edges = fetch_all_edges(self.client, graph_id)
        relationships = []
        for edge in all_edges:
            src = edge.source_node_uuid or ""
            tgt = edge.target_node_uuid or ""
            if str(node_uuid) in (str(src), str(tgt)):
                relationships.append({
                    "name": getattr(edge, "name", ""),
                    "fact": getattr(edge, "fact", ""),
                    "direction": "outgoing" if str(src) == str(node_uuid) else "incoming",
                    "related_entity": uuid_to_name.get(
                        str(tgt) if str(src) == str(node_uuid) else str(src), ""
                    ),
                })

        return EntityRelationship(
            entity_name=entity_name,
            entity_type=entity_type,
            summary=summary,
            relationships=relationships,
            source="zep",
        )

    # ------------------------------------------------------------------
    # 5) get_community_summary
    # ------------------------------------------------------------------

    def get_community_summary(self, session_id: str) -> CommunitySummary:
        """
        Return Zep's community detection summary for the graph.

        Zep auto-detects communities (clusters of densely connected
        entities). This method groups nodes by label and returns cluster
        statistics with representative members.

        Args:
            session_id: The Zep graph ID.

        Returns:
            CommunitySummary with detected communities.
        """
        if not self.available:
            return _mock_community_summary(session_id)

        from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

        all_nodes = fetch_all_nodes(self.client, session_id)
        all_edges = fetch_all_edges(self.client, session_id)

        # Group nodes by their primary label (community proxy)
        label_groups: Dict[str, List[Dict[str, Any]]] = {}
        for node in all_nodes:
            labels = getattr(node, "labels", []) or []
            primary = next((l for l in labels if l not in ("Entity", "Node")), "Other")
            if primary not in label_groups:
                label_groups[primary] = []
            label_groups[primary].append({
                "name": getattr(node, "name", ""),
                "summary": getattr(node, "summary", ""),
            })

        communities = []
        for label, members in label_groups.items():
            communities.append({
                "label": label,
                "member_count": len(members),
                "members": members[:10],  # cap preview
            })

        return CommunitySummary(
            session_id=session_id,
            communities=communities,
            total_entities=len(all_nodes),
            total_communities=len(communities),
            source="zep",
        )

    # ------------------------------------------------------------------
    # 6) get_temporal_facts
    # ------------------------------------------------------------------

    def get_temporal_facts(
        self,
        session_id: str,
        time_range: Optional[Dict[str, str]] = None,
    ) -> List[TemporalFact]:
        """
        Return facts from a specific time window.

        Filters edges by their valid_at / invalid_at / expired_at fields
        within the requested range.

        Args:
            session_id: The Zep graph ID.
            time_range: Optional dict with 'start' and/or 'end' ISO
                        timestamps. If omitted, returns all temporal facts.

        Returns:
            List of TemporalFact objects.
        """
        if not self.available:
            return _mock_temporal_facts(session_id)

        from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

        all_edges = fetch_all_edges(self.client, session_id)
        all_nodes = fetch_all_nodes(self.client, session_id)

        uuid_to_name: Dict[str, str] = {}
        for n in all_nodes:
            n_uuid = getattr(n, "uuid_", None) or getattr(n, "uuid", "")
            uuid_to_name[str(n_uuid)] = getattr(n, "name", "") or ""

        start = time_range.get("start") if time_range else None
        end = time_range.get("end") if time_range else None

        results: List[TemporalFact] = []
        for edge in all_edges:
            valid_at = _to_str(getattr(edge, "valid_at", None))
            invalid_at = _to_str(getattr(edge, "invalid_at", None))
            expired_at = _to_str(getattr(edge, "expired_at", None))
            created_at = _to_str(getattr(edge, "created_at", None))

            # Time-range filtering: use valid_at as the primary timestamp
            if start and valid_at and valid_at < start:
                continue
            if end and valid_at and valid_at > end:
                continue

            src_uuid = str(edge.source_node_uuid or "")
            tgt_uuid = str(edge.target_node_uuid or "")

            results.append(TemporalFact(
                fact=getattr(edge, "fact", "") or "",
                valid_at=valid_at,
                invalid_at=invalid_at,
                expired_at=expired_at,
                created_at=created_at,
                source_entity=uuid_to_name.get(src_uuid, src_uuid[:8]),
                target_entity=uuid_to_name.get(tgt_uuid, tgt_uuid[:8]),
            ))

        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_str(val) -> Optional[str]:
    """Convert a datetime or string value to ISO string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


# ---------------------------------------------------------------------------
# Mock data for demo/offline mode
# ---------------------------------------------------------------------------

_MOCK_ENTITIES = [
    {"name": "Intercom", "type": "Product", "summary": "AI-first customer service platform with Fin AI agent"},
    {"name": "Fin AI", "type": "Product", "summary": "Intercom's AI agent for automated customer support resolution"},
    {"name": "Zendesk", "type": "Competitor", "summary": "Legacy customer service platform, largest incumbent"},
    {"name": "Freshdesk", "type": "Competitor", "summary": "Mid-market customer service platform by Freshworks"},
    {"name": "HubSpot", "type": "Competitor", "summary": "CRM and service hub with growing support capabilities"},
    {"name": "Sarah Chen", "type": "Person", "summary": "VP of Customer Support at TechCorp, evaluating AI solutions"},
    {"name": "Marcus Rodriguez", "type": "Person", "summary": "CX Director at FinanceFlow, piloting Intercom Fin"},
    {"name": "AI Resolution Rate", "type": "Metric", "summary": "Key metric: percentage of tickets resolved by AI without human handoff"},
    {"name": "Customer Satisfaction", "type": "Metric", "summary": "CSAT score tracking across support channels"},
    {"name": "Support Ticket Volume", "type": "Metric", "summary": "Monthly inbound support request count"},
]

_MOCK_RELATIONSHIPS = [
    {"source": "Sarah Chen", "target": "Intercom", "name": "evaluates", "fact": "Sarah Chen is evaluating Intercom for enterprise support transformation"},
    {"source": "Sarah Chen", "target": "Zendesk", "name": "currently_uses", "fact": "Sarah Chen's team currently uses Zendesk but is frustrated with limitations"},
    {"source": "Marcus Rodriguez", "target": "Fin AI", "name": "pilots", "fact": "Marcus Rodriguez is running a Fin AI pilot with 47% resolution rate"},
    {"source": "Fin AI", "target": "AI Resolution Rate", "name": "measures", "fact": "Fin AI achieves 47% automated resolution in pilot deployments"},
    {"source": "Intercom", "target": "Zendesk", "name": "competes_with", "fact": "Intercom positions against Zendesk with AI-first approach"},
    {"source": "Intercom", "target": "Freshdesk", "name": "competes_with", "fact": "Intercom differentiates from Freshdesk through deeper AI integration"},
    {"source": "Intercom", "target": "Customer Satisfaction", "name": "improves", "fact": "Intercom deployments show 15-20% CSAT improvement over legacy tools"},
    {"source": "Fin AI", "target": "Support Ticket Volume", "name": "reduces", "fact": "Fin AI reduces human-handled ticket volume by 30-50% in production"},
    {"source": "Marcus Rodriguez", "target": "Customer Satisfaction", "name": "tracks", "fact": "Marcus Rodriguez tracks CSAT weekly during the Intercom pilot"},
    {"source": "HubSpot", "target": "Intercom", "name": "competes_with", "fact": "HubSpot Service Hub competes with Intercom in mid-market segment"},
]


def _mock_graph_stats(session_id: str) -> Dict[str, Any]:
    entity_types: Dict[str, int] = {}
    for e in _MOCK_ENTITIES:
        t = e["type"]
        entity_types[t] = entity_types.get(t, 0) + 1
    return {
        "graph_id": session_id,
        "node_count": len(_MOCK_ENTITIES),
        "edge_count": len(_MOCK_RELATIONSHIPS),
        "entity_types": entity_types,
        "source": "mock",
    }


def _mock_query_result(query: str) -> GraphQueryResult:
    query_lower = query.lower()
    matched_facts = []
    matched_edges = []
    for rel in _MOCK_RELATIONSHIPS:
        text = f"{rel['source']} {rel['target']} {rel['fact']}".lower()
        if any(kw in text for kw in query_lower.split()):
            matched_facts.append(rel["fact"])
            matched_edges.append({
                "name": rel["name"],
                "fact": rel["fact"],
                "source_entity": rel["source"],
                "target_entity": rel["target"],
            })

    if not matched_facts:
        matched_facts = [r["fact"] for r in _MOCK_RELATIONSHIPS[:5]]
        matched_edges = [
            {"name": r["name"], "fact": r["fact"], "source_entity": r["source"], "target_entity": r["target"]}
            for r in _MOCK_RELATIONSHIPS[:5]
        ]

    matched_nodes = [
        {"name": e["name"], "type": e["type"], "summary": e["summary"]}
        for e in _MOCK_ENTITIES
        if any(kw in e["name"].lower() or kw in e["summary"].lower() for kw in query_lower.split())
    ] or [{"name": e["name"], "type": e["type"], "summary": e["summary"]} for e in _MOCK_ENTITIES[:5]]

    return GraphQueryResult(
        facts=matched_facts,
        nodes=matched_nodes,
        edges=matched_edges,
        query=query,
        total_count=len(matched_facts),
        source="mock",
    )


def _mock_entity_relationships(entity_name: str) -> EntityRelationship:
    name_lower = entity_name.lower()
    entity_info = next(
        (e for e in _MOCK_ENTITIES if e["name"].lower() == name_lower),
        {"name": entity_name, "type": "Unknown", "summary": "Entity not found"},
    )
    relationships = []
    for rel in _MOCK_RELATIONSHIPS:
        if rel["source"].lower() == name_lower:
            relationships.append({
                "name": rel["name"],
                "fact": rel["fact"],
                "direction": "outgoing",
                "related_entity": rel["target"],
            })
        elif rel["target"].lower() == name_lower:
            relationships.append({
                "name": rel["name"],
                "fact": rel["fact"],
                "direction": "incoming",
                "related_entity": rel["source"],
            })

    return EntityRelationship(
        entity_name=entity_info["name"],
        entity_type=entity_info["type"],
        summary=entity_info["summary"],
        relationships=relationships,
        source="mock",
    )


def _mock_community_summary(session_id: str) -> CommunitySummary:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for e in _MOCK_ENTITIES:
        t = e["type"]
        if t not in groups:
            groups[t] = []
        groups[t].append({"name": e["name"], "summary": e["summary"]})

    communities = [
        {"label": label, "member_count": len(members), "members": members}
        for label, members in groups.items()
    ]
    return CommunitySummary(
        session_id=session_id,
        communities=communities,
        total_entities=len(_MOCK_ENTITIES),
        total_communities=len(communities),
        source="mock",
    )


def _mock_temporal_facts(session_id: str) -> List[TemporalFact]:
    results = []
    for i, rel in enumerate(_MOCK_RELATIONSHIPS):
        results.append(TemporalFact(
            fact=rel["fact"],
            valid_at=f"2026-03-{10 + i:02d}T00:00:00",
            invalid_at=None,
            expired_at=None,
            created_at=f"2026-03-{10 + i:02d}T00:00:00",
            source_entity=rel["source"],
            target_entity=rel["target"],
        ))
    return results
