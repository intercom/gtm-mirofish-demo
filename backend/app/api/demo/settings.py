"""Demo Settings Blueprint — mock connection test endpoints."""

from flask import Blueprint, jsonify

settings_demo_bp = Blueprint('demo_settings', __name__)


@settings_demo_bp.route("/api/settings/test-llm", methods=["POST"])
def test_llm():
    return jsonify({
        "ok": True,
        "model": "claude-sonnet-4-20250514",
        "message": "Demo mode — connection simulated",
    })


@settings_demo_bp.route("/api/settings/test-zep", methods=["POST"])
def test_zep():
    return jsonify({
        "ok": True,
        "message": "Demo mode — connection simulated",
    })


@settings_demo_bp.route("/api/settings/auth-status")
def auth_status():
    return jsonify({"authEnabled": False})
