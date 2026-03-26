"""
Settings API
Test connections and retrieve auth status for the Settings page.
"""

from flask import Blueprint, jsonify, request, current_app
from openai import OpenAI

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('/test-llm', methods=['POST'])
def test_llm():
    """Test LLM provider connection with a minimal API call."""
    data = request.get_json() or {}
    provider = data.get('provider', 'openai')
    api_key = data.get('apiKey', '')

    if not api_key:
        return jsonify({'ok': False, 'error': 'API key is required'}), 400

    from ..config import LLM_PROVIDERS
    provider_config = LLM_PROVIDERS.get(provider)
    if not provider_config:
        return jsonify({'ok': False, 'error': f'Unknown provider: {provider}'}), 400

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=provider_config['base_url'],
            timeout=15,
        )
        client.models.list()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@settings_bp.route('/test-zep', methods=['POST'])
def test_zep():
    """Test Zep Cloud connection using the SDK."""
    data = request.get_json() or {}
    api_key = data.get('apiKey', '')

    if not api_key:
        return jsonify({'ok': False, 'error': 'API key is required'}), 400

    try:
        from zep_cloud.client import Zep
        client = Zep(api_key=api_key)
        client.user.list(limit=1)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@settings_bp.route('/auth-status', methods=['GET'])
def auth_status():
    """Return current auth configuration and user info."""
    auth_enabled = current_app.config.get('AUTH_ENABLED', False)
    result = {
        'authEnabled': auth_enabled,
        'provider': current_app.config.get('AUTH_PROVIDER', 'google') if auth_enabled else None,
        'allowedDomain': current_app.config.get('AUTH_ALLOWED_DOMAIN') if auth_enabled else None,
        'user': None,
    }

    if auth_enabled:
        from flask import session
        user = session.get('user')
        if user:
            result['user'] = {
                'email': user.get('email'),
                'name': user.get('name'),
                'picture': user.get('picture'),
            }

    return jsonify(result)


# ============== Cache Management ==============

@settings_bp.route('/cache', methods=['GET'])
def cache_stats():
    """Return current cache statistics."""
    from ..services.cache import cache_manager
    return jsonify({'ok': True, 'data': cache_manager.stats()})


@settings_bp.route('/cache', methods=['DELETE'])
def cache_clear():
    """Clear all cached responses."""
    from ..services.cache import cache_manager
    removed = cache_manager.clear()
    return jsonify({'ok': True, 'cleared': removed})


@settings_bp.route('/cache/evict', methods=['POST'])
def cache_evict():
    """Evict expired entries from cache."""
    from ..services.cache import cache_manager
    evicted = cache_manager.evict_expired()
    return jsonify({'ok': True, 'evicted': evicted})
