"""
Persona Customization API
CRUD + LLM-powered generation for agent personas.
"""

from flask import Blueprint, jsonify, request

from ..services import persona_service
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.personas')

personas_bp = Blueprint('personas', __name__, url_prefix='/api/agents')


@personas_bp.route('/personas', methods=['GET'])
def list_personas():
    """List available persona templates and generated personas."""
    source = request.args.get('source')  # optional filter: template|generated|custom
    personas = persona_service.list_personas(source=source)
    return jsonify({'personas': personas, 'total': len(personas)})


@personas_bp.route('/personas/generate', methods=['POST'])
def generate_personas():
    """Generate personas from scenario parameters. Uses LLM when available, mock otherwise."""
    data = request.get_json() or {}
    scenario_type = data.get('scenario_type')
    if not scenario_type:
        return jsonify({'error': 'scenario_type is required'}), 400

    num_agents = data.get('num_agents', 4)
    if not isinstance(num_agents, int) or num_agents < 1 or num_agents > 20:
        return jsonify({'error': 'num_agents must be an integer between 1 and 20'}), 400

    role_distribution = data.get('role_distribution')
    personality_diversity = data.get('personality_diversity', 0.5)
    if not isinstance(personality_diversity, (int, float)) or not (0 <= personality_diversity <= 1):
        return jsonify({'error': 'personality_diversity must be a number between 0 and 1'}), 400

    try:
        personas = persona_service.generate_personas(
            scenario_type=scenario_type,
            num_agents=num_agents,
            role_distribution=role_distribution,
            personality_diversity=personality_diversity,
        )
        return jsonify({'personas': personas, 'total': len(personas)})
    except Exception as e:
        logger.exception("Persona generation failed")
        return jsonify({'error': str(e)}), 500


@personas_bp.route('/personas/<persona_id>', methods=['GET'])
def get_persona(persona_id: str):
    """Get full persona details by ID."""
    persona = persona_service.get_persona(persona_id)
    if persona is None:
        return jsonify({'error': 'Persona not found'}), 404
    return jsonify(persona)


@personas_bp.route('/personas/<persona_id>', methods=['PUT'])
def update_persona(persona_id: str):
    """Customize a generated persona. Sets source to 'custom'."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    persona = persona_service.update_persona(persona_id, data)
    if persona is None:
        return jsonify({'error': 'Persona not found'}), 404
    return jsonify(persona)


@personas_bp.route('/personas/<persona_id>/clone', methods=['POST'])
def clone_persona(persona_id: str):
    """Clone and optionally modify a persona."""
    overrides = request.get_json() or {}
    persona = persona_service.clone_persona(persona_id, overrides=overrides)
    if persona is None:
        return jsonify({'error': 'Persona not found'}), 404
    return jsonify(persona), 201
