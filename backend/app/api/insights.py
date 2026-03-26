"""
Insights API
Serves LLM-generated (or template-based) GTM insights with priority sorting,
category grouping, and pin/dismiss actions. Falls back to mock data when no
LLM key is configured.

Also provides an AI analyst chatbot endpoint for conversational GTM questions.
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
# AI Analyst Chatbot (canned responses + LLM)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an AI GTM analyst embedded in a go-to-market simulation platform. "
    "The user is viewing GTM data dashboards (campaigns, pipeline, churn, revenue, "
    "customer segments). Answer their questions concisely using data-driven reasoning. "
    "Reference specific metrics, percentages, and trends when possible. "
    "Keep answers to 2-4 paragraphs. Use markdown formatting for emphasis."
)

CANNED_RESPONSES = {
    "churn": (
        "Based on the current data, **monthly churn increased 1.2pp to 4.8%** last quarter, "
        "primarily driven by the SMB segment. The top factors were:\n\n"
        "1. **Onboarding friction** — 38% of churned accounts never completed setup\n"
        "2. **Support response time** — avg 18hr for churned vs 4hr for retained\n"
        "3. **Feature adoption** — churned accounts used only 2.1 of 8 core features\n\n"
        "Recommendation: focus retention efforts on accounts with <3 features adopted "
        "in their first 30 days."
    ),
    "campaign": (
        "The **\"Enterprise Webinar Series\"** campaign shows the strongest ROI at **5.2x**, "
        "generating $1.2M in pipeline from $230K spend. Key metrics:\n\n"
        "- **Email nurture**: 24% open rate, 3.8% CTR (above 2.5% benchmark)\n"
        "- **LinkedIn ads**: $42 CPL vs $78 industry avg\n"
        "- **Content syndication**: lowest performer at 1.1x ROI\n\n"
        "The paid search campaign has the highest volume but ROI has declined 15% QoQ — "
        "consider reallocating budget toward the webinar funnel."
    ),
    "pipeline": (
        "Current pipeline stands at **$4.2M** with a weighted value of **$1.8M**. "
        "Stage conversion rates:\n\n"
        "- Discovery \u2192 Evaluation: **62%** (healthy)\n"
        "- Evaluation \u2192 Proposal: **38%** (below 45% target)\n"
        "- Proposal \u2192 Closed Won: **28%**\n\n"
        "The Evaluation\u2192Proposal drop is the biggest bottleneck. "
        "Deals stalling here average **23 days** in stage vs 14 for those that advance. "
        "Enterprise segment has the worst conversion at 31% vs 44% for Mid-Market."
    ),
    "revenue": (
        "**Net Revenue Retention is 108%**, driven by expansion in the Mid-Market segment. "
        "Breakdown:\n\n"
        "- **Gross retention**: 92% (target: 90%+)\n"
        "- **Expansion revenue**: $380K this quarter (+22% QoQ)\n"
        "- **Contraction**: $95K, mostly from seat downgrades in SMB\n\n"
        "The Enterprise segment shows the strongest expansion at 118% NRR, "
        "while SMB is at 96% — below the 100% break-even threshold."
    ),
    "segment": (
        "Performance by segment (sorted by NRR):\n\n"
        "| Segment | Avg MRR | NRR | Churn Rate | CSAT |\n"
        "|---------|---------|-----|------------|------|\n"
        "| Enterprise | $12,400 | 118% | 1.2% | 4.6 |\n"
        "| Mid-Market | $3,200 | 112% | 3.1% | 4.2 |\n"
        "| SMB | $680 | 96% | 7.8% | 3.8 |\n\n"
        "**Enterprise** is the clear winner on all metrics. SMB churn is 6.5x Enterprise — "
        "the self-serve onboarding flow needs urgent attention."
    ),
}

DEFAULT_RESPONSE = (
    "Based on the available GTM data, here's what I can tell you:\n\n"
    "The overall pipeline health is **solid at $4.2M**, with net revenue retention "
    "at **108%**. The biggest opportunities are:\n\n"
    "1. **Fix the Eval\u2192Proposal bottleneck** — 38% conversion vs 45% target\n"
    "2. **Reduce SMB churn** — 7.8% monthly vs 1.2% for Enterprise\n"
    "3. **Double down on webinar campaigns** — 5.2x ROI, highest of all channels\n\n"
    "Want me to dive deeper into any of these areas?"
)


def _match_canned_response(message: str) -> str:
    """Match user message to a canned response by keyword."""
    msg = message.lower()
    for keyword, response in CANNED_RESPONSES.items():
        if keyword in msg:
            return response
    return DEFAULT_RESPONSE


def _build_messages(message: str, chat_history: list, context: dict) -> list:
    """Build the LLM message array from chat history and context."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        context_note = (
            f"The user is currently viewing: {context.get('page', 'unknown')}. "
            f"Active filters: {context.get('filters', 'none')}. "
            f"Loaded data types: {', '.join(context.get('dataTypes', ['general GTM metrics']))}."
        )
        messages.append({"role": "system", "content": context_note})

    for entry in chat_history:
        role = entry.get('role')
        content = entry.get('content')
        if role in ('user', 'assistant') and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})
    return messages


# ---------------------------------------------------------------------------
# Routes — Insight Cards
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


# ---------------------------------------------------------------------------
# Route — AI Analyst Chat
# ---------------------------------------------------------------------------

@insights_bp.route('/chat', methods=['POST'])
def insights_chat():
    """
    Chat with the AI analyst about GTM data.

    Request JSON:
        {
            "message": "Why did churn increase last month?",
            "context": {
                "page": "ChurnAnalysis",
                "filters": "Q4 2025, SMB",
                "dataTypes": ["churn", "segments"]
            },
            "chat_history": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    Response:
        {
            "success": true,
            "data": {
                "response": "Based on the data...",
                "sources": ["churn_metrics", "segment_breakdown"]
            }
        }
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({"success": False, "error": "message is required"}), 400

    if len(message) > 2000:
        return jsonify({"success": False, "error": "message exceeds 2000 characters"}), 400

    chat_history = data.get('chat_history', [])
    context = data.get('context', {})

    if Config.LLM_API_KEY:
        try:
            from ..utils.llm_client import LLMClient
            client = LLMClient()
            messages = _build_messages(message, chat_history, context)
            response_text = client.chat(messages=messages, temperature=0.5, max_tokens=1024)

            sources = []
            if context.get('dataTypes'):
                sources = context['dataTypes']

            return jsonify({
                "success": True,
                "data": {
                    "response": response_text,
                    "sources": sources,
                }
            })
        except Exception as e:
            logger.warning(f"LLM call failed, falling back to canned response: {e}")

    response_text = _match_canned_response(message)
    sources = []
    msg_lower = message.lower()
    for keyword in CANNED_RESPONSES:
        if keyword in msg_lower:
            sources.append(f"{keyword}_metrics")
    if not sources:
        sources = ["general_gtm_summary"]

    return jsonify({
        "success": True,
        "data": {
            "response": response_text,
            "sources": sources,
        }
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
