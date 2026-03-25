"""
Dynamic sentiment engine for simulation agents.

Models mood/sentiment changes during simulation rounds. Each agent has a
floating sentiment value from 1 (very negative) to 10 (very positive).
Sentiment shifts are driven by round events — good news lifts mood,
conflict drags it down, and neutral interactions regress toward the mean.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..utils.logger import get_logger

logger = get_logger('mirofish.sentiment_dynamics')

# Sentiment value boundaries
SENTIMENT_MIN = 1.0
SENTIMENT_MAX = 10.0
SENTIMENT_MEAN = 5.0

# Shift magnitudes
POSITIVE_SHIFT_MIN = 0.5
POSITIVE_SHIFT_MAX = 1.0
NEGATIVE_SHIFT_MIN = -1.0
NEGATIVE_SHIFT_MAX = -0.5
NEUTRAL_REGRESSION_RATE = 0.1  # fraction of distance to mean

# Mood swing detection threshold (absolute change between consecutive rounds)
MOOD_SWING_THRESHOLD = 2.0

# Lexicons for classifying event content
POSITIVE_WORDS = frozenset([
    'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
    'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
    'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
    'exciting', 'confident', 'strong', 'pleased', 'significant', 'positive',
    'agree', 'resolved', 'improved', 'saved', 'success', 'brilliant',
    'outstanding', 'perfect', 'fantastic', 'thrilled', 'optimistic',
])

NEGATIVE_WORDS = frozenset([
    'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
    'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
    'problem', 'unclear', 'confusing', 'frustrated', 'poor', 'slow',
    'lacks', 'overpriced', 'clunky', 'limited', 'negative', 'afraid',
    'failed', 'struggled', 'conflict', 'angry', 'disappointed', 'terrible',
    'broken', 'impossible', 'hostile', 'rejected', 'worst',
])

# Action-type sentiment bias: some actions are inherently positive/negative
ACTION_TYPE_BIAS: Dict[str, float] = {
    'LIKE_POST': 0.3,
    'UPVOTE': 0.3,
    'REPOST': 0.2,
    'RETWEET': 0.2,
    'SHARE': 0.2,
    'FOLLOW': 0.2,
    'DOWNVOTE': -0.3,
    'REPORT': -0.5,
    'BLOCK': -0.4,
}

# Sentiment-to-description mapping (inclusive ranges)
MOOD_DESCRIPTIONS = [
    (1.0, 3.0, 'frustrated and pessimistic'),
    (3.0, 5.0, 'neutral and cautious'),
    (5.0, 7.0, 'engaged and optimistic'),
    (7.0, 10.0, 'enthusiastic and confident'),
]


@dataclass
class AgentSentimentRecord:
    """Per-round sentiment snapshot for one agent."""
    round_num: int
    sentiment: float
    delta: float = 0.0  # change from previous round


@dataclass
class AgentSentimentState:
    """Tracks an individual agent's sentiment over time."""
    agent_id: str
    agent_name: str = ''
    sentiment: float = SENTIMENT_MEAN
    history: List[AgentSentimentRecord] = field(default_factory=list)


def _clamp(value: float) -> float:
    return max(SENTIMENT_MIN, min(SENTIMENT_MAX, value))


def _classify_content(content: str) -> str:
    """Classify text as 'positive', 'negative', or 'neutral'."""
    if not content:
        return 'neutral'
    lower = content.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    if pos > neg:
        return 'positive'
    if neg > pos:
        return 'negative'
    return 'neutral'


def _event_sentiment_delta(event: Dict[str, Any]) -> float:
    """Compute the sentiment shift for a single event.

    Returns a float:
      positive events  → +0.5 to +1.0
      negative events  → -1.0 to -0.5
      neutral events   → 0.0 (handled via mean regression in update_sentiment)
    """
    action_type = (event.get('action_type') or '').upper()
    content = event.get('action_args', {}).get('content', '') if isinstance(event.get('action_args'), dict) else ''

    # Start with action-type bias
    bias = ACTION_TYPE_BIAS.get(action_type, 0.0)

    # Classify content
    classification = _classify_content(content)

    if classification == 'positive':
        # Scale within [POSITIVE_SHIFT_MIN, POSITIVE_SHIFT_MAX]
        return POSITIVE_SHIFT_MIN + abs(bias) * (POSITIVE_SHIFT_MAX - POSITIVE_SHIFT_MIN)
    elif classification == 'negative':
        return NEGATIVE_SHIFT_MAX - abs(bias) * (NEGATIVE_SHIFT_MAX - NEGATIVE_SHIFT_MIN)
    else:
        # Neutral — no direct shift; bias-only actions still nudge slightly
        return bias * 0.5


