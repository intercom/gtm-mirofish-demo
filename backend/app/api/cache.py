"""
Cache API — store and replay completed simulation results offline.
"""

import traceback
from flask import Blueprint, jsonify, request

from ..services.simulation_cache import (
    cache_simulation,
    get_cached_simulation,
    list_cached_simulations,
    delete_cached_simulation,
)
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.cache')

cache_bp = Blueprint('cache', __name__, url_prefix='/api/v1/cache')


@cache_bp.route('/simulations', methods=['GET'])
def list_cached():
    """List all cached simulation snapshots (lightweight summaries)."""
    try:
        return jsonify({'success': True, 'data': list_cached_simulations()})
    except Exception as e:
        logger.error(f'Failed to list cache: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@cache_bp.route('/simulations/<simulation_id>', methods=['GET'])
def get_cached(simulation_id: str):
    """Get a full cached simulation snapshot for offline replay."""
    try:
        entry = get_cached_simulation(simulation_id)
        if not entry:
            return jsonify({'success': False, 'error': 'Not found in cache'}), 404
        return jsonify({'success': True, 'data': entry})
    except Exception as e:
        logger.error(f'Failed to get cache {simulation_id}: {e}')
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@cache_bp.route('/simulations/<simulation_id>', methods=['POST'])
def create_cached(simulation_id: str):
    """Cache a completed simulation for offline replay."""
    try:
        summary = cache_simulation(simulation_id)
        return jsonify({'success': True, 'data': summary}), 201
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Failed to cache {simulation_id}: {e}')
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@cache_bp.route('/simulations/<simulation_id>', methods=['DELETE'])
def delete_cached(simulation_id: str):
    """Delete a cached simulation."""
    try:
        deleted = delete_cached_simulation(simulation_id)
        if not deleted:
            return jsonify({'success': False, 'error': 'Not found in cache'}), 404
        return jsonify({'success': True, 'message': 'Deleted'})
    except Exception as e:
        logger.error(f'Failed to delete cache {simulation_id}: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
