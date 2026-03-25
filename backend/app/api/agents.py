"""
Agents API — CRUD and preview for wizard-created agents.
"""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

agents_bp = Blueprint('agents', __name__, url_prefix='/api/v1/agents')

# In-memory store (replaced by DB in production)
_agents_store = {}


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
