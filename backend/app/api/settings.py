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
    """Test Zep Cloud connection."""
    data = request.get_json() or {}
    api_key = data.get('apiKey', '')

    if not api_key:
        return jsonify({'ok': False, 'error': 'API key is required'}), 400

    try:
        import httpx
        resp = httpx.get(
            'https://api.getzep.com/api/v2/users',
            headers={'Authorization': f'Api-Key {api_key}'},
            timeout=15,
            params={'limit': 1},
        )
        if resp.status_code in (200, 404):
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'error': f'HTTP {resp.status_code}'}), 400
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@settings_bp.route('/service-status', methods=['GET'])
def service_status():
    """Return connectivity status of backend services (cheap check, no API calls)."""
    import os
    from ..config import Config

    llm_provider = os.environ.get('LLM_PROVIDER', '').lower()
    llm_key_set = bool(Config.LLM_API_KEY)
    zep_key_set = bool(Config.ZEP_API_KEY)

    llm_status = 'connected' if llm_key_set else 'demo'
    zep_status = 'connected' if zep_key_set else 'demo'

    overall = 'healthy'
    if not llm_key_set and not zep_key_set:
        overall = 'demo'
    elif not llm_key_set or not zep_key_set:
        overall = 'degraded'

    return jsonify({
        'success': True,
        'data': {
            'overall': overall,
            'services': {
                'llm': {
                    'status': llm_status,
                    'provider': llm_provider or 'none',
                    'model': Config.LLM_MODEL_NAME if llm_key_set else None,
                },
                'zep': {
                    'status': zep_status,
                },
                'oasis': {
                    'status': 'connected',
                },
            },
        },
    })


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
