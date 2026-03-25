"""
Health check API.
Exposes external service health so the frontend can display
degradation warnings and adapt its UI accordingly.
"""

from flask import Blueprint, jsonify

from ..utils.degradation import health_tracker

health_bp = Blueprint('health', __name__, url_prefix='/api/v1/health')


@health_bp.route('/services', methods=['GET'])
def service_health():
    """Return health status of all tracked external services."""
    status = health_tracker.get_status()
    all_healthy = all(info['healthy'] for info in status.values())
    return jsonify({
        'success': True,
        'healthy': all_healthy,
        'services': status,
    })
