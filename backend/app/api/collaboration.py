"""
Collaboration API
Serves real-time agent collaboration data derived from simulation actions.
Returns agent interaction networks (nodes + edges) with intensity metrics.
Falls back to mock data when no simulation data is available.
"""

import random
import time

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.api.collaboration')

collaboration_bp = Blueprint(
    'collaboration', __name__, url_prefix='/api/v1/simulation'
)

# Agent colors matching the frontend palette
AGENT_COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#059669', '#d97706', '#ef4444']

MOCK_AGENT_NAMES = [
    ('Sarah Chen', 'VP Sales', 'Acme Corp'),
    ('Marcus Johnson', 'CTO', 'TechFlow Inc'),
    ('Elena Rodriguez', 'Head of CS', 'Acme Corp'),
    ('David Kim', 'Product Manager', 'TechFlow Inc'),
    ('Priya Patel', 'Marketing Director', 'Acme Corp'),
    ('James Wilson', 'Solutions Engineer', 'TechFlow Inc'),
]

INTERACTION_TYPES = [
    'reply', 'mention', 'shared_topic', 'thread_collab', 'endorsement',
]

DISCUSSION_TOPICS = [
    'AI resolution rates',
    'migration timeline risks',
    'support platform costs',
    'customer satisfaction data',
    'vendor switching strategy',
    'integration requirements',
    'team readiness assessment',
    'automation capabilities',
]


def _build_mock_collaboration(num_agents=6, num_rounds=5):
    """Generate realistic mock collaboration data for demo mode."""
    agents = MOCK_AGENT_NAMES[:num_agents]
    nodes = []
    for i, (name, role, company) in enumerate(agents):
        nodes.append({
            'id': f'agent-{i}',
            'name': name,
            'role': role,
            'company': company,
            'initials': name[0],
            'color': AGENT_COLORS[i % len(AGENT_COLORS)],
            'messageCount': random.randint(3, 18),
            'activeRound': random.randint(max(1, num_rounds - 2), num_rounds),
        })

    edges = []
    edge_id = 0
    for i in range(num_agents):
        num_connections = random.randint(1, min(3, num_agents - 1))
        targets = random.sample(
            [j for j in range(num_agents) if j != i], num_connections
        )
        for j in targets:
            edges.append({
                'id': f'edge-{edge_id}',
                'source': f'agent-{i}',
                'target': f'agent-{j}',
                'weight': round(random.uniform(0.2, 1.0), 2),
                'interactionType': random.choice(INTERACTION_TYPES),
                'messageCount': random.randint(1, 8),
                'lastRound': random.randint(max(1, num_rounds - 2), num_rounds),
            })
            edge_id += 1

    messages = []
    for r in range(1, num_rounds + 1):
        num_msgs = random.randint(1, 3)
        for _ in range(num_msgs):
            sender_idx = random.randint(0, num_agents - 1)
            receiver_idx = random.choice(
                [j for j in range(num_agents) if j != sender_idx]
            )
            messages.append({
                'round': r,
                'sender': f'agent-{sender_idx}',
                'receiver': f'agent-{receiver_idx}',
                'topic': random.choice(DISCUSSION_TOPICS),
                'type': random.choice(INTERACTION_TYPES),
                'timestamp': time.time() - (num_rounds - r) * 10,
            })

    return {
        'nodes': nodes,
        'edges': edges,
        'messages': messages,
        'currentRound': num_rounds,
        'totalInteractions': sum(e['messageCount'] for e in edges),
        'activeTopic': random.choice(DISCUSSION_TOPICS),
        'collaborationScore': round(random.uniform(0.55, 0.95), 2),
    }


