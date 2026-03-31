"""Standardized API response helpers.

Provides consistent JSON envelope formatting across all Flask routes:
    {"success": true/false, "data": ..., "error": ...}
"""

from flask import jsonify


def success_response(data=None, message=None, status=200, **kwargs):
    """Return a success JSON response.

    Args:
        data: Response payload (dict, list, or scalar).
        message: Optional human-readable message.
        status: HTTP status code (default 200).
        **kwargs: Extra top-level keys merged into the envelope.
    """
    body = {"success": True}
    if data is not None:
        body["data"] = data
    if message is not None:
        body["message"] = message
    body.update(kwargs)
    return jsonify(body), status


def error_response(error, status=400):
    """Return an error JSON response.

    Args:
        error: Error description (string or Exception).
        status: HTTP status code (default 400).
    """
    return jsonify({"success": False, "error": str(error)}), status


def not_found_response(resource, identifier=None):
    """Return a 404 JSON response for a missing resource.

    Args:
        resource: Name of the resource type (e.g. "Project", "Scenario").
        identifier: Optional ID that was looked up.
    """
    msg = f"{resource} not found"
    if identifier:
        msg = f"{resource} not found: {identifier}"
    return jsonify({"success": False, "error": msg}), 404
