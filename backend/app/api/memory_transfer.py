"""
Memory transfer API endpoints.

Provides export, import, transfer, and listing of cross-simulation
agent memory bundles. All routes are mounted under /api/memory.
"""

import traceback
from flask import request, jsonify

from . import memory_transfer_bp
from ..services.memory_transfer import MemoryTransfer, MemoryFilterType, VALID_FILTERS, generate_demo_bundles
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.memory_transfer')


@memory_transfer_bp.route('/export', methods=['POST'])
def export_memory():
    """
    Export an agent's memory from a simulation.

    Body:
        simulation_id (str): Source simulation ID
        agent_id (int): Agent numeric ID
        filter_type (str): 'all' | 'decisions_only' | 'relationships_only' | 'facts_only'
    """
    try:
        data = request.get_json() or {}
        simulation_id = data.get("simulation_id")
        agent_id = data.get("agent_id")
        filter_type = data.get("filter_type", MemoryFilterType.ALL)

        if not simulation_id or agent_id is None:
            return jsonify({
                "success": False,
                "error": "simulation_id and agent_id are required"
            }), 400

        if filter_type not in VALID_FILTERS:
            return jsonify({
                "success": False,
                "error": f"filter_type must be one of: {', '.join(sorted(VALID_FILTERS))}"
            }), 400

        service = MemoryTransfer()
        bundle = service.export_agent_memory(
            agent_id=int(agent_id),
            simulation_id=simulation_id,
            filter_type=filter_type,
        )

        return jsonify({"success": True, "data": bundle})

    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Simulation data not found"
        }), 404
    except Exception as e:
        logger.error(f"Export memory failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@memory_transfer_bp.route('/import', methods=['POST'])
def import_memory():
    """
    Import a memory bundle into a target simulation.

    Body:
        simulation_id (str): Target simulation ID
        agent_id (int): Target agent numeric ID
        bundle (dict): The memory bundle to import
    """
    try:
        data = request.get_json() or {}
        simulation_id = data.get("simulation_id")
        agent_id = data.get("agent_id")
        bundle = data.get("bundle")

        if not simulation_id or agent_id is None or not bundle:
            return jsonify({
                "success": False,
                "error": "simulation_id, agent_id, and bundle are required"
            }), 400

        service = MemoryTransfer()
        receipt = service.import_agent_memory(
            agent_id=int(agent_id),
            simulation_id=simulation_id,
            memory_bundle=bundle,
        )

        return jsonify({"success": True, "data": receipt})

    except Exception as e:
        logger.error(f"Import memory failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@memory_transfer_bp.route('/transfer', methods=['POST'])
def transfer_memory():
    """
    Transfer agent memory between simulations in one step.

    Body:
        agent_id (int): Agent numeric ID
        from_simulation_id (str): Source simulation
        to_simulation_id (str): Target simulation
        filter_type (str): Memory filter
    """
    try:
        data = request.get_json() or {}
        agent_id = data.get("agent_id")
        from_sim = data.get("from_simulation_id")
        to_sim = data.get("to_simulation_id")
        filter_type = data.get("filter_type", MemoryFilterType.ALL)

        if agent_id is None or not from_sim or not to_sim:
            return jsonify({
                "success": False,
                "error": "agent_id, from_simulation_id, and to_simulation_id are required"
            }), 400

        if filter_type not in VALID_FILTERS:
            return jsonify({
                "success": False,
                "error": f"filter_type must be one of: {', '.join(sorted(VALID_FILTERS))}"
            }), 400

        service = MemoryTransfer()
        result = service.selective_transfer(
            agent_id=int(agent_id),
            from_simulation_id=from_sim,
            to_simulation_id=to_sim,
            filter_type=filter_type,
        )

        return jsonify({"success": True, "data": result})

    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "Source simulation data not found"
        }), 404
    except Exception as e:
        logger.error(f"Transfer memory failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@memory_transfer_bp.route('/bundles/<simulation_id>', methods=['GET'])
def list_bundles(simulation_id: str):
    """List all memory bundles for a simulation."""
    try:
        service = MemoryTransfer()
        bundles = service.list_bundles(simulation_id)
        return jsonify({"success": True, "data": bundles})
    except Exception as e:
        logger.error(f"List bundles failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@memory_transfer_bp.route('/bundles/<simulation_id>/<bundle_id>', methods=['GET'])
def get_bundle(simulation_id: str, bundle_id: str):
    """Get a specific memory bundle."""
    try:
        service = MemoryTransfer()
        bundle = service.get_bundle(simulation_id, bundle_id)
        if not bundle:
            return jsonify({"success": False, "error": "Bundle not found"}), 404
        return jsonify({"success": True, "data": bundle})
    except Exception as e:
        logger.error(f"Get bundle failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@memory_transfer_bp.route('/bundles/<simulation_id>/<bundle_id>', methods=['DELETE'])
def delete_bundle(simulation_id: str, bundle_id: str):
    """Delete a memory bundle."""
    try:
        service = MemoryTransfer()
        deleted = service.delete_bundle(simulation_id, bundle_id)
        if not deleted:
            return jsonify({"success": False, "error": "Bundle not found"}), 404
        return jsonify({"success": True, "data": {"deleted": bundle_id}})
    except Exception as e:
        logger.error(f"Delete bundle failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@memory_transfer_bp.route('/demo-bundles', methods=['GET'])
def get_demo_bundles():
    """Get demo/mock memory bundles for when no simulation data exists."""
    try:
        bundles = generate_demo_bundles()
        return jsonify({"success": True, "data": bundles})
    except Exception as e:
        logger.error(f"Demo bundles failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
