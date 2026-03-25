"""Demo GTM Scenarios Blueprint — scenario templates and seed data."""

import json
from pathlib import Path

from flask import Blueprint

from . import _ok, _err

gtm_demo_bp = Blueprint('demo_gtm', __name__)

SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "gtm_scenarios"


def _load_scenarios():
    scenarios = []
    for p in sorted(SCENARIOS_DIR.glob("*.json")):
        with open(p) as f:
            scenarios.append(json.load(f))
    return scenarios


@gtm_demo_bp.route("/api/gtm/scenarios")
def list_scenarios():
    from flask import jsonify
    return jsonify({"scenarios": _load_scenarios()})


@gtm_demo_bp.route("/api/gtm/scenarios/<scenario_id>")
def get_scenario(scenario_id):
    from flask import jsonify
    for s in _load_scenarios():
        if s["id"] == scenario_id:
            return jsonify(s)
    return _err("Scenario not found", 404)


@gtm_demo_bp.route("/api/gtm/scenarios/<scenario_id>/seed-text")
def get_seed_text(scenario_id):
    for s in _load_scenarios():
        if s["id"] == scenario_id:
            return _ok({"seed_text": s.get("seed_text", "")})
    return _err("Scenario not found", 404)


@gtm_demo_bp.route("/api/gtm/seed-data/<data_type>")
def get_seed_data(data_type):
    samples = {
        "companies": [
            {"name": "Acme SaaS", "size": "500-1000", "industry": "SaaS"},
            {"name": "MedFirst Health", "size": "1000-2000", "industry": "Healthcare"},
            {"name": "PayStream Financial", "size": "200-500", "industry": "Fintech"},
            {"name": "ShopNova", "size": "500-1000", "industry": "E-commerce"},
            {"name": "CloudOps Inc", "size": "1000-2000", "industry": "SaaS"},
        ],
        "personas": [
            {"name": "Sarah Chen", "title": "VP of Support", "company": "Acme SaaS"},
            {"name": "Marcus Johnson", "title": "CX Director", "company": "MedFirst Health"},
            {"name": "Priya Patel", "title": "Head of Operations", "company": "PayStream Financial"},
            {"name": "David Kim", "title": "IT Leader", "company": "ShopNova"},
            {"name": "Rachel Torres", "title": "VP of Support", "company": "CloudOps Inc"},
        ],
    }
    return _ok(samples.get(data_type, []))
