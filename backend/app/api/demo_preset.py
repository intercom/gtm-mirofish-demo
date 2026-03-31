"""
Demo Preset API — serves curated demo data for presentations.

When DEMO_PRESET=true, pre-built simulation/report/dashboard fixtures are
served from backend/data/demo_preset/ so the demo tells a compelling,
repeatable story about coalitions debating pipeline strategy.
"""

from flask import Blueprint, jsonify

from data.demo_preset.loader import (
    is_demo_preset_enabled,
    get_simulation,
    get_report,
    get_dashboard,
    get_preset_sim_id,
    get_preset_report_id,
)

demo_preset_bp = Blueprint('demo_preset', __name__, url_prefix='/api/v1/demo-preset')


def _ok(data):
    return jsonify({"success": True, "data": data})


def _err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


@demo_preset_bp.route('')
@demo_preset_bp.route('/')
def status():
    """Check if demo preset is available and loaded."""
    enabled = is_demo_preset_enabled()
    return _ok({
        "available": enabled,
        "loaded": enabled,
        "simulation_id": get_preset_sim_id() if enabled else None,
        "report_id": get_preset_report_id() if enabled else None,
    })


@demo_preset_bp.route('/load', methods=['POST'])
def load():
    """Load demo preset — returns IDs for the curated fixtures.

    When DEMO_PRESET=true the preset is always available, so this is a
    compatibility endpoint that returns the preset IDs without side effects.
    """
    if not is_demo_preset_enabled():
        return _err("Demo preset not enabled. Set DEMO_PRESET=true in environment.", 403)
    return _ok({
        "simulation_id": get_preset_sim_id(),
        "report_id": get_preset_report_id(),
        "graph_task_id": "demo-graph-preset",
    })


@demo_preset_bp.route('/simulation')
def simulation():
    """Return full preset simulation data including coalitions and belief changes."""
    if not is_demo_preset_enabled():
        return _err("Demo preset not enabled. Set DEMO_PRESET=true in environment.", 403)
    return _ok(get_simulation())


@demo_preset_bp.route('/report')
def report():
    """Return full preset report data."""
    if not is_demo_preset_enabled():
        return _err("Demo preset not enabled. Set DEMO_PRESET=true in environment.", 403)
    return _ok(get_report())


@demo_preset_bp.route('/dashboard')
def dashboard():
    """Return preset dashboard widget configuration."""
    if not is_demo_preset_enabled():
        return _err("Demo preset not enabled. Set DEMO_PRESET=true in environment.", 403)
    return _ok(get_dashboard())
