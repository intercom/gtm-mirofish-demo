"""
Batch API endpoint — execute multiple API requests in a single HTTP call.

Accepts an array of request descriptors and dispatches each one internally
through Flask's test client, returning all responses in a single payload.
"""

from flask import Blueprint, request, jsonify, current_app

batch_bp = Blueprint('batch', __name__)

MAX_BATCH_SIZE = 20
ALLOWED_METHODS = {'GET', 'POST', 'DELETE'}


@batch_bp.route('/api/batch', methods=['POST'])
def batch_requests():
    data = request.get_json(silent=True)
    if not data or 'requests' not in data:
        return jsonify({'success': False, 'error': 'Missing requests array'}), 400

    items = data['requests']
    if not isinstance(items, list):
        return jsonify({'success': False, 'error': 'requests must be an array'}), 400
    if len(items) > MAX_BATCH_SIZE:
        return jsonify({
            'success': False,
            'error': f'Batch size exceeds maximum of {MAX_BATCH_SIZE}',
        }), 400

    # Forward auth headers from the original request
    forwarded_headers = {}
    if request.headers.get('Authorization'):
        forwarded_headers['Authorization'] = request.headers['Authorization']

    responses = []
    with current_app.test_client() as tc:
        for item in items:
            req_id = item.get('id', '')
            method = item.get('method', 'GET').upper()
            path = item.get('path', '')

            if not path:
                responses.append({'id': req_id, 'status': 400, 'body': {'error': 'Missing path'}})
                continue
            if method not in ALLOWED_METHODS:
                responses.append({'id': req_id, 'status': 405, 'body': {'error': f'Method not allowed: {method}'}})
                continue

            try:
                if method == 'GET':
                    resp = tc.get(path, headers=forwarded_headers)
                elif method == 'POST':
                    body = item.get('body')
                    resp = tc.post(path, json=body, content_type='application/json', headers=forwarded_headers)
                else:
                    resp = tc.delete(path, headers=forwarded_headers)

                responses.append({
                    'id': req_id,
                    'status': resp.status_code,
                    'body': resp.get_json(silent=True),
                })
            except Exception as e:
                responses.append({
                    'id': req_id,
                    'status': 500,
                    'body': {'error': str(e)},
                })

    return jsonify({'success': True, 'responses': responses})
