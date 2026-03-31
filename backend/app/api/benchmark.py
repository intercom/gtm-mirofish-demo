"""
Performance Benchmark API
Exposes endpoints to list benchmarkable routes and run timed benchmarks.
"""

from flask import Blueprint, current_app, jsonify, request

from ..services.benchmark_runner import DEFAULT_ENDPOINTS, run_benchmark

benchmark_bp = Blueprint('benchmark', __name__, url_prefix='/api/v1/benchmark')


@benchmark_bp.route('/endpoints', methods=['GET'])
def list_endpoints():
    """Return the list of endpoints available for benchmarking."""
    return jsonify({
        'success': True,
        'data': DEFAULT_ENDPOINTS,
    })


@benchmark_bp.route('/run', methods=['POST'])
def run():
    """
    Run a performance benchmark against selected (or all default) endpoints.

    Body (optional):
      - iterations: int (1–100, default 10)
      - endpoints: list of {method, path, label} to override defaults
    """
    body = request.get_json(silent=True) or {}

    iterations = min(max(int(body.get('iterations', 10)), 1), 100)

    custom = body.get('endpoints')
    endpoints = None
    if custom and isinstance(custom, list):
        endpoints = [
            {
                'method': ep.get('method', 'GET'),
                'path': ep['path'],
                'label': ep.get('label', ep['path']),
            }
            for ep in custom
            if 'path' in ep
        ]

    results = run_benchmark(current_app._get_current_object(), iterations, endpoints)

    return jsonify({
        'success': True,
        'data': {
            'iterations': iterations,
            'endpoint_count': len(results),
            'results': results,
        },
    })
