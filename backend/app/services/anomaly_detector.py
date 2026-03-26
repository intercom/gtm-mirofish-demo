"""
Behavior anomaly detector for agent simulations.
Identifies unexpected agent behaviors using Z-score analysis of behavioral metrics.
"""

import math
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.anomaly_detector')

# Sentiment scoring (mirrors frontend SentimentTimeline logic)
POSITIVE_WORDS = [
    'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
    'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
    'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
    'exciting', 'confident', 'strong', 'pleased', 'significant', 'positive',
]

NEGATIVE_WORDS = [
    'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
    'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
    'problem', 'unclear', 'confusing', 'frustrated', 'poor', 'slow',
    'lacks', 'overpriced', 'clunky', 'limited', 'negative', 'afraid',
]


@dataclass
class Anomaly:
    """A detected behavioral anomaly."""
    anomaly_id: str
    agent_id: int
    agent_name: str
    anomaly_type: str  # sentiment_reversal | unexpected_agreement | leadership_emergence | topic_hijacking
    round_num: int
    surprise_score: float  # 0-1
    description: str
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "anomaly_type": self.anomaly_type,
            "round_num": self.round_num,
            "surprise_score": self.surprise_score,
            "description": self.description,
            "explanation": self.explanation,
        }


def _score_content(content: str) -> float:
    """Score text sentiment from -1 to 1."""
    if not content:
        return 0.0
    lower = content.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def _z_score(value: float, mean: float, std: float) -> float:
    """Calculate Z-score. Returns 0 if std is too small."""
    if std < 0.01:
        return 0.0
    return (value - mean) / std


def _normalize_surprise(z: float, threshold: float = 2.0, max_z: float = 5.0) -> float:
    """Convert absolute Z-score to 0-1 surprise score."""
    abs_z = abs(z)
    if abs_z < threshold:
        return 0.0
    return min(1.0, (abs_z - threshold) / (max_z - threshold))