def _derive_collaboration_from_actions(actions):
    """Derive collaboration network from real simulation action data."""
    agent_map = {}
    edge_counts = {}
    messages = []

    for action in actions:
        agent_name = action.get('agent_name', 'Unknown')
        agent_id = action.get('agent_id', agent_name)

        if agent_id not in agent_map:
            parts = agent_name.split(', ')
            name_part = parts[0].strip() if parts else 'Agent'
            role_company = parts[1].strip() if len(parts) > 1 else ''
            role_parts = role_company.split(' @ ')
            idx = len(agent_map)
            agent_map[agent_id] = {
                'id': agent_id,
                'name': name_part.split(' ')[0],
                'role': role_parts[0] if role_parts else '',
                'company': role_parts[1] if len(role_parts) > 1 else '',
                'initials': name_part[0].upper(),
                'color': AGENT_COLORS[idx % len(AGENT_COLORS)],
                'messageCount': 0,
                'activeRound': 0,
            }

        agent_map[agent_id]['messageCount'] += 1
        round_num = action.get('round_num', 0)
        if round_num > agent_map[agent_id]['activeRound']:
            agent_map[agent_id]['activeRound'] = round_num

    agent_ids = list(agent_map.keys())

    for action in actions:
        agent_id = action.get('agent_id', action.get('agent_name', ''))
        action_type = (action.get('action_type') or '').upper()
        round_num = action.get('round_num', 0)

        if 'REPLY' in action_type or 'COMMENT' in action_type:
            content = action.get('action_args', {}).get('content', '')
            for other_id in agent_ids:
                if other_id == agent_id:
                    continue
                other_name = agent_map[other_id]['name'].lower()
                if other_name in content.lower():
                    edge_key = tuple(sorted([agent_id, other_id]))
                    if edge_key not in edge_counts:
                        edge_counts[edge_key] = {
                            'count': 0, 'lastRound': 0,
                            'types': set(),
                        }
                    edge_counts[edge_key]['count'] += 1
                    edge_counts[edge_key]['lastRound'] = max(
                        edge_counts[edge_key]['lastRound'], round_num
                    )
                    edge_counts[edge_key]['types'].add('reply')

                    messages.append({
                        'round': round_num,
                        'sender': agent_id,
                        'receiver': other_id,
                        'topic': content[:60] if content else 'Discussion',
                        'type': 'reply',
                        'timestamp': time.time(),
                    })

        if action_type in ('CREATE_POST', 'CREATE_THREAD'):
            platform = action.get('platform', '')
            for other_id in agent_ids:
                if other_id == agent_id:
                    continue
                if agent_map[other_id].get('activeRound', 0) >= max(1, round_num - 1):
                    edge_key = tuple(sorted([agent_id, other_id]))
                    if edge_key not in edge_counts:
                        edge_counts[edge_key] = {
                            'count': 0, 'lastRound': 0,
                            'types': set(),
                        }
                    edge_counts[edge_key]['count'] += 1
                    edge_counts[edge_key]['types'].add('shared_topic')

    nodes = list(agent_map.values())
    max_count = max((e['count'] for e in edge_counts.values()), default=1)
    edges = []
    for idx, ((src, tgt), data) in enumerate(edge_counts.items()):
        edges.append({
            'id': f'edge-{idx}',
            'source': src,
            'target': tgt,
            'weight': round(data['count'] / max_count, 2),
            'interactionType': list(data['types'])[0] if data['types'] else 'shared_topic',
            'messageCount': data['count'],
            'lastRound': data['lastRound'],
        })

    total_interactions = sum(e['messageCount'] for e in edges)
    max_possible = len(nodes) * (len(nodes) - 1) / 2 if len(nodes) > 1 else 1
    collab_score = round(
        min(1.0, len(edges) / max_possible) if max_possible > 0 else 0, 2
    )

    current_round = max((n['activeRound'] for n in nodes), default=0)

    return {
        'nodes': nodes,
        'edges': edges,
        'messages': messages[-20:],
        'currentRound': current_round,
        'totalInteractions': total_interactions,
        'activeTopic': DISCUSSION_TOPICS[current_round % len(DISCUSSION_TOPICS)],
        'collaborationScore': collab_score,
    }


@collaboration_bp.route('/<simulation_id>/collaboration')
def get_collaboration(simulation_id):
    """Get real-time collaboration network for a simulation."""
    try:
        from ..services.simulation_manager import SimulationManager
        manager = SimulationManager()
        actions = manager.get_actions(simulation_id)

        if actions and len(actions) >= 2:
            data = _derive_collaboration_from_actions(actions)
        else:
            data = _build_mock_collaboration()
            data['demo'] = True

        return jsonify({'success': True, 'data': data})

    except Exception as e:
        logger.warning(
            'Falling back to mock collaboration data: %s', str(e)
        )
        data = _build_mock_collaboration()
        data['demo'] = True
        return jsonify({'success': True, 'data': data})
