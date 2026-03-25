"""
Health monitoring API.
Exposes backend health metrics collected by the HealthMonitor service.
"""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__, url_prefix='/api/v1/health')


@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """Return current health metrics, alerts, and hourly snapshots."""
    from ..services.health_monitor import health_monitor
    return jsonify(health_monitor.get_metrics())
