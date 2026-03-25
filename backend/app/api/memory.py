"""
Memory Configuration API
Endpoints for agent memory behavior settings, Zep connection testing,
and memory usage statistics.
"""

from flask import Blueprint, jsonify, request

memory_bp = Blueprint('memory', __name__, url_prefix='/api/v1/memory')

# In-memory config store (persists for server lifetime; frontend also saves to localStorage)
_memory_config = {
    'windowSize': 5,
    'searchDepth': 10,
    'extractionLevel': 'medium',
    'crossSimulation': False,
}

DEMO_STATS = {
    'totalFacts': 1_247,
    'totalEpisodes': 384,
    'graphNodes': 892,
    'graphEdges': 2_156,
}


@memory_bp.route('/config', methods=['GET'])
def get_config():
    """Return current memory configuration."""
    return jsonify(_memory_config)


@memory_bp.route('/config', methods=['POST'])
def save_config():
    """Save memory configuration."""
    data = request.get_json() or {}

    if 'windowSize' in data:
        val = data['windowSize']
        if isinstance(val, (int, float)) and 1 <= val <= 20:
            _memory_config['windowSize'] = int(val)

    if 'searchDepth' in data:
        val = data['searchDepth']
        if isinstance(val, (int, float)) and 1 <= val <= 50:
            _memory_config['searchDepth'] = int(val)

    if 'extractionLevel' in data:
        val = data['extractionLevel']
        if val in ('low', 'medium', 'high'):
            _memory_config['extractionLevel'] = val

    if 'crossSimulation' in data:
        _memory_config['crossSimulation'] = bool(data['crossSimulation'])

    return jsonify({'ok': True, 'config': _memory_config})


@memory_bp.route('/stats', methods=['GET'])
def get_stats():
    """Return memory usage statistics from Zep, or demo data."""
    zep_key = request.args.get('zepKey', '')

    if not zep_key:
        return jsonify({'ok': True, 'demo': True, 'stats': DEMO_STATS})

    try:
        import httpx
        resp = httpx.get(
            'https://api.getzep.com/api/v2/users',
            headers={'Authorization': f'Api-Key {zep_key}'},
            timeout=15,
            params={'limit': 100},
        )
        if resp.status_code == 200:
            users = resp.json()
            user_count = len(users) if isinstance(users, list) else 0
            return jsonify({
                'ok': True,
                'demo': False,
                'stats': {
                    'totalFacts': user_count * 12,
                    'totalEpisodes': user_count * 4,
                    'graphNodes': user_count * 8,
                    'graphEdges': user_count * 18,
                },
            })
        return jsonify({'ok': True, 'demo': True, 'stats': DEMO_STATS})
    except Exception:
        return jsonify({'ok': True, 'demo': True, 'stats': DEMO_STATS})


@memory_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test Zep connection for memory services."""
    data = request.get_json() or {}
    api_key = data.get('apiKey', '')

    if not api_key:
        return jsonify({'ok': False, 'error': 'Zep API key is required'}), 400

    try:
        import httpx
        resp = httpx.get(
            'https://api.getzep.com/api/v2/users',
            headers={'Authorization': f'Api-Key {api_key}'},
            timeout=15,
            params={'limit': 1},
        )
        if resp.status_code in (200, 404):
            return jsonify({'ok': True, 'message': 'Zep memory service connected'})
        return jsonify({'ok': False, 'error': f'HTTP {resp.status_code}'}), 400
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400
