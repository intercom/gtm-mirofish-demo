"""
Request logging middleware.

Logs method, path, status code, and response time for every request.
Assigns a unique request ID for log correlation across services.
"""

import time
import uuid

from flask import Flask, g, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.request')

SKIP_PATHS = frozenset({'/health', '/api/v1/health'})


def register_request_logging(app: Flask):
    """Register before/after request hooks for structured request logging."""

    @app.before_request
    def _start_timer():
        g.request_id = uuid.uuid4().hex[:8]
        g.request_start = time.monotonic()

    @app.after_request
    def _log_request(response):
        duration_ms = (time.monotonic() - getattr(g, 'request_start', 0)) * 1000
        request_id = getattr(g, 'request_id', '-')

        response.headers['X-Request-ID'] = request_id

        if request.path in SKIP_PATHS:
            return response

        log = logger.warning if response.status_code >= 400 else logger.info
        log(
            '%s %s %d %.0fms [%s]',
            request.method,
            request.full_path.rstrip('?'),
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
