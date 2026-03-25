"""
Coalition labeling service.

Uses LLM to generate descriptive labels for coalitions, with
template-based fallback when no LLM key is configured.
"""

from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from .coalition_detector import Coalition

logger = get_logger('mirofish.coalition_labeler')

# Template labels for demo/fallback mode
TEMPLATE_LABELS = [
    "Growth Advocates",
    "Pragmatic Planners",
    "Innovation Seekers",
    "Market Defenders",
    "Digital Transformers",
    "Cost Optimizers",
    "Revenue Maximizers",
    "Risk Mitigators",
    "Customer Champions",
    "Tech Progressives",
]

TEMPLATE_DESCRIPTIONS = {
    "Growth Advocates": "Focused on aggressive expansion and product-led growth strategies.",
    "Pragmatic Planners": "Prioritize measured approach with emphasis on cost efficiency and risk management.",
    "Innovation Seekers": "Champion disruption, new market entry, and cutting-edge technology adoption.",
    "Market Defenders": "Concentrate on protecting existing market share and deepening customer relationships.",
    "Digital Transformers": "Push for modernization of legacy systems and digital-first strategies.",
    "Cost Optimizers": "Advocate for operational efficiency and lean resource allocation.",
    "Revenue Maximizers": "Target revenue growth through pricing, upselling, and market expansion.",
    "Risk Mitigators": "Emphasize compliance, security, and controlled change management.",
    "Customer Champions": "Drive customer-centric decisions and satisfaction-focused initiatives.",
    "Tech Progressives": "Favor early adoption of emerging technologies and experimentation.",
}


class CoalitionLabeler:
    """Labels and describes coalitions using LLM or templates."""

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None and Config.LLM_API_KEY:
            from ..utils.llm_client import LLMClient
            try:
                self._llm = LLMClient()
            except ValueError:
                self._llm = False
        return self._llm if self._llm else None

    def label_coalition(self, coalition: Coalition) -> str:
        """Generate a descriptive label for a coalition."""
        if coalition.label:
            return coalition.label

        llm = self._get_llm()
        if llm:
            return self._llm_label(llm, coalition)
        return self._template_label(coalition)

    def describe_coalition(self, coalition: Coalition) -> str:
        """Generate a longer description of what unites this coalition."""
        llm = self._get_llm()
        if llm:
            return self._llm_describe(llm, coalition)
        return self._template_describe(coalition)

    def explain_split(self, coalition_a: Coalition, coalition_b: Coalition) -> str:
        """Explain what divides two coalitions."""
        llm = self._get_llm()
        if llm:
            return self._llm_explain_split(llm, coalition_a, coalition_b)
        return self._template_explain_split(coalition_a, coalition_b)

    def label_all(self, coalitions: List[Coalition]) -> List[Coalition]:
        """Label all coalitions, returning updated list."""
        for coalition in coalitions:
            if not coalition.label:
                coalition.label = self.label_coalition(coalition)
        return coalitions

    # ── LLM-based labeling ────────────────────────────────────────

    def _llm_label(self, llm, coalition: Coalition) -> str:
        try:
            members = ", ".join(m["agent_name"] for m in coalition.members)
            positions = ", ".join(coalition.shared_positions) if coalition.shared_positions else "various topics"
            result = llm.chat_json(
                messages=[{
                    "role": "user",
                    "content": (
                        f"Generate a short 2-3 word label for a coalition of agents in a GTM simulation.\n"
                        f"Members: {members}\n"
                        f"Shared positions/topics: {positions}\n"
                        f"Coalition strength: {coalition.strength:.0%}\n"
                        f"Return JSON: {{\"label\": \"...\"}}"
                    ),
                }],
                temperature=0.5,
                max_tokens=100,
            )
            return result.get("label", self._template_label(coalition))
        except Exception as e:
            logger.warning(f"LLM label failed: {e}")
            return self._template_label(coalition)

    def _llm_describe(self, llm, coalition: Coalition) -> str:
        try:
            members = ", ".join(m["agent_name"] for m in coalition.members)
            positions = ", ".join(coalition.shared_positions) if coalition.shared_positions else "various topics"
            result = llm.chat_json(
                messages=[{
                    "role": "user",
                    "content": (
                        f"Describe what unites this coalition of agents in a GTM simulation.\n"
                        f"Members ({len(coalition.members)}): {members}\n"
                        f"Shared positions: {positions}\n"
                        f"Strength: {coalition.strength:.0%}\n"
                        f"Return JSON: {{\"description\": \"1-2 sentence description\"}}"
                    ),
                }],
                temperature=0.5,
                max_tokens=200,
            )
            return result.get("description", self._template_describe(coalition))
        except Exception as e:
            logger.warning(f"LLM describe failed: {e}")
            return self._template_describe(coalition)

    def _llm_explain_split(self, llm, a: Coalition, b: Coalition) -> str:
        try:
            result = llm.chat_json(
                messages=[{
                    "role": "user",
                    "content": (
                        f"Explain what divides these two coalitions in a GTM simulation.\n"
                        f"Coalition A '{a.label}' ({len(a.members)} members): positions on {', '.join(a.shared_positions)}\n"
                        f"Coalition B '{b.label}' ({len(b.members)} members): positions on {', '.join(b.shared_positions)}\n"
                        f"Return JSON: {{\"explanation\": \"1-2 sentence explanation\"}}"
                    ),
                }],
                temperature=0.5,
                max_tokens=200,
            )
            return result.get("explanation", self._template_explain_split(a, b))
        except Exception as e:
            logger.warning(f"LLM explain split failed: {e}")
            return self._template_explain_split(a, b)

    # ── Template-based fallback ───────────────────────────────────

    def _template_label(self, coalition: Coalition) -> str:
        idx = coalition.coalition_id % len(TEMPLATE_LABELS)
        return TEMPLATE_LABELS[idx]

    def _template_describe(self, coalition: Coalition) -> str:
        label = coalition.label or self._template_label(coalition)
        if label in TEMPLATE_DESCRIPTIONS:
            return TEMPLATE_DESCRIPTIONS[label]
        positions = ", ".join(coalition.shared_positions[:3]) if coalition.shared_positions else "shared interests"
        return f"A coalition of {len(coalition.members)} agents aligned around {positions}."

    def _template_explain_split(self, a: Coalition, b: Coalition) -> str:
        a_pos = ", ".join(a.shared_positions[:2]) if a.shared_positions else "their priorities"
        b_pos = ", ".join(b.shared_positions[:2]) if b.shared_positions else "different priorities"
        return (
            f"'{a.label}' focuses on {a_pos}, while "
            f"'{b.label}' prioritizes {b_pos}."
        )
