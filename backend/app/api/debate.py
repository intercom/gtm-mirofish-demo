"""
Debate API endpoints
Structured debate orchestration for agent simulations.
"""

from flask import Blueprint, jsonify, request

from ..services.debate_engine import DebateEngine
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.debate')

debate_bp = Blueprint('debate', __name__)

# Singleton engine instance (in-memory state, same pattern as TaskManager)
_engine = DebateEngine()


@debate_bp.route('/api/v1/debate/setup', methods=['POST'])
def setup_debate():
    """Configure a new debate.

    Body: {
        topic: str (required),
        agents: [{agent_id, name, role, company?, persona?, team?}] (required),
        format: 'oxford'|'panel'|'roundtable' (default 'oxford'),
        moderator_id: str (optional),
        max_rebuttal_rounds: int (default 2)
    }
    """
    data = request.get_json(silent=True) or {}

    topic = data.get('topic')
    agents = data.get('agents')
    if not topic or not agents:
        return jsonify({"error": "topic and agents are required"}), 400

    if not isinstance(agents, list) or len(agents) < 2:
        return jsonify({"error": "at least 2 agents required"}), 400

    fmt = data.get('format', 'oxford')
    if fmt not in ('oxford', 'panel', 'roundtable'):
        return jsonify({"error": f"invalid format: {fmt}"}), 400

    try:
        state = _engine.setup_debate(
            topic=topic,
            agents=agents,
            format=fmt,
            moderator_id=data.get('moderator_id'),
            max_rebuttal_rounds=data.get('max_rebuttal_rounds', 2),
        )
        return jsonify(state.to_dict()), 201
    except Exception as e:
        logger.error(f"Debate setup failed: {e}")
        return jsonify({"error": str(e)}), 500


@debate_bp.route('/api/v1/debate/<debate_id>', methods=['GET'])
def get_debate(debate_id):
    """Get current debate state."""
    state = _engine.get_debate(debate_id)
    if not state:
        return jsonify({"error": "debate not found"}), 404
    return jsonify(state.to_dict())


@debate_bp.route('/api/v1/debate', methods=['GET'])
def list_debates():
    """List all debates."""
    return jsonify(_engine.list_debates())


@debate_bp.route('/api/v1/debate/<debate_id>/opening', methods=['POST'])
def run_opening(debate_id):
    """Run opening statements phase."""
    try:
        args = _engine.run_opening_statements(debate_id)
        state = _engine.get_debate(debate_id)
        return jsonify({
            "phase": "opening_statements",
            "arguments": [_arg_to_dict(a) for a in args],
            "debate": state.to_dict(),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Opening statements failed: {e}")
        return jsonify({"error": str(e)}), 500


@debate_bp.route('/api/v1/debate/<debate_id>/rebuttal', methods=['POST'])
def run_rebuttal(debate_id):
    """Run a rebuttal round."""
    try:
        args = _engine.run_rebuttal_round(debate_id)
        state = _engine.get_debate(debate_id)
        return jsonify({
            "phase": "rebuttal",
            "rebuttal_round": state.rebuttal_round,
            "arguments": [_arg_to_dict(a) for a in args],
            "persuasion_events": [
                {
                    "agent_name": p.agent_name,
                    "from_position": p.from_position,
                    "to_position": p.to_position,
                    "round_num": p.round_num,
                }
                for p in state.persuasion_events
            ],
            "debate": state.to_dict(),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Rebuttal failed: {e}")
        return jsonify({"error": str(e)}), 500


@debate_bp.route('/api/v1/debate/<debate_id>/cross-examination', methods=['POST'])
def run_cross_examination(debate_id):
    """Run cross-examination between two agents.

    Body: { questioner_id: str, respondent_id: str }
    """
    data = request.get_json(silent=True) or {}
    questioner_id = data.get('questioner_id')
    respondent_id = data.get('respondent_id')

    if not questioner_id or not respondent_id:
        return jsonify({"error": "questioner_id and respondent_id are required"}), 400

    try:
        result = _engine.run_cross_examination(debate_id, questioner_id, respondent_id)
        state = _engine.get_debate(debate_id)
        return jsonify({
            "phase": "cross_examination",
            "question": _arg_to_dict(result["question"]),
            "answer": _arg_to_dict(result["answer"]),
            "debate": state.to_dict(),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Cross-examination failed: {e}")
        return jsonify({"error": str(e)}), 500


@debate_bp.route('/api/v1/debate/<debate_id>/closing', methods=['POST'])
def run_closing(debate_id):
    """Run closing statements phase."""
    try:
        args = _engine.run_closing_statements(debate_id)
        state = _engine.get_debate(debate_id)
        return jsonify({
            "phase": "closing_statements",
            "arguments": [_arg_to_dict(a) for a in args],
            "debate": state.to_dict(),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Closing statements failed: {e}")
        return jsonify({"error": str(e)}), 500


@debate_bp.route('/api/v1/debate/<debate_id>/vote', methods=['POST'])
def run_vote(debate_id):
    """Run the vote and get results."""
    try:
        result = _engine.run_vote(debate_id)
        state = _engine.get_debate(debate_id)
        return jsonify({
            "phase": "vote",
            "result": result,
            "debate": state.to_dict(),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Vote failed: {e}")
        return jsonify({"error": str(e)}), 500


def _arg_to_dict(arg):
    return {
        "agent_id": arg.agent_id,
        "agent_name": arg.agent_name,
        "phase": arg.phase,
        "content": arg.content,
        "team": arg.team,
        "quality_score": arg.quality_score,
        "timestamp": arg.timestamp,
        "target_agent_id": arg.target_agent_id,
    }
