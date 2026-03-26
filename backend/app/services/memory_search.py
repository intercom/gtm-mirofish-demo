"""
Memory search and retrieval service.
Searches agent memories stored in the Zep knowledge graph.
"""

import re
from collections import Counter
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.memory_search')


# Memory type keywords for classification
MEMORY_TYPE_KEYWORDS = {
    'facts': ['是', '有', '属于', '包含', 'is', 'has', 'was', 'contains', '名为', '位于'],
    'beliefs': ['认为', '觉得', '相信', '支持', '反对', 'believes', 'thinks', 'feels',
                '态度', '观点', '倾向', '偏好', '喜欢', '讨厌'],
    'decisions': ['决定', '选择', '关注', '屏蔽', '发布', '转发', '点赞', '评论',
                  'decided', 'chose', 'followed', 'muted', 'posted', 'liked',
                  '搜索', '引用', '踩'],
}

# Stop words for topic extraction (Chinese + English)
STOP_WORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '让', '给',
    'the', 'a', 'an', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
    'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'only', 'own', 'same', 'than',
    'too', 'very', 'just', 'because', 'if', 'when', 'where', 'how',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his',
    'she', 'her', 'it', 'its', 'they', 'them', 'their',
}


@dataclass
class MemoryItem:
    """A single memory from the knowledge graph."""
    id: str
    content: str
    agent_name: str
    memory_type: str  # facts, beliefs, decisions
    importance: float  # 0.0 - 1.0
    source_round: Optional[int]
    timestamp: Optional[str]
    source_node: Optional[str] = None
    target_node: Optional[str] = None
    edge_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'agent_name': self.agent_name,
            'memory_type': self.memory_type,
            'importance': self.importance,
            'source_round': self.source_round,
            'timestamp': self.timestamp,
            'source_node': self.source_node,
            'target_node': self.target_node,
            'edge_name': self.edge_name,
        }


def classify_memory_type(text: str) -> str:
    """Classify a fact/edge text into a memory type."""
    scores = {mtype: 0 for mtype in MEMORY_TYPE_KEYWORDS}
    text_lower = text.lower()
    for mtype, keywords in MEMORY_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[mtype] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'facts'


def estimate_importance(text: str, query: str = '') -> float:
    """Estimate importance of a memory based on content length and query match."""
    base = min(len(text) / 200.0, 0.6)
    if query:
        query_lower = query.lower()
        text_lower = text.lower()
        if query_lower in text_lower:
            base += 0.3
        else:
            keywords = [w for w in query_lower.split() if len(w) > 1]
            matches = sum(1 for kw in keywords if kw in text_lower)
            if keywords:
                base += 0.3 * (matches / len(keywords))
    return round(min(base + 0.1, 1.0), 2)


def extract_round_from_text(text: str) -> Optional[int]:
    """Try to extract round number from memory text."""
    patterns = [r'round\s*(\d+)', r'第(\d+)轮', r'R(\d+)']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_agent_from_fact(fact: str) -> Optional[str]:
    """Extract agent name from a fact string (format: 'AgentName: did something')."""
    if ':' in fact and fact.index(':') < 40:
        return fact[:fact.index(':')].strip()
    return None


def extract_topics(facts: List[str], top_n: int = 30) -> List[Dict[str, Any]]:
    """Extract topic words and their frequencies from a list of facts."""
    word_counter = Counter()
    for fact in facts:
        # Split on non-word chars, keeping Chinese chars
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', fact)
        for word in words:
            w = word.lower()
            if w not in STOP_WORDS and len(w) >= 2:
                word_counter[w] += 1

    topics = []
    for word, count in word_counter.most_common(top_n):
        topics.append({'text': word, 'count': count})
    return topics


# Demo/mock data for when Zep is not configured
MOCK_AGENTS = [
    'Sarah Chen', 'Marcus Johnson', 'Emily Rodriguez', 'David Kim',
    'Alex Thompson', 'Lisa Wang', 'James Miller', 'Priya Patel',
]

