"""
Pipeline API
GTM funnel analytics: snapshots, conversions, velocity, and forecast.
"""

from flask import Blueprint, jsonify, request

from ..services.pipeline_data_generator import (
    generate_funnel_history,
    generate_conversion_events,
    compute_velocity_metrics,
    compute_forecast,
)

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/pipeline')


@pipeline_bp.route('/funnel', methods=['GET'])
def funnel():
    """Current funnel snapshot with all stages."""
    history = generate_funnel_history()
    latest = history[-1]
    return jsonify({"success": True, "data": latest.to_dict()})


@pipeline_bp.route('/funnel/history', methods=['GET'])
def funnel_history():
    """Monthly funnel snapshots for trend analysis."""
    months = request.args.get('months', 6, type=int)
    months = max(1, min(months, 12))
    history = generate_funnel_history(months=months)
    return jsonify({
        "success": True,
        "data": {
            "months": months,
            "snapshots": [s.to_dict() for s in history],
        },
    })


@pipeline_bp.route('/conversions', methods=['GET'])
def conversions():
    """Conversion events with optional date range filter."""
    events = generate_conversion_events()

    start = request.args.get('start')
    end = request.args.get('end')

    if start:
        events = [e for e in events if e.timestamp >= start]
    if end:
        events = [e for e in events if e.timestamp <= end]

    return jsonify({
        "success": True,
        "data": {
            "total": len(events),
            "events": [e.to_dict() for e in events],
        },
    })


@pipeline_bp.route('/velocity', methods=['GET'])
def velocity():
    """Stage-by-stage velocity metrics (avg days, median days)."""
    metrics = compute_velocity_metrics()
    return jsonify({"success": True, "data": {"stages": metrics}})


@pipeline_bp.route('/forecast', methods=['GET'])
def forecast():
    """Revenue forecast based on current pipeline × probability."""
    data = compute_forecast()
    return jsonify({"success": True, "data": data})
