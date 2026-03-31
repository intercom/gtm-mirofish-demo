"""
Counterfactual analysis service.

Given a decision point in a simulation (a specific agent action at a specific round),
generates a what-if analysis comparing the actual outcome to an alternative scenario.
Supports LLM-powered analysis and demo/mock mode.
"""

import random
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.services.counterfactual')


def _build_prompt(decision_point: Dict, actions_context: List[Dict], agent_profiles: List[Dict]) -> List[Dict[str, str]]:
    """Build the LLM prompt for counterfactual analysis."""
    agent_name = decision_point.get('agent_name', 'Unknown Agent')
    round_num = decision_point.get('round_num', 0)
    action_type = decision_point.get('action_type', 'ACTION')
    content = decision_point.get('content', '')
    alternative = decision_point.get('alternative', '')

    profiles_summary = ""
    for p in agent_profiles[:10]:
        name = p.get('name', p.get('agent_name', 'Agent'))
        role = p.get('role', p.get('description', ''))
        profiles_summary += f"- {name}: {role}\n"

    context_lines = []
    for a in actions_context[:30]:
        r = a.get('round_num', '?')
        name = a.get('agent_name', 'Agent')
        atype = a.get('action_type', 'ACTION')
        c = (a.get('action_args', {}) or {}).get('content', '')[:120]
        context_lines.append(f"  Round {r} | {name} | {atype}: {c}")
    context_block = "\n".join(context_lines) if context_lines else "  (no prior context available)"

    system_msg = (
        "You are an expert simulation analyst. Given a multi-agent social simulation, "
        "you analyze counterfactual scenarios: what would have happened if an agent made "
        "a different decision at a pivotal moment. Be specific, quantitative where possible, "
        "and provide a confidence estimate (0-100) for your counterfactual prediction."
    )

    user_msg = f"""Analyze this counterfactual scenario from a GTM (Go-To-Market) social simulation.

## Agent Profiles
{profiles_summary or '(profiles not available)'}

## Simulation Context (recent actions)
{context_block}

## Decision Point
- **Round:** {round_num}
- **Agent:** {agent_name}
- **Actual action:** {action_type} — "{content}"
- **Alternative considered:** "{alternative or 'The opposite stance/action'}"

## Instructions
Respond in valid JSON with this structure:
{{
  "actual_outcome": {{
    "summary": "What actually happened as a result of this action (2-3 sentences)",
    "sentiment_impact": <float -1.0 to 1.0>,
    "rounds_to_resolution": <int or null>,
    "key_effects": ["effect1", "effect2", "effect3"]
  }},
  "counterfactual_outcome": {{
    "summary": "What would likely have happened with the alternative action (2-3 sentences)",
    "sentiment_impact": <float -1.0 to 1.0>,
    "rounds_to_resolution": <int or null>,
    "key_effects": ["effect1", "effect2", "effect3"]
  }},
  "impact_assessment": {{
    "consensus_delta": <int, positive means faster consensus with alternative>,
    "sentiment_shift": <float, difference in group sentiment>,
    "affected_agents": ["agent1", "agent2"],
    "pivotal": <boolean, was this a truly pivotal moment?>
  }},
  "confidence": <int 0-100>,
  "narrative": "A one-paragraph natural language summary comparing both scenarios"
}}"""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def _generate_mock_analysis(decision_point: Dict, actions_context: List[Dict]) -> Dict[str, Any]:
    """Generate realistic mock data for demo mode (no LLM key configured)."""
    agent_name = decision_point.get('agent_name', 'Agent A')
    round_num = decision_point.get('round_num', 1)
    action_type = decision_point.get('action_type', 'REPLY')
    content = decision_point.get('content', 'expressed skepticism about the proposal')
    alternative = decision_point.get('alternative', 'expressed support for the proposal')

    unique_agents = list({a.get('agent_name', f'Agent_{i}') for i, a in enumerate(actions_context[:20])})
    affected = random.sample(unique_agents, min(3, len(unique_agents))) if unique_agents else ['Agent B', 'Agent C']

    actual_sentiment = round(random.uniform(-0.4, 0.3), 2)
    cf_sentiment = round(actual_sentiment + random.uniform(0.1, 0.5), 2)
    cf_sentiment = min(1.0, cf_sentiment)
    consensus_delta = random.randint(1, 4)
    confidence = random.randint(55, 85)

    return {
        "actual_outcome": {
            "summary": (
                f"{agent_name}'s {action_type.lower()} in round {round_num} — \"{content[:80]}\" — "
                f"introduced friction into the group discussion. Several agents shifted to a more "
                f"cautious stance, extending deliberation by approximately {consensus_delta} rounds."
            ),
            "sentiment_impact": actual_sentiment,
            "rounds_to_resolution": round_num + consensus_delta + random.randint(2, 5),
            "key_effects": [
                f"{affected[0] if affected else 'Agent B'} adopted a more cautious position",
                "Group polarization increased temporarily",
                "Additional evidence-gathering actions were triggered",
            ],
        },
        "counterfactual_outcome": {
            "summary": (
                f"If {agent_name} had instead \"{alternative[:80]}\", the group would likely have "
                f"converged faster. The positive signal would have encouraged {affected[0] if affected else 'other agents'} "
                f"to commit earlier, reducing deliberation by ~{consensus_delta} rounds."
            ),
            "sentiment_impact": cf_sentiment,
            "rounds_to_resolution": round_num + random.randint(1, 3),
            "key_effects": [
                f"{affected[0] if affected else 'Agent B'} would have committed to the proposal sooner",
                "Group sentiment would have trended positive earlier",
                "Fewer dissenting replies in subsequent rounds",
            ],
        },
        "impact_assessment": {
            "consensus_delta": consensus_delta,
            "sentiment_shift": round(cf_sentiment - actual_sentiment, 2),
            "affected_agents": affected,
            "pivotal": confidence > 70,
        },
        "confidence": confidence,
        "narrative": (
            f"This was a {'pivotal' if confidence > 70 else 'moderately influential'} moment in the simulation. "
            f"{agent_name}'s action in round {round_num} set the tone for subsequent interactions. "
            f"Had they taken the alternative path, our analysis suggests the group would have reached "
            f"consensus approximately {consensus_delta} round{'s' if consensus_delta != 1 else ''} earlier, "
            f"with an overall sentiment shift of +{round(cf_sentiment - actual_sentiment, 2):.2f}. "
            f"This estimate carries a confidence level of {confidence}%."
        ),
        "_mock": True,
    }


def analyze_counterfactual(
    decision_point: Dict[str, Any],
    actions_context: List[Dict[str, Any]],
    agent_profiles: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Analyze a counterfactual scenario for a simulation decision point.

    Args:
        decision_point: {agent_name, round_num, action_type, content, alternative}
        actions_context: List of surrounding actions for context
        agent_profiles: Optional list of agent profiles

    Returns:
        Analysis dict with actual_outcome, counterfactual_outcome, impact_assessment,
        confidence, and narrative.
    """
    if not Config.LLM_API_KEY:
        logger.info("No LLM key configured — returning mock counterfactual analysis")
        return _generate_mock_analysis(decision_point, actions_context)

    try:
        from ..utils.llm_client import LLMClient
        llm = LLMClient()
        messages = _build_prompt(decision_point, actions_context, agent_profiles or [])
        result = llm.chat_json(messages=messages, temperature=0.4, max_tokens=2048)
        return result
    except Exception as e:
        logger.warning(f"LLM counterfactual analysis failed, falling back to mock: {e}")
        return _generate_mock_analysis(decision_point, actions_context)
