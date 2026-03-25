"""
Memory search and retrieval API endpoints.
Provides search, agent listing, and topic extraction for the memory viewer.
"""

import traceback
from flask import Blueprint, request, jsonify

from ..config import Config
from ..services.memory_search import MemorySearchService
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.memory')

memory_bp = Blueprint('memory', __name__)


@memory_bp.route('/api/memory/<graph_id>/search', methods=['POST'])
def search_memories(graph_id: str):
    """
    Search agent memories in the knowledge graph.

    POST body:
        query: str - search text (optional, empty returns all)
        agent_name: str - filter by agent (optional)
        memory_type: str - filter by type: facts|beliefs|decisions (optional)
        sort_by: str - 'relevance' or 'chronological' (default: relevance)
        limit: int - max results (default: 50)
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get('query', '')
        agent_name = data.get('agent_name') or None
        memory_type = data.get('memory_type') or None
        sort_by = data.get('sort_by', 'relevance')
        limit = min(int(data.get('limit', 50)), 200)

        svc = MemorySearchService(graph_id)
        result = svc.search(
            query=query,
            agent_name=agent_name,
            memory_type=memory_type,
            sort_by=sort_by,
            limit=limit,
        )

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@memory_bp.route('/api/memory/<graph_id>/agents', methods=['GET'])
def list_agents(graph_id: str):
    """List agent names available in the knowledge graph."""
    try:
        svc = MemorySearchService(graph_id)
        agents = svc.get_agents()
        return jsonify({'success': True, 'data': agents})

    except Exception as e:
        logger.error(f"List agents failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@memory_bp.route('/api/memory/<graph_id>/topics', methods=['GET'])
def get_topics(graph_id: str):
    """
    Get memory topics for word cloud visualization.

    Query params:
        agent_name: str - filter by agent (optional)
        top_n: int - number of topics (default: 30)
    """
    try:
        agent_name = request.args.get('agent_name') or None
        top_n = min(int(request.args.get('top_n', 30)), 100)

        svc = MemorySearchService(graph_id)
        topics = svc.get_topics(agent_name=agent_name, top_n=top_n)

        return jsonify({'success': True, 'data': topics})

    except Exception as e:
        logger.error(f"Get topics failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500
