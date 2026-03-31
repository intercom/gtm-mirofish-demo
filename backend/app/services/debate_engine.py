"""
Debate Orchestration Engine
Structured debate mode for agent simulations.
Supports Oxford (for/against), Panel (moderated), and Roundtable (free discussion) formats.
"""

import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..utils.logger import get_logger
from ..config import Config

logger = get_logger('mirofish.debate')


class DebateFormat(str, Enum):
    OXFORD = "oxford"
    PANEL = "panel"
    ROUNDTABLE = "roundtable"


class DebatePhase(str, Enum):
    SETUP = "setup"
    OPENING = "opening_statements"
    REBUTTAL = "rebuttal"
    CROSS_EXAMINATION = "cross_examination"
    CLOSING = "closing_statements"
    VOTE = "vote"
    COMPLETED = "completed"


@dataclass
class DebateAgent:
    agent_id: str
    name: str
    role: str
    company: str = ""
    persona: str = ""
    team: Optional[str] = None  # 'for' or 'against' (Oxford format)
    is_moderator: bool = False


@dataclass
class Argument:
    agent_id: str
    agent_name: str
    phase: str
    content: str
    team: Optional[str] = None
    quality_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    target_agent_id: Optional[str] = None  # for rebuttals / cross-exam


@dataclass
class PersuasionEvent:
    agent_id: str
    agent_name: str
    from_position: str
    to_position: str
    triggered_by_argument: str
    round_num: int


@dataclass
class VoteResult:
    agent_id: str
    agent_name: str
    vote: str  # 'for', 'against', or 'abstain'
    reasoning: str
    confidence: float  # 0.0-1.0


@dataclass
class DebateState:
    debate_id: str
    topic: str
    format: DebateFormat
    phase: DebatePhase
    agents: List[DebateAgent]
    moderator: Optional[DebateAgent]
    arguments: List[Argument] = field(default_factory=list)
    persuasion_events: List[PersuasionEvent] = field(default_factory=list)
    opinion_tracker: Dict[str, str] = field(default_factory=dict)  # agent_id -> current position
    vote_results: List[VoteResult] = field(default_factory=list)
    rebuttal_round: int = 0
    max_rebuttal_rounds: int = 2
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "debate_id": self.debate_id,
            "topic": self.topic,
            "format": self.format.value,
            "phase": self.phase.value,
            "agents": [_agent_dict(a) for a in self.agents],
            "moderator": _agent_dict(self.moderator) if self.moderator else None,
            "arguments": [_argument_dict(a) for a in self.arguments],
            "persuasion_events": [_persuasion_dict(p) for p in self.persuasion_events],
            "opinion_tracker": self.opinion_tracker,
            "vote_results": [_vote_dict(v) for v in self.vote_results],
            "rebuttal_round": self.rebuttal_round,
            "max_rebuttal_rounds": self.max_rebuttal_rounds,
            "created_at": self.created_at,
        }


def _agent_dict(a: DebateAgent) -> Dict[str, Any]:
    return {
        "agent_id": a.agent_id,
        "name": a.name,
        "role": a.role,
        "company": a.company,
        "persona": a.persona,
        "team": a.team,
        "is_moderator": a.is_moderator,
    }


def _argument_dict(a: Argument) -> Dict[str, Any]:
    return {
        "agent_id": a.agent_id,
        "agent_name": a.agent_name,
        "phase": a.phase,
        "content": a.content,
        "team": a.team,
        "quality_score": a.quality_score,
        "timestamp": a.timestamp,
        "target_agent_id": a.target_agent_id,
    }


def _persuasion_dict(p: PersuasionEvent) -> Dict[str, Any]:
    return {
        "agent_id": p.agent_id,
        "agent_name": p.agent_name,
        "from_position": p.from_position,
        "to_position": p.to_position,
        "triggered_by_argument": p.triggered_by_argument,
        "round_num": p.round_num,
    }


