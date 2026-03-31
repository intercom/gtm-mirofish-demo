"""
Rate limiting middleware using a sliding window log algorithm.

Tracks request timestamps per client IP in memory. Two tiers:
- Default: general API routes (configurable, default 60 req/min)
- LLM: expensive endpoints like simulation/start, report/generate (default 10 req/min)
"""

import time
import threading
from collections import defaultdict, deque

from flask import request, jsonify, current_app

from ..utils.logger import get_logger

# Path prefixes for LLM-heavy endpoints (stricter limit)
LLM_ENDPOINTS = (
    '/api/v1/simulation/start',
    '/api/v1/report/generate',
    '/api/v1/chat',
    '/api/v1/graph/build',
)

# Paths exempt from rate limiting
EXEMPT_PATHS = ('/health', '/api/v1/health')


class RateLimiter:
    """In-memory sliding window rate limiter keyed by client IP."""

    def __init__(self):
        self._hits = defaultdict(deque)  # key -> deque of timestamps
        self._lock = threading.Lock()

    def _cleanup_key(self, key, window):
        """Remove timestamps older than the window."""
        dq = self._hits[key]
        cutoff = time.monotonic() - window
        while dq and dq[0] < cutoff:
            dq.popleft()

    def is_allowed(self, key, limit, window):
        """Check if a request is allowed and record it.

        Returns (allowed: bool, remaining: int, reset_at: float)
        """
        now = time.monotonic()
        with self._lock:
            self._cleanup_key(key, window)
            dq = self._hits[key]
            remaining = max(0, limit - len(dq))
            if len(dq) >= limit:
                reset_at = dq[0] + window
                return False, 0, reset_at - now
            dq.append(now)
            remaining = max(0, limit - len(dq))
            reset_at = dq[0] + window if dq else window
            return True, remaining, reset_at - now

    def cleanup_stale(self, window):
        """Purge keys with no recent activity. Call periodically."""
        cutoff = time.monotonic() - window
        with self._lock:
            stale = [k for k, dq in self._hits.items()
                     if not dq or dq[-1] < cutoff]
            for k in stale:
                del self._hits[k]


_limiter = RateLimiter()


def _get_client_ip():
    """Get client IP, respecting X-Forwarded-For behind proxies."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


def _is_llm_endpoint(path):
    return any(path.startswith(p) for p in LLM_ENDPOINTS)


def init_rate_limiter(app):
    """Register rate limiting middleware on a Flask app."""
    logger = get_logger('mirofish.ratelimit')

    @app.before_request
    def check_rate_limit():
        if not current_app.config.get('RATE_LIMIT_ENABLED', True):
            return None

        path = request.path
        if path in EXEMPT_PATHS or request.method == 'OPTIONS':
            return None

        window = current_app.config.get('RATE_LIMIT_WINDOW', 60)
        if _is_llm_endpoint(path):
            limit = current_app.config.get('RATE_LIMIT_LLM', 10)
            key = f"llm:{_get_client_ip()}"
        else:
            limit = current_app.config.get('RATE_LIMIT_DEFAULT', 60)
            key = f"api:{_get_client_ip()}"

        allowed, remaining, retry_after = _limiter.is_allowed(key, limit, window)

        if not allowed:
            logger.warning(f"Rate limit exceeded: {key} on {path}")
            resp = jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.',
            })
            resp.status_code = 429
            resp.headers['X-RateLimit-Limit'] = str(limit)
            resp.headers['X-RateLimit-Remaining'] = '0'
            resp.headers['Retry-After'] = str(int(retry_after) + 1)
            return resp

        # Store limit info for after_request to attach headers
        request._rate_limit = limit
        request._rate_remaining = remaining
        return None

    @app.after_request
    def add_rate_limit_headers(response):
        limit = getattr(request, '_rate_limit', None)
        if limit is not None:
            response.headers['X-RateLimit-Limit'] = str(limit)
            response.headers['X-RateLimit-Remaining'] = str(
                getattr(request, '_rate_remaining', 0))
        return response
