"""
Community detection service.

Detects communities/clusters in knowledge graph data using a simplified
Louvain-inspired modularity optimization algorithm. Falls back to
interaction-frequency clustering when Zep community data isn't available.
"""

from collections import defaultdict
import random

from ..utils.logger import get_logger

logger = get_logger('mirofish.community')


class CommunityDetector:
    """Detects communities in graph node/edge data."""

    def detect(self, nodes, edges):
        """
        Run community detection on graph data.

        Args:
            nodes: list of node dicts with 'uuid', 'name', 'labels', 'summary'
            edges: list of edge dicts with 'source_node_uuid', 'target_node_uuid', 'name'

        Returns:
            dict with 'communities' list and 'metadata'
        """
        if not nodes:
            return {'communities': [], 'metadata': {'algorithm': 'none', 'node_count': 0}}

        node_ids = {n['uuid'] for n in nodes}
        valid_edges = [
            e for e in edges
            if e.get('source_node_uuid') in node_ids and e.get('target_node_uuid') in node_ids
        ]

        adjacency = defaultdict(set)
        edge_weights = defaultdict(int)
        for e in valid_edges:
            s, t = e['source_node_uuid'], e['target_node_uuid']
            adjacency[s].add(t)
            adjacency[t].add(s)
            pair = tuple(sorted([s, t]))
            edge_weights[pair] += 1

        assignments = self._louvain_communities(node_ids, adjacency, edge_weights)

        node_map = {n['uuid']: n for n in nodes}
        communities = self._build_community_objects(assignments, node_map, adjacency, valid_edges)

        return {
            'communities': communities,
            'metadata': {
                'algorithm': 'louvain',
                'node_count': len(nodes),
                'edge_count': len(valid_edges),
                'community_count': len(communities),
            }
        }

    def _louvain_communities(self, node_ids, adjacency, edge_weights):
        """
        Simplified Louvain: greedy modularity optimization.
        Returns dict mapping node_id -> community_id.
        """
        nodes = list(node_ids)
        community = {n: i for i, n in enumerate(nodes)}
        total_weight = sum(edge_weights.values()) or 1

        degree = defaultdict(int)
        for (u, v), w in edge_weights.items():
            degree[u] += w
            degree[v] += w
        for n in nodes:
            degree.setdefault(n, 0)

        improved = True
        max_iterations = 10
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            random.shuffle(nodes)

            for node in nodes:
                current_comm = community[node]
                neighbor_comms = defaultdict(float)

                for neighbor in adjacency.get(node, set()):
                    pair = tuple(sorted([node, neighbor]))
                    w = edge_weights.get(pair, 1)
                    neighbor_comms[community[neighbor]] += w

                best_comm = current_comm
                best_gain = 0.0

                for comm, edges_to_comm in neighbor_comms.items():
                    if comm == current_comm:
                        continue
                    comm_degree = sum(
                        degree[n] for n in community if community[n] == comm
                    )
                    gain = edges_to_comm / total_weight - (degree[node] * comm_degree) / (2 * total_weight ** 2)
                    if gain > best_gain:
                        best_gain = gain
                        best_comm = comm

                if best_comm != current_comm:
                    community[node] = best_comm
                    improved = True

        # Renumber communities to be sequential starting from 0
        unique = sorted(set(community.values()))
        remap = {old: new for new, old in enumerate(unique)}
        return {n: remap[c] for n, c in community.items()}

    def _build_community_objects(self, assignments, node_map, adjacency, edges):
        """Build structured community objects with metadata."""
        groups = defaultdict(list)
        for node_id, comm_id in assignments.items():
            groups[comm_id].append(node_id)

        communities = []
        for comm_id in sorted(groups.keys()):
            member_ids = groups[comm_id]
            members = [node_map[nid] for nid in member_ids if nid in node_map]

            label = self._generate_label(members)
            topics = self._extract_topics(members)
            cohesion = self._compute_cohesion(member_ids, adjacency, edges)
            sentiment = self._estimate_sentiment(members)

            communities.append({
                'id': comm_id,
                'label': label,
                'members': [
                    {
                        'uuid': m['uuid'],
                        'name': m['name'],
                        'labels': m.get('labels', []),
                        'role': self._get_role(m),
                    }
                    for m in members
                ],
                'member_count': len(members),
                'topics': topics,
                'sentiment': sentiment,
                'cohesion': round(cohesion, 2),
            })

        return communities

    def _generate_label(self, members):
        """Auto-generate a community label from shared topics/names."""
        topic_members = [m for m in members if self._is_topic(m)]
        if topic_members:
            top = sorted(topic_members, key=lambda m: len(m.get('summary', '')), reverse=True)
            return top[0]['name']

        if len(members) == 1:
            return members[0]['name']

        persona_members = [m for m in members if self._is_persona(m)]
        if persona_members:
            return f"{persona_members[0]['name']} Group"

        return members[0]['name'] if members else 'Unknown'

    def _extract_topics(self, members):
        """Extract key topic names from community members."""
        topics = []
        for m in members:
            labels = [l.lower() for l in m.get('labels', [])]
            is_topic = any(
                kw in l for l in labels
                for kw in ('topic', 'theme', 'subject', 'concept', 'feature', 'product', 'technology')
            )
            if is_topic:
                topics.append(m['name'])
        return topics[:5]

    def _compute_cohesion(self, member_ids, adjacency, edges):
        """Cohesion = ratio of actual intra-community edges to possible edges."""
        member_set = set(member_ids)
        n = len(member_set)
        if n < 2:
            return 1.0

        intra_edges = 0
        for e in edges:
            if e['source_node_uuid'] in member_set and e['target_node_uuid'] in member_set:
                intra_edges += 1

        max_edges = n * (n - 1) / 2
        return intra_edges / max_edges if max_edges > 0 else 0.0

    def _estimate_sentiment(self, members):
        """Simple sentiment heuristic based on member summaries."""
        positive_words = {'growth', 'improve', 'success', 'gain', 'positive', 'opportunity', 'drive', 'enable'}
        negative_words = {'risk', 'churn', 'loss', 'decline', 'issue', 'problem', 'fail', 'reduce'}

        pos_count = 0
        neg_count = 0
        for m in members:
            summary = (m.get('summary') or '').lower()
            pos_count += sum(1 for w in positive_words if w in summary)
            neg_count += sum(1 for w in negative_words if w in summary)

        total = pos_count + neg_count
        if total == 0:
            return 'neutral'
        ratio = pos_count / total
        if ratio > 0.6:
            return 'positive'
        if ratio < 0.4:
            return 'negative'
        return 'mixed'

    def _get_role(self, node):
        """Determine node role from labels."""
        labels = [l.lower() for l in node.get('labels', []) if l not in ('Entity', 'Node')]
        if not labels:
            return 'entity'
        label = labels[0]
        for role in ('persona', 'person', 'agent', 'user', 'customer', 'stakeholder', 'role'):
            if role in label:
                return 'persona'
        for role in ('topic', 'theme', 'subject', 'concept', 'product', 'feature', 'technology'):
            if role in label:
                return 'topic'
        for role in ('event', 'process', 'action', 'interaction'):
            if role in label:
                return 'process'
        return 'entity'

    def _is_topic(self, node):
        return self._get_role(node) == 'topic'

    def _is_persona(self, node):
        return self._get_role(node) == 'persona'
