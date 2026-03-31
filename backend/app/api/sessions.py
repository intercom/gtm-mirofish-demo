"""
Sessions API
CRUD endpoints for session management.
"""

from flask import Blueprint, jsonify, request
from ..models.session import SessionManager, SessionStatus

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/v1/sessions')


@sessions_bp.route('', methods=['GET'])
def list_sessions():
    """List sessions, optionally filtered by status."""
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)

    if status and status not in [s.value for s in SessionStatus]:
        return jsonify({'error': f'Invalid status: {status}'}), 400

    sessions = SessionManager.list_sessions(status=status, limit=limit)
    return jsonify({
        'sessions': [s.to_dict() for s in sessions],
        'total': len(sessions),
    })


@sessions_bp.route('', methods=['POST'])
def create_session():
    """Create a new session."""
    data = request.get_json() or {}
    name = data.get('name', 'Untitled Session')

    session = SessionManager.create(
        name=name,
        scenario_id=data.get('scenario_id'),
        scenario_name=data.get('scenario_name'),
        project_id=data.get('project_id'),
        metadata=data.get('metadata', {}),
    )
    return jsonify(session.to_dict()), 201


@sessions_bp.route('/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get a single session by ID."""
    session = SessionManager.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session.to_dict())


@sessions_bp.route('/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Update session fields."""
    session = SessionManager.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    data = request.get_json() or {}

    if 'name' in data:
        session.name = data['name']
    if 'status' in data:
        try:
            session.status = SessionStatus(data['status'])
        except ValueError:
            return jsonify({'error': f'Invalid status: {data["status"]}'}), 400
    if 'scenario_id' in data:
        session.scenario_id = data['scenario_id']
    if 'scenario_name' in data:
        session.scenario_name = data['scenario_name']
    if 'project_id' in data:
        session.project_id = data['project_id']
    if 'metadata' in data:
        session.metadata.update(data['metadata'])

    SessionManager.save(session)
    return jsonify(session.to_dict())


@sessions_bp.route('/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session."""
    if not SessionManager.delete(session_id):
        return jsonify({'error': 'Session not found'}), 404
    return jsonify({'deleted': True})


@sessions_bp.route('/<session_id>/simulations', methods=['POST'])
def add_simulation(session_id):
    """Add a simulation ID to a session."""
    data = request.get_json() or {}
    simulation_id = data.get('simulation_id')
    if not simulation_id:
        return jsonify({'error': 'simulation_id is required'}), 400

    session = SessionManager.add_simulation(session_id, simulation_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session.to_dict())
