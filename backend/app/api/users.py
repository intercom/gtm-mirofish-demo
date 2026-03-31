"""
User Management API
CRUD operations for managing users, with demo/mock mode support.
"""

import logging
from flask import Blueprint, jsonify, request
from ..models.user import UserManager, UserRole, UserStatus

logger = logging.getLogger("mirofish.api.users")

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.route("", methods=["GET"])
def list_users():
    """List all users. Seeds demo users on first call if none exist."""
    users = UserManager.list_users()
    if not users:
        UserManager.seed_demo_users()
        users = UserManager.list_users()
    return jsonify({
        "success": True,
        "data": [u.to_dict() for u in users],
        "total": len(users),
    })


@users_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    """Get a single user by ID."""
    user = UserManager.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    return jsonify({"success": True, "data": user.to_dict()})


@users_bp.route("", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body is required"}), 400

    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip()
    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400
    if not name:
        return jsonify({"success": False, "error": "Name is required"}), 400

    role = data.get("role", "viewer")
    if role not in [r.value for r in UserRole]:
        return jsonify({"success": False, "error": f"Invalid role: {role}. Must be one of: admin, member, viewer"}), 400

    status = data.get("status", "active")
    if status not in [s.value for s in UserStatus]:
        return jsonify({"success": False, "error": f"Invalid status: {status}. Must be one of: active, inactive, invited"}), 400

    existing = UserManager.get_user_by_email(email)
    if existing:
        return jsonify({"success": False, "error": "A user with this email already exists"}), 409

    try:
        user = UserManager.create_user(
            email=email,
            name=name,
            role=role,
            status=status,
            department=data.get("department"),
            avatar_url=data.get("avatar_url"),
        )
        logger.info(f"Created user {user.user_id} ({email})")
        return jsonify({"success": True, "data": user.to_dict()}), 201
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@users_bp.route("/<user_id>", methods=["PUT"])
def update_user(user_id):
    """Update an existing user."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body is required"}), 400

    if "role" in data and data["role"] not in [r.value for r in UserRole]:
        return jsonify({"success": False, "error": f"Invalid role: {data['role']}"}), 400
    if "status" in data and data["status"] not in [s.value for s in UserStatus]:
        return jsonify({"success": False, "error": f"Invalid status: {data['status']}"}), 400

    if "email" in data:
        existing = UserManager.get_user_by_email(data["email"])
        if existing and existing.user_id != user_id:
            return jsonify({"success": False, "error": "A user with this email already exists"}), 409

    user = UserManager.update_user(user_id, data)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    logger.info(f"Updated user {user_id}")
    return jsonify({"success": True, "data": user.to_dict()})


@users_bp.route("/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user."""
    deleted = UserManager.delete_user(user_id)
    if not deleted:
        return jsonify({"success": False, "error": "User not found"}), 404

    logger.info(f"Deleted user {user_id}")
    return jsonify({"success": True})


@users_bp.route("/roles", methods=["GET"])
def list_roles():
    """List available roles."""
    roles = [{"id": r.value, "label": r.value.title(), "description": ""} for r in UserRole]
    return jsonify({"success": True, "data": roles})


@users_bp.route("/invite", methods=["POST"])
def invite_user():
    """Invite a new user by email (creates with 'invited' status)."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    role = data.get("role", "viewer")

    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Valid email is required"}), 400

    if role not in [r.value for r in UserRole]:
        return jsonify({"success": False, "error": f"Invalid role: {role}"}), 400

    existing = UserManager.get_user_by_email(email)
    if existing:
        return jsonify({"success": False, "error": "User already exists"}), 409

    try:
        user = UserManager.create_user(
            email=email,
            name=name or email.split("@")[0].title(),
            role=role,
            status="invited",
        )
        logger.info(f"Invited user {user.user_id} ({email})")
        return jsonify({"success": True, "data": user.to_dict()}), 201
    except Exception as e:
        logger.error(f"Error inviting user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
