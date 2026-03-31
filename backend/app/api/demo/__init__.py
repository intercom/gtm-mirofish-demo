"""
Demo API Blueprints — lightweight mock routes for demo mode.

Shared state and helpers used across all demo blueprints.
"""

import os
import time

from flask import jsonify

# Shared mutable state across demo blueprints.
# Using a dict for demo_speed so mutations propagate across module imports.
_graph_tasks = {}
_simulations = {}
_reports = {}
_config = {"demo_speed": float(os.environ.get("DEMO_SPEED", "1.0"))}

_BASE_GRAPH_BUILD_SECONDS = 6
_BASE_SIMULATION_RUN_SECONDS = 35
_BASE_REPORT_GEN_SECONDS = 18
TOTAL_ROUNDS = 144


def _speed():
    return max(0.1, _config["demo_speed"])


def GRAPH_BUILD_SECONDS():
    return _BASE_GRAPH_BUILD_SECONDS / _speed()


def SIMULATION_RUN_SECONDS():
    return _BASE_SIMULATION_RUN_SECONDS / _speed()


def REPORT_GEN_SECONDS():
    return _BASE_REPORT_GEN_SECONDS / _speed()


def _ok(data):
    return jsonify({"success": True, "data": data})


def _err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


def _elapsed(store, key):
    entry = store.get(key)
    if not entry:
        return 0.0
    return time.time() - entry["start"]


def register_demo_blueprints(app):
    """Register all demo blueprints with the Flask app."""
    from .graph import graph_demo_bp
    from .simulation import simulation_demo_bp
    from .report import report_demo_bp
    from .gtm import gtm_demo_bp
    from .settings import settings_demo_bp
    from .health import health_demo_bp

    app.register_blueprint(graph_demo_bp)
    app.register_blueprint(simulation_demo_bp)
    app.register_blueprint(report_demo_bp)
    app.register_blueprint(gtm_demo_bp)
    app.register_blueprint(settings_demo_bp)
    app.register_blueprint(health_demo_bp)
