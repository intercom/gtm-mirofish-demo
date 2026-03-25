"""
Agent Factory API
Create and manage OASIS simulation agents from GTM archetypes.
"""

from flask import Blueprint, jsonify, request

from ..services.agent_factory import AgentFactory
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.agents')

agents_bp = Blueprint('agents', __name__, url_prefix='/api/v1/agents')

_factory = AgentFactory()


# ------------------------------------------------------------------
# Archetypes
# ------------------------------------------------------------------

@agents_bp.route('/archetypes', methods=['GET'])
def list_archetypes():
    """List all available GTM agent archetypes."""
    archetypes = _factory.list_archetypes()
    return jsonify({
        'archetypes': archetypes,
        'count': len(archetypes),
    })


@agents_bp.route('/archetypes/<archetype_id>', methods=['GET'])
def get_archetype(archetype_id):
    """Get a specific archetype definition."""
    archetype = _factory.get_archetype(archetype_id)
    if not archetype:
        return jsonify({'error': f'Archetype {archetype_id} not found'}), 404

    return jsonify({
        'id': archetype['id'],
        'name': archetype['name'],
        'title': archetype['title'],
        'category': archetype['category'],
        'description': archetype['description'],
        'persona_template': archetype['persona_template'],
        'bio_template': archetype['bio_template'],
        'default_attrs': archetype['default_attrs'],
    })


# ------------------------------------------------------------------
# Agent creation
# ------------------------------------------------------------------

@agents_bp.route('/create', methods=['POST'])
def create_agent():
    """
    Create a single agent from an archetype.

    Request body:
        archetype_id (str, required): archetype key
        segment (str): SMB / Mid-Market / Enterprise (default: Mid-Market)
        user_id (int): numeric user ID (default: 1)
        use_llm (bool): use LLM for richer persona (default: false)
        overrides (dict): optional field overrides
    """
    data = request.get_json()
    if not data or 'archetype_id' not in data:
        return jsonify({'error': 'archetype_id is required'}), 400

    archetype_id = data['archetype_id']
    if not _factory.get_archetype(archetype_id):
        return jsonify({'error': f'Unknown archetype: {archetype_id}'}), 400

    try:
        profile = _factory.create_agent(
            archetype_id=archetype_id,
            user_id=data.get('user_id', 1),
            segment=data.get('segment', 'Mid-Market'),
            overrides=data.get('overrides'),
            use_llm=data.get('use_llm', False),
        )
        return jsonify({'agent': profile.to_dict()})
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('/batch', methods=['POST'])
def create_batch():
    """
    Create a batch of agents from a distribution spec.

    Request body:
        distribution (list, required): list of specs, each with:
            - archetype_id (str): archetype key
            - count (int): number of agents (default: 1)
            - segment (str, optional): company segment
            - overrides (dict, optional): field overrides
        use_llm (bool): use LLM for richer personas (default: false)
        start_user_id (int): starting user_id (default: 1)
    """
    data = request.get_json()
    if not data or 'distribution' not in data:
        return jsonify({'error': 'distribution is required'}), 400

    distribution = data['distribution']
    if not isinstance(distribution, list) or len(distribution) == 0:
        return jsonify({'error': 'distribution must be a non-empty list'}), 400

    # Validate archetype IDs
    for spec in distribution:
        aid = spec.get('archetype_id')
        if not aid or not _factory.get_archetype(aid):
            return jsonify({'error': f'Unknown archetype: {aid}'}), 400

    try:
        profiles = _factory.create_batch(
            distribution=distribution,
            use_llm=data.get('use_llm', False),
            start_user_id=data.get('start_user_id', 1),
        )
        return jsonify({
            'agents': [p.to_dict() for p in profiles],
            'count': len(profiles),
        })
    except Exception as e:
        logger.error(f"Batch creation failed: {e}")
        return jsonify({'error': str(e)}), 500


@agents_bp.route('/from-scenario', methods=['POST'])
def create_from_scenario():
    """
    Create agents from a GTM scenario template's agent_config.

    Request body:
        agent_config (dict, required): the agent_config section from a GTM scenario, with:
            - count (int): total number of agents
            - persona_types (list[str]): persona type names
            - firmographic_mix (dict, optional): segments, contract_values, etc.
        use_llm (bool): use LLM for richer personas (default: false)
        start_user_id (int): starting user_id (default: 1)
    """
    data = request.get_json()
    if not data or 'agent_config' not in data:
        return jsonify({'error': 'agent_config is required'}), 400

    try:
        profiles = _factory.create_from_scenario(
            scenario_config=data['agent_config'],
            use_llm=data.get('use_llm', False),
            start_user_id=data.get('start_user_id', 1),
        )
        return jsonify({
            'agents': [p.to_dict() for p in profiles],
            'count': len(profiles),
        })
    except Exception as e:
        logger.error(f"Scenario agent creation failed: {e}")
        return jsonify({'error': str(e)}), 500
