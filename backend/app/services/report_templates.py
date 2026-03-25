"""
Report Templates — Markdown templates for different report types.

Each template provides a pre-built structure that can be used:
1. By ReportAgent as guidance for LLM-powered generation
2. As demo/mock reports when no LLM key is configured

Templates use Jinja2-style placeholders filled by ReportAgent:
  {{chart:sentiment_trend}}, {{chart:agent_comparison}}, etc.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

from .report_agent import (
    Report, ReportOutline, ReportSection, ReportStatus, ReportManager,
    REPORT_TYPES,
)


CHART_DATA_DEMO = {
    "sentiment_trend": {
        "type": "line",
        "title": "Sentiment Trend Over Time",
        "labels": ["Round 1-12", "Round 13-24", "Round 25-36", "Round 37-48",
                    "Round 49-60", "Round 61-72", "Round 73-84", "Round 85-96"],
        "datasets": [
            {"label": "VP Support", "data": [0.2, 0.3, 0.45, 0.5, 0.55, 0.62, 0.7, 0.72]},
            {"label": "CX Director", "data": [0.1, 0.25, 0.35, 0.42, 0.5, 0.58, 0.6, 0.65]},
            {"label": "IT Leader", "data": [-0.1, 0.0, 0.1, 0.15, 0.25, 0.3, 0.35, 0.4]},
        ],
    },
    "agent_comparison": {
        "type": "horizontal_bar",
        "title": "Agent Engagement Scores",
        "labels": ["Sarah Chen (VP Support)", "Michael Torres (CX Director)",
                    "Jennifer Park (IT Leader)", "David Kim (Operations)",
                    "Lisa Johnson (Finance)"],
        "values": [87, 74, 68, 62, 55],
    },
    "persona_engagement": {
        "type": "bar",
        "title": "Persona Engagement Rates",
        "labels": ["VP Support", "CX Director", "IT Leader", "Operations Lead", "Finance"],
        "values": [92, 78, 71, 65, 58],
    },
    "decision_stages": {
        "type": "donut",
        "title": "Buyer Decision Stage Distribution",
        "labels": ["Awareness", "Interest", "Consideration", "Intent", "Evaluation", "Decision"],
        "values": [2, 3, 4, 3, 2, 1],
    },
    "competitive_mentions": {
        "type": "stacked_bar",
        "title": "Competitive Mentions Over Time",
        "labels": ["Round 1-24", "Round 25-48", "Round 49-72", "Round 73-96"],
        "datasets": [
            {"label": "Zendesk", "data": [12, 15, 8, 5]},
            {"label": "Freshdesk", "data": [8, 10, 6, 3]},
            {"label": "HubSpot", "data": [5, 7, 9, 4]},
        ],
    },
}


# ── Template definitions ──────────────────────────────────────────

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "executive_summary": {
        "title": "GTM Simulation — Executive Summary",
        "summary": "High-level findings and strategic recommendations from the agent-based GTM simulation.",
        "sections": [
            {
                "title": "Executive Overview",
                "content": (
                    "This simulation modeled **15 autonomous agents** representing key buyer "
                    "personas across enterprise SaaS evaluation. Over **96 simulated rounds** "
                    "(72 hours), agents engaged in organic social discussions on Twitter and "
                    "Reddit, revealing authentic buying signals and competitive dynamics.\n\n"
                    "**Key Metrics:**\n"
                    "- Total agent interactions: 1,247\n"
                    "- Unique topics discussed: 34\n"
                    "- Average sentiment score: +0.42 (positive)\n"
                    "- Agents reaching Decision stage: 4 of 15 (27%)\n\n"
                    "{{chart:persona_engagement}}"
                ),
            },
            {
                "title": "Key Findings",
                "content": (
                    "**1. Support leaders are the strongest advocates**\n"
                    "VP-level support leaders showed the highest engagement rates (92%) and "
                    "moved through decision stages fastest. Their primary concern is resolution "
                    "time and AI accuracy for technical tickets.\n\n"
                    "**2. IT security concerns slow adoption for technical buyers**\n"
                    "IT leaders consistently raised data residency and SOC2 compliance questions. "
                    "Addressing these early in the sales process would accelerate deal velocity "
                    "by an estimated 2-3 weeks.\n\n"
                    "**3. Competitive positioning against Zendesk is critical**\n"
                    "Zendesk was mentioned 40 times across all agent discussions — more than "
                    "double any other competitor. Agents who evaluated both products focused on "
                    "AI-native vs bolt-on AI capabilities as the key differentiator.\n\n"
                    "{{chart:sentiment_trend}}"
                ),
            },
            {
                "title": "Competitive Landscape",
                "content": (
                    "The simulation revealed clear competitive dynamics across the buyer journey:\n\n"
                    "| Competitor | Mentions | Sentiment | Key Comparison Point |\n"
                    "|-----------|----------|-----------|---------------------|\n"
                    "| Zendesk | 40 | Mixed (-0.1) | AI-native vs bolt-on |\n"
                    "| Freshdesk | 27 | Neutral (0.0) | Price/value ratio |\n"
                    "| HubSpot | 25 | Slightly positive (+0.2) | All-in-one platform |\n"
                    "| Salesforce | 12 | Negative (-0.3) | Complexity/cost |\n"
                    "| Help Scout | 8 | Positive (+0.4) | SMB simplicity |\n\n"
                    "{{chart:competitive_mentions}}"
                ),
            },
            {
                "title": "Recommendations",
                "content": (
                    "Based on the simulation results, we recommend the following strategic actions:\n\n"
                    "**Immediate (0-2 weeks):**\n"
                    "- Create a competitive battle card focused on Zendesk AI comparison\n"
                    "- Develop a security/compliance FAQ for IT buyer personas\n"
                    "- Add resolution time benchmarks to sales collateral\n\n"
                    "**Short-term (2-6 weeks):**\n"
                    "- Build a pilot program template targeting VP Support personas\n"
                    "- Create ROI calculator addressing Finance buyer concerns\n"
                    "- Develop case studies highlighting AI accuracy metrics\n\n"
                    "**Medium-term (1-3 months):**\n"
                    "- Launch a thought leadership campaign on AI-native support\n"
                    "- Build integration demos for top requested platforms\n"
                    "- Create a competitive migration guide from Zendesk"
                ),
            },
        ],
    },

    "detailed_analysis": {
        "title": "GTM Simulation — Detailed Analysis",
        "summary": "Comprehensive breakdown of agent behavior, engagement patterns, and decision trajectories.",
        "sections": [
            {
                "title": "Simulation Context",
                "content": (
                    "This detailed analysis covers the full simulation lifecycle of 15 buyer "
                    "personas engaging across Twitter and Reddit over 96 rounds (72 simulated hours).\n\n"
                    "**Simulation Parameters:**\n"
                    "- Agent count: 15\n"
                    "- Platforms: Twitter, Reddit\n"
                    "- Duration: 72 simulated hours (96 rounds)\n"
                    "- Persona types: VP Support, CX Director, IT Leader, Operations, Finance"
                ),
            },
            {
                "title": "Agent Engagement Analysis",
                "content": (
                    "{{chart:agent_comparison}}\n\n"
                    "**Top Engaged Agents:**\n\n"
                    "| Agent | Role | Posts | Replies | Engagement Score |\n"
                    "|-------|------|-------|---------|------------------|\n"
                    "| Sarah Chen | VP Support | 45 | 32 | 87 |\n"
                    "| Michael Torres | CX Director | 38 | 28 | 74 |\n"
                    "| Jennifer Park | IT Leader | 31 | 22 | 68 |\n"
                    "| David Kim | Operations | 28 | 18 | 62 |\n"
                    "| Lisa Johnson | Finance | 22 | 15 | 55 |\n\n"
                    "Support-focused personas drove the highest engagement, consistent with "
                    "product-led evaluation patterns observed in enterprise SaaS."
                ),
            },
            {
                "title": "Sentiment Evolution",
                "content": (
                    "Sentiment across all agents trended positive over the simulation period, "
                    "with a notable inflection point around Round 36 when agents began sharing "
                    "pilot results.\n\n"
                    "{{chart:sentiment_trend}}\n\n"
                    "**Key sentiment drivers:**\n"
                    "- Positive: AI accuracy reports, resolution time improvements, ease of setup\n"
                    "- Negative: Pricing concerns, integration complexity, data migration fears\n"
                    "- Neutral: Feature comparisons, general industry discussion"
                ),
            },
            {
                "title": "Decision Journey Breakdown",
                "content": (
                    "{{chart:decision_stages}}\n\n"
                    "**Stage Transitions:**\n"
                    "- Awareness → Interest: Average 8 rounds (driven by peer recommendations)\n"
                    "- Interest → Consideration: Average 14 rounds (feature evaluation phase)\n"
                    "- Consideration → Intent: Average 20 rounds (pilot/POC discussions)\n"
                    "- Intent → Decision: Average 12 rounds (budget/stakeholder alignment)\n\n"
                    "Agents with prior negative experiences with competitors moved through "
                    "stages ~30% faster than those in greenfield evaluations."
                ),
            },
            {
                "title": "Platform Behavior Differences",
                "content": (
                    "**Twitter:** Short-form opinions, competitive hot-takes, and quick reactions. "
                    "Higher volume but lower depth. 65% of total interactions occurred on Twitter.\n\n"
                    "**Reddit:** Longer-form analysis, technical deep-dives, and honest reviews. "
                    "35% of interactions, but generated 60% of actionable buying signals.\n\n"
                    "Reddit discussions were 3x more likely to contain specific product "
                    "comparison data and technical requirements."
                ),
            },
            {
                "title": "Conclusions & Next Steps",
                "content": (
                    "The simulation demonstrates strong product-market fit among support-focused "
                    "buyer personas, with AI capabilities serving as the primary differentiator. "
                    "The main friction points — security concerns and pricing — are addressable "
                    "through targeted collateral and flexible packaging.\n\n"
                    "**Recommended follow-up simulations:**\n"
                    "1. Pricing sensitivity analysis with varied tier structures\n"
                    "2. Competitive win/loss simulation against Zendesk specifically\n"
                    "3. Multi-region simulation to test geographic messaging differences"
                ),
            },
        ],
    },

    "agent_comparison": {
        "title": "GTM Simulation — Agent Comparison",
        "summary": "Side-by-side comparison of agent behaviors, influence patterns, and decision outcomes.",
        "sections": [
            {
                "title": "Agent Overview",
                "content": (
                    "This report compares the 15 simulated buyer agents across key dimensions "
                    "including engagement, sentiment, influence, and decision progress.\n\n"
                    "{{chart:agent_comparison}}"
                ),
            },
            {
                "title": "Persona Type Analysis",
                "content": (
                    "{{chart:persona_engagement}}\n\n"
                    "**VP Support personas** led in both engagement and positive sentiment, "
                    "confirming they are the ideal ICP for initial outreach. **CX Directors** "
                    "showed strong engagement but more cautious sentiment, indicating a need "
                    "for more proof points. **IT Leaders** had the lowest initial sentiment "
                    "but the steepest improvement curve once security questions were addressed."
                ),
            },
            {
                "title": "Influence Network",
                "content": (
                    "The agent influence analysis reveals key opinion leaders:\n\n"
                    "| Agent | Influence Score | Influenced By | Influences |\n"
                    "|-------|----------------|---------------|------------|\n"
                    "| Sarah Chen | 0.92 | — | Torres, Kim, Johnson |\n"
                    "| Michael Torres | 0.78 | Chen | Park, Kim |\n"
                    "| Jennifer Park | 0.71 | Torres | Kim |\n"
                    "| David Kim | 0.55 | Chen, Park | Johnson |\n"
                    "| Lisa Johnson | 0.48 | Kim | — |\n\n"
                    "Sarah Chen (VP Support) emerged as the primary opinion leader, with her "
                    "positive pilot results influencing 3 other agents to advance in their "
                    "decision journey."
                ),
            },
            {
                "title": "Decision Stage Comparison",
                "content": (
                    "{{chart:decision_stages}}\n\n"
                    "**Fastest movers:** VP Support and CX Director personas reached Evaluation "
                    "stage within 60 rounds.\n\n"
                    "**Slowest movers:** Finance and IT personas required more data points "
                    "and peer validation before advancing past Consideration stage."
                ),
            },
        ],
    },

    "decision_audit": {
        "title": "GTM Simulation — Decision Audit Trail",
        "summary": "Chronological record of key decisions, rationale, and dissenting opinions from the simulation.",
        "sections": [
            {
                "title": "Audit Overview",
                "content": (
                    "This audit trail documents every significant decision point observed "
                    "during the simulation, including the rationale expressed by agents and "
                    "any dissenting opinions.\n\n"
                    "**Total decision events tracked: 23**\n"
                    "**Agents reaching final Decision stage: 4**\n"
                    "**Average rounds to decision: 72**"
                ),
            },
            {
                "title": "Decision Timeline",
                "content": (
                    "**Round 12 — Initial Interest Signals**\n"
                    "Sarah Chen (VP Support) shares positive experience with AI-powered ticket "
                    "routing. Three agents engage with follow-up questions.\n\n"
                    "**Round 24 — Feature Evaluation Begins**\n"
                    "Michael Torres (CX Director) posts detailed comparison of AI capabilities "
                    "across three vendors. Jennifer Park (IT) raises SOC2 compliance question.\n\n"
                    "**Round 36 — Pilot Results Shared**\n"
                    "Sarah Chen reports 47% improvement in resolution time during pilot. This "
                    "becomes the most-referenced data point in subsequent discussions.\n\n"
                    "**Round 48 — Competitive Debate Peak**\n"
                    "Extended Twitter thread comparing AI-native vs bolt-on approaches. "
                    "Zendesk is mentioned 18 times in this period alone.\n\n"
                    "**Round 60 — Budget Discussions**\n"
                    "Lisa Johnson (Finance) raises pricing concerns. David Kim (Operations) "
                    "counters with efficiency gains data.\n\n"
                    "**Round 72 — Decision Convergence**\n"
                    "4 agents indicate intent to recommend or proceed with evaluation. "
                    "2 agents remain skeptical due to unresolved security questions."
                ),
            },
            {
                "title": "Dissenting Opinions",
                "content": (
                    "**Jennifer Park (IT Leader):** Consistently raised data residency and "
                    "compliance concerns. While acknowledging the product's capabilities, "
                    "she withheld positive recommendation pending security documentation.\n\n"
                    "**Lisa Johnson (Finance):** Questioned ROI projections and requested "
                    "more concrete cost-savings data. Her influence delayed budget discussions "
                    "by approximately 12 rounds.\n\n"
                    "These dissenting voices represent real objections that will arise during "
                    "enterprise sales cycles and should be proactively addressed."
                ),
            },
            {
                "title": "Decision Outcomes",
                "content": (
                    "| Agent | Final Stage | Sentiment | Key Factor |\n"
                    "|-------|------------|-----------|------------|\n"
                    "| Sarah Chen | Decision | +0.72 | Pilot results |\n"
                    "| Michael Torres | Evaluation | +0.65 | AI capabilities |\n"
                    "| Jennifer Park | Consideration | +0.40 | Security pending |\n"
                    "| David Kim | Intent | +0.55 | Efficiency gains |\n"
                    "| Lisa Johnson | Interest | +0.35 | ROI data needed |\n\n"
                    "The simulation suggests that addressing security documentation and "
                    "providing concrete ROI data could move 2-3 additional agents to "
                    "Decision stage in a follow-up simulation."
                ),
            },
        ],
    },
}


def get_template_outline(report_type: str) -> ReportOutline:
    """Get a ReportOutline from a template definition."""
    template = TEMPLATES.get(report_type, TEMPLATES["executive_summary"])
    sections = [
        ReportSection(title=s["title"], content="")
        for s in template["sections"]
    ]
    return ReportOutline(
        title=template["title"],
        summary=template["summary"],
        sections=sections,
    )


def generate_demo_report(
    report_id: str,
    simulation_id: str,
    report_type: str = "executive_summary",
    custom_prompt: Optional[str] = None,
    include_charts: bool = True,
) -> Report:
    """
    Generate a complete demo report from templates.

    Used when no LLM key is configured — produces a realistic
    pre-built report so the full UI flow can be demonstrated.
    """
    template = TEMPLATES.get(report_type, TEMPLATES["executive_summary"])

    sections = [
        ReportSection(title=s["title"], content=s["content"])
        for s in template["sections"]
    ]
    outline = ReportOutline(
        title=template["title"],
        summary=template["summary"],
        sections=sections,
    )

    md = outline.to_markdown()

    chart_data = CHART_DATA_DEMO if include_charts else None

    now = datetime.now().isoformat()
    report = Report(
        report_id=report_id,
        simulation_id=simulation_id,
        graph_id="demo",
        simulation_requirement=custom_prompt or f"Demo {report_type} report",
        status=ReportStatus.COMPLETED,
        outline=outline,
        markdown_content=md,
        created_at=now,
        completed_at=now,
        report_type=report_type,
        custom_prompt=custom_prompt,
        include_charts=include_charts,
        chart_data=chart_data,
    )

    ReportManager.save_report(report)
    # Save individual sections for the sections endpoint
    for i, section in enumerate(sections, start=1):
        ReportManager.save_section(report_id, i, section)

    return report
