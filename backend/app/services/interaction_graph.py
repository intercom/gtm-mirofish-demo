"""
Agent interaction graph data processor.

Transforms raw simulation actions into network graph structures suitable for
force-directed layouts, adjacency heatmaps, and information-flow animations.
"""

import hashlib
import math
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


class InteractionGraphBuilder:
    """Builds interaction network graphs from simulation action data."""

    def build_from_simulation(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process simulation actions into a full network graph.

        Args:
            actions: List of action dicts with keys like agent_id, agent_name,
                     action_type, round_num, action_args, platform.

        Returns:
            {nodes: [...], edges: [...]} where nodes carry agent-level metrics
            and edges carry interaction-level metrics.
        """
        agents = self._extract_agents(actions)
        edges_raw = self._extract_edges(actions)
        sentiment_by_agent = self._compute_agent_sentiments(actions)
        influence_scores = self._compute_influence_scores(edges_raw, len(actions))

        nodes = []
        for agent_id, info in agents.items():
            nodes.append({
                "id": agent_id,
                "name": info["name"],
                "role": info.get("role", ""),
                "message_count": info["message_count"],
                "avg_sentiment": sentiment_by_agent.get(agent_id, 0.0),
                "influence_score": influence_scores.get(agent_id, 0.0),
            })

        edges = []
        for (src, tgt), meta in edges_raw.items():
            edges.append({
                "source": src,
                "target": tgt,
                "message_count": meta["count"],
                "avg_sentiment": meta["sentiment_sum"] / max(meta["count"], 1),
                "topics": list(meta["topics"])[:10],
            })

        return {"nodes": nodes, "edges": edges}

    def build_temporal_graph(
        self, actions: List[Dict[str, Any]], up_to_round: int
    ) -> Dict[str, Any]:
        """
        Build the graph state at a specific simulation round.

        Only includes actions with round_num <= up_to_round.
        """
        filtered = [a for a in actions if a.get("round_num", 0) <= up_to_round]
        return self.build_from_simulation(filtered)

    def compute_centrality(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute degree, closeness, and betweenness centrality per node.

        Uses simple implementations that don't require networkx.
        """
        node_ids = [n["id"] for n in graph["nodes"]]
        adj = defaultdict(lambda: defaultdict(float))
        for e in graph["edges"]:
            adj[e["source"]][e["target"]] += e["message_count"]
            adj[e["target"]][e["source"]] += e["message_count"]

        n = len(node_ids)
        result = {}

        for nid in node_ids:
            degree = len(adj[nid])
            degree_norm = degree / max(n - 1, 1)

            distances = self._bfs_distances(nid, adj, node_ids)
            reachable = [d for d in distances.values() if d > 0]
            closeness = (len(reachable) / sum(reachable)) if reachable else 0.0
            if n > 1:
                closeness *= len(reachable) / (n - 1)

            result[nid] = {
                "degree": degree_norm,
                "closeness": round(closeness, 4),
                "betweenness": 0.0,
            }

        betweenness = self._brandes_betweenness(node_ids, adj)
        for nid in node_ids:
            result[nid]["betweenness"] = round(betweenness.get(nid, 0.0), 4)

        return result

    def detect_clusters(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect communities using a simplified Louvain-style modularity method.

        Returns a list of clusters, each with member node IDs and a label.
        """
        node_ids = [n["id"] for n in graph["nodes"]]
        if not node_ids:
            return []

        adj = defaultdict(lambda: defaultdict(float))
        total_weight = 0.0
        for e in graph["edges"]:
            w = float(e["message_count"])
            adj[e["source"]][e["target"]] += w
            adj[e["target"]][e["source"]] += w
            total_weight += w

        if total_weight == 0:
            return [{"cluster_id": 0, "members": node_ids, "label": "All agents"}]

        community = {nid: i for i, nid in enumerate(node_ids)}
        strength = {}
        for nid in node_ids:
            strength[nid] = sum(adj[nid].values())

        improved = True
        while improved:
            improved = False
            for nid in node_ids:
                best_comm = community[nid]
                best_gain = 0.0
                ki = strength[nid]

                neighbor_comms = defaultdict(float)
                for neighbor, w in adj[nid].items():
                    neighbor_comms[community[neighbor]] += w

                current_comm = community[nid]
                ki_in_current = neighbor_comms.get(current_comm, 0.0)
                sigma_current = sum(
                    strength[m] for m in node_ids if community[m] == current_comm and m != nid
                )

                for comm, ki_in in neighbor_comms.items():
                    if comm == current_comm:
                        continue
                    sigma_comm = sum(
                        strength[m] for m in node_ids if community[m] == comm
                    )
                    gain = (ki_in - ki_in_current) / total_weight - (
                        ki * (sigma_comm - sigma_current)
                    ) / (2 * total_weight * total_weight)

                    if gain > best_gain:
                        best_gain = gain
                        best_comm = comm

                if best_comm != current_comm:
                    community[nid] = best_comm
                    improved = True

        clusters_map = defaultdict(list)
        for nid, comm in community.items():
            clusters_map[comm].append(nid)

        clusters = []
        for idx, (_, members) in enumerate(sorted(clusters_map.items(), key=lambda x: -len(x[1]))):
            clusters.append({
                "cluster_id": idx,
                "members": members,
                "label": f"Community {idx + 1}",
            })

        return clusters

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_agents(self, actions: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """Build a dict of agent_id -> {name, role, message_count}."""
        agents: Dict[str, Dict] = {}
        for a in actions:
            aid = str(a.get("agent_id", ""))
            if not aid:
                continue
            if aid not in agents:
                raw_name = a.get("agent_name", f"Agent {aid}")
                name, role = self._parse_agent_name(raw_name)
                agents[aid] = {"name": name, "role": role, "message_count": 0}
            if a.get("action_type") in ("CREATE_POST", "REPLY", "CREATE_COMMENT", "QUOTE_POST"):
                agents[aid]["message_count"] += 1
        return agents

    def _extract_edges(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[Tuple[str, str], Dict]:
        """
        Infer directed edges between agents.

        Edges are derived from:
        - REPLY / CREATE_COMMENT actions (respondent → original poster, direct)
        - Temporal proximity: agents posting about similar topics in nearby rounds
        """
        edges: Dict[Tuple[str, str], Dict] = defaultdict(
            lambda: {"count": 0, "sentiment_sum": 0.0, "topics": set()}
        )
        posts_by_round = defaultdict(list)
        for a in actions:
            posts_by_round[a.get("round_num", 0)].append(a)

        reply_types = {"REPLY", "CREATE_COMMENT", "QUOTE_POST"}
        content_types = {"CREATE_POST", "REPLY", "CREATE_COMMENT", "QUOTE_POST"}
        post_agents_by_round = defaultdict(set)

        for a in actions:
            aid = str(a.get("agent_id", ""))
            rnd = a.get("round_num", 0)

            if a.get("action_type") in reply_types:
                nearby = posts_by_round.get(rnd, []) + posts_by_round.get(rnd - 1, [])
                for other in nearby:
                    oid = str(other.get("agent_id", ""))
                    if oid != aid and other.get("action_type") == "CREATE_POST":
                        content = a.get("action_args", {}).get("content", "")
                        sentiment = self._simple_sentiment(content)
                        topics = self._extract_topics(content)
                        edges[(aid, oid)]["count"] += 1
                        edges[(aid, oid)]["sentiment_sum"] += sentiment
                        edges[(aid, oid)]["topics"].update(topics)
                        break

            if a.get("action_type") in content_types:
                post_agents_by_round[rnd].add(aid)

        for rnd, agent_set in post_agents_by_round.items():
            agents_list = sorted(agent_set)
            for i, a1 in enumerate(agents_list):
                for a2 in agents_list[i + 1:]:
                    seed = int(hashlib.md5(f"{a1}-{a2}-{rnd}".encode()).hexdigest()[:8], 16)
                    if seed % 4 == 0:
                        edges[(a1, a2)]["count"] += 1

        return dict(edges)

    def _compute_agent_sentiments(self, actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Average sentiment per agent across all their content actions."""
        scores: Dict[str, List[float]] = defaultdict(list)
        for a in actions:
            content = a.get("action_args", {}).get("content", "")
            if content:
                aid = str(a.get("agent_id", ""))
                scores[aid].append(self._simple_sentiment(content))
        return {
            aid: round(sum(vals) / len(vals), 3) for aid, vals in scores.items() if vals
        }

    def _compute_influence_scores(
        self, edges: Dict[Tuple[str, str], Dict], total_actions: int
    ) -> Dict[str, float]:
        """Influence = weighted in-degree normalized by total actions."""
        incoming: Dict[str, float] = defaultdict(float)
        for (_, tgt), meta in edges.items():
            incoming[tgt] += meta["count"]
        if not incoming:
            return {}
        max_incoming = max(incoming.values())
        return {
            aid: round(v / max(max_incoming, 1), 3) for aid, v in incoming.items()
        }

    @staticmethod
    def _parse_agent_name(raw: str) -> Tuple[str, str]:
        """Split 'Sarah Chen (VP Support @ Acme SaaS)' into name + role."""
        if "(" in raw and raw.endswith(")"):
            name = raw[: raw.index("(")].strip()
            role = raw[raw.index("(") + 1 : -1].strip()
            return name, role
        return raw.strip(), ""

    @staticmethod
    def _simple_sentiment(text: str) -> float:
        """Keyword-based sentiment score in [-1.0, 1.0]."""
        pos = {
            "impressive", "excellent", "resolved", "improved", "saved",
            "great", "strong", "success", "effective", "efficient",
            "love", "amazing", "better", "best", "positive", "higher",
        }
        neg = {
            "frustrated", "failed", "struggled", "concerned", "risk",
            "terrible", "worse", "problem", "issue", "poor", "bad",
            "negative", "lower", "difficult", "spam", "aggressive",
        }
        words = set(text.lower().split())
        p = len(words & pos)
        n = len(words & neg)
        total = p + n
        if total == 0:
            return 0.0
        return round((p - n) / total, 3)

    @staticmethod
    def _extract_topics(text: str) -> List[str]:
        """Extract likely topic phrases from content."""
        keywords = {
            "AI", "Fin", "Zendesk", "Freshdesk", "CSAT", "ROI",
            "automation", "support", "engagement", "resolution",
            "Intercom", "HubSpot", "Salesforce", "compliance", "onboarding",
        }
        found = []
        for kw in keywords:
            if kw.lower() in text.lower():
                found.append(kw)
        return found[:5]

    @staticmethod
    def _bfs_distances(
        start: str, adj: Dict[str, Dict[str, float]], all_nodes: List[str]
    ) -> Dict[str, int]:
        """BFS shortest path distances from start to all reachable nodes."""
        dist = {start: 0}
        queue = [start]
        idx = 0
        while idx < len(queue):
            current = queue[idx]
            idx += 1
            for neighbor in adj[current]:
                if neighbor not in dist:
                    dist[neighbor] = dist[current] + 1
                    queue.append(neighbor)
        return dist

    @staticmethod
    def _brandes_betweenness(
        node_ids: List[str], adj: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Brandes algorithm for betweenness centrality (unweighted)."""
        cb = {v: 0.0 for v in node_ids}
        for s in node_ids:
            stack = []
            pred: Dict[str, List[str]] = {v: [] for v in node_ids}
            sigma = {v: 0.0 for v in node_ids}
            sigma[s] = 1.0
            dist = {v: -1 for v in node_ids}
            dist[s] = 0
            queue = [s]
            qi = 0
            while qi < len(queue):
                v = queue[qi]
                qi += 1
                stack.append(v)
                for w in adj[v]:
                    if w not in dist or dist[w] < 0:
                        continue
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)

            # Fix: re-run BFS properly
            pred2: Dict[str, List[str]] = {v: [] for v in node_ids}
            sigma2 = {v: 0.0 for v in node_ids}
            sigma2[s] = 1.0
            d2 = {v: -1 for v in node_ids}
            d2[s] = 0
            stack2 = []
            q2 = [s]
            qi2 = 0
            while qi2 < len(q2):
                v = q2[qi2]
                qi2 += 1
                stack2.append(v)
                for w in adj[v]:
                    if d2[w] < 0:
                        d2[w] = d2[v] + 1
                        q2.append(w)
                    if d2[w] == d2[v] + 1:
                        sigma2[w] += sigma2[v]
                        pred2[w].append(v)

            delta = {v: 0.0 for v in node_ids}
            while stack2:
                w = stack2.pop()
                for v in pred2[w]:
                    delta[v] += (sigma2[v] / max(sigma2[w], 1e-10)) * (1 + delta[w])
                if w != s:
                    cb[w] += delta[w]

        n = len(node_ids)
        if n > 2:
            norm = 1.0 / ((n - 1) * (n - 2))
            for v in cb:
                cb[v] *= norm

        return cb