MOCK_MEMORIES = [
    {'content': 'Sarah Chen posted about AI-driven GTM strategies and received positive engagement',
     'agent': 'Sarah Chen', 'type': 'decisions', 'importance': 0.85, 'round': 3},
    {'content': 'Marcus Johnson believes that product-led growth is more effective than sales-led for SaaS startups',
     'agent': 'Marcus Johnson', 'type': 'beliefs', 'importance': 0.72, 'round': 2},
    {'content': 'Emily Rodriguez is a senior product manager at a mid-stage B2B company',
     'agent': 'Emily Rodriguez', 'type': 'facts', 'importance': 0.60, 'round': 1},
    {'content': 'David Kim decided to follow Sarah Chen after reading her post on competitive positioning',
     'agent': 'David Kim', 'type': 'decisions', 'importance': 0.78, 'round': 4},
    {'content': 'Alex Thompson thinks enterprise sales cycles are getting shorter due to self-serve tools',
     'agent': 'Alex Thompson', 'type': 'beliefs', 'importance': 0.65, 'round': 2},
    {'content': 'Lisa Wang liked Marcus Johnson\'s post about developer experience metrics',
     'agent': 'Lisa Wang', 'type': 'decisions', 'importance': 0.55, 'round': 5},
    {'content': 'James Miller has 8 years of experience in B2B marketing automation',
     'agent': 'James Miller', 'type': 'facts', 'importance': 0.50, 'round': 1},
    {'content': 'Priya Patel believes that community-led growth is the future of developer tools marketing',
     'agent': 'Priya Patel', 'type': 'beliefs', 'importance': 0.88, 'round': 3},
    {'content': 'Sarah Chen reposted Emily Rodriguez\'s analysis of PLG conversion funnels',
     'agent': 'Sarah Chen', 'type': 'decisions', 'importance': 0.70, 'round': 6},
    {'content': 'Marcus Johnson searched for competitive intelligence tools and compared options',
     'agent': 'Marcus Johnson', 'type': 'decisions', 'importance': 0.62, 'round': 4},
    {'content': 'David Kim is a VP of Sales at a Series B fintech startup',
     'agent': 'David Kim', 'type': 'facts', 'importance': 0.58, 'round': 1},
    {'content': 'Alex Thompson commented on the importance of aligning sales and marketing metrics',
     'agent': 'Alex Thompson', 'type': 'decisions', 'importance': 0.75, 'round': 5},
    {'content': 'Lisa Wang believes that personalization at scale requires better data infrastructure',
     'agent': 'Lisa Wang', 'type': 'beliefs', 'importance': 0.80, 'round': 3},
    {'content': 'Priya Patel decided to mute accounts posting low-quality growth hacking content',
     'agent': 'Priya Patel', 'type': 'decisions', 'importance': 0.45, 'round': 7},
    {'content': 'James Miller posted a thread about measuring ROI of brand marketing in B2B',
     'agent': 'James Miller', 'type': 'decisions', 'importance': 0.82, 'round': 6},
]


