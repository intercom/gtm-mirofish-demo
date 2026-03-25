"""
In-memory API response cache with TTL support.

Provides a thread-safe cache for Flask API responses, reducing redundant
disk reads, Zep API calls, and LLM invocations for repeated identical requests.

Usage:
    from ..services.cache import cached_response, cache_manager

    @bp.route('/data')
    @cached_response(ttl=300)  # cache for 5 minutes
    def get_data():
        return jsonify(expensive_operation())

    # Invalidate specific entries
    cache_manager.invalidate('/api/gtm/scenarios')

    # Clear all
    cache_manager.clear()
"""

import hashlib
import threading
import time
from functools import wraps

from flask import request, jsonify

from ..utils.logger import get_logger

logger = get_logger('mirofish.cache')


class CacheEntry:
    __slots__ = ('value', 'expires_at', 'created_at')

    def __init__(self, value, ttl):
        now = time.monotonic()
        self.value = value
        self.created_at = now
        self.expires_at = now + ttl


class CacheManager:
    """Thread-safe in-memory cache with TTL eviction."""

    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, path: str, query_string: str = '') -> str:
        raw = f"{path}?{query_string}" if query_string else path
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def set(self, key: str, value, ttl: float):
        with self._lock:
            self._store[key] = CacheEntry(value, ttl)

    def invalidate(self, path_prefix: str):
        """Remove all entries whose original path starts with the given prefix."""
        with self._lock:
            keys_to_delete = [
                k for k, v in self._store.items()
                if hasattr(v, '_path') and v._path.startswith(path_prefix)
            ]
            for k in keys_to_delete:
                del self._store[k]

    def clear(self):
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._hits = 0
            self._misses = 0
            return count

    def stats(self) -> dict:
        with self._lock:
            now = time.monotonic()
            active = sum(1 for e in self._store.values() if now < e.expires_at)
            expired = len(self._store) - active
            return {
                'active_entries': active,
                'expired_entries': expired,
                'total_entries': len(self._store),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': (
                    round(self._hits / (self._hits + self._misses), 3)
                    if (self._hits + self._misses) > 0 else 0
                ),
            }

    def evict_expired(self):
        """Remove expired entries (called lazily or on demand)."""
        with self._lock:
            now = time.monotonic()
            expired_keys = [
                k for k, v in self._store.items() if now >= v.expires_at
            ]
            for k in expired_keys:
                del self._store[k]
            return len(expired_keys)


# Singleton instance shared across the app
cache_manager = CacheManager()


def cached_response(ttl: float = 300, key_prefix: str = ''):
    """
    Flask route decorator that caches JSON responses.

    Only caches GET requests that return 2xx status codes.

    Args:
        ttl: Time-to-live in seconds (default 5 minutes).
        key_prefix: Optional prefix for cache key disambiguation.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method != 'GET':
                return f(*args, **kwargs)

            prefix = key_prefix or request.path
            cache_key = cache_manager._make_key(prefix, request.query_string.decode())

            cached = cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache HIT: {request.path}")
                response = jsonify(cached)
                response.headers['X-Cache'] = 'HIT'
                return response

            logger.debug(f"Cache MISS: {request.path}")
            result = f(*args, **kwargs)

            # Handle both (response, status_code) tuples and plain responses
            if isinstance(result, tuple):
                response_data, status_code = result[0], result[1]
                if status_code >= 300:
                    return result
                # Extract JSON data from the response
                if hasattr(response_data, 'get_json'):
                    cache_manager.set(cache_key, response_data.get_json(), ttl)
                return result
            else:
                if hasattr(result, 'status_code') and result.status_code >= 300:
                    return result
                if hasattr(result, 'get_json'):
                    cache_manager.set(cache_key, result.get_json(), ttl)
                elif isinstance(result, dict):
                    cache_manager.set(cache_key, result, ttl)
                    result = jsonify(result)

                result.headers['X-Cache'] = 'MISS'
                return result

        return wrapper
    return decorator
