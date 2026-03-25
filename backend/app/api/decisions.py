"""
Decision Explanation API
Endpoints for generating human-readable explanations of agent decisions.
"""

from flask import Blueprint, jsonify, request

from ..services.decision_explainer import DecisionExplainer
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.decisions')

decisions_bp = Blueprint('decisions', __name__, url_prefix='/api/v1/decisions')

_explainer = DecisionExplainer()


@decisions_bp.route('/explain', methods=['POST'])
def explain_decision():
    """
    Generate a plain-English explanation of an agent's decision.

    Request JSON:
        {
            "agent_id": "agent_01",
            "decision": { "action": "post_tweet", "target": "VP Engineering", ... },
            "context": { "traits": ["analytical", "cautious"], "scenario": "..." }
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    agent_id = data.get('agent_id')
    decision = data.get('decision')
    if not agent_id or not decision:
        return jsonify({
            "success": False,
            "error": "agent_id and decision are required",
        }), 400

    try:
        result = _explainer.explain_decision(
            agent_id=agent_id,
            decision=decision,
            context=data.get('context'),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error("explain_decision failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@decisions_bp.route('/counterfactual', methods=['POST'])
def counterfactual():
    """
    Generate a counterfactual: what would have happened with a different choice.

    Request JSON:
        {
            "decision": { "action": "post_tweet", ... },
            "alternative": { "action": "send_email", ... },
            "context": { ... }
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    decision = data.get('decision')
    alternative = data.get('alternative')
    if not decision or not alternative:
        return jsonify({
            "success": False,
            "error": "decision and alternative are required",
        }), 400

    try:
        result = _explainer.generate_counterfactual(
            decision=decision,
            alternative=alternative,
            context=data.get('context'),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error("counterfactual failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@decisions_bp.route('/score', methods=['POST'])
def score_decision():
    """
    Retrospectively score how good a decision was given its outcome.

    Request JSON:
        {
            "decision": { "action": "post_tweet", ... },
            "outcome": { "engagement": 8, "reach": 15, ... },
            "context": { ... }
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body required"}), 400

    decision = data.get('decision')
    outcome = data.get('outcome')
    if not decision or not outcome:
        return jsonify({
            "success": False,
            "error": "decision and outcome are required",
        }), 400

    try:
        result = _explainer.score_decision_quality(
            decision=decision,
            outcome=outcome,
            context=data.get('context'),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error("score_decision failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
