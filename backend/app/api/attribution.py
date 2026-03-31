"""
Attribution analysis API endpoints.
"""

from flask import Blueprint, jsonify, request

from ..services.attribution_service import get_attribution_analysis
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.attribution')

attribution_bp = Blueprint('attribution', __name__, url_prefix='/api/v1/attribution')


@attribution_bp.route('/analysis', methods=['GET'])
def get_analysis():
    """Return full attribution analysis with demo data."""
    simulation_id = request.args.get('simulation_id')
    try:
        data = get_attribution_analysis(simulation_id=simulation_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Attribution analysis failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
