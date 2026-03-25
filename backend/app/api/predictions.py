"""
Prediction API endpoints.
All routes attach to the simulation blueprint (prefix /api/simulation).
"""

import traceback
from flask import request, jsonify

from . import simulation_bp
from ..services.behavior_predictor import BehaviorPredictor
from ..services.anomaly_detector import AnomalyDetector
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.predictions')


@simulation_bp.route('/<simulation_id>/predictions', methods=['GET'])
def get_predictions(simulation_id: str):
    """Current predictions for all agents in a simulation."""
    try:
        predictor = BehaviorPredictor()
        predictions = predictor.predict_all_agents(simulation_id)
        consensus = predictor.predict_consensus_round(simulation_id)
        outcome = predictor.predict_outcome(simulation_id)

        return jsonify({
            'success': True,
            'data': {
                'agent_predictions': predictions,
                'consensus': consensus,
                'outcome': outcome,
            },
        })
    except Exception as e:
        logger.error(f"Failed to get predictions: {simulation_id}, error={e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@simulation_bp.route('/<simulation_id>/predictions/accuracy', methods=['GET'])
def get_prediction_accuracy(simulation_id: str):
    """
    Prediction accuracy scorecard.

    Compares past predictions against actual outcomes where available.
    Since predictions are computed live (not stored), this endpoint
    reports confidence calibration from the current model.
    """
    try:
        predictor = BehaviorPredictor()
        predictions = predictor.predict_all_agents(simulation_id)

        if not predictions:
            return jsonify({
                'success': True,
                'data': {
                    'overall_confidence': 0,
                    'agents_analyzed': 0,
                    'scorecard': [],
                    'demo': True,
                },
            })

        total_confidence = 0
        scorecard = []
        for p in predictions:
            total_confidence += p.get('confidence', 0)
            scorecard.append({
                'agent_id': p['agent_id'],
                'predicted_action': p['predicted_action'],
                'confidence': p['confidence'],
                'actions_analyzed': p.get('based_on_actions', 0),
            })

        avg_confidence = (
            round(total_confidence / len(predictions), 3)
            if predictions
            else 0
        )

        return jsonify({
            'success': True,
            'data': {
                'overall_confidence': avg_confidence,
                'agents_analyzed': len(predictions),
                'scorecard': scorecard,
            },
        })
    except Exception as e:
        logger.error(f"Failed to get prediction accuracy: {simulation_id}, error={e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@simulation_bp.route('/<simulation_id>/anomalies', methods=['GET'])
def get_anomalies(simulation_id: str):
    """Detected anomalies with surprise scores."""
    try:
        round_num = request.args.get('round', type=int)

        detector = AnomalyDetector()
        anomalies = detector.detect_anomalies(simulation_id, target_round=round_num)

        total = len(anomalies)
        most_surprising_agent = None
        if anomalies:
            most_surprising_agent = anomalies[0].get('agent_id')

        return jsonify({
            'success': True,
            'data': {
                'anomalies': anomalies,
                'summary': {
                    'total_anomalies': total,
                    'most_surprising_agent': most_surprising_agent,
                },
            },
        })
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {simulation_id}, error={e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@simulation_bp.route('/<simulation_id>/predictions/what-if', methods=['POST'])
def what_if_prediction(simulation_id: str):
    """
    What-if prediction with modified agent traits.

    Body: {"modifications": [{"agent_id": 1, "trait": "assertive", "new_value": 0.9}]}
    """
    try:
        data = request.get_json(silent=True) or {}
        modifications = data.get('modifications', [])

        if not modifications:
            return jsonify({
                'success': False,
                'error': 'modifications array is required',
            }), 400

        predictor = BehaviorPredictor()
        result = predictor.predict_what_if(simulation_id, modifications)

        return jsonify({
            'success': True,
            'data': result,
        })
    except Exception as e:
        logger.error(f"Failed what-if prediction: {simulation_id}, error={e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@simulation_bp.route('/<simulation_id>/patterns', methods=['GET'])
def get_patterns(simulation_id: str):
    """Detected recurring behavior patterns."""
    try:
        detector = AnomalyDetector()
        patterns = detector.get_patterns(simulation_id)

        return jsonify({
            'success': True,
            'data': {
                'patterns': patterns,
                'total': len(patterns),
            },
        })
    except Exception as e:
        logger.error(f"Failed to get patterns: {simulation_id}, error={e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@simulation_bp.route('/<simulation_id>/influence', methods=['GET'])
def get_influence(simulation_id: str):
    """Influence flow graph data (nodes and edges)."""
    try:
        detector = AnomalyDetector()
        graph = detector.get_influence_graph(simulation_id)

        return jsonify({
            'success': True,
            'data': graph,
        })
    except Exception as e:
        logger.error(f"Failed to get influence graph: {simulation_id}, error={e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
