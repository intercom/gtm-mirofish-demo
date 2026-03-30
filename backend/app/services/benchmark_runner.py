"""
Performance Benchmark Runner
Measures API response times by invoking endpoints via Flask's test client.
"""

import statistics
import time


# Endpoints to benchmark — safe, read-only routes that work in demo mode
DEFAULT_ENDPOINTS = [
    {'method': 'GET', 'path': '/health', 'label': 'Health (root)'},
    {'method': 'GET', 'path': '/api/health', 'label': 'Health (API)'},
    {'method': 'GET', 'path': '/api/health/detailed', 'label': 'Health (detailed)'},
    {'method': 'GET', 'path': '/api/health/services', 'label': 'Service health'},
    {'method': 'GET', 'path': '/api/health/metrics', 'label': 'Health metrics'},
    {'method': 'GET', 'path': '/api/v1/gtm/scenarios', 'label': 'GTM scenarios'},
    {'method': 'GET', 'path': '/api/v1/graph/project/list', 'label': 'Project list'},
    {'method': 'GET', 'path': '/api/v1/simulation/list', 'label': 'Simulation list'},
    {'method': 'GET', 'path': '/api/v1/settings/auth-status', 'label': 'Auth status'},
]


def _percentile(sorted_values, p):
    """Calculate the p-th percentile from a pre-sorted list."""
    if not sorted_values:
        return 0
    idx = max(0, int((p / 100) * len(sorted_values)) - 1)
    return sorted_values[idx]


def run_benchmark(app, iterations=10, endpoints=None):
    """
    Benchmark API endpoints using Flask's test client.

    Returns a list of results, one per endpoint, each containing timing stats
    (avg, min, max, p95, p99, median) in milliseconds.
    """
    targets = endpoints or DEFAULT_ENDPOINTS
    results = []

    with app.test_client() as client:
        for ep in targets:
            method = ep.get('method', 'GET').upper()
            path = ep['path']
            label = ep.get('label', path)
            timings = []
            errors = 0

            for _ in range(iterations):
                start = time.perf_counter()
                try:
                    if method == 'GET':
                        resp = client.get(path)
                    elif method == 'POST':
                        resp = client.post(path, json=ep.get('body', {}))
                    else:
                        resp = client.get(path)

                    elapsed_ms = (time.perf_counter() - start) * 1000
                    timings.append(elapsed_ms)

                    if resp.status_code >= 400:
                        errors += 1
                except Exception:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    timings.append(elapsed_ms)
                    errors += 1

            sorted_t = sorted(timings)

            results.append({
                'endpoint': path,
                'method': method,
                'label': label,
                'iterations': iterations,
                'errors': errors,
                'timings_ms': {
                    'avg': round(statistics.mean(sorted_t), 2) if sorted_t else 0,
                    'min': round(sorted_t[0], 2) if sorted_t else 0,
                    'max': round(sorted_t[-1], 2) if sorted_t else 0,
                    'median': round(statistics.median(sorted_t), 2) if sorted_t else 0,
                    'p95': round(_percentile(sorted_t, 95), 2),
                    'p99': round(_percentile(sorted_t, 99), 2),
                    'stddev': round(statistics.stdev(sorted_t), 2) if len(sorted_t) > 1 else 0,
                },
            })

    return results
