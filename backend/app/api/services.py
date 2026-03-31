"""
Unified Service Availability API
Single endpoint to check backend, LLM, and Zep availability using server-side config.
"""

from flask import Blueprint, jsonify, current_app
from openai import OpenAI

services_bp = Blueprint('services', __name__, url_prefix='/api/v1/services')


def _check_llm():
    """Check LLM provider availability using server-side config."""
    api_key = current_app.config.get('LLM_API_KEY')
    if not api_key:
        return {'status': 'unconfigured', 'message': 'LLM_API_KEY not set'}

    provider = current_app.config.get('LLM_PROVIDER', '').lower()
    base_url = current_app.config.get('LLM_BASE_URL')
    try:
        if provider == 'anthropic':
            import httpx
            resp = httpx.get(
                'https://api.anthropic.com/v1/models',
                headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01'},
                timeout=10,
            )
            if resp.status_code == 200:
                return {'status': 'ok'}
            return {'status': 'error', 'message': f'HTTP {resp.status_code}'}
        else:
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=10)
            client.models.list()
            return {'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def _check_zep():
    """Check Zep Cloud availability using server-side config."""
    api_key = current_app.config.get('ZEP_API_KEY')
    if not api_key:
        return {'status': 'unconfigured', 'message': 'ZEP_API_KEY not set'}

    try:
        import httpx
        resp = httpx.get(
            'https://api.getzep.com/api/v2/sessions',
            headers={'Authorization': f'Api-Key {api_key}'},
            timeout=10,
            params={'limit': 1},
        )
        if resp.status_code in (200, 404):
            return {'status': 'ok'}
        return {'status': 'error', 'message': f'HTTP {resp.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@services_bp.route('/status', methods=['GET'])
def status():
    """Unified service availability check.

    Returns status for all services: backend (always ok if reachable),
    LLM provider, and Zep Cloud. Each service returns one of:
      - ok: service is reachable and working
      - unconfigured: API key not set (demo mode for this service)
      - error: configured but unreachable
    """
    llm_result = _check_llm()
    zep_result = _check_zep()

    all_ok = llm_result['status'] == 'ok' and zep_result['status'] == 'ok'
    any_unconfigured = (
        llm_result['status'] == 'unconfigured'
        or zep_result['status'] == 'unconfigured'
    )

    return jsonify({
        'ok': all_ok,
        'demo': any_unconfigured,
        'services': {
            'backend': {'status': 'ok'},
            'llm': llm_result,
            'zep': zep_result,
        },
    })
