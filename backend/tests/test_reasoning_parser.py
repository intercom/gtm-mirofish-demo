"""Tests for app.services.reasoning_parser — multi-format LLM response parsing."""

import json
import pytest

from app.services.reasoning_parser import (
    ReasoningParser,
    ParsedReasoning,
    ReasoningStep,
    LogicLink,
    StepType,
)


@pytest.fixture
def parser():
    return ReasoningParser()


class TestStepType:
    def test_enum_values(self):
        assert StepType.OBSERVATION == "observation"
        assert StepType.INFERENCE == "inference"
        assert StepType.EVALUATION == "evaluation"
        assert StepType.DECISION == "decision"
        assert StepType.JUSTIFICATION == "justification"


class TestReasoningStep:
    def test_to_dict(self):
        step = ReasoningStep(step_type="observation", content="test", confidence=0.8)
        d = step.to_dict()
        assert d == {"step_type": "observation", "content": "test", "confidence": 0.8}

    def test_default_confidence(self):
        step = ReasoningStep(step_type="decision", content="choose A")
        assert step.confidence == 0.5


class TestParsedReasoning:
    def test_to_dict(self):
        pr = ParsedReasoning(
            thought="thinking...",
            message="result",
            decision="choose A",
            sentiment="positive",
            reasoning_steps=[ReasoningStep("observation", "I see X")],
        )
        d = pr.to_dict()
        assert d["thought"] == "thinking..."
        assert d["message"] == "result"
        assert d["unparsed"] is False
        assert len(d["reasoning_steps"]) == 1


class TestLogicLink:
    def test_to_dict(self):
        link = LogicLink(cause="A happened", effect="B followed", step_type="observation → inference")
        d = link.to_dict()
        assert d["cause"] == "A happened"
        assert d["effect"] == "B followed"


class TestParseJSON:
    def test_parses_json_with_thought_and_decision(self, parser):
        response = json.dumps({
            "thought": "The data shows growth",
            "decision": "Recommend expansion",
            "message": "We should expand",
        })
        result = parser.parse_response(response)
        assert result.thought == "The data shows growth"
        assert result.decision == "Recommend expansion"
        assert result.unparsed is False

    def test_parses_json_with_steps_array(self, parser):
        response = json.dumps({
            "reasoning_steps": [
                {"step_type": "observation", "content": "Revenue is up", "confidence": 0.9},
                {"step_type": "decision", "content": "Proceed with plan"},
            ]
        })
        result = parser.parse_response(response)
        assert len(result.reasoning_steps) == 2
        assert result.reasoning_steps[0].content == "Revenue is up"
        assert result.reasoning_steps[0].confidence == 0.9

    def test_parses_json_in_code_fence(self, parser):
        response = '```json\n{"thought": "test", "decision": "decide"}\n```'
        result = parser.parse_response(response)
        assert result.thought == "test"
        assert result.unparsed is False

    def test_ignores_json_without_reasoning_keys(self, parser):
        response = json.dumps({"name": "Alice", "age": 30})
        result = parser.parse_response(response)
        assert result.unparsed is True

    def test_extracts_json_embedded_in_text(self, parser):
        response = 'Here is my analysis: {"thought": "deep analysis", "decision": "go ahead"} That is all.'
        result = parser.parse_response(response)
        assert result.thought == "deep analysis"

    def test_parses_steps_as_strings(self, parser):
        response = json.dumps({
            "thought": "thinking",
            "steps": ["First I noticed X", "Then I concluded Y"],
        })
        result = parser.parse_response(response)
        assert len(result.reasoning_steps) >= 2


class TestParseXML:
    def test_parses_xml_tags(self, parser):
        response = """
        <thinking>I need to evaluate the market</thinking>
        <decision>We should enter the market</decision>
        The market looks promising.
        """
        result = parser.parse_response(response)
        assert result.thought == "I need to evaluate the market"
        assert result.decision == "We should enter the market"
        assert result.unparsed is False

    def test_extracts_reasoning_steps_from_tags(self, parser):
        response = """
        <observation>Sales are declining</observation>
        <inference>Competition is increasing</inference>
        <evaluation>Current strategy insufficient</evaluation>
        <decision>Pivot to new market</decision>
        """
        result = parser.parse_response(response)
        assert len(result.reasoning_steps) == 4
        types = [s.step_type for s in result.reasoning_steps]
        assert StepType.OBSERVATION in types
        assert StepType.INFERENCE in types
        assert StepType.DECISION in types

    def test_text_outside_tags_becomes_message(self, parser):
        response = """
        <thinking>Analyzing data</thinking>
        This is my final answer about the topic.
        """
        result = parser.parse_response(response)
        assert "final answer" in result.message

    def test_empty_tags_skipped(self, parser):
        response = "<thinking></thinking><decision>Do X</decision>"
        result = parser.parse_response(response)
        assert len(result.reasoning_steps) == 1


