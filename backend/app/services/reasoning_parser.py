"""
Agent Reasoning Parser

Parses LLM agent responses to extract structured reasoning steps.
Supports multiple LLM output formats: Claude (XML tags), GPT (JSON), Gemini (structured text).
Falls back gracefully to raw response with 'unparsed' flag when parsing fails.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.reasoning_parser')


class StepType(str, Enum):
    """Reasoning step types"""
    OBSERVATION = "observation"
    INFERENCE = "inference"
    EVALUATION = "evaluation"
    DECISION = "decision"
    JUSTIFICATION = "justification"


@dataclass
class ReasoningStep:
    """A single reasoning step extracted from an agent response"""
    step_type: str
    content: str
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_type": self.step_type,
            "content": self.content,
            "confidence": self.confidence,
        }


@dataclass
class ParsedReasoning:
    """Complete parsed reasoning from an agent response"""
    thought: str = ""
    message: str = ""
    decision: str = ""
    sentiment: str = ""
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    unparsed: bool = False
    raw_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought": self.thought,
            "message": self.message,
            "decision": self.decision,
            "sentiment": self.sentiment,
            "reasoning_steps": [s.to_dict() for s in self.reasoning_steps],
            "unparsed": self.unparsed,
            "raw_response": self.raw_response,
        }


@dataclass
class LogicLink:
    """A single cause-and-effect link in a logic chain"""
    cause: str
    effect: str
    step_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause": self.cause,
            "effect": self.effect,
            "step_type": self.step_type,
        }


# Keywords for sentiment classification
_POSITIVE_WORDS = frozenset([
    'impressive', 'excellent', 'resolved', 'improved', 'saved', 'great',
    'effective', 'successful', 'beneficial', 'strong', 'positive', 'optimistic',
    'confident', 'advantage', 'opportunity', 'growth', 'innovative', 'promising',
])
_NEGATIVE_WORDS = frozenset([
    'frustrated', 'failed', 'struggled', 'concerned', 'risk', 'poor',
    'ineffective', 'problematic', 'weak', 'negative', 'pessimistic', 'threat',
    'decline', 'loss', 'difficult', 'obstacle', 'worried', 'disappointing',
])

# XML tag patterns for Claude-style output
_XML_TAG_PATTERN = re.compile(
    r'<(thinking|thought|observation|reasoning|decision|evaluation|'
    r'inference|justification|analysis|conclusion|message|action|reflection)>'
    r'(.*?)'
    r'</\1>',
    re.DOTALL | re.IGNORECASE,
)

# Step type mapping from tag names to canonical StepType values
_TAG_TO_STEP_TYPE = {
    'thinking': StepType.OBSERVATION,
    'thought': StepType.OBSERVATION,
    'observation': StepType.OBSERVATION,
    'reasoning': StepType.INFERENCE,
    'inference': StepType.INFERENCE,
    'analysis': StepType.INFERENCE,
    'evaluation': StepType.EVALUATION,
    'reflection': StepType.EVALUATION,
    'decision': StepType.DECISION,
    'action': StepType.DECISION,
    'conclusion': StepType.DECISION,
    'justification': StepType.JUSTIFICATION,
    'message': StepType.JUSTIFICATION,
}

# Section header patterns for Gemini-style structured text
_SECTION_HEADER_PATTERN = re.compile(
    r'^(?:#+\s*)?(?:\*\*)?'
    r'(Observation|Thought|Thinking|Reasoning|Inference|Analysis|'
    r'Evaluation|Reflection|Decision|Action|Conclusion|Justification|Message)'
    r'(?:\*\*)?[:\s]*(.*)$',
    re.IGNORECASE | re.MULTILINE,
)


class ReasoningParser:
    """
    Parses agent responses to extract structured reasoning steps.

    Handles three LLM output formats:
    - Claude: XML tags like <thinking>, <decision>, etc.
    - GPT: JSON objects with reasoning keys
    - Gemini: Markdown-style section headers

    Falls back to raw response with 'unparsed' flag when none match.
    """

    def parse_response(self, raw_response: str) -> ParsedReasoning:
        """
        Parse an agent response into structured reasoning.

        Tries formats in order: JSON → XML tags → section headers → fallback.

        Args:
            raw_response: Raw text response from an LLM agent.

        Returns:
            ParsedReasoning with extracted fields and reasoning_steps.
        """
        if not raw_response or not raw_response.strip():
            return ParsedReasoning(unparsed=True, raw_response=raw_response or "")

        text = raw_response.strip()

        # Try JSON first (GPT-style structured output)
        result = self._try_parse_json(text)
        if result:
            result.raw_response = raw_response
            result.sentiment = result.sentiment or self._classify_sentiment(text)
            return result

        # Try XML tags (Claude-style)
        result = self._try_parse_xml(text)
        if result:
            result.raw_response = raw_response
            result.sentiment = result.sentiment or self._classify_sentiment(text)
            return result

        # Try section headers (Gemini-style)
        result = self._try_parse_sections(text)
        if result:
            result.raw_response = raw_response
            result.sentiment = result.sentiment or self._classify_sentiment(text)
            return result

        # Fallback: return raw response as unparsed
        logger.debug("Could not parse structured reasoning, returning unparsed")
        return ParsedReasoning(
            message=text,
            sentiment=self._classify_sentiment(text),
            unparsed=True,
            raw_response=raw_response,
        )

    def extract_logic_chain(self, reasoning_steps: List[ReasoningStep]) -> List[LogicLink]:
        """
        Extract a simplified cause-and-effect chain from reasoning steps.

        Pairs consecutive steps where an earlier observation/inference
        leads to a later evaluation/decision.

        Args:
            reasoning_steps: Ordered list of ReasoningStep objects.

        Returns:
            List of LogicLink objects representing cause → effect pairs.
        """
        if len(reasoning_steps) < 2:
            return []

        chain = []
        for i in range(len(reasoning_steps) - 1):
            current = reasoning_steps[i]
            next_step = reasoning_steps[i + 1]
            chain.append(LogicLink(
                cause=current.content,
                effect=next_step.content,
                step_type=f"{current.step_type} → {next_step.step_type}",
            ))
        return chain

    def identify_assumptions(self, reasoning_steps: List[ReasoningStep]) -> List[str]:
        """
        Identify implicit assumptions from reasoning steps.

        Scans for hedging language, conditional statements, and unstated premises
        that indicate the agent is making assumptions.

        Args:
            reasoning_steps: Ordered list of ReasoningStep objects.

        Returns:
            List of assumption strings extracted from the steps.
        """
        assumption_markers = [
            (re.compile(r'(?:assuming|assume)\s+(?:that\s+)?(.{10,80}?)(?:[.,;]|$)', re.IGNORECASE), None),
            (re.compile(r'(?:if|given that|provided that)\s+(.{10,80}?)(?:,\s*then|[.,;]|$)', re.IGNORECASE), "Assumes: "),
            (re.compile(r'(?:likely|probably|presumably)\s+(.{10,80}?)(?:[.,;]|$)', re.IGNORECASE), "Implicit: "),
            (re.compile(r'(?:should|would|expect(?:ed)?)\s+(.{10,80}?)(?:[.,;]|$)', re.IGNORECASE), "Expects: "),
            (re.compile(r'(?:based on the (?:assumption|premise))\s+(?:that\s+)?(.{10,80}?)(?:[.,;]|$)', re.IGNORECASE), None),
        ]

        assumptions = []
        seen = set()

        for step in reasoning_steps:
            for pattern, prefix in assumption_markers:
                for match in pattern.finditer(step.content):
                    text = match.group(1).strip()
                    if text and text.lower() not in seen:
                        seen.add(text.lower())
                        assumptions.append(f"{prefix}{text}" if prefix else text)

        return assumptions

    # ── Private parsing methods ──────────────────────────────────

    def _try_parse_json(self, text: str) -> Optional[ParsedReasoning]:
        """Try parsing as JSON (GPT-style structured output)."""
        # Try to extract JSON from the response
        json_obj = self._extract_json(text)
        if not json_obj:
            return None

        # Must have at least one reasoning-related key
        reasoning_keys = {
            'thought', 'thinking', 'reasoning', 'observation',
            'decision', 'message', 'steps', 'reasoning_steps',
            'evaluation', 'analysis', 'conclusion',
        }
        if not any(k in json_obj for k in reasoning_keys):
            return None

        steps = []

        # Extract explicit steps array
        steps_data = json_obj.get('steps') or json_obj.get('reasoning_steps') or []
        if isinstance(steps_data, list):
            for item in steps_data:
                if isinstance(item, dict):
                    steps.append(ReasoningStep(
                        step_type=self._normalize_step_type(
                            item.get('step_type') or item.get('type', 'observation')
                        ),
                        content=str(item.get('content') or item.get('text', '')),
                        confidence=float(item.get('confidence', 0.5)),
                    ))
                elif isinstance(item, str):
                    steps.append(ReasoningStep(
                        step_type=StepType.OBSERVATION,
                        content=item,
                    ))

        # Extract reasoning from individual keys if no steps array
        if not steps:
            key_step_map = [
                (['thought', 'thinking', 'observation'], StepType.OBSERVATION),
                (['reasoning', 'inference', 'analysis'], StepType.INFERENCE),
                (['evaluation', 'reflection'], StepType.EVALUATION),
                (['decision', 'action', 'conclusion'], StepType.DECISION),
                (['justification', 'rationale', 'explanation'], StepType.JUSTIFICATION),
            ]
            for keys, step_type in key_step_map:
                for key in keys:
                    val = json_obj.get(key)
                    if val and isinstance(val, str):
                        steps.append(ReasoningStep(
                            step_type=step_type,
                            content=val,
                        ))
                        break

        thought = str(json_obj.get('thought') or json_obj.get('thinking') or json_obj.get('observation') or '')
        decision = str(json_obj.get('decision') or json_obj.get('action') or json_obj.get('conclusion') or '')
        message = str(json_obj.get('message') or json_obj.get('response') or json_obj.get('output') or '')
        sentiment = str(json_obj.get('sentiment', ''))

        return ParsedReasoning(
            thought=thought,
            message=message or decision,
            decision=decision,
            sentiment=sentiment,
            reasoning_steps=steps,
        )

    def _try_parse_xml(self, text: str) -> Optional[ParsedReasoning]:
        """Try parsing XML-tagged output (Claude-style)."""
        matches = _XML_TAG_PATTERN.findall(text)
        if not matches:
            return None

        steps = []
        thought = ""
        decision = ""
        message = ""

        for tag_name, content in matches:
            tag_lower = tag_name.lower()
            content = content.strip()
            if not content:
                continue

            step_type = _TAG_TO_STEP_TYPE.get(tag_lower, StepType.OBSERVATION)
            steps.append(ReasoningStep(step_type=step_type, content=content))

            if tag_lower in ('thinking', 'thought', 'observation') and not thought:
                thought = content
            elif tag_lower in ('decision', 'action', 'conclusion') and not decision:
                decision = content
            elif tag_lower == 'message' and not message:
                message = content

        if not steps:
            return None

        # Any text outside XML tags is the message if not already captured
        if not message:
            outside_text = _XML_TAG_PATTERN.sub('', text).strip()
            if outside_text:
                message = outside_text

        return ParsedReasoning(
            thought=thought,
            message=message or decision,
            decision=decision,
            reasoning_steps=steps,
        )

    def _try_parse_sections(self, text: str) -> Optional[ParsedReasoning]:
        """Try parsing section-header structured text (Gemini-style)."""
        matches = list(_SECTION_HEADER_PATTERN.finditer(text))
        if not matches:
            return None

        steps = []
        thought = ""
        decision = ""
        message = ""

        for i, match in enumerate(matches):
            header = match.group(1).lower()
            # Content runs from after this header to the next header (or end)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            # Include inline content from the header line itself
            inline = match.group(2).strip()
            if inline and content:
                content = f"{inline}\n{content}"
            elif inline:
                content = inline

            if not content:
                continue

            step_type = _TAG_TO_STEP_TYPE.get(header, StepType.OBSERVATION)
            steps.append(ReasoningStep(step_type=step_type, content=content))

            if header in ('thinking', 'thought', 'observation') and not thought:
                thought = content
            elif header in ('decision', 'action', 'conclusion') and not decision:
                decision = content
            elif header == 'message' and not message:
                message = content

        if not steps:
            return None

        return ParsedReasoning(
            thought=thought,
            message=message or decision,
            decision=decision,
            reasoning_steps=steps,
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a JSON object from text, handling markdown code fences."""
        # Try direct parse first
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except (json.JSONDecodeError, ValueError):
            pass

        # Try stripping markdown code fences
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
        if cleaned != text:
            try:
                obj = json.loads(cleaned)
                if isinstance(obj, dict):
                    return obj
            except (json.JSONDecodeError, ValueError):
                pass

        # Try extracting first JSON object from within text
        brace_match = re.search(r'\{', text)
        if brace_match:
            start = brace_match.start()
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(text[start:i + 1])
                            if isinstance(obj, dict):
                                return obj
                        except (json.JSONDecodeError, ValueError):
                            pass
                        break

        return None

    def _normalize_step_type(self, raw_type: str) -> str:
        """Normalize a step type string to a canonical StepType value."""
        normalized = raw_type.lower().strip()
        for step_type in StepType:
            if step_type.value == normalized:
                return step_type.value
        # Map common synonyms
        synonyms = {
            'thought': StepType.OBSERVATION,
            'thinking': StepType.OBSERVATION,
            'analysis': StepType.INFERENCE,
            'reasoning': StepType.INFERENCE,
            'reflection': StepType.EVALUATION,
            'action': StepType.DECISION,
            'conclusion': StepType.DECISION,
            'rationale': StepType.JUSTIFICATION,
            'explanation': StepType.JUSTIFICATION,
        }
        return synonyms.get(normalized, StepType.OBSERVATION).value

    def _classify_sentiment(self, text: str) -> str:
        """Classify overall sentiment of text as positive/negative/neutral."""
        words = set(re.findall(r'[a-z]+', text.lower()))
        pos = len(words & _POSITIVE_WORDS)
        neg = len(words & _NEGATIVE_WORDS)

        if pos > neg + 1:
            return "positive"
        elif neg > pos + 1:
            return "negative"
        return "neutral"
