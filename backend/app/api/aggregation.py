"""
Scenario Aggregation API
Cross-simulation comparison and statistical analysis endpoints.
"""

import traceback
from flask import Blueprint, jsonify, request

from ..services.scenario_aggregator import ScenarioAggregator
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.aggregation')

aggregation_bp = Blueprint('aggregation', __name__, url_prefix='/api/v1')


def _parse_ids() -> list:
    """Parse simulation IDs from 'ids' query parameter (comma-separated)."""
    raw = request.args.get('ids', '')
    return [sid.strip() for sid in raw.split(',') if sid.strip()]


@aggregation_bp.route('/simulations/aggregate', methods=['GET'])
def aggregate_simulations():
    """
    Aggregate metrics across multiple simulations.

    Query params:
        ids: comma-separated simulation IDs (required)
        mode: aggregation mode — 'metrics' (default), 'common', 'rare', 'ci', 'cluster', 'all'
        metric: metric name for confidence interval mode (default: 'total_actions')

    Returns aggregated data based on mode.
    """
    try:
        sim_ids = _parse_ids()
        if not sim_ids:
            return jsonify({
                "success": False,
                "error": "Missing 'ids' query parameter. Provide comma-separated simulation IDs."
            }), 400

        mode = request.args.get('mode', 'metrics')
        aggregator = ScenarioAggregator()

        if mode == 'metrics':
            result = aggregator.aggregate_metrics(sim_ids)
        elif mode == 'common':
            result = aggregator.find_common_outcomes(sim_ids)
        elif mode == 'rare':
            result = aggregator.find_rare_events(sim_ids)
        elif mode == 'ci':
            metric = request.args.get('metric', 'total_actions')
            result = aggregator.compute_confidence_intervals(sim_ids, metric)
        elif mode == 'cluster':
            result = aggregator.cluster_simulations(sim_ids)
        elif mode == 'all':
            result = {
                "metrics": aggregator.aggregate_metrics(sim_ids),
                "common_outcomes": aggregator.find_common_outcomes(sim_ids),
                "rare_events": aggregator.find_rare_events(sim_ids),
                "confidence_intervals": {
                    m: aggregator.compute_confidence_intervals(sim_ids, m)
                    for m in ["total_actions", "avg_sentiment", "unique_agents"]
                },
                "clusters": aggregator.cluster_simulations(sim_ids),
            }
        else:
            return jsonify({
                "success": False,
                "error": f"Unknown mode: {mode}. Valid: metrics, common, rare, ci, cluster, all"
            }), 400

        logger.info(f"Aggregation [{mode}] for {len(sim_ids)} simulations")

        return jsonify({
            "success": True,
            "data": result,
            "mode": mode,
        })

    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