class TestParseSections:
    def test_parses_markdown_headers(self, parser):
        response = """## Observation
The user base is growing rapidly.

## Decision
We should scale our infrastructure.
"""
        result = parser.parse_response(response)
        assert result.thought == "The user base is growing rapidly."
        assert result.decision == "We should scale our infrastructure."
        assert result.unparsed is False

    def test_parses_bold_headers(self, parser):
        response = """**Thinking:** The metrics indicate improvement.

**Decision:** Continue the current strategy.
"""
        result = parser.parse_response(response)
        assert "metrics indicate improvement" in result.thought
        assert result.unparsed is False


class TestFallback:
    def test_unparsed_plain_text(self, parser):
        response = "I think we should proceed with the plan."
        result = parser.parse_response(response)
        assert result.unparsed is True
        assert result.message == response
        assert result.raw_response == response

    def test_empty_response(self, parser):
        result = parser.parse_response("")
        assert result.unparsed is True

    def test_none_response(self, parser):
        result = parser.parse_response(None)
        assert result.unparsed is True

    def test_whitespace_only(self, parser):
        result = parser.parse_response("   \n  ")
        assert result.unparsed is True


class TestSentimentClassification:
    def test_positive_sentiment(self, parser):
        response = "This is excellent and innovative, a strong opportunity for growth"
        result = parser.parse_response(response)
        assert result.sentiment == "positive"

    def test_negative_sentiment(self, parser):
        response = "This is problematic and risky, a poor threat with decline"
        result = parser.parse_response(response)
        assert result.sentiment == "negative"

    def test_neutral_sentiment(self, parser):
        response = "The sky is blue and the grass is green"
        result = parser.parse_response(response)
        assert result.sentiment == "neutral"


class TestExtractLogicChain:
    def test_pairs_consecutive_steps(self, parser):
        steps = [
            ReasoningStep("observation", "Revenue dropped 20%"),
            ReasoningStep("inference", "Market conditions changed"),
            ReasoningStep("decision", "Adjust pricing strategy"),
        ]
        chain = parser.extract_logic_chain(steps)
        assert len(chain) == 2
        assert chain[0].cause == "Revenue dropped 20%"
        assert chain[0].effect == "Market conditions changed"
        assert chain[1].cause == "Market conditions changed"
        assert chain[1].effect == "Adjust pricing strategy"

    def test_single_step_returns_empty(self, parser):
        steps = [ReasoningStep("observation", "Just one step")]
        assert parser.extract_logic_chain(steps) == []

    def test_empty_steps_returns_empty(self, parser):
        assert parser.extract_logic_chain([]) == []


class TestIdentifyAssumptions:
    def test_detects_assuming_keyword(self, parser):
        steps = [
            ReasoningStep("inference", "Assuming that the market will recover by next quarter, we should hold.")
        ]
        assumptions = parser.identify_assumptions(steps)
        assert len(assumptions) >= 1
        assert any("market" in a.lower() for a in assumptions)

    def test_detects_conditional(self, parser):
        steps = [
            ReasoningStep("inference", "If the user growth continues at current rates, we can expand.")
        ]
        assumptions = parser.identify_assumptions(steps)
        assert len(assumptions) >= 1

    def test_no_assumptions_in_plain_text(self, parser):
        steps = [
            ReasoningStep("observation", "The data shows a clear upward trend in revenue.")
        ]
        assumptions = parser.identify_assumptions(steps)
        assert len(assumptions) == 0

    def test_deduplicates_assumptions(self, parser):
        steps = [
            ReasoningStep("inference", "Assuming that costs remain stable throughout the year."),
            ReasoningStep("evaluation", "Assuming that costs remain stable throughout the year."),
        ]
        assumptions = parser.identify_assumptions(steps)
        assert len(assumptions) == 1


class TestNormalizeStepType:
    def test_canonical_types(self, parser):
        assert parser._normalize_step_type("observation") == "observation"
        assert parser._normalize_step_type("inference") == "inference"
        assert parser._normalize_step_type("decision") == "decision"

    def test_synonyms(self, parser):
        assert parser._normalize_step_type("thinking") == "observation"
        assert parser._normalize_step_type("analysis") == "inference"
        assert parser._normalize_step_type("action") == "decision"
        assert parser._normalize_step_type("rationale") == "justification"

    def test_unknown_defaults_to_observation(self, parser):
        assert parser._normalize_step_type("unknown_type") == "observation"
