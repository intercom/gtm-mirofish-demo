"""
ReportAgent Execution Engine

Higher-level orchestrator for generating typed analysis reports using a ReACT
(Reasoning + Acting) pattern with a global tool budget.

Report types:
  - executive_summary: concise 3-section overview
  - detailed_analysis: deep-dive with 5 sections
  - agent_comparison: side-by-side agent behavior analysis
  - decision_audit: decision trail with evidence
  - custom: user-defined prompt drives structure

Unlike the per-section ReACT loops in report_agent.py, this engine runs a
single planning + gathering phase with a hard cap of 10 tool calls, then
compiles all observations into structured sections in one pass.
"""

import json
import re
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .zep_tools import ZepToolsService

logger = get_logger('mirofish.report_agent_engine')


# ═══════════════════════════════════════════════════════════════
# Data types
# ═══════════════════════════════════════════════════════════════

class ReportType(str, Enum):
    EXECUTIVE_SUMMARY = 'executive_summary'
    DETAILED_ANALYSIS = 'detailed_analysis'
    AGENT_COMPARISON = 'agent_comparison'
    DECISION_AUDIT = 'decision_audit'
    CUSTOM = 'custom'


@dataclass
class ToolCallRecord:
    tool_name: str
    parameters: Dict[str, Any]
    result_preview: str
    timestamp: str
    iteration: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'parameters': self.parameters,
            'result_preview': self.result_preview,
            'timestamp': self.timestamp,
            'iteration': self.iteration,
        }


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 0

    def track(self, prompt_text: str, completion_text: str):
        p = len(prompt_text) // 4
        c = len(completion_text) // 4
        self.prompt_tokens += p
        self.completion_tokens += c
        self.total_tokens += p + c
        self.llm_calls += 1

    def to_dict(self) -> Dict[str, int]:
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'llm_calls': self.llm_calls,
        }


@dataclass
class EngineResult:
    success: bool
    report_type: str
    title: str
    sections: List[Dict[str, str]]
    markdown: str
    tool_call_history: List[Dict[str, Any]]
    token_usage: Dict[str, int]
    generation_time_seconds: float
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'report_type': self.report_type,
            'title': self.title,
            'sections': self.sections,
            'markdown': self.markdown,
            'tool_call_history': self.tool_call_history,
            'token_usage': self.token_usage,
            'generation_time_seconds': round(self.generation_time_seconds, 2),
            'error': self.error,
        }


# ═══════════════════════════════════════════════════════════════
# Report type configurations
# ═══════════════════════════════════════════════════════════════

