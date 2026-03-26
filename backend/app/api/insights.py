"""
Insights API
Serves LLM-generated (or template-based) GTM insights with priority sorting,
category grouping, and pin/dismiss actions. Falls back to mock data when no
LLM key is configured.
"""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..config import Config
from ..services.insight_generator import (
    InsightGenerator,
    RateLimitError,
    SUPPORTED_DATA_TYPES,
)
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.insights')

insights_bp = Blueprint('insights', __name__, url_prefix='/api/v1/insights')

_generator = InsightGenerator()

# ---------------------------------------------------------------------------
# In-memory card store (pin / dismiss state; replaced by DB in production)
# ---------------------------------------------------------------------------
_insights_store = {}
_initialized = False


def _mock_insights():
    """Generate realistic GTM insights for demo mode."""
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "ins-revenue-01",
            "title": "Enterprise deal velocity slowing in EMEA",
            "description": "Average days-to-close for enterprise deals in EMEA increased from 68 to 94 days over the last simulated quarter, driven by longer legal review cycles.",
            "category": "revenue",
            "confidence": 0.91,
            "priority": 1,
            "evidence": [
                "Mean close time rose 38% (68 \u2192 94 days) in EMEA enterprise segment",
                "Legal review stage accounts for 62% of the added cycle time",
                "Win rate held steady at 34%, suggesting pipeline quality is unchanged",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
        {
            "id": "ins-pipeline-01",
            "title": "Mid-market pipeline shows strong inbound momentum",
            "description": "Simulated inbound pipeline for mid-market grew 27% quarter-over-quarter, with product-led signups converting at 2.1x the historical average.",
            "category": "pipeline",
            "confidence": 0.87,
            "priority": 2,
            "evidence": [
                "Inbound MQLs up 27% QoQ in the $50K\u2013$200K ACV band",
                "Product-led signup \u2192 SQL conversion at 14.3% vs 6.8% baseline",
                "Demo request volume correlates with recent product launch activity",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
        {
            "id": "ins-ops-01",
            "title": "SDR response time exceeds SLA in APAC hours",
            "description": "During APAC business hours, average lead response time is 4.2 hours \u2014 well above the 1-hour SLA target \u2014 due to timezone coverage gaps.",
            "category": "operations",
            "confidence": 0.84,
            "priority": 3,
            "evidence": [
                "Average first-touch response: 4.2h during APAC hours vs 0.8h in NA",
                "Only 2 of 12 SDRs have APAC-overlapping working hours",
                "Leads contacted within 1h convert at 3.1x the rate of 4h+ responses",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
        {
            "id": "ins-sim-01",
            "title": "Agent consensus: pricing objection is top barrier",
            "description": "Across 200 simulated buyer agents, 67% flagged pricing as the primary objection during late-stage negotiations, suggesting a positioning gap.",
            "category": "simulation",
            "confidence": 0.79,
            "priority": 4,
            "evidence": [
                "134 of 200 agents cited pricing as top-3 concern in negotiation rounds",
                "Agents with competitor exposure were 2.4x more likely to raise pricing",
                "Discount threshold for deal closure averaged 18% \u2014 above typical 12%",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
        {
            "id": "ins-pipeline-02",
            "title": "Outbound sequences underperforming in financial services",
            "description": "Email open rates for financial services vertical dropped to 11%, significantly below the 22% cross-vertical average, indicating message-market misalignment.",
            "category": "pipeline",
            "confidence": 0.76,
            "priority": 5,
            "evidence": [
                "Financial services open rate: 11% vs 22% portfolio average",
                "Reply rate is 1.8% vs 4.2% average \u2014 suggesting subject line issues",
                "Competitor messaging analysis shows compliance-first framing wins in FS",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
        {
            "id": "ins-revenue-02",
            "title": "Expansion revenue accelerating in existing accounts",
            "description": "Net revenue retention among simulated accounts reached 118%, with cross-sell adoption increasing after product usage milestones.",
            "category": "revenue",
            "confidence": 0.82,
            "priority": 6,
            "evidence": [
                "NRR at 118% \u2014 up from 109% in prior simulation cycle",
                "Accounts reaching 80% feature adoption expand at 2.7x the rate",
                "CSM-initiated expansion conversations convert at 41%",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
    ]


def _get_store():
    """Initialize the in-memory store on first access."""
    global _initialized
    if not _initialized:
        for insight in _mock_insights():
            _insights_store[insight["id"]] = insight
        _initialized = True
    return _insights_store


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@insights_bp.route('', methods=['GET'])
def get_insights():
    """
    Dual-purpose GET endpoint:
      - With ?data_type=<type>  -> generate analytical insights via LLM / templates
      - Without data_type       -> list insight cards sorted by priority (pinned first)
    """
    data_type = request.args.get('data_type')

    if data_type:
        # -- Analytical insight generation (requires data_type) --
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

    # -- Card listing (no data_type) --
    store = _get_store()
    category = request.args.get('category')

    items = [i for i in store.values() if not i["dismissed"]]

    if category:
        items = [i for i in items if i["category"] == category]

    items.sort(key=lambda i: (not i["pinned"], i["priority"]))

    return jsonify({"success": True, "data": items})


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


@insights_bp.route('/refresh', methods=['POST'])
def refresh_insights():
    """Regenerate insights. In demo mode, resets to mock data."""
    global _initialized
    _insights_store.clear()
    _initialized = False
    store = _get_store()

    items = [i for i in store.values() if not i["dismissed"]]
    items.sort(key=lambda i: (not i["pinned"], i["priority"]))

    logger.info("Insights refreshed (mock mode)")
    return jsonify({"success": True, "data": items})


@insights_bp.route('/<insight_id>/pin', methods=['POST'])
def pin_insight(insight_id):
    """Toggle pin state for an insight."""
    store = _get_store()
    insight = store.get(insight_id)
    if not insight:
        return jsonify({"success": False, "error": "Insight not found"}), 404

    insight["pinned"] = not insight["pinned"]
    return jsonify({"success": True, "data": insight})


@insights_bp.route('/<insight_id>/dismiss', methods=['POST'])
def dismiss_insight(insight_id):
    """Dismiss an insight (soft delete)."""
    store = _get_store()
    insight = store.get(insight_id)
    if not insight:
        return jsonify({"success": False, "error": "Insight not found"}), 404

    insight["dismissed"] = True
    return jsonify({"success": True, "data": insight})


def _demo_data(data_type: str) -> dict:
    """Provide demo data so the generation endpoint works without a request body."""
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
