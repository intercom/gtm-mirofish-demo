"""
Personality-aware prompt modification service.

Modifies agent system prompts based on personality vectors and sentiment state,
producing rich, evolving agent characters during simulation.

Integrates with:
- PersonalityDynamics (personality_dynamics.py) for trait vectors
- SentimentDynamics (sentiment_dynamics.py) for mood state
- OasisProfileGenerator for base persona context
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import random

from ..utils.logger import get_logger

logger = get_logger('mirofish.agent_prompts')

# Personality trait names (5-dimensional vector, each 0-100)
PERSONALITY_TRAITS = [
    'analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant',
]

# Threshold for "high" trait expression (at or above)
HIGH_THRESHOLD = 65
# Threshold for "low" trait expression (at or below)
LOW_THRESHOLD = 35

# Trait behavior descriptions injected into prompts
TRAIT_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    'analytical': {
        'high': 'You prefer data-driven arguments and ask for evidence.',
        'low': 'You rely on intuition and gut feelings rather than detailed analysis.',
    },
    'creative': {
        'high': 'You often suggest unconventional approaches and think outside the box.',
        'low': 'You prefer proven methods and established best practices.',
    },
    'assertive': {
        'high': 'You speak confidently and advocate strongly for your positions.',
        'low': 'You tend to defer to others and seek group consensus before voicing opinions.',
    },
    'empathetic': {
        'high': "You consider others' feelings and seek win-win outcomes.",
        'low': 'You focus on objective outcomes rather than interpersonal dynamics.',
    },
    'risk_tolerant': {
        'high': 'You are comfortable with uncertainty and favor bold moves.',
        'low': 'You prefer cautious, well-tested approaches and avoid unnecessary risk.',
    },
}

# Sentiment ranges mapped to mood descriptions
SENTIMENT_MOODS: List[Dict[str, Any]] = [
    {'min': 1, 'max': 3, 'label': 'frustrated/pessimistic',
     'prompt': 'Your current mood is frustrated and pessimistic. You are skeptical of optimistic claims and focus on potential problems.'},
    {'min': 4, 'max': 5, 'label': 'neutral/cautious',
     'prompt': 'Your current mood is neutral and cautious. You weigh options carefully without strong emotional bias.'},
    {'min': 6, 'max': 7, 'label': 'engaged/optimistic',
     'prompt': 'Your current mood is engaged and optimistic. You are receptive to new ideas and see opportunities.'},
    {'min': 8, 'max': 10, 'label': 'enthusiastic/confident',
     'prompt': 'Your current mood is enthusiastic and confident. You champion ideas energetically and inspire momentum.'},
]


@dataclass
class PersonalityVector:
    """5-dimensional personality trait vector. Each trait is 0-100."""
    analytical: int = 50
    creative: int = 50
    assertive: int = 50
    empathetic: int = 50
    risk_tolerant: int = 50

    def to_dict(self) -> Dict[str, int]:
        return {t: getattr(self, t) for t in PERSONALITY_TRAITS}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'PersonalityVector':
        return cls(**{t: data.get(t, 50) for t in PERSONALITY_TRAITS})


@dataclass
class AgentPromptContext:
    """All context needed to build a personality-aware prompt."""
    agent_id: int
    agent_name: str
    base_persona: str
    personality: PersonalityVector = field(default_factory=PersonalityVector)
    sentiment: float = 5.0  # 1-10 scale
    memories: Optional[List[str]] = None


class AgentPromptModifier:
    """
    Builds personality-aware system prompts for simulation agents.

    Combines:
    - Base persona (role, background, priorities)
    - Personality vector (5 traits → behavioral instructions)
    - Sentiment (mood modifier → tone shift)
    - Recent memories (optional context)
    """

    @staticmethod
    def get_trait_modifiers(personality: PersonalityVector) -> List[str]:
        """Return behavioral instruction strings for traits that exceed thresholds."""
        modifiers = []
        for trait in PERSONALITY_TRAITS:
            value = getattr(personality, trait)
            if value >= HIGH_THRESHOLD:
                modifiers.append(TRAIT_DESCRIPTIONS[trait]['high'])
            elif value <= LOW_THRESHOLD:
                modifiers.append(TRAIT_DESCRIPTIONS[trait]['low'])
        return modifiers

    @staticmethod
    def get_mood_description(sentiment: float) -> str:
        """Map a sentiment score (1-10) to a mood prompt string."""
        clamped = max(1.0, min(10.0, sentiment))
        for mood in SENTIMENT_MOODS:
            if mood['min'] <= clamped <= mood['max']:
                return mood['prompt']
        return SENTIMENT_MOODS[1]['prompt']  # default neutral

    @staticmethod
    def build_system_prompt(ctx: AgentPromptContext) -> str:
        """
        Build a complete personality-aware system prompt.

        Layers:
        1. Base persona (who you are)
        2. Personality traits (how you think and act)
        3. Sentiment/mood (current emotional state)
        4. Memories (what you remember)
        """
        sections = []

        # 1. Base persona
        if ctx.base_persona:
            sections.append(ctx.base_persona)

        # 2. Personality traits
        trait_mods = AgentPromptModifier.get_trait_modifiers(ctx.personality)
        if trait_mods:
            sections.append(
                'Your behavioral tendencies:\n- ' + '\n- '.join(trait_mods)
            )

        # 3. Mood modifier
        mood = AgentPromptModifier.get_mood_description(ctx.sentiment)
        sections.append(mood)

        # 4. Memories
        if ctx.memories:
            recent = ctx.memories[:10]  # cap to avoid prompt bloat
            sections.append(
                'Your recent memories:\n- ' + '\n- '.join(recent)
            )

        return '\n\n'.join(sections)

    @staticmethod
    def modify_existing_prompt(
        original_prompt: str,
        personality: PersonalityVector,
        sentiment: float = 5.0,
        memories: Optional[List[str]] = None,
    ) -> str:
        """
        Append personality/sentiment modifiers to an existing system prompt.

        Use when you already have a base prompt and want to enrich it with
        personality dynamics without replacing it entirely.
        """
        additions = []

        trait_mods = AgentPromptModifier.get_trait_modifiers(personality)
        if trait_mods:
            additions.append(
                'Your behavioral tendencies:\n- ' + '\n- '.join(trait_mods)
            )

        mood = AgentPromptModifier.get_mood_description(sentiment)
        additions.append(mood)

        if memories:
            recent = memories[:10]
            additions.append(
                'Your recent memories:\n- ' + '\n- '.join(recent)
            )

        if not additions:
            return original_prompt

        return original_prompt.rstrip() + '\n\n' + '\n\n'.join(additions)

    @staticmethod
    def generate_default_personality(
        persona_template: Optional[Dict[str, Any]] = None,
    ) -> PersonalityVector:
        """
        Generate a plausible default personality vector.

        If a persona template (from persona_templates.json) is provided,
        bias traits to match the role archetype. Otherwise, use randomized
        mid-range values.
        """
        if persona_template:
            return _personality_from_template(persona_template)

        # Random mid-range values (30-70) for a balanced default
        return PersonalityVector(**{
            t: random.randint(30, 70) for t in PERSONALITY_TRAITS
        })

    @staticmethod
    def generate_default_sentiment() -> float:
        """Return a neutral-leaning default sentiment."""
        return round(random.uniform(4.5, 6.5), 1)


def _personality_from_template(template: Dict[str, Any]) -> PersonalityVector:
    """
    Derive personality traits from a GTM persona template.

    Maps role archetypes and communication styles to trait biases.
    """
    style = (template.get('communication_style') or '').lower()
    role = (template.get('role') or '').lower()
    authority = (template.get('decision_authority') or '').lower()

    analytical = 50
    creative = 50
    assertive = 50
    empathetic = 50
    risk_tolerant = 50

    # Communication style signals
    if 'data-driven' in style or 'technical' in style or 'metrics' in style:
        analytical += 15
    if 'collaborative' in style or 'quality' in style:
        empathetic += 10
        creative += 5
    if 'strategic' in style:
        analytical += 10
        risk_tolerant += 5
    if 'pragmatic' in style or 'efficiency' in style:
        analytical += 5
        risk_tolerant -= 5
    if 'risk-aware' in style or 'process-oriented' in style:
        risk_tolerant -= 10
        analytical += 5

    # Decision authority signals
    if authority == 'final_approver':
        assertive += 15
        risk_tolerant += 5
    elif authority == 'technical_veto':
        analytical += 10
        assertive += 10
        risk_tolerant -= 10
    elif authority == 'influencer':
        empathetic += 10
        creative += 5

    # Role-based bias
    if 'vp' in role or 'head' in role:
        assertive += 5
    if 'it' in role or 'technical' in role:
        analytical += 5
    if 'cx' in role or 'experience' in role:
        empathetic += 10

    # Clamp to valid range (20-80 per PRD spec)
    return PersonalityVector(
        analytical=max(20, min(80, analytical)),
        creative=max(20, min(80, creative)),
        assertive=max(20, min(80, assertive)),
        empathetic=max(20, min(80, empathetic)),
        risk_tolerant=max(20, min(80, risk_tolerant)),
    )
