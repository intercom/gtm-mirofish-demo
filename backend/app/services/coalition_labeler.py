"""
Coalition labeling service.

Auto-generates descriptive labels for agent coalitions detected
during OASIS simulations. Uses LLM when available, falls back to
deterministic template-based labels.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('mirofish.coalition_labeler')


@dataclass
class Coalition:
    """A group of aligned agents within a simulation."""
    members: List[Dict[str, Any]]
    shared_positions: List[str]
    formation_round: int = 0
    strength: float = 0.0
    label: str = ''


# Template fragments for deterministic fallback labeling
_DEPARTMENT_KEYWORDS = {
    'sales': 'Sales',
    'marketing': 'Marketing',
    'product': 'Product',
    'engineering': 'Engineering',
    'customer success': 'CS',
    'support': 'Support',
    'finance': 'Finance',
    'leadership': 'Leadership',
    'ops': 'Ops',
    'operations': 'Ops',
}

_TOPIC_KEYWORDS = {
    'revenue': 'Revenue',
    'growth': 'Growth',
    'retention': 'Retention',
    'pricing': 'Pricing',
    'expansion': 'Expansion',
    'churn': 'Churn',
    'cost': 'Cost',
    'automation': 'Automation',
    'ai': 'AI',
    'enterprise': 'Enterprise',
    'smb': 'SMB',
    'self-serve': 'Self-Serve',
    'outbound': 'Outbound',
    'inbound': 'Inbound',
    'product-led': 'PLG',
    'innovation': 'Innovation',
    'quality': 'Quality',
    'scale': 'Scale',
    'efficiency': 'Efficiency',
}

_TRAIT_KEYWORDS = {
    'aggressive': 'Aggressive',
    'conservative': 'Conservative',
    'optimistic': 'Optimistic',
    'cautious': 'Cautious',
    'innovative': 'Innovative',
    'pragmatic': 'Pragmatic',
    'risk': 'Risk-Aware',
    'data-driven': 'Data-Driven',
    'customer-first': 'Customer-First',
}

_FALLBACK_LABELS = [
    'Alpha Coalition',
    'Beta Coalition',
    'Gamma Coalition',
    'Delta Coalition',
    'Epsilon Coalition',
    'Zeta Coalition',
]


def _normalize_coalition(coalition) -> Dict[str, Any]:
    """Accept a Coalition dataclass or a plain dict."""
    if isinstance(coalition, Coalition):
        return {
            'members': coalition.members,
            'shared_positions': coalition.shared_positions,
            'formation_round': coalition.formation_round,
            'strength': coalition.strength,
            'label': coalition.label,
        }
    return coalition


def _positions_text(positions: List[str]) -> str:
    return '; '.join(positions) if positions else 'no clear shared positions'


def _members_text(members: List[Dict[str, Any]]) -> str:
    names = [m.get('name', m.get('agent_name', 'Unknown')) for m in members]
    return ', '.join(names[:10])


def _stable_hash(text: str) -> int:
    """Deterministic hash for consistent fallback selection."""
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


class CoalitionLabeler:
    """Auto-generates descriptive labels for agent coalitions."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client

    @property
    def llm(self) -> Optional[LLMClient]:
        if self._llm_client is None:
            try:
                self._llm_client = LLMClient()
            except ValueError:
                logger.info("No LLM key configured — using template fallback labels")
                return None
        return self._llm_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def label_coalition(self, coalition) -> str:
        """Generate a short descriptive name for a coalition.

        Returns labels like 'Revenue Optimists', 'Product-First Advocates'.
        Uses LLM when available, otherwise deterministic template matching.
        """
        data = _normalize_coalition(coalition)
        positions = data.get('shared_positions', [])
        members = data.get('members', [])

        llm = self.llm
        if llm is not None:
            try:
                return self._llm_label(llm, positions, members)
            except Exception as e:
                logger.warning("LLM labeling failed, falling back to template: %s", e)

        return self._template_label(positions, members)

    def describe_coalition(self, coalition) -> str:
        """Generate a longer description of what the coalition stands for."""
        data = _normalize_coalition(coalition)
        positions = data.get('shared_positions', [])
        members = data.get('members', [])

        llm = self.llm
        if llm is not None:
            try:
                return self._llm_describe(llm, positions, members)
            except Exception as e:
                logger.warning("LLM describe failed, falling back to template: %s", e)

        return self._template_describe(positions, members)

    def explain_split(self, coalition_a, coalition_b) -> str:
        """Explain what divides two coalitions."""
        a = _normalize_coalition(coalition_a)
        b = _normalize_coalition(coalition_b)

        llm = self.llm
        if llm is not None:
            try:
                return self._llm_explain_split(llm, a, b)
            except Exception as e:
                logger.warning("LLM explain_split failed, falling back to template: %s", e)

        return self._template_explain_split(a, b)

    # ------------------------------------------------------------------
    # LLM-powered implementations
    # ------------------------------------------------------------------

    def _llm_label(self, llm: LLMClient, positions: List[str], members: List[Dict]) -> str:
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a GTM simulation analyst. Generate a short, catchy '
                    '2-3 word coalition label based on the shared positions of the '
                    'group members. Examples: "Revenue Optimists", "Conservative Growth", '
                    '"Product-First Advocates". Return ONLY the label, nothing else.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Coalition members: {_members_text(members)}\n'
                    f'Shared positions: {_positions_text(positions)}\n\n'
                    f'Generate a concise coalition label:'
                ),
            },
        ]
        label = llm.chat(messages=messages, temperature=0.7, max_tokens=30)
        return label.strip().strip('"\'')

    def _llm_describe(self, llm: LLMClient, positions: List[str], members: List[Dict]) -> str:
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a GTM simulation analyst. Write a 2-3 sentence '
                    'description of what a coalition of simulation agents stands for, '
                    'based on their shared positions. Be specific and analytical.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Coalition members ({len(members)}): {_members_text(members)}\n'
                    f'Shared positions: {_positions_text(positions)}\n\n'
                    f'Describe what this coalition stands for:'
                ),
            },
        ]
        return llm.chat(messages=messages, temperature=0.5, max_tokens=200).strip()

    def _llm_explain_split(self, llm: LLMClient, a: Dict, b: Dict) -> str:
        label_a = a.get('label') or 'Coalition A'
        label_b = b.get('label') or 'Coalition B'
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a GTM simulation analyst. Explain in 2-3 sentences '
                    'what fundamentally divides two coalitions of agents. Focus on '
                    'the key disagreement or strategic tension.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'{label_a} positions: {_positions_text(a.get("shared_positions", []))}\n'
                    f'{label_b} positions: {_positions_text(b.get("shared_positions", []))}\n\n'
                    f'Explain what divides these two groups:'
                ),
            },
        ]
        return llm.chat(messages=messages, temperature=0.5, max_tokens=250).strip()

    # ------------------------------------------------------------------
    # Template fallback implementations
    # ------------------------------------------------------------------

    def _template_label(self, positions: List[str], members: List[Dict]) -> str:
        """Deterministic label from keyword matching against positions."""
        combined = ' '.join(positions).lower()

        # Try department-based: '{Department} Block'
        for kw, dept in _DEPARTMENT_KEYWORDS.items():
            if kw in combined:
                return f'{dept} Block'

        # Try topic-based: 'Pro-{topic} Group'
        for kw, topic in _TOPIC_KEYWORDS.items():
            if kw in combined:
                return f'Pro-{topic} Group'

        # Try trait-based: '{Trait}-Leaning'
        for kw, trait in _TRAIT_KEYWORDS.items():
            if kw in combined:
                return f'{trait}-Leaning'

        # Deterministic fallback based on content hash
        idx = _stable_hash(combined) % len(_FALLBACK_LABELS)
        return _FALLBACK_LABELS[idx]

    def _template_describe(self, positions: List[str], members: List[Dict]) -> str:
        n = len(members)
        label = self._template_label(positions, members)
        if positions:
            top = positions[:3]
            pos_str = ', '.join(top)
            return (
                f'The "{label}" coalition ({n} members) shares alignment on: '
                f'{pos_str}. This group tends to advocate collectively for '
                f'these positions during the simulation.'
            )
        return (
            f'The "{label}" coalition ({n} members) formed around implicit '
            f'behavioral alignment rather than explicit shared positions.'
        )

    def _template_explain_split(self, a: Dict, b: Dict) -> str:
        label_a = a.get('label') or self._template_label(
            a.get('shared_positions', []), a.get('members', [])
        )
        label_b = b.get('label') or self._template_label(
            b.get('shared_positions', []), b.get('members', [])
        )
        pos_a = a.get('shared_positions', [])
        pos_b = b.get('shared_positions', [])

        # Find unique positions
        set_a = {p.lower() for p in pos_a}
        set_b = {p.lower() for p in pos_b}
        only_a = set_a - set_b
        only_b = set_b - set_a

        if only_a and only_b:
            diff_a = next(p for p in pos_a if p.lower() in only_a)
            diff_b = next(p for p in pos_b if p.lower() in only_b)
            return (
                f'"{label_a}" and "{label_b}" diverge on key issues. '
                f'The first group emphasizes "{diff_a}" while the second '
                f'prioritizes "{diff_b}", reflecting a fundamental strategic tension.'
            )

        return (
            f'"{label_a}" and "{label_b}" represent different strategic '
            f'orientations within the simulation, with differing emphasis '
            f'on priorities and approach.'
        )
