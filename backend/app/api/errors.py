"""
Frontend Error Tracking API
Receives error reports from the frontend and logs them to a dedicated file.
"""

import json
import os
from logging.handlers import RotatingFileHandler
import logging

from flask import Blueprint, jsonify, request

errors_bp = Blueprint('errors', __name__, url_prefix='/api/errors')

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

def _get_frontend_logger():
    logger = logging.getLogger('mirofish.frontend_errors')
    if logger.handlers:
        return logger
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'frontend-errors.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


@errors_bp.route('', methods=['POST'])
def report_error():
    """Receive a frontend error report and write it to the log file."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'ok': False, 'error': 'JSON body required'}), 400

    logger = _get_frontend_logger()
    logger.info(json.dumps(data, ensure_ascii=False, default=str))

    return jsonify({'ok': True}), 201
