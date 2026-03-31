"""
Report Templates Service

Pre-defined report templates for GTM simulation analysis, plus
demo content templates for offline/mock mode.

Two template systems:
1. ReportTemplate — metadata/structure that guides LLM report generation
2. DEMO_TEMPLATES — full pre-written content for demo mode (no LLM key)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from .report_agent import (
    Report, ReportOutline, ReportSection, ReportStatus, ReportManager,
    REPORT_TYPES,
)


# ═══════════════════════════════════════════════════════════════
# Template Metadata (for LLM-guided generation)
# ═══════════════════════════════════════════════════════════════

@dataclass
class TemplateSectionDef:
    """A section definition within a report template."""
    title: str
    description: str
    formatting_hint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "formatting_hint": self.formatting_hint,
        }


@dataclass
class ReportTemplate:
    """A report template with predefined structure and formatting."""
    id: str
    name: str
    description: str
    icon: str
    category: str
    sections: List[TemplateSectionDef]
    formatting: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "sections": [s.to_dict() for s in self.sections],
            "formatting": self.formatting,
        }

    def to_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "section_count": len(self.sections),
        }


# ── Template Registry ────────────────────────────────────────

TEMPLATES: Dict[str, ReportTemplate] = {}


def _register(template: ReportTemplate):
    TEMPLATES[template.id] = template


_register(ReportTemplate(
    id="executive_summary",
    name="Executive Summary",
    description="Concise 2-section briefing for leadership. Highlights key outcomes and strategic recommendations.",
    icon="briefcase",
    category="leadership",
    sections=[
        TemplateSectionDef(
            title="Key Outcomes & Findings",
            description="Top-line results from the simulation: what happened, which signals were strongest, and the most significant behavioral patterns observed.",
            formatting_hint="Lead with the single most important finding. Use bold callouts for metrics. Keep paragraphs short — this section should be scannable in under 2 minutes.",
        ),
        TemplateSectionDef(
            title="Strategic Recommendations",
            description="Actionable next steps derived from the simulation outcomes. Prioritize by impact and feasibility.",
            formatting_hint="Use a numbered list of 3-5 recommendations. Each recommendation should have a bold title followed by 1-2 sentences of context. End with a clear call-to-action.",
        ),
    ],
    formatting={
        "tone": "executive",
        "length": "concise",
        "style": "Lead with conclusions, support with evidence. Avoid jargon. Every paragraph should answer 'so what?'",
    },
))

_register(ReportTemplate(
    id="campaign_analysis",
    name="Campaign Performance Analysis",
    description="Deep-dive into outbound campaign simulation results: messaging effectiveness, persona engagement, and sequence optimization.",
    icon="chart-bar",
    category="marketing",
    sections=[
        TemplateSectionDef(
            title="Messaging Effectiveness",
            description="Which messages and subject lines resonated with the target audience? Compare engagement patterns across messaging variants.",
            formatting_hint="Include direct quotes from simulated agents showing their reactions to different messages. Use comparative language (e.g., 'Message A outperformed Message B by...').",
        ),
        TemplateSectionDef(
            title="Persona Engagement Breakdown",
            description="How did different buyer personas (VP Support, CX Director, IT Leader, etc.) respond? Identify which personas are most receptive and which are resistant.",
            formatting_hint="Organize by persona type. For each persona, describe their reaction pattern and include representative quotes. Highlight surprising findings.",
        ),
        TemplateSectionDef(
            title="Objection Patterns & Resistance",
            description="What objections and concerns emerged? Map objections by persona and industry vertical.",
            formatting_hint="Group objections thematically. Quote agent responses that illustrate each objection type. Note which objections are addressable vs. deal-breakers.",
        ),
        TemplateSectionDef(
            title="Optimization Recommendations",
            description="Data-backed recommendations for improving campaign performance: messaging tweaks, targeting refinements, and cadence adjustments.",
            formatting_hint="Use a numbered list format. Each recommendation should cite specific simulation evidence. Include a priority indicator (high/medium/low impact).",
        ),
    ],
    formatting={
        "tone": "analytical",
        "length": "detailed",
        "style": "Data-driven with agent quotes as evidence. Use comparative analysis between variants. Include specific percentages and patterns where the data supports them.",
    },
))

_register(ReportTemplate(
    id="competitive_intel",
    name="Competitive Intelligence Report",
    description="How prospects perceive competitive positioning. Maps brand sentiment, switching barriers, and displacement opportunities.",
    icon="shield",
    category="strategy",
    sections=[
        TemplateSectionDef(
            title="Competitive Perception Landscape",
            description="How do simulated prospects perceive the competitive landscape? What are their existing loyalties and how strong are they?",
            formatting_hint="Map the competitive landscape from the prospect's viewpoint. Include quotes showing sentiment toward both the incumbent and the challenger. Note emotional vs. rational drivers.",
        ),
        TemplateSectionDef(
            title="Switching Barriers & Triggers",
            description="What prevents prospects from switching? What events or conditions would trigger a switch? Identify the tipping points.",
            formatting_hint="Separate barriers (reasons to stay) from triggers (reasons to switch). Use agent quotes to illustrate each. Rank barriers by how frequently they appeared in the simulation.",
        ),
        TemplateSectionDef(
            title="Displacement Strategy Insights",
            description="Based on simulation outcomes, which competitive displacement strategies work and which backfire? What messaging angles are most effective?",
            formatting_hint="Contrast what works vs. what doesn't. Include specific examples of messaging that triggered positive vs. negative reactions. End with clear strategic guidance.",
        ),
    ],
    formatting={
        "tone": "strategic",
        "length": "moderate",
        "style": "Strategic narrative backed by agent behavior evidence. Balance qualitative insights with behavioral patterns. Focus on actionable competitive intelligence.",
    },
))

_register(ReportTemplate(
    id="audience_insights",
    name="Audience Insights Deep Dive",
    description="Behavioral segmentation and persona analysis. Reveals how different audience segments think, react, and decide.",
    icon="users",
    category="research",
    sections=[
        TemplateSectionDef(
            title="Behavioral Segments Identified",
            description="What distinct behavioral clusters emerged from the simulation? How do prospects naturally segment based on their reactions and engagement patterns?",
            formatting_hint="Name each segment with a descriptive label (e.g., 'Active Evaluators', 'Budget Blockers'). For each segment, describe their defining behaviors and include representative quotes.",
        ),
        TemplateSectionDef(
            title="Decision-Making Patterns",
            description="How do different personas approach the buying decision? What information do they seek? What influences their opinion?",
            formatting_hint="Organize by persona or segment. Describe the decision journey including triggers, information needs, and influencing factors. Use quotes to illustrate decision-making rationale.",
        ),
        TemplateSectionDef(
            title="Sentiment & Emotional Drivers",
            description="What emotions drive prospect behavior? Map the sentiment landscape across different segments and topics.",
            formatting_hint="Describe the emotional spectrum observed. Include quotes showing both positive and negative sentiment. Identify which emotions correlate with engagement vs. disengagement.",
        ),
    ],
    formatting={
        "tone": "research",
        "length": "detailed",
        "style": "Rich with behavioral evidence and direct quotes. Use empathetic framing — help the reader understand how prospects think and feel. Highlight non-obvious insights.",
    },
))

_register(ReportTemplate(
    id="full_gtm_analysis",
    name="Full GTM Analysis",
    description="Comprehensive multi-chapter analysis. The AI plans the optimal report structure based on simulation results.",
    icon="document-text",
    category="comprehensive",
    sections=[],
    formatting={
        "tone": "comprehensive",
        "length": "detailed",
        "style": "Let the AI determine the optimal structure based on what the simulation reveals. This produces the most thorough analysis.",
    },
))


def list_templates() -> List[Dict[str, Any]]:
    return [t.to_summary() for t in TEMPLATES.values()]


def get_template(template_id: str) -> Optional[ReportTemplate]:
    return TEMPLATES.get(template_id)


def get_template_dict(template_id: str) -> Optional[Dict[str, Any]]:
    t = TEMPLATES.get(template_id)
    return t.to_dict() if t else None


# ═══════════════════════════════════════════════════════════════
# Demo Content Templates (for offline/mock mode)
# ═══════════════════════════════════════════════════════════════

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


DEMO_TEMPLATES: Dict[str, Dict[str, Any]] = {
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
    """Get a ReportOutline from a demo template definition."""
    template = DEMO_TEMPLATES.get(report_type, DEMO_TEMPLATES["executive_summary"])
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
    template = DEMO_TEMPLATES.get(report_type, DEMO_TEMPLATES["executive_summary"])

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
    for i, section in enumerate(sections, start=1):
        ReportManager.save_section(report_id, i, section)

    return report