class MemorySearchService:
    """Search and retrieve agent memories from the Zep knowledge graph."""

    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        self._zep_available = bool(Config.ZEP_API_KEY)

    def search(
        self,
        query: str = '',
        agent_name: Optional[str] = None,
        memory_type: Optional[str] = None,
        sort_by: str = 'relevance',
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Search agent memories.

        Args:
            query: Search text (empty returns all)
            agent_name: Filter by agent name
            memory_type: Filter by type (facts/beliefs/decisions)
            sort_by: 'relevance' or 'chronological'
            limit: Max results

        Returns:
            Dict with 'memories' list and 'total' count
        """
        if not self._zep_available:
            return self._search_mock(query, agent_name, memory_type, sort_by, limit)

        return self._search_zep(query, agent_name, memory_type, sort_by, limit)

    def get_agents(self) -> List[str]:
        """Get list of agent names from the graph."""
        if not self._zep_available:
            return MOCK_AGENTS

        try:
            from .zep_entity_reader import ZepEntityReader
            reader = ZepEntityReader()
            all_nodes = reader.get_all_nodes(self.graph_id)
            agents = set()
            for node in all_nodes:
                labels = node.get('labels', [])
                custom = [l for l in labels if l not in ('Entity', 'Node')]
                if custom:
                    agents.add(node.get('name', ''))
            return sorted(a for a in agents if a)
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            return MOCK_AGENTS

    def get_topics(self, agent_name: Optional[str] = None, top_n: int = 30) -> List[Dict[str, Any]]:
        """Get memory topics for word cloud visualization."""
        if not self._zep_available:
            return self._get_mock_topics(agent_name, top_n)

        try:
            from .zep_tools import ZepToolsService
            svc = ZepToolsService()

            all_edges = svc.get_all_edges(self.graph_id)
            facts = []
            for edge in all_edges:
                fact = edge.fact if hasattr(edge, 'fact') else edge.get('fact', '')
                if not fact:
                    continue
                if agent_name:
                    extracted = extract_agent_from_fact(fact)
                    if extracted and extracted != agent_name:
                        continue
                facts.append(fact)

            return extract_topics(facts, top_n)
        except Exception as e:
            logger.error(f"Failed to get topics: {e}")
            return self._get_mock_topics(agent_name, top_n)

    def _search_zep(
        self, query, agent_name, memory_type, sort_by, limit
    ) -> Dict[str, Any]:
        """Search using Zep graph."""
        try:
            from .zep_tools import ZepToolsService
            svc = ZepToolsService()

            if query:
                result = svc.search_graph(self.graph_id, query, limit=limit * 2)
                raw_facts = result.facts
                raw_edges = result.edges
            else:
                all_edges = svc.get_all_edges(self.graph_id)
                raw_facts = []
                raw_edges = []
                for edge in all_edges:
                    fact = edge.fact if hasattr(edge, 'fact') else edge.get('fact', '')
                    if fact:
                        raw_facts.append(fact)
                        raw_edges.append(
                            edge.to_dict() if hasattr(edge, 'to_dict') else edge
                        )

            memories = []
            for i, fact in enumerate(raw_facts):
                extracted_agent = extract_agent_from_fact(fact)

                if agent_name and extracted_agent and extracted_agent != agent_name:
                    continue

                mtype = classify_memory_type(fact)
                if memory_type and mtype != memory_type:
                    continue

                edge_data = raw_edges[i] if i < len(raw_edges) else {}
                item = MemoryItem(
                    id=edge_data.get('uuid', f'mem-{i}'),
                    content=fact,
                    agent_name=extracted_agent or 'Unknown',
                    memory_type=mtype,
                    importance=estimate_importance(fact, query),
                    source_round=extract_round_from_text(fact),
                    timestamp=edge_data.get('created_at'),
                    source_node=edge_data.get('source_node_uuid'),
                    target_node=edge_data.get('target_node_uuid'),
                    edge_name=edge_data.get('name'),
                )
                memories.append(item)

            if sort_by == 'chronological':
                memories.sort(key=lambda m: m.source_round or 0)
            else:
                memories.sort(key=lambda m: m.importance, reverse=True)

            memories = memories[:limit]
            return {
                'memories': [m.to_dict() for m in memories],
                'total': len(memories),
            }
        except Exception as e:
            logger.error(f"Zep memory search failed, falling back to mock: {e}")
            return self._search_mock(query, agent_name, memory_type, sort_by, limit)

    def _search_mock(
        self, query, agent_name, memory_type, sort_by, limit
    ) -> Dict[str, Any]:
        """Return mock memory data for demo mode."""
        results = []
        for i, m in enumerate(MOCK_MEMORIES):
            if agent_name and m['agent'] != agent_name:
                continue
            if memory_type and m['type'] != memory_type:
                continue
            if query:
                q = query.lower()
                if q not in m['content'].lower():
                    # Check keyword overlap
                    keywords = [w for w in q.split() if len(w) > 1]
                    if not any(kw in m['content'].lower() for kw in keywords):
                        continue

            results.append(MemoryItem(
                id=f'mock-{i}',
                content=m['content'],
                agent_name=m['agent'],
                memory_type=m['type'],
                importance=m['importance'],
                source_round=m['round'],
                timestamp=None,
            ))

        if sort_by == 'chronological':
            results.sort(key=lambda m: m.source_round or 0)
        else:
            results.sort(key=lambda m: m.importance, reverse=True)

        results = results[:limit]
        return {
            'memories': [m.to_dict() for m in results],
            'total': len(results),
        }

    def _get_mock_topics(self, agent_name: Optional[str], top_n: int) -> List[Dict[str, Any]]:
        """Return mock topics for demo mode."""
        relevant = MOCK_MEMORIES
        if agent_name:
            relevant = [m for m in relevant if m['agent'] == agent_name]
        facts = [m['content'] for m in relevant]
        return extract_topics(facts, top_n)
