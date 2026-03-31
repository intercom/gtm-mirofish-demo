"""
Presence API — simulated multi-user presence for the GTM demo.

Provides endpoints for querying who is "online", their cursor positions,
and a stream of presence events. All data is simulated — no real users
are tracked.
"""

from flask import Blueprint, jsonify, request

from ..services.presence_manager import presence_manager
from ..utils.logger import get_logger

logger = get_logger('mirofish.presence')

presence_bp = Blueprint('presence', __name__, url_prefix='/api/v1/presence')


@presence_bp.route('', methods=['GET'])
def get_presence():
    """Return current simulated presence state."""
    data = presence_manager.get_presence()
    return jsonify({'success': True, 'data': data})


@presence_bp.route('/cursors', methods=['GET'])
def get_cursors():
    """Return cursor positions for active simulated users."""
    cursors = presence_manager.get_cursors()
    return jsonify({'success': True, 'data': {'cursors': cursors}})


@presence_bp.route('/events', methods=['GET'])
def get_events():
    """Return recent presence events, optionally filtered by timestamp."""
    since = request.args.get('since', 0, type=float)
    events = presence_manager.get_events(since=since)
    return jsonify({'success': True, 'data': {'events': events}})


@presence_bp.route('/reset', methods=['POST'])
def reset_presence():
    """Reset all presence state and re-initialize."""
    presence_manager.reset()
    return jsonify({'success': True, 'data': {'message': 'Presence reset'}})
