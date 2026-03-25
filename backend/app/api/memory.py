"""
Agent memory API endpoints.

Exposes the AgentMemory abstraction layer over REST. Works in demo/mock
mode (in-memory backend) when no ZEP_API_KEY is configured.
"""

from typing import Optional

from flask import Blueprint, jsonify, request

from ..services.agent_memory import AgentMemory
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.memory')

memory_bp = Blueprint('memory', __name__, url_prefix='/api/v1/memory')

_memory: Optional[AgentMemory] = None


def _get_memory() -> AgentMemory:
    global _memory
    if _memory is None:
        _memory = AgentMemory()
    return _memory


@memory_bp.route('/store', methods=['POST'])
def store_message():
    """Store a message in agent memory."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    agent_id = data.get("agent_id")
    session_id = data.get("session_id")
    role = data.get("role")
    content = data.get("content")

    if not all([agent_id, session_id, role, content]):
        return jsonify({"error": "agent_id, session_id, role, and content are required"}), 400

    try:
        msg = _get_memory().store_message(
            agent_id=agent_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=data.get("metadata"),
        )
        return jsonify(msg.to_dict()), 201
    except Exception as exc:
        logger.error(f"Failed to store message: {exc}")
        return jsonify({"error": str(exc)}), 500


@memory_bp.route('/history/<agent_id>/<session_id>', methods=['GET'])
def get_history(agent_id: str, session_id: str):
    """Get recent messages for an agent in a session."""
    last_n = request.args.get("last_n", 10, type=int)
    try:
        messages = _get_memory().get_history(agent_id, session_id, last_n=last_n)
        return jsonify({
            "agent_id": agent_id,
            "session_id": session_id,
            "messages": [m.to_dict() for m in messages],
            "count": len(messages),
        })
    except Exception as exc:
        logger.error(f"Failed to get history: {exc}")
        return jsonify({"error": str(exc)}), 500


@memory_bp.route('/search', methods=['POST'])
def search_memory():
    """Semantic/keyword search over an agent's memory."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    agent_id = data.get("agent_id")
    query = data.get("query")
    if not agent_id or not query:
        return jsonify({"error": "agent_id and query are required"}), 400

    try:
        limit = data.get("limit", 5)
        results = _get_memory().search_memory(agent_id, query, limit=limit)
        return jsonify({
            "agent_id": agent_id,
            "query": query,
            "results": [r.to_dict() for r in results],
            "count": len(results),
        })
    except Exception as exc:
        logger.error(f"Failed to search memory: {exc}")
        return jsonify({"error": str(exc)}), 500


@memory_bp.route('/facts/<agent_id>', methods=['GET'])
def get_facts(agent_id: str):
    """Get extracted facts about an agent."""
    try:
        facts = _get_memory().get_facts(agent_id)
        return jsonify({
            "agent_id": agent_id,
            "facts": facts,
            "count": len(facts),
        })
    except Exception as exc:
        logger.error(f"Failed to get facts: {exc}")
        return jsonify({"error": str(exc)}), 500


@memory_bp.route('/<agent_id>', methods=['DELETE'])
def clear_all_memory(agent_id: str):
    """Clear all memory for an agent."""
    try:
        _get_memory().clear_memory(agent_id)
        return jsonify({"ok": True, "agent_id": agent_id})
    except Exception as exc:
        logger.error(f"Failed to clear memory: {exc}")
        return jsonify({"error": str(exc)}), 500


@memory_bp.route('/<agent_id>/<session_id>', methods=['DELETE'])
def clear_session_memory(agent_id: str, session_id: str):
    """Clear memory for a specific agent session."""
    try:
        _get_memory().clear_memory(agent_id, session_id=session_id)
        return jsonify({"ok": True, "agent_id": agent_id, "session_id": session_id})
    except Exception as exc:
        logger.error(f"Failed to clear session memory: {exc}")
        return jsonify({"error": str(exc)}), 500


@memory_bp.route('/status', methods=['GET'])
def memory_status():
    """Return which memory backend is active."""
    mem = _get_memory()
    return jsonify({
        "backend": mem.backend_type,
        "available": True,
    })