REPORT_TYPE_CONFIGS: Dict[ReportType, Dict[str, Any]] = {
    ReportType.EXECUTIVE_SUMMARY: {
        'title_suffix': 'Executive Summary',
        'section_templates': [
            {'title': 'Key Findings', 'focus': 'top-line simulation results and critical insights'},
            {'title': 'Impact Assessment', 'focus': 'who is affected and how — agent behavior patterns'},
            {'title': 'Recommendations', 'focus': 'actionable next steps based on simulation outcomes'},
        ],
    },
    ReportType.DETAILED_ANALYSIS: {
        'title_suffix': 'Detailed Analysis',
        'section_templates': [
            {'title': 'Simulation Overview', 'focus': 'scenario setup, parameters, and scope'},
            {'title': 'Agent Behavior Patterns', 'focus': 'how different agent types behaved during simulation'},
            {'title': 'Key Events & Turning Points', 'focus': 'critical moments that shaped outcomes'},
            {'title': 'Quantitative Findings', 'focus': 'metrics, counts, and statistical observations'},
            {'title': 'Conclusions & Recommendations', 'focus': 'synthesis of findings and suggested actions'},
        ],
    },
    ReportType.AGENT_COMPARISON: {
        'title_suffix': 'Agent Comparison',
        'section_templates': [
            {'title': 'Agent Overview', 'focus': 'types of agents, their roles, and initial conditions'},
            {'title': 'Behavioral Comparison', 'focus': 'side-by-side analysis of agent actions and strategies'},
            {'title': 'Interaction Dynamics', 'focus': 'how agents influenced each other'},
            {'title': 'Performance Assessment', 'focus': 'which agent types were most/least effective and why'},
        ],
    },
    ReportType.DECISION_AUDIT: {
        'title_suffix': 'Decision Audit',
        'section_templates': [
            {'title': 'Decision Timeline', 'focus': 'chronological sequence of key decisions agents made'},
            {'title': 'Decision Rationale', 'focus': 'why agents made specific choices — evidence trail'},
            {'title': 'Outcome Analysis', 'focus': 'consequences of each major decision'},
            {'title': 'Audit Summary', 'focus': 'patterns, biases, and lessons from the decision trail'},
        ],
    },
    ReportType.CUSTOM: {
        'title_suffix': 'Analysis Report',
        'section_templates': [
            {'title': 'Overview', 'focus': 'context and scope of the analysis'},
            {'title': 'Findings', 'focus': 'detailed findings based on the custom analysis prompt'},
            {'title': 'Summary', 'focus': 'key takeaways and recommendations'},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# Prompt templates
# ═══════════════════════════════════════════════════════════════

REACT_SYSTEM_PROMPT = """\
You are a report-writing agent with access to a simulated world's knowledge graph.
Your task is to gather information by calling tools, then compile your findings
into a structured report.

Simulation scenario: {simulation_requirement}
Report type: {report_type} — {title_suffix}

Sections to produce:
{sections_spec}

You have a budget of {remaining_budget} tool calls. Use them wisely to gather
evidence for ALL sections before writing.

Available tools (call one at a time):
1. insight_forge(query, report_context) — deep multi-dimensional retrieval
2. panorama_search(query, include_expired) — breadth-first full context search
3. quick_search(query, limit) — fast semantic search
4. interview_agents(interview_topic, max_agents) — interview simulated agents

Workflow:
- THINK about what information each section needs
- CALL tools to gather that information (one tool per response)
- After gathering enough data, output "COMPILE_REPORT" followed by the full
  report in Markdown with all sections

Tool call format:
<tool_call>{{"name": "tool_name", "parameters": {{"key": "value"}}}}</tool_call>

Report output format (when ready):
COMPILE_REPORT
# Report Title
## Section Title
Content...

Rules:
- Each response: EITHER one tool call OR the final report. Never both.
- Reference specific agent quotes and facts from tool results.
- Max {max_tool_calls} tool calls total. Plan ahead."""

REACT_OBSERVATION_MSG = """\
Tool result from {tool_name}:
{result}

Tool calls used: {used}/{budget}. {hint}"""

REACT_FORCE_COMPILE_MSG = """\
Tool budget exhausted. You MUST now output the final report using all gathered
information. Start your response with COMPILE_REPORT followed by the full
Markdown report with all required sections."""

COMPILE_SYSTEM_PROMPT = """\
You are a report compiler. Given the gathered observations below, produce a
well-structured Markdown report.

Simulation scenario: {simulation_requirement}
Report type: {report_type}

Required sections:
{sections_spec}

Use specific quotes and data points from the observations. Write clearly and
concisely. Output ONLY the Markdown report, starting with a # title."""


# ═══════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════

class ReportAgentEngine:
    """
    Execution engine for generating typed analysis reports.

    Uses a ReACT (Reasoning + Acting) pattern with a global tool budget
    of 10 calls per report. Supports 5 report types and falls back to
    template-based generation when no LLM is available.
    """

    MAX_TOOL_CALLS = 10
    MAX_ITERATIONS = 20
    VALID_TOOL_NAMES = {'insight_forge', 'panorama_search', 'quick_search', 'interview_agents'}

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None,
    ):
        self.llm = llm_client
        self.zep_tools = zep_tools
        self._llm_available = self._check_llm_available(llm_client)

    @staticmethod
    def _check_llm_available(llm_client: Optional[LLMClient]) -> bool:
        if llm_client is not None:
            return True
        return bool(Config.LLM_API_KEY)

    # ── public API ──────────────────────────────────────────

    def generate_report(
        self,
        simulation_id: str,
        report_type: str = 'detailed_analysis',
        custom_prompt: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> EngineResult:
        """
        Main entry point for report generation.

        Args:
            simulation_id: ID of the simulation to report on.
            report_type: One of the 5 supported report types.
            custom_prompt: Optional prompt override (used with 'custom' type).
            progress_callback: Optional (stage, percent, message) callback.

        Returns:
            EngineResult with report content, tool history, and token usage.
        """
        start = datetime.now()
        token_usage = TokenUsage()
        tool_history: List[ToolCallRecord] = []

        # Validate report type
        try:
            rtype = ReportType(report_type)
        except ValueError:
            valid = [rt.value for rt in ReportType]
            return self._error_result(
                report_type, token_usage, start,
                f"Invalid report type '{report_type}'. Must be one of: {valid}",
            )

        # Load simulation context
        sim_context = self._load_simulation_context(simulation_id)
        if sim_context is None:
            return self._error_result(
                report_type, token_usage, start,
                f"Simulation not found: {simulation_id}",
            )

        graph_id = sim_context['graph_id']
        simulation_requirement = custom_prompt or sim_context['simulation_requirement']
        if not simulation_requirement:
            return self._error_result(
                report_type, token_usage, start,
                "No simulation requirement or custom prompt provided.",
            )

        config = REPORT_TYPE_CONFIGS[rtype]
        title = f"{simulation_requirement[:80]} — {config['title_suffix']}"

        if progress_callback:
            progress_callback('initializing', 0, 'Loading simulation context...')

        # Fallback: template-based report when LLM unavailable
        if not self._llm_available:
            logger.info("LLM unavailable — generating template-based fallback report")
            return self._generate_fallback_report(
                rtype, config, title, graph_id, simulation_requirement,
                token_usage, start, progress_callback,
            )

        # Ensure LLM client is initialized
        if self.llm is None:
            self.llm = LLMClient()
        if self.zep_tools is None:
            self.zep_tools = ZepToolsService()

        # Run ReACT loop
        return self._run_react_loop(
            rtype, config, title, graph_id, simulation_id,
            simulation_requirement, token_usage, tool_history,
            start, progress_callback,
        )

    # ── ReACT loop ──────────────────────────────────────────

    def _run_react_loop(
        self,
        rtype: ReportType,
        config: Dict[str, Any],
        title: str,
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        token_usage: TokenUsage,
        tool_history: List[ToolCallRecord],
        start: datetime,
        progress_callback: Optional[Callable],
    ) -> EngineResult:
        sections_spec = self._build_sections_spec(config)
        tool_calls_used = 0
        observations: List[Dict[str, str]] = []

        system_prompt = REACT_SYSTEM_PROMPT.format(
            simulation_requirement=simulation_requirement,
            report_type=rtype.value,
            title_suffix=config['title_suffix'],
            sections_spec=sections_spec,
            remaining_budget=self.MAX_TOOL_CALLS,
            max_tool_calls=self.MAX_TOOL_CALLS,
        )

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': (
                f"Generate a {rtype.value} report for this simulation. "
                f"Start by gathering information with tool calls, then compile the report.\n\n"
                f"Simulation requirement: {simulation_requirement}"
            )},
        ]

        if progress_callback:
            progress_callback('gathering', 5, 'Starting information gathering...')

        for iteration in range(self.MAX_ITERATIONS):
            # Call LLM
            prompt_text = json.dumps(messages)
            response = self.llm.chat(
                messages=messages,
                temperature=Config.REPORT_AGENT_TEMPERATURE,
                max_tokens=4096,
            )

            if response is None:
                logger.warning(f"LLM returned None on iteration {iteration + 1}")
                if iteration < self.MAX_ITERATIONS - 1:
                    messages.append({'role': 'assistant', 'content': '(empty response)'})
                    messages.append({'role': 'user', 'content': 'Please continue.'})
                    continue
                break

            token_usage.track(prompt_text, response)

            # Check for final report
            has_compile = 'COMPILE_REPORT' in response
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)

            # Conflict: both tool call and compile in same response
            if has_tool_calls and has_compile:
                messages.append({'role': 'assistant', 'content': response})
                messages.append({'role': 'user', 'content': (
                    "Error: you included both a tool call and COMPILE_REPORT in the same "
                    "response. Please do ONLY one: either call a tool OR output the final report."
                )})
                continue

            # Final report compiled
            if has_compile:
                report_md = response.split('COMPILE_REPORT', 1)[1].strip()
                sections = self._parse_markdown_sections(report_md)
                elapsed = (datetime.now() - start).total_seconds()

                if progress_callback:
                    progress_callback('completed', 100, 'Report generation complete.')

                return EngineResult(
                    success=True,
                    report_type=rtype.value,
                    title=title,
                    sections=sections,
                    markdown=report_md,
                    tool_call_history=[r.to_dict() for r in tool_history],
                    token_usage=token_usage.to_dict(),
                    generation_time_seconds=elapsed,
                )

            # Tool call
            if has_tool_calls:
                if tool_calls_used >= self.MAX_TOOL_CALLS:
                    messages.append({'role': 'assistant', 'content': response})
                    messages.append({'role': 'user', 'content': REACT_FORCE_COMPILE_MSG})
                    continue

                call = tool_calls[0]
                tool_name = call.get('name', '')
                params = call.get('parameters', {})

                logger.info(f"Iteration {iteration + 1}: calling {tool_name}")
                result = self._execute_tool(
                    tool_name, params, graph_id, simulation_id,
                    simulation_requirement,
                )

                tool_calls_used += 1
                observations.append({
                    'tool': tool_name,
                    'query': params.get('query', params.get('interview_topic', '')),
                    'result': result,
                })
                tool_history.append(ToolCallRecord(
                    tool_name=tool_name,
                    parameters=params,
                    result_preview=result[:500],
                    timestamp=datetime.now().isoformat(),
                    iteration=iteration + 1,
                ))

                remaining = self.MAX_TOOL_CALLS - tool_calls_used
                hint = (
                    f"{remaining} tool calls remaining."
                    if remaining > 0
                    else "No tool calls remaining — compile the report next."
                )

                if progress_callback:
                    pct = 5 + int((tool_calls_used / self.MAX_TOOL_CALLS) * 60)
                    progress_callback(
                        'gathering', pct,
                        f"Called {tool_name} ({tool_calls_used}/{self.MAX_TOOL_CALLS})",
                    )

                messages.append({'role': 'assistant', 'content': response})
                messages.append({'role': 'user', 'content': REACT_OBSERVATION_MSG.format(
                    tool_name=tool_name,
                    result=result[:6000],
                    used=tool_calls_used,
                    budget=self.MAX_TOOL_CALLS,
                    hint=hint,
                )})
                continue

            # Neither tool call nor compile — nudge LLM
            messages.append({'role': 'assistant', 'content': response})
            if tool_calls_used >= self.MAX_TOOL_CALLS:
                messages.append({'role': 'user', 'content': REACT_FORCE_COMPILE_MSG})
            else:
                messages.append({'role': 'user', 'content': (
                    "Please either call a tool to gather more information, or if you "
                    "have enough data, output COMPILE_REPORT followed by the full report."
                )})

        # Loop exhausted — attempt a compile from observations
        logger.warning("ReACT loop exhausted, forcing compilation from gathered observations")
        return self._compile_from_observations(
            rtype, config, title, simulation_requirement,
            observations, token_usage, tool_history, start, progress_callback,
        )

    # ── Tool execution ──────────────────────────────────────

    def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
    ) -> str:
        try:
            if tool_name == 'insight_forge':
                result = self.zep_tools.insight_forge(
                    graph_id=graph_id,
                    query=parameters.get('query', ''),
                    simulation_requirement=simulation_requirement,
                    report_context=parameters.get('report_context', ''),
                )
                return result.to_text()

            elif tool_name == 'panorama_search':
                include_expired = parameters.get('include_expired', True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ('true', '1', 'yes')
                result = self.zep_tools.panorama_search(
                    graph_id=graph_id,
                    query=parameters.get('query', ''),
                    include_expired=include_expired,
                )
                return result.to_text()

            elif tool_name == 'quick_search':
                limit = parameters.get('limit', 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result = self.zep_tools.quick_search(
                    graph_id=graph_id,
                    query=parameters.get('query', ''),
                    limit=limit,
                )
                return result.to_text()

            elif tool_name == 'interview_agents':
                topic = parameters.get('interview_topic', parameters.get('query', ''))
                max_agents = min(int(parameters.get('max_agents', 5)), 10)
                result = self.zep_tools.interview_agents(
                    simulation_id=simulation_id,
                    interview_requirement=topic,
                    simulation_requirement=simulation_requirement,
                    max_agents=max_agents,
                )
                return result.to_text()

            else:
                return f"Unknown tool: {tool_name}. Use: insight_forge, panorama_search, quick_search, interview_agents"

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} — {e}")
            return f"Tool execution failed: {e}"

    # ── Compile from observations (fallback when loop exhausts) ─

    def _compile_from_observations(
        self,
        rtype: ReportType,
        config: Dict[str, Any],
        title: str,
        simulation_requirement: str,
        observations: List[Dict[str, str]],
        token_usage: TokenUsage,
        tool_history: List[ToolCallRecord],
        start: datetime,
        progress_callback: Optional[Callable],
    ) -> EngineResult:
        if progress_callback:
            progress_callback('compiling', 80, 'Compiling report from observations...')

        sections_spec = self._build_sections_spec(config)
        obs_text = '\n\n---\n\n'.join(
            f"[{o['tool']}] query={o['query']}\n{o['result'][:4000]}"
            for o in observations
        )

        messages = [
            {'role': 'system', 'content': COMPILE_SYSTEM_PROMPT.format(
                simulation_requirement=simulation_requirement,
                report_type=rtype.value,
                sections_spec=sections_spec,
            )},
            {'role': 'user', 'content': f"Observations:\n\n{obs_text}\n\nCompile the report now."},
        ]

        prompt_text = json.dumps(messages)
        response = self.llm.chat(
            messages=messages,
            temperature=Config.REPORT_AGENT_TEMPERATURE,
            max_tokens=4096,
        )
        token_usage.track(prompt_text, response or '')

        report_md = (response or '').strip()
        sections = self._parse_markdown_sections(report_md)
        elapsed = (datetime.now() - start).total_seconds()

        if progress_callback:
            progress_callback('completed', 100, 'Report generation complete.')

        return EngineResult(
            success=True,
            report_type=rtype.value,
            title=title,
            sections=sections,
            markdown=report_md,
            tool_call_history=[r.to_dict() for r in tool_history],
            token_usage=token_usage.to_dict(),
            generation_time_seconds=elapsed,
        )

    # ── Template fallback (no LLM) ─────────────────────────

    def _generate_fallback_report(
        self,
        rtype: ReportType,
        config: Dict[str, Any],
        title: str,
        graph_id: str,
        simulation_requirement: str,
        token_usage: TokenUsage,
        start: datetime,
        progress_callback: Optional[Callable],
    ) -> EngineResult:
        """Generate a template-based report from raw Zep data without LLM."""
        if progress_callback:
            progress_callback('gathering', 10, 'Fetching simulation data (no LLM)...')

        if self.zep_tools is None:
            self.zep_tools = ZepToolsService()

        # Gather raw data
        raw_data = {}
        try:
            raw_data['statistics'] = self.zep_tools.get_graph_statistics(graph_id)
        except Exception as e:
            raw_data['statistics'] = {'error': str(e)}

        try:
            search_result = self.zep_tools.quick_search(
                graph_id=graph_id,
                query=simulation_requirement,
                limit=20,
            )
            raw_data['search'] = search_result.to_text()
        except Exception as e:
            raw_data['search'] = f"Search failed: {e}"

        if progress_callback:
            progress_callback('compiling', 50, 'Building template report...')

        # Build template sections
        stats = raw_data.get('statistics', {})
        total_nodes = stats.get('total_nodes', 'N/A')
        total_edges = stats.get('total_edges', 'N/A')
        entity_types = stats.get('entity_types', {})

        sections = []
        for tmpl in config['section_templates']:
            content = (
                f"*Focus: {tmpl['focus']}*\n\n"
                f"**Simulation scenario:** {simulation_requirement}\n\n"
                f"**Graph statistics:** {total_nodes} entities, "
                f"{total_edges} relationships\n\n"
                f"**Entity types:** {', '.join(entity_types.keys()) if isinstance(entity_types, dict) else str(entity_types)}\n\n"
                f"---\n\n"
                f"*This section was generated in template mode because no LLM API key "
                f"is configured. Configure LLM_API_KEY in .env for AI-generated reports.*\n\n"
                f"**Raw search results:**\n\n{raw_data.get('search', 'No data available.')[:3000]}"
            )
            sections.append({'title': tmpl['title'], 'content': content})

        markdown = f"# {title}\n\n"
        markdown += f"> Template-based report (LLM unavailable)\n\n"
        for sec in sections:
            markdown += f"## {sec['title']}\n\n{sec['content']}\n\n"

        elapsed = (datetime.now() - start).total_seconds()

        if progress_callback:
            progress_callback('completed', 100, 'Template report complete.')

        return EngineResult(
            success=True,
            report_type=rtype.value,
            title=title,
            sections=sections,
            markdown=markdown,
            tool_call_history=[],
            token_usage=token_usage.to_dict(),
            generation_time_seconds=elapsed,
        )

    # ── Helpers ─────────────────────────────────────────────

    def _load_simulation_context(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Load simulation metadata. Returns None if simulation not found."""
        from .simulation_manager import SimulationManager
        from ..models.project import ProjectManager

        sim_manager = SimulationManager()
        state = sim_manager.get_simulation(simulation_id)
        if not state:
            return None

        project = ProjectManager.get_project(state.project_id)
        simulation_requirement = ''
        if project and project.simulation_requirement:
            simulation_requirement = project.simulation_requirement

        return {
            'graph_id': state.graph_id,
            'simulation_requirement': simulation_requirement,
            'simulation_id': simulation_id,
            'project_id': state.project_id,
        }

    @staticmethod
    def _build_sections_spec(config: Dict[str, Any]) -> str:
        lines = []
        for i, tmpl in enumerate(config['section_templates'], 1):
            lines.append(f"{i}. **{tmpl['title']}** — {tmpl['focus']}")
        return '\n'.join(lines)

    @staticmethod
    def _parse_tool_calls(response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response (XML-wrapped JSON)."""
        tool_calls = []

        # Primary: <tool_call>{...}</tool_call>
        for match in re.finditer(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', response, re.DOTALL):
            try:
                data = json.loads(match.group(1))
                if 'name' in data:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                pass

        if tool_calls:
            return tool_calls

        # Fallback: bare JSON with a valid tool name
        stripped = response.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                data = json.loads(stripped)
                if data.get('name') in ReportAgentEngine.VALID_TOOL_NAMES:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                pass

        return tool_calls

    @staticmethod
    def _parse_markdown_sections(markdown: str) -> List[Dict[str, str]]:
        """Split markdown into sections by ## headers."""
        sections = []
        current_title = None
        current_lines = []

        for line in markdown.split('\n'):
            if line.startswith('## '):
                if current_title is not None:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_lines).strip(),
                    })
                current_title = line[3:].strip()
                current_lines = []
            elif current_title is not None:
                current_lines.append(line)

        if current_title is not None:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_lines).strip(),
            })

        return sections

    @staticmethod
    def _error_result(
        report_type: str,
        token_usage: TokenUsage,
        start: datetime,
        error: str,
    ) -> EngineResult:
        return EngineResult(
            success=False,
            report_type=report_type,
            title='',
            sections=[],
            markdown='',
            tool_call_history=[],
            token_usage=token_usage.to_dict(),
            generation_time_seconds=(datetime.now() - start).total_seconds(),
            error=error,
        )
