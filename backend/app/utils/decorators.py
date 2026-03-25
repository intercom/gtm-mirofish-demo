"""Route-level decorators for Flask API endpoints."""

import functools
import traceback

from flask import jsonify, request

from ..config import Config


def handle_errors(logger):
    """Wrap a Flask route with standardized error handling.

    Catches unhandled exceptions, logs them, and returns a consistent
    500 JSON error response so callers never see raw tracebacks.

    Usage::

        @bp.route('/items')
        @handle_errors(logger)
        def list_items():
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"{fn.__name__} failed: {e}")
                logger.debug(traceback.format_exc())
                return jsonify({
                    "success": False,
                    "error": str(e),
                }), 500
        return wrapper
    return decorator


def require_json(*fields):
    """Validate that the request body contains required JSON fields.

    Returns a 400 error response listing the first missing field.
    Injects the parsed JSON dict as ``data`` keyword argument into
    the wrapped function.

    Usage::

        @bp.route('/simulate', methods=['POST'])
        @require_json('seed_text', 'project_id')
        def simulate(data):
            seed_text = data['seed_text']
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            for field in fields:
                value = data.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    return jsonify({
                        "success": False,
                        "error": f"'{field}' is required",
                    }), 400
            kwargs["data"] = data
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_config(*keys):
    """Ensure configuration values are set before the route executes.

    Returns a 500 error if any of the specified ``Config`` attributes
    are falsy (empty string, None, etc.).

    Usage::

        @bp.route('/entities/<graph_id>')
        @require_config('ZEP_API_KEY')
        def get_entities(graph_id):
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for key in keys:
                if not getattr(Config, key, None):
                    return jsonify({
                        "success": False,
                        "error": f"{key} is not configured",
                    }), 500
            return fn(*args, **kwargs)
        return wrapper
    return decorator
