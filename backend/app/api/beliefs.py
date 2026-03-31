"""
Beliefs API
Endpoints for agent belief system tracking and analysis.
"""

from flask import Blueprint, jsonify, request

from ..config import Config
from ..services.belief_tracker import (
    BELIEF_DIMENSIONS,
    extract_beliefs_from_actions,
    extract_beliefs_llm,
    generate_demo_beliefs,
)
from ..utils.logger import get_logger

logger = get_logger('mirofish.beliefs')

beliefs_bp = Blueprint('beliefs', __name__, url_prefix='/api/v1/beliefs')


@beliefs_bp.route('/dimensions', methods=['GET'])
def get_dimensions():
    """Return the list of tracked belief dimensions with display metadata."""
    meta = {
        'product_quality': {'label': 'Product Quality', 'color': '#2068FF'},
        'pricing': {'label': 'Pricing Perception', 'color': '#ff5600'},
        'brand_trust': {'label': 'Brand Trust', 'color': '#009900'},
        'competitive_position': {'label': 'Competitive Position', 'color': '#AA00FF'},
        'adoption_intent': {'label': 'Adoption Intent', 'color': '#E67E00'},
    }
    return jsonify({
        'dimensions': [
            {'key': d, **meta.get(d, {'label': d, 'color': '#888'})}
            for d in BELIEF_DIMENSIONS
        ]
    })


@beliefs_bp.route('/<simulation_id>/extract', methods=['POST'])
def extract_beliefs(simulation_id):
    """
    Extract beliefs from simulation actions.

    Expects JSON body:
      { "actions": [...], "use_llm": false }

    If actions are not provided, returns demo data.
    """
    data = request.get_json(silent=True) or {}
    actions = data.get('actions', [])
    use_llm = data.get('use_llm', False)

    if not actions:
        logger.info(f"No actions for {simulation_id}, returning demo beliefs")
        beliefs = generate_demo_beliefs()
        return jsonify({
            'simulation_id': simulation_id,
            'mode': 'demo',
            'rounds': _format_rounds(beliefs),
        })

    if use_llm and Config.LLM_API_KEY:
        try:
            from ..utils.llm_client import LLMClient
            client = LLMClient()
            beliefs = extract_beliefs_llm(actions, client)
            mode = 'llm'
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to keywords")
            beliefs = extract_beliefs_from_actions(actions)
            mode = 'keyword'
    else:
        beliefs = extract_beliefs_from_actions(actions)
        mode = 'keyword'

    return jsonify({
        'simulation_id': simulation_id,
        'mode': mode,
        'rounds': _format_rounds(beliefs),
    })


@beliefs_bp.route('/demo', methods=['GET'])
def demo_beliefs():
    """Return demo belief data for testing/preview."""
    num_rounds = request.args.get('rounds', 10, type=int)
    num_rounds = max(1, min(50, num_rounds))
    beliefs = generate_demo_beliefs(num_rounds)
    return jsonify({
        'simulation_id': 'demo',
        'mode': 'demo',
        'rounds': _format_rounds(beliefs),
    })


def _format_rounds(beliefs: dict) -> list:
    """Convert internal round dict to sorted list for API response."""
    return [
        {
            'round': rn,
            **data,
        }
        for rn, data in sorted(beliefs.items())
    ]