def _vote_dict(v: VoteResult) -> Dict[str, Any]:
    return {
        "agent_id": v.agent_id,
        "agent_name": v.agent_name,
        "vote": v.vote,
        "reasoning": v.reasoning,
        "confidence": v.confidence,
    }


# ---------------------------------------------------------------------------
# Mock data for demo/fallback mode
# ---------------------------------------------------------------------------

_MOCK_OPENING_FOR = [
    "I firmly believe {topic} is the right direction. The data shows a clear trend toward this approach, and early adopters are already seeing 30-40% improvements in key metrics. Our competitive analysis supports moving forward decisively.",
    "The evidence overwhelmingly supports this position. Market research from Q3 shows customer sentiment shifting strongly in this direction, and our pilot programs have validated the core hypothesis with statistically significant results.",
    "From a strategic perspective, this is not just a good idea — it's essential. Companies that have embraced this approach report higher NPS scores, better retention, and faster growth. We can't afford to fall behind.",
]

_MOCK_OPENING_AGAINST = [
    "While I understand the appeal, the risks here significantly outweigh the potential benefits. Our current approach is delivering steady results, and a pivot of this magnitude could destabilize what's already working.",
    "I respectfully disagree. The data being cited is cherry-picked from favorable conditions. When we look at the full picture — including implementation costs, team disruption, and opportunity cost — the case falls apart.",
    "We need to be pragmatic. The organizations that rushed into this saw mixed results at best. A more measured, incremental approach would let us capture upside while managing downside risk.",
]

_MOCK_PANEL_OPENING = [
    "This is a nuanced topic. I see merit on multiple sides, but I believe the key factor is timing. The market conditions today are different from six months ago, and we should weigh recent signals heavily.",
    "My perspective is shaped by what I've seen on the ground with customers. They're asking for this, but they also want stability. The challenge is threading that needle — delivering innovation without disrupting their workflows.",
    "I want to bring a data-driven perspective. Looking at our funnel metrics, there's a clear case for experimentation here, but we should define success criteria upfront and be willing to course-correct.",
]

_MOCK_REBUTTALS = [
    "I hear the concern about {target_point}, but the data tells a different story. When we control for market conditions, the correlation between this approach and positive outcomes is strong — R² of 0.73 in our analysis.",
    "That's a fair point about risk, but consider the risk of inaction. Our competitors aren't standing still. The cost of maintaining the status quo is higher than it appears when you factor in market share erosion.",
    "While {target_agent} raises valid concerns about implementation complexity, we've seen similar transitions executed successfully. The key is phased rollout with clear milestones, not a big-bang approach.",
    "I appreciate the caution, but I think we're overweighting short-term disruption versus long-term advantage. Every major strategic shift feels uncomfortable at first — that doesn't mean it's wrong.",
]

_MOCK_CROSS_EXAM_QUESTIONS = [
    "Can you quantify the downside risk you're concerned about? What specific metrics would decline, and by how much?",
    "You mentioned competitor pressure — which competitors specifically, and what's their timeline? Are we reacting or proactively positioning?",
    "What's your confidence level in the data supporting your position? Have the assumptions been stress-tested against different market scenarios?",
    "If we adopted your approach, what would success look like in 6 months? What are the leading indicators we should track?",
]

_MOCK_CROSS_EXAM_ANSWERS = [
    "Based on our modeling, the primary risk is a 15-20% dip in conversion during the transition period, recovering within two quarters. The long-term trajectory is positive — we project 25% improvement by month 9.",
    "That's a good question. We've stress-tested against three scenarios: bull case, base case, and bear case. Even in the bear case, we come out ahead of the status quo within 18 months.",
    "Our confidence is moderate — about 70%. The main uncertainty is customer adoption speed. But the directional signal is clear, and waiting for perfect data means losing first-mover advantage.",
    "In six months, I'd expect to see early pipeline signals — increased demo requests, higher engagement scores, and improved sentiment in competitive deals. The lagging indicators like revenue follow in Q3-Q4.",
]

