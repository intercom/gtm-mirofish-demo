"""
Branch Management API

Endpoints for forking simulations at specific rounds, listing branches,
viewing branch trees, comparing branches, and deleting branches.

All routes are registered on simulation_bp (prefix /api/simulation).
"""

import traceback
from flask import request, jsonify

from . import simulation_bp
from ..services.branch_manager import BranchManager
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.branches')


# ============== Branch Management ==============

@simulation_bp.route('/<simulation_id>/branch', methods=['POST'])
def create_branch(simulation_id: str):
    """
    Fork a simulation at a specific round.

    Request (JSON):
        {
            "at_round": 50,
            "label": "Higher engagement scenario",
            "modifications": [
                {"type": "engagement_boost", "value": 1.5},
                {"type": "add_competitor", "value": "Drift"}
            ],
            "parent_branch_id": null  // optional, for nested branches
        }

    Returns:
        {
            "success": true,
            "data": { branch object }
        }
    """
    try:
        data = request.get_json() or {}

        at_round = data.get('at_round')
        if at_round is None or not isinstance(at_round, int) or at_round < 0:
            return jsonify({
                "success": False,
                "error": "at_round is required and must be a non-negative integer"
            }), 400

        label = data.get('label', '').strip()
        if not label:
            return jsonify({
                "success": False,
                "error": "label is required"
            }), 400

        modifications = data.get('modifications', [])
        if not isinstance(modifications, list):
            return jsonify({
                "success": False,
                "error": "modifications must be a list"
            }), 400

        parent_branch_id = data.get('parent_branch_id')

        manager = BranchManager()
        branch = manager.create_branch(
            simulation_id=simulation_id,
            at_round=at_round,
            label=label,
            modifications=modifications,
            parent_branch_id=parent_branch_id,
        )

        return jsonify({
            "success": True,
            "data": branch.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Failed to create branch: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/branches', methods=['GET'])
def list_branches(simulation_id: str):
    """
    List all branches for a simulation.

    Returns:
        {
            "success": true,
            "data": [ branch objects ],
            "count": 3
        }
    """
    try:
        manager = BranchManager()
        branches = manager.list_branches(simulation_id)

        return jsonify({
            "success": True,
            "data": [b.to_dict() for b in branches],
            "count": len(branches)
        })

    except Exception as e:
        logger.error(f"Failed to list branches: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/branch-tree', methods=['GET'])
def get_branch_tree(simulation_id: str):
    """
    Get the full branch tree structure for a simulation.

    Returns a nested tree with the simulation as root and branches as children.

    Returns:
        {
            "success": true,
            "data": {
                "id": "sim_abc123",
                "type": "simulation",
                "label": "Main simulation",
                "at_round": 0,
                "children": [
                    {
                        "id": "br_xxx",
                        "type": "branch",
                        "label": "...",
                        "at_round": 50,
                        "children": [...]
                    }
                ]
            }
        }
    """
    try:
        manager = BranchManager()
        tree = manager.get_branch_tree(simulation_id)

        return jsonify({
            "success": True,
            "data": tree
        })

    except Exception as e:
        logger.error(f"Failed to get branch tree: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/compare-branches', methods=['GET'])
def compare_branches():
    """
    Compare multiple branches across simulations.

    Query params:
        ids: comma-separated branch IDs (e.g. ?ids=br_aaa,br_bbb,br_ccc)
        simulation_id: the simulation these branches belong to

    Returns:
        {
            "success": true,
            "data": {
                "branches": [...],
                "metrics": [...],
                "summary": { per-metric winners }
            }
        }
    """
    try:
        ids_str = request.args.get('ids', '')
        simulation_id = request.args.get('simulation_id', '')

        if not ids_str:
            return jsonify({
                "success": False,
                "error": "ids query parameter is required"
            }), 400

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id query parameter is required"
            }), 400

        branch_ids = [bid.strip() for bid in ids_str.split(',') if bid.strip()]
        if len(branch_ids) < 2:
            return jsonify({
                "success": False,
                "error": "At least 2 branch IDs are required for comparison"
            }), 400

        manager = BranchManager()
        result = manager.compare_branches(simulation_id, branch_ids)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Failed to compare branches: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/branch', methods=['DELETE'])
def delete_branch(simulation_id: str):
    """
    Delete a branch (and optionally its descendants).

    Query params:
        branch_id: the branch to delete (required)
        cascade: "true" to also delete child branches (default: false)

    Returns:
        {"success": true}
    """
    try:
        branch_id = request.args.get('branch_id', '').strip()
        if not branch_id:
            return jsonify({
                "success": False,
                "error": "branch_id query parameter is required"
            }), 400

        cascade = request.args.get('cascade', 'false').lower() == 'true'

        manager = BranchManager()
        deleted = manager.delete_branch(simulation_id, branch_id, cascade=cascade)

        if not deleted:
            return jsonify({
                "success": False,
                "error": f"Branch {branch_id} not found"
            }), 404

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Failed to delete branch: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
