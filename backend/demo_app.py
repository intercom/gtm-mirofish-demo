"""
MiroFish Demo Backend — Lightweight mock Flask server.

Serves realistic, pre-built demo data for all frontend endpoints so the app
can run without the heavy camel-ai / PyTorch production backend.  Total
image size drops from ~5.8 GB to ~150 MB.

Routes are organized into Flask Blueprints under app/api/demo/.
"""

import os
import sys
import importlib.util as _ilu
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
load_dotenv(override=True)

# Add backend/ to sys.path for llm_client, and app/api/ for the demo package.
# Importing as "from demo import ..." avoids loading the production app/__init__.py.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _backend_dir)
sys.path.insert(0, os.path.join(_backend_dir, "app", "api"))

from flask import Flask, jsonify, request
from flask_cors import CORS

from demo import register_demo_blueprints

app = Flask(__name__)
CORS(app)
register_demo_blueprints(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data):
    return jsonify({"success": True, "data": data})


def _err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


# ---------------------------------------------------------------------------
# What-If Analysis API
# ---------------------------------------------------------------------------

_spec = _ilu.spec_from_file_location(
    "whatif_engine", Path(__file__).parent / "app/services/whatif_engine.py",
)
_whatif_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_whatif_mod)
WhatIfEngine = _whatif_mod.WhatIfEngine

_whatif_engine = WhatIfEngine()


@app.route("/api/v1/whatif/scenarios", methods=["POST"])
def whatif_create_scenario():
    """Create a what-if scenario variant from a base with modifications."""
    body = request.get_json(silent=True) or {}
    base_id = body.get("base_scenario_id")
    modifications = body.get("modifications", [])
    label = body.get("label", "")

    if not modifications:
        return _err("At least one modification is required")

    try:
        scenario = _whatif_engine.create_scenario(base_id, modifications, label)
        return _ok(scenario.to_dict())
    except Exception as e:
        return _err(str(e))


@app.route("/api/v1/whatif/scenarios", methods=["GET"])
def whatif_list_scenarios():
    """List all what-if scenarios."""
    scenarios = _whatif_engine.list_scenarios()
    return _ok({"scenarios": [s.to_dict() for s in scenarios]})


@app.route("/api/v1/whatif/scenarios/<scenario_id>")
def whatif_get_scenario(scenario_id):
    """Get a specific what-if scenario."""
    scenario = _whatif_engine.get_scenario(scenario_id)
    if not scenario:
        return _err("Scenario not found", 404)
    return _ok(scenario.to_dict())


@app.route("/api/v1/whatif/scenarios/<scenario_id>/run", methods=["POST"])
def whatif_run_scenario(scenario_id):
    """Run a what-if scenario and return results."""
    try:
        results = _whatif_engine.run_scenario(scenario_id)
        return _ok(results.to_dict())
    except ValueError as e:
        return _err(str(e), 404)
    except Exception as e:
        return _err(str(e))


@app.route("/api/v1/whatif/scenarios/<scenario_id>/results")
def whatif_get_results(scenario_id):
    """Get results for a previously-run scenario."""
    results = _whatif_engine.get_results(scenario_id)
    if not results:
        return _err("No results found. Run the scenario first.", 404)
    return _ok(results.to_dict())


@app.route("/api/v1/whatif/compare", methods=["POST"])
def whatif_compare():
    """Compare a variant to its base scenario."""
    body = request.get_json(silent=True) or {}
    base_id = body.get("base_id", "")
    variant_id = body.get("variant_id", "")

    if not base_id or not variant_id:
        return _err("Both base_id and variant_id are required")

    try:
        comparison = _whatif_engine.compare_to_base(base_id, variant_id)
        return _ok(comparison.to_dict())
    except ValueError as e:
        return _err(str(e), 404)


@app.route("/api/v1/whatif/sensitivity", methods=["POST"])
def whatif_sensitivity():
    """Run a parameter sensitivity sweep."""
    body = request.get_json(silent=True) or {}
    base_id = body.get("base_scenario_id")
    parameter = body.get("parameter", "")
    value_range = body.get("value_range", [])

    if not parameter:
        return _err("parameter is required")
    if not value_range or len(value_range) < 2:
        return _err("value_range must contain at least 2 values")

    try:
        result = _whatif_engine.run_sensitivity(base_id, parameter, value_range)
        return _ok(result.to_dict())
    except Exception as e:
        return _err(str(e))


@app.route("/api/v1/whatif/scenarios/<base_id>/variants")
def whatif_get_variants(base_id):
    """Get all variants linked to a base scenario."""
    variants = _whatif_engine.get_variants(base_id)
    return _ok({"variants": [v.to_dict() for v in variants]})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"MiroFish Demo Backend starting on port {port} (demo mode)")
    app.run(host="0.0.0.0", port=port, debug=debug)