_MOCK_CLOSING = [
    "After hearing all perspectives, I'm more convinced than ever. The rebuttals raised valid concerns, but none that can't be mitigated with proper planning. The opportunity cost of inaction is the real risk here.",
    "This debate has sharpened my thinking. While I maintain my original position, I acknowledge the implementation risks raised. I'd advocate for a phased approach with clear go/no-go gates.",
    "I've been persuaded by some of the counterarguments. My position has evolved — I now support a modified version that captures the upside while addressing the legitimate concerns raised about timing and execution.",
    "The discussion has been productive. I still believe strongly in my position, but I'm now more open to the staged approach several colleagues have advocated. Speed matters, but so does getting it right.",
]

_MOCK_VOTE_REASONING = {
    "for": [
        "The strategic upside is too significant to ignore. With proper execution guardrails, the risk is manageable.",
        "The competitive landscape demands action. Waiting is itself a decision — and the wrong one.",
    ],
    "against": [
        "The implementation risks haven't been adequately addressed. I'd support a smaller pilot first.",
        "The timing isn't right. Let's revisit after we've stabilized our current initiatives.",
    ],
    "abstain": [
        "Both sides presented compelling arguments. I need more data before committing to a direction.",
    ],
}


def _deterministic_seed(debate_id: str, agent_id: str, phase: str) -> int:
    h = hashlib.md5(f"{debate_id}:{agent_id}:{phase}".encode()).hexdigest()
    return int(h[:8], 16)


def _pick(items: list, seed: int) -> str:
    return items[seed % len(items)]


