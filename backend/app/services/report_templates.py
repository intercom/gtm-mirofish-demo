"""
Report Templates Service

Pre-defined report templates for GTM simulation analysis.
Each template provides a structured outline (sections + formatting directives)
that bypasses the LLM planning phase, giving users predictable report structures
while the LLM focuses on content generation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


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


# ═══════════════════════════════════════════════════════════════
# Template Registry
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def list_templates() -> List[Dict[str, Any]]:
    return [t.to_summary() for t in TEMPLATES.values()]


def get_template(template_id: str) -> Optional[ReportTemplate]:
    return TEMPLATES.get(template_id)


def get_template_dict(template_id: str) -> Optional[Dict[str, Any]]:
    t = TEMPLATES.get(template_id)
    return t.to_dict() if t else None
