"""
Temporal Memory API

Endpoints for Zep-backed temporal memory: adding episodes, querying at a
point in time, tracking entity evolution, and detecting contradictions.
"""

from flask import Blueprint, jsonify, request

from ..services.zep_temporal_memory import TemporalMemory
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.temporal_memory')

temporal_memory_bp = Blueprint('temporal_memory', __name__, url_prefix='/api/v1/temporal-memory')

# Lazy singleton — created on first request so Config is loaded
_memory: TemporalMemory | None = None


def _get_memory() -> TemporalMemory:
    global _memory
    if _memory is None:
        _memory = TemporalMemory()
    return _memory


@temporal_memory_bp.route('/episodes', methods=['POST'])
def add_episode():
    """Add a timestamped conversation episode.

    Body JSON:
        session_id (str, required): Graph/session ID.
        messages (list, required): ``[{"role": "...", "content": "..."}]``
        timestamp (str, optional): ISO 8601 timestamp.
    """
    data = request.get_json(silent=True) or {}

    session_id = data.get('session_id')
    messages = data.get('messages')

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    if not messages or not isinstance(messages, list):
        return jsonify({"error": "messages must be a non-empty list"}), 400

    try:
        result = _get_memory().add_episode(
            session_id=session_id,
            messages=messages,
            timestamp=data.get('timestamp'),
        )
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"add_episode error: {e}")
        return jsonify({"error": str(e)}), 500


@temporal_memory_bp.route('/query', methods=['POST'])
def query_at_time():
    """Retrieve facts known at a specific time.

    Body JSON:
        session_id (str, required): Graph/session ID.
        query (str, required): Search query.
        before_timestamp (str, required): Only facts valid before this time.
        limit (int, optional): Max results (default 20).
    """
    data = request.get_json(silent=True) or {}

    session_id = data.get('session_id')
    query = data.get('query')
    before_timestamp = data.get('before_timestamp')

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    if not query and query != '':
        return jsonify({"error": "query is required"}), 400
    if not before_timestamp:
        return jsonify({"error": "before_timestamp is required"}), 400

    try:
        result = _get_memory().query_at_time(
            session_id=session_id,
            query=query,
            before_timestamp=before_timestamp,
            limit=data.get('limit', 20),
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"query_at_time error: {e}")
        return jsonify({"error": str(e)}), 500


@temporal_memory_bp.route('/evolution/<session_id>/<entity>', methods=['GET'])
def get_memory_evolution(session_id: str, entity: str):
    """Show how knowledge about an entity changed over time.

    Path params:
        session_id: Graph/session ID.
        entity: Entity name to track.
    """
    try:
        result = _get_memory().get_memory_evolution(
            session_id=session_id,
            entity=entity,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"get_memory_evolution error: {e}")
        return jsonify({"error": str(e)}), 500


@temporal_memory_bp.route('/contradictions/<session_id>', methods=['GET'])
def get_contradictions(session_id: str):
    """Identify contradictory facts in memory.

    Path params:
        session_id: Graph/session ID.
    """
    try:
        result = _get_memory().get_contradictions(session_id=session_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"get_contradictions error: {e}")
        return jsonify({"error": str(e)}), 500


@temporal_memory_bp.route('/status', methods=['GET'])
def temporal_memory_status():
    """Check temporal memory backend status."""
    mem = _get_memory()
    return jsonify({
        "available": True,
        "backend": "zep" if mem.is_zep_available else "local",
    })
