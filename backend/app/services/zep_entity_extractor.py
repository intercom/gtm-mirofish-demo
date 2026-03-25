"""
Zep entity extraction service
Extracts structured entities from simulation interactions (agent messages/actions).
Uses Zep's built-in entity extraction when available, falls back to regex-based extraction.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_entity_extractor')

# Entity types extracted from simulation messages
ENTITY_TYPES = ["Person", "Company", "Product", "Metric", "Decision", "Risk", "Opportunity"]


@dataclass
class ExtractedEntity:
    """A single entity extracted from simulation text."""
    name: str
    type: str
    first_mentioned_round: int
    mention_count: int = 1
    associated_agents: List[str] = field(default_factory=list)
    sentiment_context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "first_mentioned_round": self.first_mentioned_round,
            "mention_count": self.mention_count,
            "associated_agents": self.associated_agents,
            "sentiment_context": self.sentiment_context,
        }


@dataclass
class EntityMap:
    """Complete entity map built from simulation rounds."""
    simulation_id: str
    entities: Dict[str, ExtractedEntity] = field(default_factory=dict)
    rounds_processed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "entity_count": len(self.entities),
            "rounds_processed": self.rounds_processed,
            "by_type": self._group_by_type(),
        }

    def _group_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for entity in self.entities.values():
            grouped.setdefault(entity.type, []).append(entity.to_dict())
        return grouped


# Regex patterns for fallback entity extraction.
# Order matters: specific types must precede the general Person catch-all,
# so that e.g. "Acme Corp" → Company and "launched Azure Pro" → Product.
_PATTERNS: Dict[str, re.Pattern] = {
    "Company": re.compile(
        r"[A-Z][A-Za-z&]+(?:\s+[A-Z][A-Za-z&]+)*"
        r"\s+(?:Inc\.?|Corp\.?|LLC|Ltd\.?|Co\.?|Group|Technologies|Solutions|Partners|Enterprises)"
    ),
    "Product": re.compile(
        r"(?:launched|released|announced|introduced|using|adopted|deployed|integrated)\s+"
        r"([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})",
    ),
    "Metric": re.compile(
        r"\$[\d,.]+[BMKbmk]?"
        r"|[\d,.]+\s*%"
        r"|(?:revenue|profit|growth|ARR|MRR|NPS|CSAT|CAC|LTV|churn|conversion)\s*(?:of|at|:)?\s*[\d,.]+[BMKbmk%]?"
        r"|[\d,.]+[BMKbmk]?\s+(?:users|customers|subscribers|downloads|installs|sessions)",
        re.IGNORECASE,
    ),
    "Decision": re.compile(
        r"(?:decided|approved|committed|agreed|resolved|chose|elected|voted)\s+to\s+[^.!?]{5,80}",
        re.IGNORECASE,
    ),
    "Risk": re.compile(
        r"(?:risk|threat|vulnerability|concern|warning|danger|exposure)(?:\s+(?:of|that|from|regarding))?\s+[^.!?]{5,60}",
        re.IGNORECASE,
    ),
    "Opportunity": re.compile(
        r"(?:opportunity|potential|upside|prospect|chance)(?:\s+(?:to|for|in|of))?\s+[^.!?]{5,60}",
        re.IGNORECASE,
    ),
    "Person": re.compile(
        r"(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*"
        r"|(?<![.\w])[A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){1,3}(?!\w)"
    ),
}


class EntityExtractor:
    """
    Extracts entities from simulation interactions.

    Uses Zep's graph search when a ZEP_API_KEY is configured;
    falls back to regex-based extraction otherwise.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        self._zep_client = None
        if self.api_key:
            try:
                from zep_cloud.client import Zep
                self._zep_client = Zep(api_key=self.api_key)
                logger.info("EntityExtractor initialized with Zep client")
            except Exception as e:
                logger.warning(f"Failed to initialize Zep client, using regex fallback: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_message(
        self,
        message: str,
        agent_name: str,
        round_num: int = 0,
        graph_id: Optional[str] = None,
    ) -> List[ExtractedEntity]:
        """
        Extract entities from a single agent message.

        Args:
            message: The text content of the agent's action/message.
            agent_name: Name of the agent that produced the message.
            round_num: Simulation round number.
            graph_id: Optional Zep graph ID for graph-backed extraction.

        Returns:
            List of extracted entities.
        """
        if not message or not message.strip():
            return []

        if self._zep_client and graph_id:
            try:
                return self._extract_via_zep(message, agent_name, round_num, graph_id)
            except Exception as e:
                logger.warning(f"Zep extraction failed, falling back to regex: {e}")

        return self._extract_via_regex(message, agent_name, round_num)

    def extract_from_round(
        self,
        round_data: Dict[str, Any],
        graph_id: Optional[str] = None,
    ) -> List[ExtractedEntity]:
        """
        Extract entities from all actions in a simulation round.

        Args:
            round_data: A round dict with ``round_num`` and ``actions`` keys
                        (matches ``RoundSummary.to_dict()`` format).
            graph_id: Optional Zep graph ID.

        Returns:
            Deduplicated list of entities found in this round.
        """
        round_num = round_data.get("round_num", 0)
        actions = round_data.get("actions", [])
        entity_map: Dict[str, ExtractedEntity] = {}

        for action in actions:
            text = self._text_from_action(action)
            if not text:
                continue

            agent_name = action.get("agent_name", "unknown")
            entities = self.extract_from_message(text, agent_name, round_num, graph_id)

            for entity in entities:
                key = f"{entity.type}::{entity.name}"
                if key in entity_map:
                    existing = entity_map[key]
                    existing.mention_count += 1
                    if agent_name not in existing.associated_agents:
                        existing.associated_agents.append(agent_name)
                else:
                    entity_map[key] = entity

        return list(entity_map.values())

    def build_entity_map(
        self,
        simulation_id: str,
        rounds: List[Dict[str, Any]],
        graph_id: Optional[str] = None,
    ) -> EntityMap:
        """
        Build a complete entity map across all simulation rounds.

        Args:
            simulation_id: Unique simulation identifier.
            rounds: List of round dicts (``RoundSummary.to_dict()`` format).
            graph_id: Optional Zep graph ID.

        Returns:
            EntityMap aggregating all entities across rounds.
        """
        entity_map = EntityMap(simulation_id=simulation_id)

        for round_data in rounds:
            round_entities = self.extract_from_round(round_data, graph_id)
            for entity in round_entities:
                key = f"{entity.type}::{entity.name}"
                if key in entity_map.entities:
                    existing = entity_map.entities[key]
                    existing.mention_count += entity.mention_count
                    for agent in entity.associated_agents:
                        if agent not in existing.associated_agents:
                            existing.associated_agents.append(agent)
                    if not existing.sentiment_context and entity.sentiment_context:
                        existing.sentiment_context = entity.sentiment_context
                else:
                    entity_map.entities[key] = entity

            entity_map.rounds_processed += 1

        logger.info(
            f"Entity map built for simulation {simulation_id}: "
            f"{len(entity_map.entities)} entities from {entity_map.rounds_processed} rounds"
        )
        return entity_map

    # ------------------------------------------------------------------
    # Private: Zep-backed extraction
    # ------------------------------------------------------------------

    def _extract_via_zep(
        self,
        message: str,
        agent_name: str,
        round_num: int,
        graph_id: str,
    ) -> List[ExtractedEntity]:
        """Use Zep graph search to identify entities mentioned in the message."""
        results = self._zep_client.graph.search(
            graph_ids=[graph_id],
            query=message,
            limit=10,
        )

        entities: List[ExtractedEntity] = []
        seen_names: set = set()

        if results and hasattr(results, "edges"):
            for edge in results.edges or []:
                for node_name in [
                    getattr(edge, "source_node_name", None),
                    getattr(edge, "target_node_name", None),
                ]:
                    if not node_name or node_name in seen_names:
                        continue
                    if node_name.lower() in message.lower():
                        seen_names.add(node_name)
                        entity_type = self._infer_type_from_name(node_name, message)
                        entities.append(
                            ExtractedEntity(
                                name=node_name,
                                type=entity_type,
                                first_mentioned_round=round_num,
                                associated_agents=[agent_name],
                                sentiment_context=self._extract_sentiment(node_name, message),
                            )
                        )

        if results and hasattr(results, "nodes"):
            for node in results.nodes or []:
                node_name = getattr(node, "name", None)
                if not node_name or node_name in seen_names:
                    continue
                if node_name.lower() in message.lower():
                    seen_names.add(node_name)
                    labels = getattr(node, "labels", []) or []
                    entity_type = self._type_from_labels(labels)
                    entities.append(
                        ExtractedEntity(
                            name=node_name,
                            type=entity_type,
                            first_mentioned_round=round_num,
                            associated_agents=[agent_name],
                            sentiment_context=self._extract_sentiment(node_name, message),
                        )
                    )

        return entities

    # ------------------------------------------------------------------
    # Private: Regex-based fallback extraction
    # ------------------------------------------------------------------

    def _extract_via_regex(
        self,
        message: str,
        agent_name: str,
        round_num: int,
    ) -> List[ExtractedEntity]:
        """Extract entities using regex patterns when Zep is unavailable."""
        entities: List[ExtractedEntity] = []
        seen: set = set()

        for entity_type, pattern in _PATTERNS.items():
            for match in pattern.finditer(message):
                # Product pattern uses a capture group
                name = (match.group(1) if match.lastindex else match.group(0)).strip()
                if len(name) < 2 or name in seen:
                    continue
                # Skip common false positives
                if name.lower() in _STOPWORDS:
                    continue
                seen.add(name)
                entities.append(
                    ExtractedEntity(
                        name=name,
                        type=entity_type,
                        first_mentioned_round=round_num,
                        associated_agents=[agent_name],
                        sentiment_context=self._extract_sentiment(name, message),
                    )
                )

        return entities

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _text_from_action(action: Dict[str, Any]) -> str:
        """Pull the most relevant text from an agent action dict."""
        args = action.get("action_args", {})
        parts = []
        for key in ("content", "comment", "post_content"):
            val = args.get(key)
            if val:
                parts.append(val)
        result = action.get("result")
        if result:
            parts.append(result)
        return " ".join(parts)

    @staticmethod
    def _type_from_labels(labels: List[str]) -> str:
        """Map Zep node labels to our entity types."""
        label_map = {
            "Person": "Person",
            "Organization": "Company",
            "Company": "Company",
            "Product": "Product",
            "University": "Company",
            "GovernmentAgency": "Company",
            "MediaOutlet": "Company",
        }
        for label in labels:
            if label in label_map:
                return label_map[label]
        return "Person"

    @staticmethod
    def _infer_type_from_name(name: str, context: str) -> str:
        """Best-effort type inference from name and surrounding context."""
        company_signals = re.compile(
            r"(?:Inc|Corp|LLC|Ltd|Co|Group|Technologies|Solutions|Partners)\b", re.IGNORECASE
        )
        if company_signals.search(name):
            return "Company"

        metric_signals = re.compile(r"\$|%|\d{2,}")
        if metric_signals.search(name):
            return "Metric"

        return "Person"

    @staticmethod
    def _extract_sentiment(entity_name: str, message: str) -> str:
        """Extract a brief sentiment context around the entity mention."""
        idx = message.lower().find(entity_name.lower())
        if idx == -1:
            return ""
        start = max(0, idx - 40)
        end = min(len(message), idx + len(entity_name) + 40)
        return message[start:end].strip()


# Common words that should not be extracted as Person entities
_STOPWORDS = frozenset({
    "the", "this", "that", "they", "their", "there", "then", "than",
    "what", "when", "where", "which", "while", "with", "will", "would",
    "have", "has", "had", "been", "being", "some", "such", "just",
    "also", "into", "over", "only", "very", "more", "most", "much",
    "many", "each", "every", "both", "few", "all", "any", "other",
    "about", "after", "before", "between", "through", "during",
    "however", "although", "because", "since", "could", "should",
    "from", "here", "how", "but", "not", "our", "out", "now",
    "new", "may", "let", "one", "two", "three", "its",
    # Common action words that appear capitalized at sentence start
    "Posted", "Liked", "Shared", "Commented", "Replied", "Followed",
    "Created", "Updated", "Deleted", "Searched", "Viewed",
})
