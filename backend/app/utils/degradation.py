"""
Graceful degradation middleware.

Tracks external service health (LLM, Zep) and provides automatic fallback
responses when services are unavailable — so every endpoint can work in
demo/mock mode.

Components:
  - ServiceHealthTracker: circuit-breaker that tracks service availability
  - @graceful_degradation: route decorator returning mock data on failure
  - register_degradation_middleware: Flask integration (error handlers, g context)
"""

import time
import threading
import functools

from flask import g, jsonify, request

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.degradation')


class ServiceHealthTracker:
    """
    Circuit-breaker style health tracker for external services.

    States per service:
      - healthy=True   → calls proceed normally
      - healthy=False  → calls short-circuit to fallback
      - After RECOVERY_INTERVAL seconds, the breaker enters "half-open" and
        allows one real attempt to detect recovery.
    """

    RECOVERY_INTERVAL = 120  # seconds before retrying a failed service

    def __init__(self):
        self._status = {}
        self._lock = threading.Lock()

    def init_from_config(self):
        """Seed initial health from environment configuration."""
        with self._lock:
            self._status['llm'] = {
                'healthy': bool(Config.LLM_API_KEY),
                'configured': bool(Config.LLM_API_KEY),
                'last_failure': 0,
                'error': None if Config.LLM_API_KEY else 'LLM_API_KEY not configured',
            }
            self._status['zep'] = {
                'healthy': bool(Config.ZEP_API_KEY),
                'configured': bool(Config.ZEP_API_KEY),
                'last_failure': 0,
                'error': None if Config.ZEP_API_KEY else 'ZEP_API_KEY not configured',
            }

    def mark_unhealthy(self, service, error):
        """Record a runtime failure for a service."""
        with self._lock:
            if service in self._status:
                self._status[service]['healthy'] = False
                self._status[service]['error'] = str(error)
                self._status[service]['last_failure'] = time.time()
                logger.warning(f"Service '{service}' marked unhealthy: {error}")

    def mark_healthy(self, service):
        """Record a successful call to a service."""
        with self._lock:
            if service in self._status:
                was_unhealthy = not self._status[service]['healthy']
                self._status[service]['healthy'] = True
                self._status[service]['error'] = None
                if was_unhealthy:
                    logger.info(f"Service '{service}' recovered")

    def should_attempt(self, service):
        """
        Whether to let a real call through.

        Returns True if healthy, or if RECOVERY_INTERVAL has elapsed since
        the last failure (half-open state).  Returns False if the service
        key isn't configured or the breaker is still open.
        """
        with self._lock:
            info = self._status.get(service)
            if not info or not info.get('configured'):
                return False
            if info['healthy']:
                return True
            elapsed = time.time() - info.get('last_failure', 0)
            return elapsed > self.RECOVERY_INTERVAL

    def get_status(self):
        """Snapshot of all service statuses (safe to serialize)."""
        with self._lock:
            return {
                svc: {
                    'healthy': info['healthy'],
                    'configured': info['configured'],
                    'error': info['error'],
                }
                for svc, info in self._status.items()
            }

    @property
    def degraded_services(self):
        """List of currently unhealthy service names."""
        with self._lock:
            return [
                svc for svc, info in self._status.items()
                if not info['healthy']
            ]


# Module-level singleton — shared across the app
health_tracker = ServiceHealthTracker()


def graceful_degradation(service, fallback):
    """
    Route decorator that returns mock data when *service* is unavailable.

    If the service is known-unhealthy (breaker open), the fallback is
    returned immediately without calling the real handler.  If the real
    handler raises, the service is marked unhealthy and the fallback is
    returned for this request (and future ones until recovery).

    Args:
        service:  Service name ('llm' or 'zep').
        fallback: Callable returning a dict of mock response data.

    Usage::

        @bp.route('/generate')
        @graceful_degradation('llm', lambda: {"text": "Demo response"})
        def generate():
            # real LLM call ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not health_tracker.should_attempt(service):
                logger.info(
                    f"Degraded response for {request.path} "
                    f"({service} unavailable)"
                )
                mock_data = fallback() if callable(fallback) else fallback
                return jsonify({
                    'success': True,
                    'degraded': True,
                    'degraded_service': service,
                    'data': mock_data,
                })

            try:
                response = fn(*args, **kwargs)
                health_tracker.mark_healthy(service)
                return response
            except Exception as e:
                logger.warning(
                    f"{request.path} failed ({service}): {e}"
                )
                health_tracker.mark_unhealthy(service, e)
                mock_data = fallback() if callable(fallback) else fallback
                return jsonify({
                    'success': True,
                    'degraded': True,
                    'degraded_service': service,
                    'error': str(e),
                    'data': mock_data,
                })
        return wrapper
    return decorator


def register_degradation_middleware(app):
    """
    Wire up degradation support on the Flask app:
      1. Seed service health from config
      2. Attach health info to every request via flask.g
      3. Register global JSON error handlers (no tracebacks to clients)
    """
    health_tracker.init_from_config()

    @app.before_request
    def attach_service_health():
        g.degraded_services = health_tracker.degraded_services
        g.service_health = health_tracker.get_status()

    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"Unhandled 500 on {request.method} {request.path}: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
        }), 500

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({
            'success': False,
            'error': 'Not found',
        }), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({
            'success': False,
            'error': 'Method not allowed',
        }), 405

    degraded = health_tracker.degraded_services
    if degraded:
        logger.warning(f"Degraded services at startup: {', '.join(degraded)}")
    logger.info("Graceful degradation middleware registered")
