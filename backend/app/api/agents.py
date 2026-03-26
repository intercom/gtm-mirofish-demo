"""
Agents API — wizard CRUD, preview, and OASIS agent factory.
"""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..services.agent_factory import AgentFactory
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.agents')

agents_bp = Blueprint('agents', __name__, url_prefix='/api/v1/agents')

# In-memory store for wizard-created agents
_agents_store = {}

_factory = AgentFactory()


# ------------------------------------------------------------------
# Wizard CRUD
# ------------------------------------------------------------------

@agents_bp.route('', methods=['POST'])
def create_agent():
    """Create a new agent from wizard data."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    basic = data.get('basic', {})
    if not basic.get('name'):
        return jsonify({'error': 'Agent name is required'}), 400

    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    agent = {
        'id': agent_id,
        'basic': basic,
        'personality': data.get('personality', {}),
        'expertise': data.get('expertise', {}),
        'createdAt': now,
        'updatedAt': now,
    }

    _agents_store[agent_id] = agent
    return jsonify({'agent': agent}), 201


@agents_bp.route('', methods=['GET'])
def list_agents():
    """List all agents."""
    agents = sorted(_agents_store.values(), key=lambda a: a['createdAt'], reverse=True)
    return jsonify({'agents': agents})


@agents_bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a single agent by ID."""
    agent = _agents_store.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify({'agent': agent})


@agents_bp.route('/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent."""
    if agent_id not in _agents_store:
        return jsonify({'error': 'Agent not found'}), 404
    del _agents_store[agent_id]
    return jsonify({'ok': True})


@agents_bp.route('/preview-response', methods=['POST'])
def preview_response():
    """Generate a sample in-character response for the agent preview step."""
    data = request.get_json() or {}
    basic = data.get('basic', {})
    personality = data.get('personality', {})
    expertise = data.get('expertise', {})

    try:
        from ..utils.llm_client import LLMClient
        client = LLMClient()

        tags = ', '.join(expertise.get('tags', [])) or 'general'
        biases = ', '.join(expertise.get('biases', [])) or 'none specified'
        goals = ', '.join(expertise.get('goals', [])) or 'none specified'

        prompt = (
            "You are roleplaying as a GTM simulation agent. Stay fully in character.\n\n"
            f"Name: {basic.get('name', 'Agent')}\n"
            f"Role: {basic.get('role', 'Stakeholder')}\n"
            f"Department: {basic.get('department', 'General')}\n"
            f"Backstory: {basic.get('backstory', 'N/A')}\n\n"
            "Personality (0-100 scale):\n"
            f"- Analytical: {personality.get('analytical', 50)}\n"
            f"- Creative: {personality.get('creative', 50)}\n"
            f"- Assertive: {personality.get('assertive', 50)}\n"
            f"- Empathetic: {personality.get('empathetic', 50)}\n"
            f"- Risk Tolerant: {personality.get('riskTolerant', 50)}\n"
            f"- Communication Style: {personality.get('communicationStyle', 'balanced')}\n\n"
            f"Expertise: {tags}\n"
            f"Known Biases: {biases}\n"
            f"Goals: {goals}\n\n"
            "Scenario: A vendor is pitching a new AI-powered customer support platform "
            "to your organization. Give a brief (2-3 sentence) authentic reaction "
            "based on your personality and expertise."
        )

        response = client.chat(
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.8,
            max_tokens=256,
        )
        return jsonify({'response': response})
    except Exception:
        response = _template_response(basic, personality)
        return jsonify({'response': response})


def _template_response(basic, personality):
    """Fallback template response when no LLM is available."""
    role = basic.get('role', 'Stakeholder')
    analytical = personality.get('analytical', 50)
    creative = personality.get('creative', 50)
    assertive = personality.get('assertive', 50)
    risk_tolerant = personality.get('riskTolerant', 50)

    if analytical > 70:
        return (
            f"As {role}, I'd need to see concrete metrics before committing. "
            "Show me the ROI data, integration benchmarks, and a comparison against our current stack."
        )
    if creative > 70:
        return (
            "Interesting approach — I can see some creative applications for our team. "
            "I'd love to explore how we could customize this beyond the standard use cases."
        )
    if assertive > 70:
        return (
            "Let's cut to the chase — what makes this different from the dozen other "
            "tools I've evaluated? I need clear differentiation and a pilot timeline within 2 weeks."
        )
    if risk_tolerant > 70:
        return (
            "I'm intrigued. Our team has been looking for something like this. "
            "Let's set up a pilot — I'm willing to test this in production with a small segment."
        )
    return (
        "This looks promising, but I'd want to involve the broader team in the evaluation. "
        "Can you provide case studies from companies similar to ours and arrange a demo for my colleagues?"
    )


# ------------------------------------------------------------------
# Archetypes (Agent Factory)
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
# Agent Factory creation
# ------------------------------------------------------------------

@agents_bp.route('/create', methods=['POST'])
def create_agent_from_archetype():
    """Create a single agent from an archetype."""
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
    """Create a batch of agents from a distribution spec."""
    data = request.get_json()
    if not data or 'distribution' not in data:
        return jsonify({'error': 'distribution is required'}), 400

    distribution = data['distribution']
    if not isinstance(distribution, list) or len(distribution) == 0:
        return jsonify({'error': 'distribution must be a non-empty list'}), 400

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
    """Create agents from a GTM scenario template's agent_config."""
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
