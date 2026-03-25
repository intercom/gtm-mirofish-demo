"""
Debate scoring service.
Scores debate participants and arguments using LLM assessment
with keyword-based heuristic fallback for demo/mock mode.
"""

import hashlib
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.debate_scorer')


class DebateFormat(str, Enum):
    OXFORD = "oxford"
    PANEL = "panel"
    ROUNDTABLE = "roundtable"


SCORING_DIMENSIONS = ["evidence", "logic", "relevance", "persuasion"]

# Keyword lists for heuristic scoring fallback
EVIDENCE_KEYWORDS = [
    "data", "study", "research", "report", "survey", "statistics",
    "according to", "evidence", "analysis", "findings", "metric",
    "measured", "benchmark", "case study", "example", "demonstrated",
    "percent", "%", "growth", "revenue", "pipeline", "quota",
]
LOGIC_KEYWORDS = [
    "therefore", "because", "consequently", "thus", "hence",
    "implies", "follows", "reason", "given that", "if then",
    "leads to", "results in", "causes", "since", "due to",
    "correlation", "causation", "assumption", "conclusion",
]
RELEVANCE_KEYWORDS = [
    "specifically", "directly", "regarding", "on topic", "as stated",
    "the question", "the proposition", "our motion", "this debate",
    "to address", "in response", "the point", "at hand",
]
PERSUASION_KEYWORDS = [
    "clearly", "undeniably", "compelling", "critical", "essential",
    "must", "cannot ignore", "fundamental", "imperative", "urgent",
    "consider", "imagine", "ask yourself", "we all know", "obviously",
    "the real question", "what matters", "bottom line",
]

KEYWORD_SETS = {
    "evidence": EVIDENCE_KEYWORDS,
    "logic": LOGIC_KEYWORDS,
    "relevance": RELEVANCE_KEYWORDS,
    "persuasion": PERSUASION_KEYWORDS,
}

# Rebuttal quality indicators
REBUTTAL_KEYWORDS = [
    "however", "but", "on the contrary", "disagree", "flawed",
    "overlooks", "ignores", "fails to", "misses", "incorrect",
    "actually", "in fact", "counterpoint", "rebuttal", "challenge",
]

# Question quality indicators
QUESTION_KEYWORDS = [
    "how do you", "can you explain", "what about", "why would",
    "have you considered", "isn't it true", "do you agree",
    "what evidence", "how does that", "where is the",
]


@dataclass
class ArgumentScore:
    """Score for a single argument across 4 dimensions."""
    evidence: float = 0.0
    logic: float = 0.0
    relevance: float = 0.0
    persuasion: float = 0.0

    @property
    def overall(self) -> float:
        return round(
            (self.evidence + self.logic + self.relevance + self.persuasion) / 4, 2
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence": round(self.evidence, 2),
            "logic": round(self.logic, 2),
            "relevance": round(self.relevance, 2),
            "persuasion": round(self.persuasion, 2),
            "overall": self.overall,
        }


@dataclass
class AgentPerformance:
    """Aggregated debate performance for one agent."""
    agent_id: str
    agent_name: str
    side: Optional[str] = None
    argument_scores: List[ArgumentScore] = field(default_factory=list)
    rebuttal_effectiveness: float = 0.0
    question_quality: float = 0.0
    audience_impact: float = 0.0

    @property
    def argument_quality_avg(self) -> float:
        if not self.argument_scores:
            return 0.0
        return round(
            sum(s.overall for s in self.argument_scores) / len(self.argument_scores), 2
        )

    @property
    def total_score(self) -> float:
        weights = {
            "argument": 0.40,
            "rebuttal": 0.25,
            "question": 0.15,
            "audience": 0.20,
        }
        return round(
            self.argument_quality_avg * weights["argument"]
            + self.rebuttal_effectiveness * weights["rebuttal"]
            + self.question_quality * weights["question"]
            + self.audience_impact * weights["audience"],
            2,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "side": self.side,
            "argument_quality_avg": self.argument_quality_avg,
            "rebuttal_effectiveness": round(self.rebuttal_effectiveness, 2),
            "question_quality": round(self.question_quality, 2),
            "audience_impact": round(self.audience_impact, 2),
            "total_score": self.total_score,
            "argument_scores": [s.to_dict() for s in self.argument_scores],
        }


