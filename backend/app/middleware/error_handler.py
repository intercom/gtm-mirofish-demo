"""
Centralized error handling middleware.

Registers Flask error handlers that return consistent JSON responses
and prevent leaking tracebacks to clients.
"""

import traceback

from flask import jsonify
from werkzeug.exceptions import HTTPException

from ..utils.logger import get_logger

logger = get_logger('mirofish.error')


def register_error_handlers(app):
    """Register global error handlers on the Flask app."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "success": False,
            "error": e.description if isinstance(e, HTTPException) else "Bad request",
        }), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "error": "Resource not found",
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "success": False,
            "error": "Method not allowed",
        }), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({
            "success": False,
            "error": e.description if isinstance(e, HTTPException) else "Unprocessable entity",
        }), 422

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
        }), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({
                "success": False,
                "error": e.description,
            }), e.code

        logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
        }), 500
