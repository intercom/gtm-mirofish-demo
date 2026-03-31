"""
Health Check & Monitoring API
Provides /api/health (basic), /api/health/detailed (dependency status),
/api/health/services (external service degradation status),
and /api/health/metrics (runtime health metrics from HealthMonitor).
"""

import platform
import sys
import time

from flask import Blueprint, jsonify

from ..config import Config
from ..utils.degradation import health_tracker

health_bp = Blueprint('health', __name__, url_prefix='/api/v1/health')

_start_time = time.time()


@health_bp.route('', methods=['GET'])
def basic_health():
    """Basic liveness check — returns 200 if the service is running."""
    return jsonify({
        'status': 'ok',
        'service': 'MiroFish Backend',
    })


@health_bp.route('/detailed', methods=['GET'])
def detailed_health():
    """Detailed readiness check — reports configuration and dependency status."""
    llm_configured = bool(Config.LLM_API_KEY)
    zep_configured = bool(Config.ZEP_API_KEY)

    checks = {
        'llm': {
            'configured': llm_configured,
            'provider': Config.LLM_BASE_URL and _provider_from_url(Config.LLM_BASE_URL),
            'model': Config.LLM_MODEL_NAME if llm_configured else None,
        },
        'zep': {
            'configured': zep_configured,
        },
        'auth': {
            'enabled': Config.AUTH_ENABLED,
            'provider': Config.AUTH_PROVIDER if Config.AUTH_ENABLED else None,
        },
    }

    all_ok = llm_configured and zep_configured

    return jsonify({
        'status': 'ok' if all_ok else 'degraded',
        'service': 'MiroFish Backend',
        'uptime_seconds': round(time.time() - _start_time, 1),
        'python_version': sys.version.split()[0],
        'platform': platform.system(),
        'checks': checks,
    })


@health_bp.route('/services', methods=['GET'])
def service_health():
    """Return health status of all tracked external services."""
    status = health_tracker.get_status()
    all_healthy = all(info['healthy'] for info in status.values())
    return jsonify({
        'success': True,
        'healthy': all_healthy,
        'services': status,
    })


@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """Return current health metrics, alerts, and hourly snapshots."""
    from ..services.health_monitor import health_monitor
    return jsonify(health_monitor.get_metrics())


def _provider_from_url(base_url: str) -> str | None:
    """Derive a human-readable provider name from the LLM base URL."""
    if not base_url:
        return None
    url = base_url.lower()
    if 'anthropic' in url:
        return 'anthropic'
    if 'openai' in url:
        return 'openai'
    if 'googleapis' in url or 'gemini' in url:
        return 'gemini'
    return 'custom'
