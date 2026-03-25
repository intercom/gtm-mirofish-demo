"""
Persona API — generate, list, and manage GTM buyer personas.

Endpoints:
  GET  /api/v1/personas                — list generated personas (session-scoped)
  POST /api/v1/personas/generate       — generate a team from scenario + graph
  GET  /api/v1/personas/<id>           — get a single persona
  PUT  /api/v1/personas/<id>           — update a persona
  POST /api/v1/personas/<id>/enhance   — enhance with simulation context
"""

import traceback

from flask import Blueprint, jsonify, request

from ..config import Config
from ..services.persona_from_graph import PersonaGenerator, Persona
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.personas')

personas_bp = Blueprint('personas', __name__, url_prefix='/api/v1/personas')

# In-memory store (session-scoped; resets on restart).
# Keyed by persona.id → Persona.
_persona_store: dict[str, Persona] = {}


# ─── helpers ───────────────────────────────────────────────────────

def _mock_personas() -> list[dict]:
    """Generate demo personas when no LLM/Zep keys are configured."""
    gen = PersonaGenerator()
    mock_scenario = {
        "id": "demo",
        "name": "Demo Scenario",
        "agent_config": {
            "persona_types": ["VP of Support", "CX Director", "IT Leader", "Head of Operations"],
            "firmographic_mix": {
                "industries": ["SaaS", "Healthcare", "Fintech", "E-commerce"],
                "company_sizes": ["200-500", "500-1000", "1000-2000"],
                "regions": ["North America", "EMEA", "APAC"],
            },
        },
    }
    personas = gen.generate_team(mock_scenario, num_agents=4)
    for p in personas:
        _persona_store[p.id] = p
    return [p.to_dict() for p in personas]


# ─── endpoints ─────────────────────────────────────────────────────

@personas_bp.route('', methods=['GET'])
def list_personas():
    """Return all personas in the current session."""
    personas = [p.to_dict() for p in _persona_store.values()]
    return jsonify({"personas": personas, "count": len(personas)})


@personas_bp.route('/generate', methods=['POST'])
def generate_personas():
    """
    Generate a team of personas.

    Request JSON:
        {
            "scenario": { ... scenario object ... },
            "num_agents": 10,          // optional, default 10
            "graph_id": "xxx"          // optional, uses graph from scenario if absent
        }

    In demo mode (no LLM key), returns template-based personas.
    """
    try:
        data = request.get_json() or {}
        scenario = data.get("scenario", {})
        num_agents = min(data.get("num_agents", 10), 100)

        if data.get("graph_id"):
            scenario["graph_id"] = data["graph_id"]

        gen = PersonaGenerator()
        personas = gen.generate_team(scenario, num_agents=num_agents)

        _persona_store.clear()
        for p in personas:
            _persona_store[p.id] = p

        return jsonify({
            "success": True,
            "personas": [p.to_dict() for p in personas],
            "count": len(personas),
            "source": personas[0].source if personas else "template",
        })
    except Exception as e:
        logger.error(f"Persona generation failed: {e}")
        logger.debug(traceback.format_exc())

        # Graceful degradation: return mock data
        try:
            mock = _mock_personas()
            return jsonify({
                "success": True,
                "personas": mock,
                "count": len(mock),
                "source": "template",
                "warning": f"Fell back to templates: {str(e)[:120]}",
            })
        except Exception as fallback_err:
            return jsonify({"success": False, "error": str(fallback_err)}), 500


@personas_bp.route('/<persona_id>', methods=['GET'])
def get_persona(persona_id: str):
    """Get a single persona by ID."""
    persona = _persona_store.get(persona_id)
    if not persona:
        return jsonify({"error": "Persona not found"}), 404
    return jsonify(persona.to_dict())


@personas_bp.route('/<persona_id>', methods=['PUT'])
def update_persona(persona_id: str):
    """Update fields on an existing persona."""
    persona = _persona_store.get(persona_id)
    if not persona:
        return jsonify({"error": "Persona not found"}), 404

    data = request.get_json() or {}
    updatable = [
        "name", "title", "department", "personality_traits", "expertise_areas",
        "biases", "known_facts", "goals", "communication_style",
        "decision_authority", "typical_objections", "firmographic", "mbti",
    ]
    for field in updatable:
        if field in data:
            setattr(persona, field, data[field])
    persona.source = "custom"

    return jsonify({"success": True, "persona": persona.to_dict()})


@personas_bp.route('/<persona_id>/enhance', methods=['POST'])
def enhance_persona(persona_id: str):
    """Enhance a persona with simulation context via LLM."""
    persona = _persona_store.get(persona_id)
    if not persona:
        return jsonify({"error": "Persona not found"}), 404

    data = request.get_json() or {}
    simulation_context = data.get("simulation_context", {})

    gen = PersonaGenerator()
    enhanced = gen.enhance_persona(persona, simulation_context)
    _persona_store[persona_id] = enhanced

    return jsonify({"success": True, "persona": enhanced.to_dict()})