class AnomalyDetector:
    """
    Detects unexpected agent behaviors in simulation data.

    Uses Z-score analysis on per-agent behavioral metrics to identify outliers.
    Supports four anomaly types:
    - sentiment_reversal: agent sentiment changes drastically between rounds
    - unexpected_agreement: hostile agent suddenly agrees
    - leadership_emergence: quiet agent suddenly becomes influential
    - topic_hijacking: agent dramatically changes the subject
    """

    Z_THRESHOLD = 2.0

    def detect_anomalies(
        self,
        actions: List[Dict[str, Any]],
        round_num: Optional[int] = None,
    ) -> List[Anomaly]:
        """
        Detect anomalies from a list of action dicts.

        Args:
            actions: List of action dicts (from SimulationRunner.get_actions().to_dict())
            round_num: If provided, only return anomalies for this round.

        Returns:
            List of Anomaly objects sorted by surprise_score descending.
        """
        if not actions:
            return []

        # Build per-agent, per-round metrics
        agent_rounds = self._build_agent_round_metrics(actions)

        anomalies: List[Anomaly] = []
        anomalies.extend(self._detect_sentiment_reversals(agent_rounds))
        anomalies.extend(self._detect_unexpected_agreements(agent_rounds))
        anomalies.extend(self._detect_leadership_emergence(agent_rounds))
        anomalies.extend(self._detect_topic_hijacking(agent_rounds))

        if round_num is not None:
            anomalies = [a for a in anomalies if a.round_num == round_num]

        anomalies.sort(key=lambda a: a.surprise_score, reverse=True)
        return anomalies

    def score_surprise(self, anomaly: Anomaly) -> float:
        """Return the surprise score for an anomaly (already computed)."""
        return anomaly.surprise_score

    def explain_anomaly(self, anomaly: Anomaly) -> str:
        """
        Generate a human-readable explanation using LLM.
        Falls back to the description if LLM is unavailable.
        """
        try:
            from ..utils.llm_client import LLMClient
            llm = LLMClient()
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert analyst of agent-based social simulations. "
                        "Provide a brief (2-3 sentence) explanation of why this behavioral "
                        "anomaly is significant and what it might indicate."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Anomaly type: {anomaly.anomaly_type}\n"
                        f"Agent: {anomaly.agent_name}\n"
                        f"Round: {anomaly.round_num}\n"
                        f"Surprise score: {anomaly.surprise_score:.2f}\n"
                        f"Description: {anomaly.description}\n\n"
                        "Explain why this is unusual and what it might mean."
                    ),
                },
            ]
            return llm.chat(messages, temperature=0.5, max_tokens=200)
        except Exception as e:
            logger.debug(f"LLM explanation unavailable: {e}")
            return anomaly.description

    # -- Internal methods --

    def _build_agent_round_metrics(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[int, Dict[int, Dict[str, Any]]]:
        """
        Build per-agent, per-round metrics.

        Returns:
            {agent_id: {round_num: {sentiment, action_count, content_words, agent_name, contents}}}
        """
        metrics: Dict[int, Dict[int, Dict[str, Any]]] = {}

        for action in actions:
            agent_id = action.get("agent_id")
            rnd = action.get("round_num")
            if agent_id is None or rnd is None:
                continue

            if agent_id not in metrics:
                metrics[agent_id] = {}
            if rnd not in metrics[agent_id]:
                metrics[agent_id][rnd] = {
                    "agent_name": action.get("agent_name", f"Agent_{agent_id}"),
                    "sentiment_sum": 0.0,
                    "action_count": 0,
                    "content_words": set(),
                    "contents": [],
                    "action_types": {},
                    "interactions": set(),
                }

            m = metrics[agent_id][rnd]
            content = action.get("action_args", {}).get("content", "")
            m["sentiment_sum"] += _score_content(content)
            m["action_count"] += 1

            if content:
                m["contents"].append(content)
                words = set(content.lower().split())
                m["content_words"].update(words)

            action_type = action.get("action_type", "")
            m["action_types"][action_type] = m["action_types"].get(action_type, 0) + 1

            # Track who the agent interacts with (replies/comments)
            parent_id = action.get("action_args", {}).get("parent_agent_id")
            if parent_id is not None:
                m["interactions"].add(parent_id)

        # Compute averages
        for agent_id in metrics:
            for rnd in metrics[agent_id]:
                m = metrics[agent_id][rnd]
                count = m["action_count"]
                m["avg_sentiment"] = m["sentiment_sum"] / count if count > 0 else 0.0

        return metrics

    def _detect_sentiment_reversals(
        self, agent_rounds: Dict[int, Dict[int, Dict[str, Any]]]
    ) -> List[Anomaly]:
        """Detect sudden sentiment reversals (>3 points swing on -1..1 scale mapped to -5..5)."""
        anomalies = []

        for agent_id, rounds in agent_rounds.items():
            sorted_rounds = sorted(rounds.keys())
            if len(sorted_rounds) < 2:
                continue

            # Compute sentiment deltas between consecutive rounds
            deltas = []
            for i in range(1, len(sorted_rounds)):
                prev_rnd = sorted_rounds[i - 1]
                curr_rnd = sorted_rounds[i]
                prev_sent = rounds[prev_rnd]["avg_sentiment"]
                curr_sent = rounds[curr_rnd]["avg_sentiment"]
                # Map -1..1 to -5..5 scale for "3 point" threshold
                delta = (curr_sent - prev_sent) * 5
                deltas.append((curr_rnd, delta, prev_sent, curr_sent))

            if not deltas:
                continue

            mean_delta = sum(d[1] for d in deltas) / len(deltas)
            std_delta = math.sqrt(sum((d[1] - mean_delta) ** 2 for d in deltas) / len(deltas)) if len(deltas) > 1 else 0

            for rnd, delta, prev_sent, curr_sent in deltas:
                z = _z_score(abs(delta), abs(mean_delta), std_delta)
                surprise = _normalize_surprise(z)

                if surprise > 0 or abs(delta) >= 3.0:
                    actual_surprise = max(surprise, min(1.0, abs(delta) / 5.0))
                    agent_name = rounds[rnd]["agent_name"]
                    direction = "positive" if delta > 0 else "negative"
                    anomalies.append(Anomaly(
                        anomaly_id=f"sr_{uuid.uuid4().hex[:8]}",
                        agent_id=agent_id,
                        agent_name=agent_name,
                        anomaly_type="sentiment_reversal",
                        round_num=rnd,
                        surprise_score=round(actual_surprise, 3),
                        description=(
                            f"{agent_name} had a sharp sentiment shift to {direction} "
                            f"in round {rnd} (from {prev_sent:.2f} to {curr_sent:.2f})"
                        ),
                    ))

        return anomalies

    def _detect_unexpected_agreements(
        self, agent_rounds: Dict[int, Dict[int, Dict[str, Any]]]
    ) -> List[Anomaly]:
        """Detect when agents with historically negative sentiment suddenly become positive."""
        anomalies = []

        for agent_id, rounds in agent_rounds.items():
            sorted_rounds = sorted(rounds.keys())
            if len(sorted_rounds) < 3:
                continue

            sentiments = [rounds[r]["avg_sentiment"] for r in sorted_rounds]
            mean_sent = sum(sentiments) / len(sentiments)

            # Only consider agents that are generally negative (hostile)
            if mean_sent >= -0.1:
                continue

            for i, rnd in enumerate(sorted_rounds):
                curr_sent = rounds[rnd]["avg_sentiment"]
                if curr_sent > 0.2:
                    # Hostile agent is suddenly positive
                    std_sent = math.sqrt(sum((s - mean_sent) ** 2 for s in sentiments) / len(sentiments))
                    z = _z_score(curr_sent, mean_sent, std_sent)
                    surprise = _normalize_surprise(z)

                    if surprise > 0:
                        agent_name = rounds[rnd]["agent_name"]
                        anomalies.append(Anomaly(
                            anomaly_id=f"ua_{uuid.uuid4().hex[:8]}",
                            agent_id=agent_id,
                            agent_name=agent_name,
                            anomaly_type="unexpected_agreement",
                            round_num=rnd,
                            surprise_score=round(surprise, 3),
                            description=(
                                f"{agent_name} (usually negative, avg {mean_sent:.2f}) "
                                f"unexpectedly turned positive ({curr_sent:.2f}) in round {rnd}"
                            ),
                        ))

        return anomalies

    def _detect_leadership_emergence(
        self, agent_rounds: Dict[int, Dict[int, Dict[str, Any]]]
    ) -> List[Anomaly]:
        """Detect when a quiet agent suddenly becomes very active."""
        anomalies = []

        for agent_id, rounds in agent_rounds.items():
            sorted_rounds = sorted(rounds.keys())
            if len(sorted_rounds) < 3:
                continue

            counts = [rounds[r]["action_count"] for r in sorted_rounds]
            mean_count = sum(counts) / len(counts)
            std_count = math.sqrt(sum((c - mean_count) ** 2 for c in counts) / len(counts)) if len(counts) > 1 else 0

            # Only consider agents that are generally quiet
            if mean_count >= 3:
                continue

            for i, rnd in enumerate(sorted_rounds):
                count = rounds[rnd]["action_count"]
                z = _z_score(count, mean_count, std_count)
                surprise = _normalize_surprise(z)

                if surprise > 0 and count > mean_count * 2:
                    agent_name = rounds[rnd]["agent_name"]
                    anomalies.append(Anomaly(
                        anomaly_id=f"le_{uuid.uuid4().hex[:8]}",
                        agent_id=agent_id,
                        agent_name=agent_name,
                        anomaly_type="leadership_emergence",
                        round_num=rnd,
                        surprise_score=round(surprise, 3),
                        description=(
                            f"{agent_name} (usually ~{mean_count:.0f} actions/round) "
                            f"surged to {count} actions in round {rnd}"
                        ),
                    ))

        return anomalies

    def _detect_topic_hijacking(
        self, agent_rounds: Dict[int, Dict[int, Dict[str, Any]]]
    ) -> List[Anomaly]:
        """Detect when an agent's vocabulary changes dramatically between rounds."""
        anomalies = []

        for agent_id, rounds in agent_rounds.items():
            sorted_rounds = sorted(rounds.keys())
            if len(sorted_rounds) < 2:
                continue

            # Compute word overlap (Jaccard similarity) between consecutive rounds
            overlaps = []
            for i in range(1, len(sorted_rounds)):
                prev_words = rounds[sorted_rounds[i - 1]]["content_words"]
                curr_words = rounds[sorted_rounds[i]]["content_words"]
                if not prev_words or not curr_words:
                    continue
                intersection = prev_words & curr_words
                union = prev_words | curr_words
                jaccard = len(intersection) / len(union) if union else 1.0
                overlaps.append((sorted_rounds[i], jaccard))

            if len(overlaps) < 2:
                continue

            similarities = [o[1] for o in overlaps]
            mean_sim = sum(similarities) / len(similarities)
            std_sim = math.sqrt(sum((s - mean_sim) ** 2 for s in similarities) / len(similarities))

            for rnd, jaccard in overlaps:
                # Low jaccard = vocabulary changed a lot (potential hijacking)
                z = _z_score(jaccard, mean_sim, std_sim)
                # We want negative Z-scores (similarity dropped)
                if z < -self.Z_THRESHOLD:
                    surprise = _normalize_surprise(z)
                    agent_name = rounds[rnd]["agent_name"]
                    anomalies.append(Anomaly(
                        anomaly_id=f"th_{uuid.uuid4().hex[:8]}",
                        agent_id=agent_id,
                        agent_name=agent_name,
                        anomaly_type="topic_hijacking",
                        round_num=rnd,
                        surprise_score=round(surprise, 3),
                        description=(
                            f"{agent_name} dramatically changed topics in round {rnd} "
                            f"(vocabulary overlap dropped to {jaccard:.0%})"
                        ),
                    ))

        return anomalies


def generate_demo_anomalies() -> List[Dict[str, Any]]:
    """Generate synthetic anomalies for demo mode when no simulation data exists."""
    demo = [
        Anomaly(
            anomaly_id="demo_sr_1",
            agent_id=1,
            agent_name="Sarah Chen (VP Sales)",
            anomaly_type="sentiment_reversal",
            round_num=5,
            surprise_score=0.92,
            description="Sarah Chen had a sharp sentiment shift to negative in round 5 (from 0.45 to -0.38)",
            explanation="Sarah's abrupt shift from positive to negative sentiment suggests she encountered a deal-breaker objection. This reversal often signals a critical pain point being surfaced.",
        ),
        Anomaly(
            anomaly_id="demo_ua_1",
            agent_id=3,
            agent_name="Marcus Rodriguez (CTO)",
            anomaly_type="unexpected_agreement",
            round_num=7,
            surprise_score=0.78,
            description="Marcus Rodriguez (usually negative, avg -0.32) unexpectedly turned positive (0.41) in round 7",
            explanation="The CTO's sudden agreement after sustained skepticism often indicates a compelling technical demonstration or proof point was presented that addressed core concerns.",
        ),
        Anomaly(
            anomaly_id="demo_le_1",
            agent_id=5,
            agent_name="Priya Patel (End User)",
            anomaly_type="leadership_emergence",
            round_num=4,
            surprise_score=0.65,
            description="Priya Patel (usually ~1 actions/round) surged to 6 actions in round 4",
            explanation="This quiet end-user suddenly becoming vocal suggests the discussion touched on a topic directly relevant to their daily workflow, making them a potential internal champion.",
        ),
        Anomaly(
            anomaly_id="demo_th_1",
            agent_id=2,
            agent_name="James Liu (CFO)",
            anomaly_type="topic_hijacking",
            round_num=6,
            surprise_score=0.55,
            description="James Liu dramatically changed topics in round 6 (vocabulary overlap dropped to 15%)",
            explanation="The CFO shifting the conversation away from features to a new topic typically indicates budget or ROI concerns being raised, which may need to be addressed before the deal can progress.",
        ),
    ]
    return [a.to_dict() for a in demo]
