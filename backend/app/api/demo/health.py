"""Demo Health Blueprint — health check, auth stubs, and demo playback control."""

from flask import Blueprint, jsonify, request

from . import (
    _config, _graph_tasks, _simulations, _reports, _ok, _err,
)

health_demo_bp = Blueprint('demo_health', __name__)


@health_demo_bp.route("/api/health")
def health():
    return jsonify({"status": "ok", "mode": "demo"})


@health_demo_bp.route("/api/auth/logout")
def auth_logout():
    return jsonify({"ok": True})


@health_demo_bp.route("/api/demo/speed", methods=["GET", "POST"])
def demo_speed():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        _config["demo_speed"] = max(0.1, float(body.get("speed", 1.0)))
        return _ok({"speed": _config["demo_speed"]})
    return _ok({"speed": _config["demo_speed"]})


@health_demo_bp.route("/api/demo/skip/<phase>", methods=["POST"])
def demo_skip(phase):
    """Instantly complete a phase by backdating its start time."""
    if phase == "graph":
        for task_id in _graph_tasks:
            _graph_tasks[task_id]["start"] = 0
        return _ok({"skipped": "graph"})
    elif phase == "simulation":
        for sim_id in _simulations:
            _simulations[sim_id]["start"] = 0
        return _ok({"skipped": "simulation"})
    elif phase == "report":
        for report_id in _reports:
            _reports[report_id]["start"] = 0
        return _ok({"skipped": "report"})
    return _err(f"Unknown phase: {phase}")


@health_demo_bp.route("/api/demo/reset", methods=["POST"])
def demo_reset():
    """Clear all in-memory state for a fresh demo."""
    _graph_tasks.clear()
    _simulations.clear()
    _reports.clear()
    _config["demo_speed"] = 1.0
    return _ok({"reset": True})