@dataclass
class DebateScorecard:
    """Full scorecard for a completed debate."""
    topic: str
    debate_format: str
    winner: Optional[Dict[str, Any]] = None
    performances: List[AgentPerformance] = field(default_factory=list)
    overall_quality: float = 0.0
    best_moment: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        ranked = sorted(self.performances, key=lambda p: p.total_score, reverse=True)
        return {
            "topic": self.topic,
            "format": self.debate_format,
            "winner": self.winner,
            "overall_quality": round(self.overall_quality, 2),
            "best_moment": self.best_moment,
            "rankings": [p.to_dict() for p in ranked],
        }


class DebateScorer:
    """
    Scores debate participants and arguments.

    Uses LLM for nuanced argument quality assessment when an API key
    is configured, otherwise falls back to keyword-based heuristics.
    """

    def __init__(self):
        self._llm = None
        if Config.LLM_API_KEY:
            try:
                from ..utils.llm_client import LLMClient
                self._llm = LLMClient()
                logger.info("DebateScorer initialized with LLM scoring")
            except Exception as e:
                logger.warning(f"LLM unavailable, using heuristic scoring: {e}")
        else:
            logger.info("DebateScorer initialized with heuristic scoring (no LLM key)")

    def score_argument(self, argument: Dict[str, Any]) -> ArgumentScore:
        """
        Score a single argument on 4 dimensions (0-10 each).

        Args:
            argument: Dict with keys: content (str), agent_id (str),
                      topic (str), phase (str, e.g. 'opening'/'rebuttal').

        Returns:
            ArgumentScore with evidence, logic, relevance, persuasion.
        """
        content = argument.get("content", "")
        topic = argument.get("topic", "")

        if self._llm:
            return self._score_argument_llm(content, topic)
        return self._score_argument_heuristic(content, topic)

    def score_agent_performance(
        self, agent_id: str, debate: Dict[str, Any]
    ) -> AgentPerformance:
        """
        Compute full debate performance for one agent.

        Args:
            agent_id: The agent to score.
            debate: Full debate data with 'topic', 'format', 'agents',
                    'phases' (list of phase dicts each with 'arguments').

        Returns:
            AgentPerformance with all metrics filled in.
        """
        topic = debate.get("topic", "")
        agents_map = {a["id"]: a for a in debate.get("agents", [])}
        agent_info = agents_map.get(agent_id, {})

        perf = AgentPerformance(
            agent_id=agent_id,
            agent_name=agent_info.get("name", agent_id),
            side=agent_info.get("side"),
        )

        all_arguments = []
        rebuttals = []
        questions = []

        for phase in debate.get("phases", []):
            phase_type = phase.get("type", "")
            for arg in phase.get("arguments", []):
                if arg.get("agent_id") != agent_id:
                    continue
                all_arguments.append(arg)
                if phase_type == "rebuttal":
                    rebuttals.append(arg)
                elif phase_type == "cross_examination":
                    questions.append(arg)

        # Score each argument
        for arg in all_arguments:
            arg["topic"] = topic
            score = self.score_argument(arg)
            perf.argument_scores.append(score)

        # Rebuttal effectiveness
        perf.rebuttal_effectiveness = self._score_rebuttals(rebuttals)

        # Question quality
        perf.question_quality = self._score_questions(questions)

        # Audience impact: how much opposing agents shifted position
        perf.audience_impact = self._compute_audience_impact(
            agent_id, debate
        )

        return perf

    def determine_winner(self, debate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the winning side/agent based on aggregate scoring.

        Args:
            debate: Full debate data.

        Returns:
            Dict with 'winner_type' ('side' or 'agent'), 'winner',
            'score', and 'margin'.
        """
        debate_format = debate.get("format", DebateFormat.OXFORD.value)
        agents = debate.get("agents", [])

        performances = []
        for agent in agents:
            perf = self.score_agent_performance(agent["id"], debate)
            performances.append(perf)

        if debate_format == DebateFormat.OXFORD.value:
            return self._determine_winner_oxford(performances)
        else:
            return self._determine_winner_individual(performances)

    def generate_scorecard(self, debate: Dict[str, Any]) -> DebateScorecard:
        """
        Generate a complete scorecard with per-agent breakdown.

        Args:
            debate: Full debate data.

        Returns:
            DebateScorecard with all scores, rankings, winner, and best moment.
        """
        topic = debate.get("topic", "")
        debate_format = debate.get("format", DebateFormat.OXFORD.value)
        agents = debate.get("agents", [])

        performances = []
        for agent in agents:
            perf = self.score_agent_performance(agent["id"], debate)
            performances.append(perf)

        winner = self._determine_winner_from_performances(
            performances, debate_format
        )

        best_moment = self._find_best_moment(performances, debate)

        all_scores = [p.total_score for p in performances]
        overall_quality = (
            round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
        )

        return DebateScorecard(
            topic=topic,
            debate_format=debate_format,
            winner=winner,
            performances=performances,
            overall_quality=overall_quality,
            best_moment=best_moment,
        )

    # ---- LLM-based scoring ----

    def _score_argument_llm(self, content: str, topic: str) -> ArgumentScore:
        """Use the LLM to evaluate argument quality on 4 dimensions."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a debate judge. Score the following argument on "
                    "4 dimensions, each 0-10. Return ONLY valid JSON:\n"
                    '{"evidence": N, "logic": N, "relevance": N, "persuasion": N}\n'
                    "evidence = factual support / data cited\n"
                    "logic = coherence and reasoning quality\n"
                    "relevance = on-topic and addresses the proposition\n"
                    "persuasion = rhetorical effectiveness and impact"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Debate topic: {topic}\n\nArgument:\n{content}"
                ),
            },
        ]
        try:
            result = self._llm.chat_json(
                messages=messages, temperature=0.2, max_tokens=256
            )
            return ArgumentScore(
                evidence=self._clamp(result.get("evidence", 5)),
                logic=self._clamp(result.get("logic", 5)),
                relevance=self._clamp(result.get("relevance", 5)),
                persuasion=self._clamp(result.get("persuasion", 5)),
            )
        except Exception as e:
            logger.warning(f"LLM scoring failed, falling back to heuristic: {e}")
            return self._score_argument_heuristic(content, topic)

    # ---- Heuristic fallback scoring ----

    def _score_argument_heuristic(
        self, content: str, topic: str
    ) -> ArgumentScore:
        """Score argument using keyword matching when no LLM is available."""
        content_lower = content.lower()
        topic_lower = topic.lower()
        word_count = len(content.split())

        scores = {}
        for dim, keywords in KEYWORD_SETS.items():
            hits = sum(1 for kw in keywords if kw in content_lower)
            # Base score from keyword density, scaled to 0-10
            raw = min(hits / max(len(keywords) * 0.15, 1), 1.0) * 7.0
            # Length bonus: longer arguments tend to be more developed
            length_bonus = min(word_count / 200, 1.0) * 2.0
            scores[dim] = min(raw + length_bonus, 10.0)

        # Relevance boost if topic terms appear in content
        topic_terms = [t for t in topic_lower.split() if len(t) > 3]
        if topic_terms:
            overlap = sum(1 for t in topic_terms if t in content_lower)
            relevance_boost = (overlap / len(topic_terms)) * 2.0
            scores["relevance"] = min(scores["relevance"] + relevance_boost, 10.0)

        # Add deterministic jitter so scores aren't identical
        seed = int(hashlib.md5(content.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        for dim in scores:
            scores[dim] += rng.uniform(-0.5, 0.5)
            scores[dim] = max(0.0, min(10.0, scores[dim]))

        return ArgumentScore(**scores)

    def _score_rebuttals(self, rebuttals: List[Dict[str, Any]]) -> float:
        """Score rebuttal effectiveness (0-10)."""
        if not rebuttals:
            return 0.0

        total = 0.0
        for r in rebuttals:
            content_lower = r.get("content", "").lower()
            hits = sum(1 for kw in REBUTTAL_KEYWORDS if kw in content_lower)
            word_count = len(r.get("content", "").split())
            raw = min(hits / max(len(REBUTTAL_KEYWORDS) * 0.2, 1), 1.0) * 7.0
            length_bonus = min(word_count / 150, 1.0) * 2.0
            total += min(raw + length_bonus, 10.0)

        return round(total / len(rebuttals), 2)

    def _score_questions(self, questions: List[Dict[str, Any]]) -> float:
        """Score question quality in cross-examination (0-10)."""
        if not questions:
            return 0.0

        total = 0.0
        for q in questions:
            content_lower = q.get("content", "").lower()
            hits = sum(1 for kw in QUESTION_KEYWORDS if kw in content_lower)
            has_question_mark = "?" in q.get("content", "")
            raw = min(hits / max(len(QUESTION_KEYWORDS) * 0.2, 1), 1.0) * 7.0
            qm_bonus = 2.0 if has_question_mark else 0.0
            total += min(raw + qm_bonus, 10.0)

        return round(total / len(questions), 2)

    def _compute_audience_impact(
        self, agent_id: str, debate: Dict[str, Any]
    ) -> float:
        """
        Estimate audience impact using deterministic scoring.

        In a real scenario, this would track opinion changes during the
        debate. For now, derive from argument scores + a seeded factor.
        """
        # Deterministic seed from agent_id + topic
        seed_str = f"{agent_id}:{debate.get('topic', '')}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Base impact from arguments made in the debate
        agent_args = []
        for phase in debate.get("phases", []):
            for arg in phase.get("arguments", []):
                if arg.get("agent_id") == agent_id:
                    agent_args.append(arg)

        if not agent_args:
            return 0.0

        # Avg content length as a proxy for substantiveness
        avg_len = sum(len(a.get("content", "").split()) for a in agent_args) / len(
            agent_args
        )
        base = min(avg_len / 100, 1.0) * 6.0
        return round(base + rng.uniform(1.0, 3.0), 2)

    # ---- Winner determination ----

    def _determine_winner_oxford(
        self, performances: List[AgentPerformance]
    ) -> Dict[str, Any]:
        """Winner by side aggregate (For vs Against) in Oxford format."""
        side_scores: Dict[str, List[float]] = {}
        for p in performances:
            side = p.side or "unknown"
            side_scores.setdefault(side, []).append(p.total_score)

        side_avgs = {
            side: round(sum(scores) / len(scores), 2)
            for side, scores in side_scores.items()
            if scores
        }

        if not side_avgs:
            return {"winner_type": "none", "winner": None, "score": 0, "margin": 0}

        best_side = max(side_avgs, key=side_avgs.get)
        sorted_sides = sorted(side_avgs.values(), reverse=True)
        margin = round(sorted_sides[0] - sorted_sides[1], 2) if len(sorted_sides) > 1 else sorted_sides[0]

        return {
            "winner_type": "side",
            "winner": best_side,
            "score": side_avgs[best_side],
            "margin": margin,
            "side_scores": side_avgs,
        }

    def _determine_winner_individual(
        self, performances: List[AgentPerformance]
    ) -> Dict[str, Any]:
        """Winner by individual score for panel/roundtable formats."""
        if not performances:
            return {"winner_type": "none", "winner": None, "score": 0, "margin": 0}

        ranked = sorted(performances, key=lambda p: p.total_score, reverse=True)
        margin = (
            round(ranked[0].total_score - ranked[1].total_score, 2)
            if len(ranked) > 1
            else ranked[0].total_score
        )

        return {
            "winner_type": "agent",
            "winner": ranked[0].agent_name,
            "winner_id": ranked[0].agent_id,
            "score": ranked[0].total_score,
            "margin": margin,
        }

    def _determine_winner_from_performances(
        self,
        performances: List[AgentPerformance],
        debate_format: str,
    ) -> Dict[str, Any]:
        """Route to the right winner logic based on format."""
        if debate_format == DebateFormat.OXFORD.value:
            return self._determine_winner_oxford(performances)
        return self._determine_winner_individual(performances)

    def _find_best_moment(
        self,
        performances: List[AgentPerformance],
        debate: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Find the single highest-scored argument in the debate."""
        best_score = -1.0
        best_moment = None

        for perf in performances:
            # Walk debate phases to pair scores with content
            arg_idx = 0
            for phase in debate.get("phases", []):
                for arg in phase.get("arguments", []):
                    if arg.get("agent_id") != perf.agent_id:
                        continue
                    if arg_idx < len(perf.argument_scores):
                        score = perf.argument_scores[arg_idx]
                        if score.overall > best_score:
                            best_score = score.overall
                            best_moment = {
                                "agent_id": perf.agent_id,
                                "agent_name": perf.agent_name,
                                "phase": phase.get("type", "unknown"),
                                "content": arg.get("content", "")[:300],
                                "score": score.to_dict(),
                            }
                        arg_idx += 1

        return best_moment

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
        """Clamp a numeric value to [lo, hi]."""
        try:
            return max(lo, min(hi, float(value)))
        except (TypeError, ValueError):
            return 5.0
