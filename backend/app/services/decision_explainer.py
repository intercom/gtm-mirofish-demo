"""
Decision Explanation Generator

Generates human-readable explanations of agent decisions during simulation.
Supports LLM-powered explanations with template-based fallback for demo mode.
"""

import json
import random
from typing import Dict, Any, Optional, List

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('mirofish.services.decision_explainer')


class DecisionExplainer:
    """Generates interpretable explanations for agent decisions in simulations."""

    def __init__(self):
        self._llm = None

    @property
    def llm(self) -> Optional[LLMClient]:
        if self._llm is None:
            try:
                self._llm = LLMClient()
            except ValueError:
                logger.info("No LLM key configured — using template fallback")
                self._llm = False  # sentinel: tried and failed
        return self._llm if self._llm is not False else None

    # ── Public API ──────────────────────────────────────────

    def explain_decision(
        self,
        agent_id: str,
        decision: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a human-readable explanation of why an agent made a decision.

        Args:
            agent_id: Identifier of the simulated agent.
            decision: Dict with keys like action, target, content, etc.
            context: Optional surrounding context (agent traits, scenario, history).

        Returns:
            Dict with explanation, factors, main_factor, and confidence.
        """
        context = context or {}

        if self.llm:
            return self._explain_with_llm(agent_id, decision, context)
        return self._explain_with_template(agent_id, decision, context)

    def generate_counterfactual(
        self,
        decision: Dict[str, Any],
        alternative: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a counterfactual: what would have happened with a different choice.

        Args:
            decision: The actual decision taken.
            alternative: The hypothetical alternative decision.
            context: Optional surrounding context.

        Returns:
            Dict with counterfactual narrative, impact_delta, and likelihood.
        """
        context = context or {}

        if self.llm:
            return self._counterfactual_with_llm(decision, alternative, context)
        return self._counterfactual_with_template(decision, alternative, context)

    def score_decision_quality(
        self,
        decision: Dict[str, Any],
        outcome: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retrospectively score how good a decision was given its outcome.

        Args:
            decision: The decision that was made.
            outcome: What actually happened as a result.
            context: Optional surrounding context.

        Returns:
            Dict with score (0-100), rating, rationale, and improvements.
        """
        context = context or {}

        if self.llm:
            return self._score_with_llm(decision, outcome, context)
        return self._score_with_template(decision, outcome, context)

    # ── LLM-powered implementations ────────────────────────

    def _explain_with_llm(
        self, agent_id: str, decision: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        traits = context.get("traits", [])
        history = context.get("history", [])
        scenario = context.get("scenario", "")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an analyst explaining simulated agent decisions in a GTM "
                    "(go-to-market) simulation. Respond in JSON with keys: "
                    "explanation (string, 2-3 sentences in plain English), "
                    "factors (array of strings — things the agent considered), "
                    "main_factor (string — the single most influential factor), "
                    "confidence (number 0-1 indicating how certain this explanation is)."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "agent_id": agent_id,
                        "decision": decision,
                        "agent_traits": traits,
                        "recent_history": history[-5:] if history else [],
                        "scenario": scenario,
                    }
                ),
            },
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.4, max_tokens=1024)
            return {
                "explanation": result.get("explanation", ""),
                "factors": result.get("factors", []),
                "main_factor": result.get("main_factor", ""),
                "confidence": min(max(float(result.get("confidence", 0.7)), 0), 1),
            }
        except Exception as e:
            logger.warning("LLM explain_decision failed, falling back to template: %s", e)
            return self._explain_with_template(agent_id, decision, context)

    def _counterfactual_with_llm(
        self,
        decision: Dict[str, Any],
        alternative: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an analyst generating counterfactual scenarios for a GTM simulation. "
                    "Given the actual decision and a hypothetical alternative, explain what would "
                    "have happened differently. Respond in JSON with keys: "
                    "narrative (string, 2-3 sentences), "
                    "impact_delta (string, e.g. '+15% engagement' or '-20% reach'), "
                    "likelihood (number 0-1, how likely the alternative outcome was)."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "actual_decision": decision,
                        "alternative_decision": alternative,
                        "context": context,
                    }
                ),
            },
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.5, max_tokens=1024)
            return {
                "narrative": result.get("narrative", ""),
                "impact_delta": result.get("impact_delta", ""),
                "likelihood": min(max(float(result.get("likelihood", 0.5)), 0), 1),
            }
        except Exception as e:
            logger.warning("LLM counterfactual failed, falling back to template: %s", e)
            return self._counterfactual_with_template(decision, alternative, context)

    def _score_with_llm(
        self,
        decision: Dict[str, Any],
        outcome: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an analyst scoring agent decision quality in a GTM simulation. "
                    "Respond in JSON with keys: "
                    "score (integer 0-100), "
                    "rating (string: 'excellent', 'good', 'fair', or 'poor'), "
                    "rationale (string, 1-2 sentences explaining the score), "
                    "improvements (array of strings — what could have been done better)."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"decision": decision, "outcome": outcome, "context": context}
                ),
            },
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.3, max_tokens=1024)
            score = min(max(int(result.get("score", 50)), 0), 100)
            return {
                "score": score,
                "rating": result.get("rating", _rating_from_score(score)),
                "rationale": result.get("rationale", ""),
                "improvements": result.get("improvements", []),
            }
        except Exception as e:
            logger.warning("LLM score_decision failed, falling back to template: %s", e)
            return self._score_with_template(decision, outcome, context)

    # ── Template fallback implementations ──────────────────

    def _explain_with_template(
        self, agent_id: str, decision: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        action = decision.get("action", "act")
        target = decision.get("target", "the audience")
        traits = context.get("traits", [])
        main_trait = traits[0] if traits else "strategic thinking"

        factors = [
            f"Agent's personality trait: {main_trait}",
            f"Target audience: {target}",
            f"Current scenario conditions",
        ]
        if len(traits) > 1:
            factors.append(f"Secondary trait: {traits[1]}")

        explanation = (
            f"Agent {agent_id} decided to {action} targeting {target}. "
            f"They considered the current scenario conditions and audience receptivity. "
            f"The main factor was alignment with their personality trait of {main_trait}."
        )

        return {
            "explanation": explanation,
            "factors": factors,
            "main_factor": factors[0],
            "confidence": 0.6,
        }

    def _counterfactual_with_template(
        self,
        decision: Dict[str, Any],
        alternative: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        actual_action = decision.get("action", "the chosen action")
        alt_action = alternative.get("action", "the alternative action")

        impact_options = ["+12% engagement", "-8% reach", "+5% conversion", "-15% visibility"]

        return {
            "narrative": (
                f"If the agent had chosen to {alt_action} instead of {actual_action}, "
                f"the outcome would likely have shifted. The alternative approach would have "
                f"traded off some immediate impact for longer-term positioning."
            ),
            "impact_delta": random.choice(impact_options),
            "likelihood": round(random.uniform(0.3, 0.7), 2),
        }

    def _score_with_template(
        self,
        decision: Dict[str, Any],
        outcome: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        engagement = outcome.get("engagement", 0)
        reach = outcome.get("reach", 0)

        # Simple heuristic scoring
        score = min(50 + int(engagement * 5) + int(reach * 2), 100)
        rating = _rating_from_score(score)

        improvements = []
        if engagement < 5:
            improvements.append("Consider more engaging content formats")
        if reach < 10:
            improvements.append("Broaden targeting to increase reach")
        if not improvements:
            improvements.append("Maintain current strategy — results are strong")

        return {
            "score": score,
            "rating": rating,
            "rationale": (
                f"Decision scored {score}/100 based on observed engagement ({engagement}) "
                f"and reach ({reach}). Overall rating: {rating}."
            ),
            "improvements": improvements,
        }


def _rating_from_score(score: int) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"
