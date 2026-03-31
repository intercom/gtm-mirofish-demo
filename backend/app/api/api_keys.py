"""
API Key Management endpoints.
Create, list, and revoke API keys for programmatic access.
"""

from flask import Blueprint, jsonify, request
from ..services.api_key_service import ApiKeyService, AVAILABLE_SCOPES

api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/api/v1/api-keys')


@api_keys_bp.route('', methods=['GET'])
def list_keys():
    """List all active API keys (without full key values)."""
    service = ApiKeyService()
    keys = service.list_keys()
    return jsonify({"ok": True, "data": keys})


@api_keys_bp.route('', methods=['POST'])
def create_key():
    """Create a new API key. Returns the full key value exactly once."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    scopes = data.get('scopes', [])

    if not name:
        return jsonify({"ok": False, "error": "Key name is required"}), 400

    if len(name) > 64:
        return jsonify({"ok": False, "error": "Key name must be 64 characters or fewer"}), 400

    service = ApiKeyService()
    result = service.create_key(name, scopes)
    return jsonify({"ok": True, "data": result}), 201


@api_keys_bp.route('/<key_id>', methods=['DELETE'])
def revoke_key(key_id):
    """Revoke an API key."""
    service = ApiKeyService()
    revoked = service.revoke_key(key_id)

    if not revoked:
        return jsonify({"ok": False, "error": "Key not found or already revoked"}), 404

    return jsonify({"ok": True})


@api_keys_bp.route('/scopes', methods=['GET'])
def list_scopes():
    """List available permission scopes."""
    return jsonify({"ok": True, "data": AVAILABLE_SCOPES})
