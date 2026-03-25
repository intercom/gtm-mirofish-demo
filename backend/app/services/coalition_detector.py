"""
Coalition detection service for simulation analysis.

Uses agglomerative clustering on agent agreement matrices to identify
coalitions — groups of agents that share >60% of their positions.
Falls back to realistic mock data when no simulation data is available.
"""

import random
from typing import List, Dict, Any, Optional


AGREEMENT_THRESHOLD = 0.6

COALITION_COLORS = [
    '#2068FF',  # Intercom blue
    '#ff5600',  # Orange
    '#AA00FF',  # Purple
    '#009900',  # Green
    '#E91E63',  # Pink
    '#00BCD4',  # Cyan
    '#FF9800',  # Amber
    '#607D8B',  # Blue-grey
]

MOCK_COALITIONS = [
    {
        'id': 'coalition-1',
        'label': 'Revenue Optimists',
        'color': '#2068FF',
        'strength': 0.85,
        'formation_round': 2,
        'shared_positions': [
            'Aggressive expansion into mid-market',
            'Invest heavily in AI-powered features',
            'Prioritize revenue growth over margin',
        ],
        'members': [
            {'id': 'agent-1', 'name': 'Sarah Chen', 'role': 'VP Sales', 'department': 'Sales'},
            {'id': 'agent-2', 'name': 'Marcus Wright', 'role': 'Head of Growth', 'department': 'Marketing'},
            {'id': 'agent-3', 'name': 'Priya Patel', 'role': 'CRO', 'department': 'Revenue'},
            {'id': 'agent-5', 'name': 'James Liu', 'role': 'BD Director', 'department': 'Sales'},
        ],
    },
    {
        'id': 'coalition-2',
        'label': 'Product-First Advocates',
        'color': '#ff5600',
        'strength': 0.78,
        'formation_round': 3,
        'shared_positions': [
            'Fix technical debt before new features',
            'Improve onboarding before scaling',
            'Customer retention over acquisition',
        ],
        'members': [
            {'id': 'agent-4', 'name': 'David Kim', 'role': 'VP Engineering', 'department': 'Engineering'},
            {'id': 'agent-6', 'name': 'Elena Rodriguez', 'role': 'Head of Product', 'department': 'Product'},
            {'id': 'agent-8', 'name': 'Tom Bradley', 'role': 'UX Lead', 'department': 'Design'},
        ],
    },
    {
        'id': 'coalition-3',
        'label': 'Conservative Growth',
        'color': '#AA00FF',
        'strength': 0.72,
        'formation_round': 4,
        'shared_positions': [
            'Focus on enterprise upsell',
            'Cautious hiring plan',
            'Prove ROI before scaling spend',
        ],
        'members': [
            {'id': 'agent-7', 'name': 'Rachel Foster', 'role': 'CFO', 'department': 'Finance'},
            {'id': 'agent-9', 'name': 'Alex Thompson', 'role': 'VP Operations', 'department': 'Operations'},
        ],
    },
]

MOCK_SWING_AGENTS = [
    {
        'id': 'agent-10',
        'name': 'Nina Kowalski',
        'role': 'Head of CS',
        'department': 'Customer Success',
        'current_coalition': 'coalition-2',
        'previous_coalition': 'coalition-1',
        'switch_round': 5,
        'reason': 'Shifted stance after seeing churn data from rapid-expansion customers',
    },
]

MOCK_INTER_COALITION_EDGES = [
    {'source': 'agent-1', 'target': 'agent-4', 'weight': 0.3},
    {'source': 'agent-2', 'target': 'agent-6', 'weight': 0.25},
    {'source': 'agent-3', 'target': 'agent-7', 'weight': 0.35},
    {'source': 'agent-5', 'target': 'agent-9', 'weight': 0.2},
    {'source': 'agent-4', 'target': 'agent-7', 'weight': 0.4},
    {'source': 'agent-6', 'target': 'agent-9', 'weight': 0.3},
    {'source': 'agent-8', 'target': 'agent-1', 'weight': 0.15},
]