class DebateEngine:
    """Orchestrates structured debates between simulation agents."""

    def __init__(self):
        self._debates: Dict[str, DebateState] = {}
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            try:
                from ..utils.llm_client import LLMClient
                self._llm = LLMClient()
            except (ValueError, Exception) as e:
                logger.info(f"LLM not available, using mock mode: {e}")
                self._llm = False  # sentinel: tried and failed
        return self._llm if self._llm is not False else None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup_debate(
        self,
        topic: str,
        agents: List[Dict[str, Any]],
        format: str = "oxford",
        moderator_id: Optional[str] = None,
        max_rebuttal_rounds: int = 2,
    ) -> DebateState:
        """Configure a structured debate.

        Args:
            topic: The debate proposition.
            agents: List of agent dicts with at least {agent_id, name, role}.
                    For Oxford format, include 'team': 'for'|'against'.
            format: 'oxford', 'panel', or 'roundtable'.
            moderator_id: Optional agent_id to act as moderator.
            max_rebuttal_rounds: Number of rebuttal rounds (default 2).

        Returns:
            The initialized DebateState.
        """
        debate_id = str(uuid.uuid4())
        fmt = DebateFormat(format)

        debate_agents = []
        moderator = None

        for i, a in enumerate(agents):
            agent = DebateAgent(
                agent_id=a.get("agent_id", str(i)),
                name=a["name"],
                role=a.get("role", "Participant"),
                company=a.get("company", ""),
                persona=a.get("persona", ""),
                team=a.get("team"),
                is_moderator=a.get("agent_id") == moderator_id,
            )
            if agent.is_moderator:
                moderator = agent
            else:
                debate_agents.append(agent)

        # Oxford format: auto-assign teams if not provided
        if fmt == DebateFormat.OXFORD:
            unassigned = [a for a in debate_agents if a.team not in ("for", "against")]
            if unassigned:
                half = len(unassigned) // 2
                for idx, a in enumerate(unassigned):
                    a.team = "for" if idx < half else "against"

        # Set initial opinion positions
        opinion_tracker = {}
        for a in debate_agents:
            if fmt == DebateFormat.OXFORD:
                opinion_tracker[a.agent_id] = a.team or "neutral"
            else:
                seed = _deterministic_seed(debate_id, a.agent_id, "initial")
                opinion_tracker[a.agent_id] = ["for", "against", "neutral"][seed % 3]

        state = DebateState(
            debate_id=debate_id,
            topic=topic,
            format=fmt,
            phase=DebatePhase.SETUP,
            agents=debate_agents,
            moderator=moderator,
            opinion_tracker=opinion_tracker,
            max_rebuttal_rounds=max_rebuttal_rounds,
        )
        self._debates[debate_id] = state
        logger.info(f"Debate setup: id={debate_id} topic='{topic}' format={format} agents={len(debate_agents)}")
        return state

    # ------------------------------------------------------------------
    # Opening Statements
    # ------------------------------------------------------------------

    def run_opening_statements(self, debate_id: str) -> List[Argument]:
        """Each agent presents their initial position."""
        state = self._get_debate(debate_id)
        state.phase = DebatePhase.OPENING
        new_args = []

        for agent in state.agents:
            content = self._generate_opening(state, agent)
            arg = Argument(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                phase=DebatePhase.OPENING.value,
                content=content,
                team=agent.team,
            )
            arg.quality_score = self._score_argument_heuristic(content)
            state.arguments.append(arg)
            new_args.append(arg)

        logger.info(f"Debate {debate_id}: opening statements from {len(new_args)} agents")
        return new_args

    # ------------------------------------------------------------------
    # Rebuttal
    # ------------------------------------------------------------------

    def run_rebuttal_round(self, debate_id: str) -> List[Argument]:
        """Agents respond to opposing positions."""
        state = self._get_debate(debate_id)
        state.phase = DebatePhase.REBUTTAL
        state.rebuttal_round += 1
        new_args = []

        for agent in state.agents:
            opposing = self._get_opposing_arguments(state, agent)
            if not opposing:
                continue
            content = self._generate_rebuttal(state, agent, opposing)
            arg = Argument(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                phase=DebatePhase.REBUTTAL.value,
                content=content,
                team=agent.team,
                target_agent_id=opposing[0].agent_id if opposing else None,
            )
            arg.quality_score = self._score_argument_heuristic(content)
            state.arguments.append(arg)
            new_args.append(arg)

            # Check for persuasion events
            self._check_persuasion(state, agent, opposing, state.rebuttal_round)

        logger.info(f"Debate {debate_id}: rebuttal round {state.rebuttal_round} — {len(new_args)} arguments")
        return new_args

    # ------------------------------------------------------------------
    # Cross-Examination
    # ------------------------------------------------------------------

    def run_cross_examination(
        self, debate_id: str, questioner_id: str, respondent_id: str
    ) -> Dict[str, Argument]:
        """One agent questions another. Returns {question, answer}."""
        state = self._get_debate(debate_id)
        state.phase = DebatePhase.CROSS_EXAMINATION

        questioner = self._find_agent(state, questioner_id)
        respondent = self._find_agent(state, respondent_id)

        question_content = self._generate_cross_exam_question(state, questioner, respondent)
        question = Argument(
            agent_id=questioner.agent_id,
            agent_name=questioner.name,
            phase=DebatePhase.CROSS_EXAMINATION.value,
            content=question_content,
            team=questioner.team,
            target_agent_id=respondent.agent_id,
        )
        question.quality_score = self._score_argument_heuristic(question_content)
        state.arguments.append(question)

        answer_content = self._generate_cross_exam_answer(state, respondent, questioner, question_content)
        answer = Argument(
            agent_id=respondent.agent_id,
            agent_name=respondent.name,
            phase=DebatePhase.CROSS_EXAMINATION.value,
            content=answer_content,
            team=respondent.team,
            target_agent_id=questioner.agent_id,
        )
        answer.quality_score = self._score_argument_heuristic(answer_content)
        state.arguments.append(answer)

        logger.info(f"Debate {debate_id}: cross-exam {questioner.name} → {respondent.name}")
        return {"question": question, "answer": answer}

    # ------------------------------------------------------------------
    # Closing Statements
    # ------------------------------------------------------------------

    def run_closing_statements(self, debate_id: str) -> List[Argument]:
        """Final positions after hearing all arguments."""
        state = self._get_debate(debate_id)
        state.phase = DebatePhase.CLOSING
        new_args = []

        for agent in state.agents:
            content = self._generate_closing(state, agent)
            arg = Argument(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                phase=DebatePhase.CLOSING.value,
                content=content,
                team=agent.team,
            )
            arg.quality_score = self._score_argument_heuristic(content)
            state.arguments.append(arg)
            new_args.append(arg)

        logger.info(f"Debate {debate_id}: closing statements from {len(new_args)} agents")
        return new_args

    # ------------------------------------------------------------------
    # Vote
    # ------------------------------------------------------------------

    def run_vote(self, debate_id: str) -> Dict[str, Any]:
        """All agents vote on the debate topic. Returns tally and per-agent results."""
        state = self._get_debate(debate_id)
        state.phase = DebatePhase.VOTE
        state.vote_results = []

        for agent in state.agents:
            result = self._generate_vote(state, agent)
            state.vote_results.append(result)

        tally = {"for": 0, "against": 0, "abstain": 0}
        for v in state.vote_results:
            tally[v.vote] = tally.get(v.vote, 0) + 1

        total = len(state.vote_results)
        winner = max(tally, key=tally.get)
        margin = (tally[winner] / total * 100) if total > 0 else 0

        state.phase = DebatePhase.COMPLETED

        summary = {
            "tally": tally,
            "winner": winner,
            "margin_percent": round(margin, 1),
            "total_votes": total,
            "votes": [_vote_dict(v) for v in state.vote_results],
        }
        logger.info(f"Debate {debate_id}: vote complete — {winner} wins ({tally[winner]}/{total})")
        return summary

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    def get_debate(self, debate_id: str) -> Optional[DebateState]:
        return self._debates.get(debate_id)

    def list_debates(self) -> List[Dict[str, Any]]:
        return [
            {
                "debate_id": s.debate_id,
                "topic": s.topic,
                "format": s.format.value,
                "phase": s.phase.value,
                "agent_count": len(s.agents),
                "argument_count": len(s.arguments),
                "created_at": s.created_at,
            }
            for s in self._debates.values()
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_debate(self, debate_id: str) -> DebateState:
        state = self._debates.get(debate_id)
        if not state:
            raise ValueError(f"Debate not found: {debate_id}")
        return state

    def _find_agent(self, state: DebateState, agent_id: str) -> DebateAgent:
        for a in state.agents:
            if a.agent_id == agent_id:
                return a
        raise ValueError(f"Agent not found: {agent_id}")

    def _get_opposing_arguments(self, state: DebateState, agent: DebateAgent) -> List[Argument]:
        """Get arguments from other agents (opposing team in Oxford, any others otherwise)."""
        if state.format == DebateFormat.OXFORD and agent.team:
            return [a for a in state.arguments if a.team and a.team != agent.team]
        return [a for a in state.arguments if a.agent_id != agent.agent_id]

    def _check_persuasion(
        self, state: DebateState, agent: DebateAgent,
        opposing_args: List[Argument], round_num: int
    ):
        """Deterministically check if an agent shifts position based on argument quality."""
        if state.format == DebateFormat.OXFORD:
            return  # Oxford debaters stay on their assigned team

        seed = _deterministic_seed(state.debate_id, agent.agent_id, f"persuasion_{round_num}")
        avg_opposing_quality = sum(a.quality_score for a in opposing_args) / max(len(opposing_args), 1)

        # Higher opposing quality → higher chance of shift
        if avg_opposing_quality > 6.5 and (seed % 100) < 25:
            old_pos = state.opinion_tracker.get(agent.agent_id, "neutral")
            new_pos = "for" if old_pos in ("against", "neutral") else "against"
            state.opinion_tracker[agent.agent_id] = new_pos
            trigger = opposing_args[seed % len(opposing_args)].content[:80]
            state.persuasion_events.append(PersuasionEvent(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                from_position=old_pos,
                to_position=new_pos,
                triggered_by_argument=trigger,
                round_num=round_num,
            ))
            logger.info(f"Persuasion: {agent.name} shifted {old_pos} → {new_pos}")

    def _score_argument_heuristic(self, content: str) -> float:
        """Simple heuristic scoring based on content features."""
        score = 5.0
        words = content.split()
        # Length: reward substantive arguments
        if len(words) > 40:
            score += 1.0
        if len(words) > 80:
            score += 0.5
        # Evidence signals
        evidence_words = {"data", "research", "study", "analysis", "evidence", "metrics", "results", "statistics", "percent", "%"}
        evidence_count = sum(1 for w in words if w.lower().strip(".,;:") in evidence_words)
        score += min(evidence_count * 0.3, 1.5)
        # Logical connectors
        logic_words = {"because", "therefore", "however", "furthermore", "moreover", "consequently", "although"}
        logic_count = sum(1 for w in words if w.lower() in logic_words)
        score += min(logic_count * 0.2, 1.0)
        # Specificity (numbers)
        num_count = sum(1 for w in words if any(c.isdigit() for c in w))
        score += min(num_count * 0.2, 1.0)
        return round(min(score, 10.0), 1)

    # ------------------------------------------------------------------
    # Content generation (LLM with mock fallback)
    # ------------------------------------------------------------------

    def _generate_opening(self, state: DebateState, agent: DebateAgent) -> str:
        llm = self._get_llm()
        if llm:
            return self._llm_opening(llm, state, agent)
        return self._mock_opening(state, agent)

    def _generate_rebuttal(self, state: DebateState, agent: DebateAgent, opposing: List[Argument]) -> str:
        llm = self._get_llm()
        if llm:
            return self._llm_rebuttal(llm, state, agent, opposing)
        return self._mock_rebuttal(state, agent, opposing)

    def _generate_cross_exam_question(self, state: DebateState, questioner: DebateAgent, respondent: DebateAgent) -> str:
        llm = self._get_llm()
        if llm:
            return self._llm_cross_exam_question(llm, state, questioner, respondent)
        return self._mock_cross_exam_question(state, questioner, respondent)

    def _generate_cross_exam_answer(self, state: DebateState, respondent: DebateAgent, questioner: DebateAgent, question: str) -> str:
        llm = self._get_llm()
        if llm:
            return self._llm_cross_exam_answer(llm, state, respondent, questioner, question)
        return self._mock_cross_exam_answer(state, respondent, questioner)

    def _generate_closing(self, state: DebateState, agent: DebateAgent) -> str:
        llm = self._get_llm()
        if llm:
            return self._llm_closing(llm, state, agent)
        return self._mock_closing(state, agent)

    def _generate_vote(self, state: DebateState, agent: DebateAgent) -> VoteResult:
        llm = self._get_llm()
        if llm:
            return self._llm_vote(llm, state, agent)
        return self._mock_vote(state, agent)

    # ------------------------------------------------------------------
    # Mock generators (deterministic, seeded by debate_id + agent_id)
    # ------------------------------------------------------------------

    def _mock_opening(self, state: DebateState, agent: DebateAgent) -> str:
        seed = _deterministic_seed(state.debate_id, agent.agent_id, "opening")
        if state.format == DebateFormat.OXFORD:
            pool = _MOCK_OPENING_FOR if agent.team == "for" else _MOCK_OPENING_AGAINST
        else:
            pool = _MOCK_PANEL_OPENING
        template = _pick(pool, seed)
        return template.format(topic=state.topic)

    def _mock_rebuttal(self, state: DebateState, agent: DebateAgent, opposing: List[Argument]) -> str:
        seed = _deterministic_seed(state.debate_id, agent.agent_id, f"rebuttal_{state.rebuttal_round}")
        target = opposing[seed % len(opposing)] if opposing else None
        template = _pick(_MOCK_REBUTTALS, seed)
        return template.format(
            target_point=target.content[:60] + "..." if target else "the opposing view",
            target_agent=target.agent_name if target else "my colleague",
        )

    def _mock_cross_exam_question(self, state: DebateState, questioner: DebateAgent, respondent: DebateAgent) -> str:
        seed = _deterministic_seed(state.debate_id, questioner.agent_id, f"question_{respondent.agent_id}")
        return _pick(_MOCK_CROSS_EXAM_QUESTIONS, seed)

    def _mock_cross_exam_answer(self, state: DebateState, respondent: DebateAgent, questioner: DebateAgent) -> str:
        seed = _deterministic_seed(state.debate_id, respondent.agent_id, f"answer_{questioner.agent_id}")
        return _pick(_MOCK_CROSS_EXAM_ANSWERS, seed)

    def _mock_closing(self, state: DebateState, agent: DebateAgent) -> str:
        seed = _deterministic_seed(state.debate_id, agent.agent_id, "closing")
        return _pick(_MOCK_CLOSING, seed)

    def _mock_vote(self, state: DebateState, agent: DebateAgent) -> VoteResult:
        seed = _deterministic_seed(state.debate_id, agent.agent_id, "vote")
        position = state.opinion_tracker.get(agent.agent_id, "neutral")

        if state.format == DebateFormat.OXFORD:
            vote = agent.team or "abstain"
        elif position == "neutral":
            vote = ["for", "against", "abstain"][seed % 3]
        else:
            # Slight chance of switching from initial position based on persuasion
            vote = position

        reasoning = _pick(_MOCK_VOTE_REASONING.get(vote, _MOCK_VOTE_REASONING["abstain"]), seed)
        confidence = round(0.5 + (seed % 50) / 100, 2)

        return VoteResult(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            vote=vote,
            reasoning=reasoning,
            confidence=confidence,
        )

    # ------------------------------------------------------------------
    # LLM generators
    # ------------------------------------------------------------------

    def _build_debate_context(self, state: DebateState) -> str:
        """Build a summary of the debate so far for LLM context."""
        lines = [f"Debate topic: \"{state.topic}\"", f"Format: {state.format.value}", ""]
        if state.arguments:
            lines.append("Arguments so far:")
            for a in state.arguments[-10:]:  # last 10 to stay within token limits
                team_label = f" [{a.team}]" if a.team else ""
                lines.append(f"- {a.agent_name}{team_label} ({a.phase}): {a.content[:200]}")
        return "\n".join(lines)

    def _agent_system_prompt(self, agent: DebateAgent, state: DebateState) -> str:
        team_str = f" You are on the '{agent.team}' team." if agent.team else ""
        return (
            f"You are {agent.name}, {agent.role} at {agent.company}. "
            f"Persona: {agent.persona}.{team_str} "
            f"You are participating in a {state.format.value} debate. "
            "Stay in character. Be specific, use data-like references, and argue persuasively. "
            "Keep responses to 2-4 sentences."
        )

    def _llm_opening(self, llm, state: DebateState, agent: DebateAgent) -> str:
        try:
            return llm.chat(
                messages=[
                    {"role": "system", "content": self._agent_system_prompt(agent, state)},
                    {"role": "user", "content": f"Present your opening statement on: \"{state.topic}\""},
                ],
                temperature=0.8,
                max_tokens=300,
            )
        except Exception as e:
            logger.warning(f"LLM opening failed for {agent.name}: {e}")
            return self._mock_opening(state, agent)

    def _llm_rebuttal(self, llm, state: DebateState, agent: DebateAgent, opposing: List[Argument]) -> str:
        try:
            context = self._build_debate_context(state)
            opp_summary = "\n".join(f"- {a.agent_name}: {a.content[:150]}" for a in opposing[-3:])
            return llm.chat(
                messages=[
                    {"role": "system", "content": self._agent_system_prompt(agent, state)},
                    {"role": "user", "content": (
                        f"Debate context:\n{context}\n\n"
                        f"Respond to these opposing arguments:\n{opp_summary}\n\n"
                        "Present your rebuttal."
                    )},
                ],
                temperature=0.8,
                max_tokens=300,
            )
        except Exception as e:
            logger.warning(f"LLM rebuttal failed for {agent.name}: {e}")
            return self._mock_rebuttal(state, agent, opposing)

    def _llm_cross_exam_question(self, llm, state: DebateState, questioner: DebateAgent, respondent: DebateAgent) -> str:
        try:
            context = self._build_debate_context(state)
            resp_args = [a for a in state.arguments if a.agent_id == respondent.agent_id]
            resp_summary = "\n".join(f"- {a.content[:150]}" for a in resp_args[-3:])
            return llm.chat(
                messages=[
                    {"role": "system", "content": self._agent_system_prompt(questioner, state)},
                    {"role": "user", "content": (
                        f"Debate context:\n{context}\n\n"
                        f"{respondent.name}'s positions:\n{resp_summary}\n\n"
                        f"Ask {respondent.name} a probing question to challenge or clarify their position."
                    )},
                ],
                temperature=0.8,
                max_tokens=200,
            )
        except Exception as e:
            logger.warning(f"LLM cross-exam question failed: {e}")
            return self._mock_cross_exam_question(state, questioner, respondent)

    def _llm_cross_exam_answer(self, llm, state: DebateState, respondent: DebateAgent, questioner: DebateAgent, question: str) -> str:
        try:
            context = self._build_debate_context(state)
            return llm.chat(
                messages=[
                    {"role": "system", "content": self._agent_system_prompt(respondent, state)},
                    {"role": "user", "content": (
                        f"Debate context:\n{context}\n\n"
                        f"{questioner.name} asks you: \"{question}\"\n\n"
                        "Answer the question directly and defend your position."
                    )},
                ],
                temperature=0.7,
                max_tokens=300,
            )
        except Exception as e:
            logger.warning(f"LLM cross-exam answer failed: {e}")
            return self._mock_cross_exam_answer(state, respondent, questioner)

    def _llm_closing(self, llm, state: DebateState, agent: DebateAgent) -> str:
        try:
            context = self._build_debate_context(state)
            return llm.chat(
                messages=[
                    {"role": "system", "content": self._agent_system_prompt(agent, state)},
                    {"role": "user", "content": (
                        f"Debate context:\n{context}\n\n"
                        "Deliver your closing statement. Summarize your strongest points "
                        "and acknowledge any arguments that influenced your thinking."
                    )},
                ],
                temperature=0.7,
                max_tokens=300,
            )
        except Exception as e:
            logger.warning(f"LLM closing failed for {agent.name}: {e}")
            return self._mock_closing(state, agent)

    def _llm_vote(self, llm, state: DebateState, agent: DebateAgent) -> VoteResult:
        try:
            context = self._build_debate_context(state)
            response = llm.chat_json(
                messages=[
                    {"role": "system", "content": (
                        self._agent_system_prompt(agent, state) +
                        " Respond with JSON: {\"vote\": \"for\"|\"against\"|\"abstain\", "
                        "\"reasoning\": \"...\", \"confidence\": 0.0-1.0}"
                    )},
                    {"role": "user", "content": (
                        f"Debate context:\n{context}\n\n"
                        f"Cast your vote on: \"{state.topic}\""
                    )},
                ],
                temperature=0.5,
                max_tokens=200,
            )
            vote = response.get("vote", "abstain")
            if vote not in ("for", "against", "abstain"):
                vote = "abstain"
            return VoteResult(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                vote=vote,
                reasoning=response.get("reasoning", ""),
                confidence=max(0.0, min(1.0, float(response.get("confidence", 0.7)))),
            )
        except Exception as e:
            logger.warning(f"LLM vote failed for {agent.name}: {e}")
            return self._mock_vote(state, agent)
