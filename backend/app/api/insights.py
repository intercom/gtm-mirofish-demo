"""
Insights API — AI analyst chatbot for GTM data questions.

Provides a chat endpoint that uses the configured LLM to answer
questions about loaded GTM data (campaigns, pipeline, churn, etc.).
Falls back to canned responses when no LLM key is configured.
"""

import logging
from flask import Blueprint, jsonify, request

from ..config import Config

logger = logging.getLogger('mirofish.insights')

insights_bp = Blueprint('insights', __name__, url_prefix='/api/insights')

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
        "- Discovery → Evaluation: **62%** (healthy)\n"
        "- Evaluation → Proposal: **38%** (below 45% target)\n"
        "- Proposal → Closed Won: **28%**\n\n"
        "The Evaluation→Proposal drop is the biggest bottleneck. "
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
    "1. **Fix the Eval→Proposal bottleneck** — 38% conversion vs 45% target\n"
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


@insights_bp.route('/chat', methods=['POST'])
def insights_chat():
    """
    Chat with the AI analyst about GTM data.

    Request JSON:
        {
            "message": "Why did churn increase last month?",
            "context": {                        // optional
                "page": "ChurnAnalysis",
                "filters": "Q4 2025, SMB",
                "dataTypes": ["churn", "segments"]
            },
            "chat_history": [                   // optional
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

    # Try LLM if configured, otherwise fall back to canned responses
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

    # Demo / fallback mode — keyword-matched canned responses
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