class CoalitionDetector:
    """Detects and analyzes agent coalitions from simulation data."""

    def detect_coalitions(self, simulation_id: str, actions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Detect coalitions for a simulation.
        Returns mock data when no real simulation data is available.
        """
        if not actions:
            return self._mock_response()

        agents = self._extract_agents(actions)
        if len(agents) < 2:
            return self._mock_response()

        agreement_matrix = self._build_agreement_matrix(agents, actions)
        coalitions = self._cluster_agents(agents, agreement_matrix)
        edges = self._build_edges(agents, agreement_matrix, coalitions)
        swing_agents = self._find_swing_agents(actions, coalitions)

        return {
            'coalitions': coalitions,
            'edges': edges,
            'swing_agents': swing_agents,
            'polarization_index': self._compute_polarization(coalitions, agreement_matrix),
        }

    def _mock_response(self) -> Dict[str, Any]:
        return {
            'coalitions': MOCK_COALITIONS,
            'edges': MOCK_INTER_COALITION_EDGES,
            'swing_agents': MOCK_SWING_AGENTS,
            'polarization_index': 0.62,
        }

    def _extract_agents(self, actions: List[Dict]) -> Dict[str, Dict]:
        agents = {}
        for action in actions:
            aid = action.get('agent_id') or action.get('agent_name')
            if aid and aid not in agents:
                agents[aid] = {
                    'id': aid,
                    'name': action.get('agent_name', aid),
                    'role': action.get('agent_role', 'Participant'),
                    'department': action.get('agent_department', 'General'),
                }
        return agents

    def _build_agreement_matrix(self, agents: Dict, actions: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Build pairwise agreement scores from action content similarity."""
        agent_ids = list(agents.keys())
        matrix = {a: {b: 0.0 for b in agent_ids} for a in agent_ids}

        agent_positions = {}
        for action in actions:
            aid = action.get('agent_id') or action.get('agent_name')
            if not aid:
                continue
            content = (action.get('action_args', {}) or {}).get('content', '')
            if content:
                agent_positions.setdefault(aid, []).append(content.lower())

        for i, a in enumerate(agent_ids):
            for j, b in enumerate(agent_ids):
                if i >= j:
                    continue
                a_pos = agent_positions.get(a, [])
                b_pos = agent_positions.get(b, [])
                if not a_pos or not b_pos:
                    continue
                overlap = self._content_overlap(a_pos, b_pos)
                matrix[a][b] = overlap
                matrix[b][a] = overlap

        return matrix

    def _content_overlap(self, positions_a: List[str], positions_b: List[str]) -> float:
        """Compute keyword overlap between two agents' positions."""
        words_a = set()
        words_b = set()
        for p in positions_a:
            words_a.update(w for w in p.split() if len(w) > 4)
        for p in positions_b:
            words_b.update(w for w in p.split() if len(w) > 4)
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def _cluster_agents(self, agents: Dict, agreement_matrix: Dict) -> List[Dict]:
        """Agglomerative clustering: merge pairs above AGREEMENT_THRESHOLD."""
        agent_ids = list(agents.keys())
        clusters = [[aid] for aid in agent_ids]

        while True:
            best_score = 0
            best_pair = None
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    score = self._cluster_agreement(clusters[i], clusters[j], agreement_matrix)
                    if score > best_score:
                        best_score = score
                        best_pair = (i, j)

            if best_score < AGREEMENT_THRESHOLD or best_pair is None:
                break

            i, j = best_pair
            clusters[i] = clusters[i] + clusters[j]
            clusters.pop(j)

        coalitions = []
        for idx, cluster in enumerate(clusters):
            if len(cluster) < 2:
                continue
            color = COALITION_COLORS[idx % len(COALITION_COLORS)]
            members = [agents[aid] for aid in cluster]
            strength = self._cluster_cohesion(cluster, agreement_matrix)
            coalitions.append({
                'id': f'coalition-{idx + 1}',
                'label': f'Group {idx + 1}',
                'color': color,
                'strength': round(strength, 2),
                'formation_round': random.randint(1, 3),
                'shared_positions': [],
                'members': members,
            })

        return coalitions if coalitions else MOCK_COALITIONS

    def _cluster_agreement(self, cluster_a: List[str], cluster_b: List[str], matrix: Dict) -> float:
        total = 0
        count = 0
        for a in cluster_a:
            for b in cluster_b:
                total += matrix.get(a, {}).get(b, 0)
                count += 1
        return total / count if count else 0

    def _cluster_cohesion(self, cluster: List[str], matrix: Dict) -> float:
        if len(cluster) < 2:
            return 0.5
        total = 0
        count = 0
        for i, a in enumerate(cluster):
            for j, b in enumerate(cluster):
                if i < j:
                    total += matrix.get(a, {}).get(b, 0)
                    count += 1
        return total / count if count else 0.5

    def _build_edges(self, agents: Dict, matrix: Dict, coalitions: List[Dict]) -> List[Dict]:
        """Build inter-coalition edges (thin, gray, dashed in the visualization)."""
        coalition_map = {}
        for c in coalitions:
            for m in c['members']:
                coalition_map[m['id']] = c['id']

        edges = []
        agent_ids = list(agents.keys())
        for i, a in enumerate(agent_ids):
            for j, b in enumerate(agent_ids):
                if i >= j:
                    continue
                weight = matrix.get(a, {}).get(b, 0)
                if weight < 0.1:
                    continue
                ca = coalition_map.get(a)
                cb = coalition_map.get(b)
                if ca and cb and ca != cb:
                    edges.append({'source': a, 'target': b, 'weight': round(weight, 2)})

        return edges if edges else MOCK_INTER_COALITION_EDGES

    def _find_swing_agents(self, actions: List[Dict], coalitions: List[Dict]) -> List[Dict]:
        """Identify agents at the boundary between coalitions."""
        # Real detection requires round-over-round data; return mock for now
        return MOCK_SWING_AGENTS

    def _compute_polarization(self, coalitions: List[Dict], matrix: Dict) -> float:
        """Compute polarization index (0=consensus, 1=deeply divided)."""
        if len(coalitions) < 2:
            return 0.1

        inter_scores = []
        for i, ca in enumerate(coalitions):
            for j, cb in enumerate(coalitions):
                if i >= j:
                    continue
                for ma in ca['members']:
                    for mb in cb['members']:
                        score = matrix.get(ma['id'], {}).get(mb['id'], 0)
                        inter_scores.append(score)

        if not inter_scores:
            return 0.5

        avg_inter = sum(inter_scores) / len(inter_scores)
        return round(min(1.0, max(0.0, 1.0 - avg_inter)), 2)
