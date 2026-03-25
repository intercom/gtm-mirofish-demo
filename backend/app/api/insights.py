"""
Insights API
Serves LLM-generated (or template-based) GTM insights.
"""

from flask import Blueprint, jsonify, request

from ..services.insight_generator import (
    InsightGenerator,
    RateLimitError,
    SUPPORTED_DATA_TYPES,
)
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.insights')

insights_bp = Blueprint('insights', __name__, url_prefix='/api/v1/insights')

_generator = InsightGenerator()


@insights_bp.route('', methods=['GET'])
def get_insights():
    """
    Generate insights for a given data type.

    Query params:
        data_type  – one of: revenue, pipeline, simulation_results, campaign, reconciliation
        limit      – max insights to return (default 5, max 20)

    The request body (JSON) supplies the data to analyze.
    For GET convenience, data can also be empty — the endpoint will
    return demo insights for the given data_type.

    Returns:
        {
            "success": true,
            "data": {
                "insights": [ { title, description, evidence, confidence, insight_type, data_type } ],
                "count": 3,
                "data_type": "revenue",
                "mode": "llm" | "template"
            }
        }
    """
    data_type = request.args.get('data_type')
    if not data_type:
        return jsonify({
            "success": False,
            "error": "Missing required query parameter: data_type",
            "supported": SUPPORTED_DATA_TYPES,
        }), 400

    if data_type not in SUPPORTED_DATA_TYPES:
        return jsonify({
            "success": False,
            "error": f"Unsupported data_type: {data_type}",
            "supported": SUPPORTED_DATA_TYPES,
        }), 400

    limit = request.args.get('limit', 5, type=int)
    limit = max(1, min(limit, 20))

    data = request.get_json(silent=True) or _demo_data(data_type)

    try:
        insights = _generator.generate_insights(data_type=data_type, data=data, limit=limit)
        from ..config import Config
        mode = "llm" if Config.LLM_API_KEY else "template"

        return jsonify({
            "success": True,
            "data": {
                "insights": [i.to_dict() for i in insights],
                "count": len(insights),
                "data_type": data_type,
                "mode": mode,
            },
        })

    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        return jsonify({"success": False, "error": str(e)}), 429

    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@insights_bp.route('', methods=['POST'])
def post_insights():
    """
    Generate insights from supplied data (POST variant).

    Body (JSON):
        {
            "data_type": "revenue",
            "data": { ... },
            "limit": 5
        }
    """
    body = request.get_json(silent=True) or {}
    data_type = body.get('data_type')
    if not data_type:
        return jsonify({
            "success": False,
            "error": "Missing required field: data_type",
            "supported": SUPPORTED_DATA_TYPES,
        }), 400

    if data_type not in SUPPORTED_DATA_TYPES:
        return jsonify({
            "success": False,
            "error": f"Unsupported data_type: {data_type}",
            "supported": SUPPORTED_DATA_TYPES,
        }), 400

    limit = body.get('limit', 5)
    limit = max(1, min(int(limit), 20))
    data = body.get('data', _demo_data(data_type))

    try:
        insights = _generator.generate_insights(data_type=data_type, data=data, limit=limit)
        from ..config import Config
        mode = "llm" if Config.LLM_API_KEY else "template"

        return jsonify({
            "success": True,
            "data": {
                "insights": [i.to_dict() for i in insights],
                "count": len(insights),
                "data_type": data_type,
                "mode": mode,
            },
        })

    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        return jsonify({"success": False, "error": str(e)}), 429

    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@insights_bp.route('/types', methods=['GET'])
def list_types():
    """Return supported data types and insight types."""
    return jsonify({
        "success": True,
        "data": {
            "data_types": SUPPORTED_DATA_TYPES,
            "insight_types": ["trend", "anomaly", "recommendation", "comparison"],
        },
    })


def _demo_data(data_type: str) -> dict:
    """Provide demo data so the endpoint works without a request body."""
    demos = {
        "revenue": {
            "total": 1_250_000,
            "target": 1_500_000,
            "growth_rate": 12.5,
            "period": "Q1 2026",
        },
        "pipeline": {
            "total_deals": 47,
            "avg_deal_size": 32_000,
            "conversion_rate": 11.2,
            "pipeline_value": 1_504_000,
        },
        "simulation_results": {
            "total_actions": 1_830,
            "total_rounds": 10,
            "avg_sentiment": 0.72,
            "engagement_rate": 0.45,
        },
        "campaign": {
            "ctr": 3.8,
            "total_spend": 45_000,
            "roas": 2.1,
            "impressions": 520_000,
        },
        "reconciliation": {
            "matched_pct": 87.3,
            "discrepancy": -12_400,
            "total_records": 5_200,
        },
    }
    return demos.get(data_type, {})
