"""
Personality Dynamics API
Endpoints for querying and updating agent personality vectors during simulation.
"""

import random
from flask import Blueprint, jsonify, request

from ..services.personality_dynamics import (
    get_engine,
    PersonalityDynamics,
    TRAITS,
    OUTCOME_EFFECTS,
    TRAIT_MIN,
    TRAIT_MAX,
)
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.personality')

personality_bp = Blueprint('personality', __name__, url_prefix='/api/v1/personality')


def _demo_engine(simulation_id: str) -> PersonalityDynamics:
    """Get or create a demo-populated engine for when no real simulation exists."""
    engine = get_engine(simulation_id)
    if not engine.get_agent_ids():
        demo_agents = ['agent_1', 'agent_2', 'agent_3', 'agent_4', 'agent_5']
        outcomes = list(OUTCOME_EFFECTS.keys())
        for aid in demo_agents:
            engine.initialize_agent(aid)
            for r in range(1, 6):
                outcome = random.choice(outcomes)
                engine.update_personality(aid, outcome, round_num=r)
    return engine


@personality_bp.route('/<simulation_id>/agents', methods=['GET'])
def list_agents(simulation_id: str):
    """List all agents and their current personality vectors."""
    try:
        engine = get_engine(simulation_id)
        agents = engine.get_all_agents()
        if not agents:
            engine = _demo_engine(simulation_id)
            agents = engine.get_all_agents()

        return jsonify({
            'success': True,
            'data': {
                'simulation_id': simulation_id,
                'agents': agents,
                'traits': TRAITS,
                'bounds': {'min': TRAIT_MIN, 'max': TRAIT_MAX},
            },
        })
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@personality_bp.route('/<simulation_id>/agents/<agent_id>', methods=['GET'])
def get_agent_snapshot(simulation_id: str, agent_id: str):
    """Get personality snapshot for an agent at a specific round (or latest)."""
    try:
        round_num = request.args.get('round', type=int)
        engine = get_engine(simulation_id)

        snapshot = engine.get_personality_snapshot(agent_id, round_num)
        if not snapshot:
            engine = _demo_engine(simulation_id)
            snapshot = engine.get_personality_snapshot(agent_id, round_num)

        if not snapshot:
            return jsonify({'success': False, 'error': f'Agent {agent_id} not found'}), 404

        return jsonify({'success': True, 'data': snapshot})
    except Exception as e:
        logger.error(f"Error getting agent snapshot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@personality_bp.route('/<simulation_id>/agents/<agent_id>/trajectory', methods=['GET'])
def get_agent_trajectory(simulation_id: str, agent_id: str):
    """Get full personality evolution timeline for an agent."""
    try:
        engine = get_engine(simulation_id)
        trajectory = engine.get_personality_trajectory(agent_id)
        if not trajectory:
            engine = _demo_engine(simulation_id)
            trajectory = engine.get_personality_trajectory(agent_id)

        if not trajectory:
            return jsonify({'success': False, 'error': f'Agent {agent_id} not found'}), 404

        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent_id,
                'trajectory': trajectory,
                'traits': TRAITS,
            },
        })
    except Exception as e:
        logger.error(f"Error getting trajectory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@personality_bp.route('/<simulation_id>/update', methods=['POST'])
def update_personality(simulation_id: str):
    """
    Update an agent's personality based on an interaction outcome.

    Body: { "agent_id": "...", "interaction_outcome": "...", "round_num": 0 }
    """
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')
        outcome = data.get('interaction_outcome')
        round_num = data.get('round_num', 0)

        if not agent_id or not outcome:
            return jsonify({
                'success': False,
                'error': 'agent_id and interaction_outcome are required',
            }), 400

        if outcome not in OUTCOME_EFFECTS:
            return jsonify({
                'success': False,
                'error': f'Unknown outcome: {outcome}. Valid: {list(OUTCOME_EFFECTS.keys())}',
            }), 400

        engine = get_engine(simulation_id)
        vec = engine.update_personality(agent_id, outcome, round_num)

        return jsonify({
            'success': True,
            'data': {
                'agent_id': agent_id,
                'round_num': round_num,
                'interaction_outcome': outcome,
                'vector': vec.to_dict(),
            },
        })
    except Exception as e:
        logger.error(f"Error updating personality: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@personality_bp.route('/<simulation_id>/initialize', methods=['POST'])
def initialize_agent(simulation_id: str):
    """
    Initialize an agent's personality (or batch-initialize multiple).

    Body: { "agent_id": "...", "initial_vector": { ... } }
      or: { "agents": [{ "agent_id": "...", "initial_vector": { ... } }, ...] }
    """
    try:
        data = request.get_json() or {}
        engine = get_engine(simulation_id)
        results = []

        agents_list = data.get('agents', [])
        if not agents_list and data.get('agent_id'):
            agents_list = [data]

        if not agents_list:
            return jsonify({'success': False, 'error': 'No agents provided'}), 400

        for agent_data in agents_list:
            aid = agent_data.get('agent_id')
            if not aid:
                continue
            vec = engine.initialize_agent(aid, agent_data.get('initial_vector'))
            results.append({'agent_id': aid, 'vector': vec.to_dict()})

        return jsonify({
            'success': True,
            'data': {'initialized': results},
        })
    except Exception as e:
        logger.error(f"Error initializing agents: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@personality_bp.route('/outcomes', methods=['GET'])
def list_outcomes():
    """List all valid interaction outcome types and their trait effects."""
    outcomes = {}
    for outcome_key, effects in OUTCOME_EFFECTS.items():
        outcomes[outcome_key] = [
            {'trait': trait, 'min_delta': lo, 'max_delta': hi}
            for trait, lo, hi in effects
        ]
    return jsonify({
        'success': True,
        'data': {
            'outcomes': outcomes,
            'traits': TRAITS,
            'bounds': {'min': TRAIT_MIN, 'max': TRAIT_MAX},
        },
    })
