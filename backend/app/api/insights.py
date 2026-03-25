"""
Insights API
Serves AI-generated GTM insights with priority sorting, category grouping,
and pin/dismiss actions. Falls back to mock data when no LLM key is configured.
"""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.insights')

insights_bp = Blueprint('insights', __name__, url_prefix='/api/v1/insights')

# In-memory store (replaced by DB in production)
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
                "Mean close time rose 38% (68 → 94 days) in EMEA enterprise segment",
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
                "Inbound MQLs up 27% QoQ in the $50K–$200K ACV band",
                "Product-led signup → SQL conversion at 14.3% vs 6.8% baseline",
                "Demo request volume correlates with recent product launch activity",
            ],
            "pinned": False,
            "dismissed": False,
            "created_at": now,
        },
        {
            "id": "ins-ops-01",
            "title": "SDR response time exceeds SLA in APAC hours",
            "description": "During APAC business hours, average lead response time is 4.2 hours — well above the 1-hour SLA target — due to timezone coverage gaps.",
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
                "Discount threshold for deal closure averaged 18% — above typical 12%",
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
                "Reply rate is 1.8% vs 4.2% average — suggesting subject line issues",
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
                "NRR at 118% — up from 109% in prior simulation cycle",
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


@insights_bp.route('', methods=['GET'])
def list_insights():
    """List all non-dismissed insights, sorted by priority (pinned first)."""
    store = _get_store()
    category = request.args.get('category')

    insights = [i for i in store.values() if not i["dismissed"]]

    if category:
        insights = [i for i in insights if i["category"] == category]

    insights.sort(key=lambda i: (not i["pinned"], i["priority"]))

    return jsonify({"success": True, "data": insights})


@insights_bp.route('/refresh', methods=['POST'])
def refresh_insights():
    """Regenerate insights. In demo mode, resets to mock data."""
    global _initialized
    _insights_store.clear()
    _initialized = False
    store = _get_store()

    insights = [i for i in store.values() if not i["dismissed"]]
    insights.sort(key=lambda i: (not i["pinned"], i["priority"]))

    logger.info("Insights refreshed (mock mode)")
    return jsonify({"success": True, "data": insights})


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
