"""
OASIS Metrics API
Unified endpoint for aggregated simulation metrics.
"""

import traceback

from flask import Blueprint, jsonify, request

from ..services.metrics_collector import MetricsCollector
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.metrics')

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/v1/metrics')


@metrics_bp.route('/simulation/<simulation_id>', methods=['GET'])
def get_simulation_metrics(simulation_id: str):
    """
    Collect aggregated metrics for a simulation.

    Returns a unified snapshot including summary stats, platform breakdown,
    action distribution, agent leaderboard, and per-round time-series.

    Query params:
        demo: if "true", returns generated demo data regardless of simulation state
    """
    try:
        use_demo = request.args.get('demo', '').lower() == 'true'

        if use_demo:
            data = MetricsCollector.generate_demo_metrics(simulation_id)
        else:
            data = MetricsCollector.collect(simulation_id)

        return jsonify({
            'success': True,
            'data': data,
        })

    except Exception as e:
        logger.error(f"Failed to collect metrics for {simulation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@metrics_bp.route('/demo', methods=['GET'])
def get_demo_metrics():
    """
    Generate demo metrics without requiring a real simulation.
    Useful for frontend development and demo mode.
    """
    try:
        data = MetricsCollector.generate_demo_metrics()
        return jsonify({
            'success': True,
            'data': data,
        })
    except Exception as e:
        logger.error(f"Failed to generate demo metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