class SentimentDynamics:
    """Models mood/sentiment changes during simulation.

    Usage::

        engine = SentimentDynamics()
        engine.register_agent('agent_1', 'Alice Chen')

        # After each round, feed the agent's events:
        engine.update_sentiment('agent_1', round_events)

        # Query mood for prompt injection:
        prompt_line = engine.get_prompt_injection('agent_1')

        # Group-level analytics:
        group_mood = engine.get_group_mood()
        swings = engine.detect_mood_swings('agent_1')
    """

    def __init__(self) -> None:
        self._agents: Dict[str, AgentSentimentState] = {}

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str, agent_name: str = '', initial_sentiment: float = SENTIMENT_MEAN) -> None:
        """Register an agent with an optional starting sentiment."""
        if agent_id in self._agents:
            return
        self._agents[agent_id] = AgentSentimentState(
            agent_id=agent_id,
            agent_name=agent_name,
            sentiment=_clamp(initial_sentiment),
        )

    # ------------------------------------------------------------------
    # Core sentiment update
    # ------------------------------------------------------------------

    def update_sentiment(self, agent_id: str, events: List[Dict[str, Any]], round_num: int = 0) -> float:
        """Shift an agent's sentiment based on round events.

        Rules:
          - Positive events (agreement / good news): +0.5 to +1.0
          - Negative events (conflict / bad news): -0.5 to -1.0
          - Neutral interactions: slight regression toward mean (5.0)

        Returns the agent's new sentiment value.
        """
        if agent_id not in self._agents:
            self.register_agent(agent_id)

        state = self._agents[agent_id]
        prev = state.sentiment

        if not events:
            # No events — regress toward mean
            state.sentiment = _clamp(
                prev + (SENTIMENT_MEAN - prev) * NEUTRAL_REGRESSION_RATE
            )
        else:
            total_delta = 0.0
            for event in events:
                total_delta += _event_sentiment_delta(event)

            if total_delta == 0.0:
                # All events were truly neutral → regress
                state.sentiment = _clamp(
                    prev + (SENTIMENT_MEAN - prev) * NEUTRAL_REGRESSION_RATE
                )
            else:
                # Average the delta across events to prevent wild swings from many events
                avg_delta = total_delta / len(events)
                state.sentiment = _clamp(prev + avg_delta)

        delta = state.sentiment - prev
        state.history.append(AgentSentimentRecord(
            round_num=round_num,
            sentiment=state.sentiment,
            delta=delta,
        ))

        return state.sentiment

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_sentiment(self, agent_id: str) -> float:
        """Return an agent's current sentiment (1-10)."""
        state = self._agents.get(agent_id)
        return state.sentiment if state else SENTIMENT_MEAN

    def get_group_mood(self) -> Dict[str, Any]:
        """Average sentiment across all registered agents.

        Returns a dict with ``average``, ``min``, ``max``, ``count``,
        and a human-readable ``description``.
        """
        if not self._agents:
            return {
                'average': SENTIMENT_MEAN,
                'min': SENTIMENT_MEAN,
                'max': SENTIMENT_MEAN,
                'count': 0,
                'description': _describe_mood(SENTIMENT_MEAN),
            }

        values = [s.sentiment for s in self._agents.values()]
        avg = sum(values) / len(values)
        return {
            'average': round(avg, 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'count': len(values),
            'description': _describe_mood(avg),
        }

    def detect_mood_swings(self, agent_id: str, threshold: float = MOOD_SWING_THRESHOLD) -> List[Dict[str, Any]]:
        """Identify rounds where the agent's sentiment changed abruptly.

        A mood swing is any consecutive-round delta whose absolute value
        exceeds *threshold* (default 2.0 on the 1-10 scale).

        Returns a list of dicts with ``round_num``, ``delta``,
        ``from_sentiment``, and ``to_sentiment``.
        """
        state = self._agents.get(agent_id)
        if not state or len(state.history) < 2:
            return []

        swings: List[Dict[str, Any]] = []
        for i in range(1, len(state.history)):
            prev_rec = state.history[i - 1]
            curr_rec = state.history[i]
            delta = curr_rec.sentiment - prev_rec.sentiment
            if abs(delta) >= threshold:
                swings.append({
                    'round_num': curr_rec.round_num,
                    'delta': round(delta, 2),
                    'from_sentiment': round(prev_rec.sentiment, 2),
                    'to_sentiment': round(curr_rec.sentiment, 2),
                })
        return swings

    # ------------------------------------------------------------------
    # Prompt injection
    # ------------------------------------------------------------------

    def get_prompt_injection(self, agent_id: str) -> str:
        """Generate a mood line suitable for injecting into an agent's system prompt.

        Example output:
          "Your current mood is engaged and optimistic. This affects your tone."
        """
        sentiment = self.get_sentiment(agent_id)
        description = _describe_mood(sentiment)
        return f'Your current mood is {description}. This affects your tone.'

    # ------------------------------------------------------------------
    # Serialisation helpers (for API responses)
    # ------------------------------------------------------------------

    def get_agent_sentiment_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Return the full round-by-round sentiment history for one agent."""
        state = self._agents.get(agent_id)
        if not state:
            return []
        return [
            {
                'round_num': r.round_num,
                'sentiment': round(r.sentiment, 2),
                'delta': round(r.delta, 2),
            }
            for r in state.history
        ]

    def get_all_agents_snapshot(self) -> List[Dict[str, Any]]:
        """Current sentiment for every registered agent."""
        return [
            {
                'agent_id': s.agent_id,
                'agent_name': s.agent_name,
                'sentiment': round(s.sentiment, 2),
                'description': _describe_mood(s.sentiment),
                'rounds_tracked': len(s.history),
            }
            for s in self._agents.values()
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Full serialisation of the engine state."""
        return {
            'agents': self.get_all_agents_snapshot(),
            'group_mood': self.get_group_mood(),
        }


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _describe_mood(sentiment: float) -> str:
    """Map a 1-10 sentiment value to a human-readable description."""
    for low, high, desc in MOOD_DESCRIPTIONS:
        if sentiment <= high:
            return desc
    return MOOD_DESCRIPTIONS[-1][2]
