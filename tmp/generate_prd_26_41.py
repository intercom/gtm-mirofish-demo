#!/usr/bin/env python3
"""Generate tasks for groups 26-41 (OASIS + Zep + Advanced Visualizations)."""
import json

NEW_TASKS = []

def t(group, title, desc):
    NEW_TASKS.append({"title": title, "completed": False, "parallel_group": group, "description": desc})

# ═══════════════════════════════════════════════════════
# GROUP 26: OASIS Framework Integration (8 tasks)
# ═══════════════════════════════════════════════════════
t(26, "Install and configure camel-ai OASIS dependencies",
  "Add camel-ai[all] to backend/requirements.txt if not already present. "
  "Create backend/app/services/oasis_config.py that configures the OASIS framework: "
  "1) Import from camel.agents and camel.societies. "
  "2) Define OasisConfig dataclass: num_agents, environment_type, llm_provider, max_rounds, temperature. "
  "3) Create `get_oasis_config()` that reads from environment variables with sensible defaults. "
  "4) Add LLM provider mapping: anthropic→Claude, openai→GPT-4, gemini→Gemini Pro. "
  "5) Validate that at least one LLM provider key is available, or fall back to demo mode. "
  "Test import: `python -c 'from camel.agents import ChatAgent; print(\"OASIS OK\")'`.")

t(26, "Create OASIS agent factory",
  "Create backend/app/services/oasis_agent_factory.py that builds configured OASIS agents. "
  "Define `create_agent(persona, role, llm_config)` that creates a camel ChatAgent with: "
  "- System message based on persona (name, background, personality traits, domain expertise) "
  "- LLM model configuration from llm_client.py "
  "- Temperature and max_tokens from OasisConfig "
  "Define persona templates for GTM simulation roles: "
  "Sales Rep (aggressive, quota-driven), Marketing Manager (data-driven, brand-focused), "
  "Customer Success (empathetic, retention-focused), Product Manager (feature-focused, user-centric), "
  "Finance Analyst (risk-averse, numbers-driven), Executive (strategic, growth-oriented). "
  "Each persona has 3-5 personality traits that affect their simulation behavior. "
  "Add `create_agent_team(scenario_type, num_agents)` that builds a balanced team.")

t(26, "Create OASIS environment manager",
  "Create backend/app/services/oasis_environment.py that manages simulation environments. "
  "Define EnvironmentManager class with: "
  "1) `create_environment(env_type, config)` — sets up the simulation space (GTM pipeline, market, internal meeting). "
  "2) `add_agents(environment, agents)` — places agents into the environment. "
  "3) `set_constraints(environment, rules)` — adds behavioral rules (budget limits, market conditions, competitive pressure). "
  "4) `step(environment)` — advances simulation by one time step, triggering agent interactions. "
  "5) `get_state(environment)` — returns current environment state (agent positions, interactions, metrics). "
  "Environment types: 'pipeline_review', 'deal_negotiation', 'market_simulation', 'team_standup', 'quarterly_review'. "
  "Each type has specific constraints and interaction patterns.")

t(26, "Create OASIS interaction protocol",
  "Create backend/app/services/oasis_interaction.py defining how agents interact within OASIS. "
  "Define interaction types: "
  "1) DirectMessage — one agent messages another (e.g., sales rep → customer). "
  "2) GroupDiscussion — multiple agents discuss a topic (e.g., deal review meeting). "
  "3) Broadcast — one agent broadcasts to all (e.g., marketing campaign launch). "
  "4) Reaction — agent responds to an event (e.g., competitor price change). "
  "Each interaction produces a structured InteractionResult: participants, messages, sentiment_scores, decisions_made, next_actions. "
  "Implement `run_interaction(agents, interaction_type, context)` that orchestrates the LLM calls through OASIS. "
  "Track token usage per interaction for cost monitoring.")

t(26, "Create OASIS simulation orchestrator",
  "Create backend/app/services/oasis_orchestrator.py — the main simulation loop coordinator. "
  "OasisOrchestrator class with: "
  "1) `initialize(scenario, config)` — creates environment, agents, and initial state. "
  "2) `run_round(round_number)` — executes one simulation round: each agent acts, interactions resolve, state updates. "
  "3) `run_full(max_rounds)` — runs complete simulation with progress tracking. "
  "4) `get_results()` — returns structured simulation results (rounds, interactions, metrics, agent states). "
  "5) `pause()` / `resume()` — control simulation execution. "
  "Emit events at each round for real-time streaming. "
  "Handle LLM errors gracefully — retry with backoff, skip agent on persistent failure. "
  "Log all interactions to backend/logs/ with structured JSON format.")

t(26, "Create OASIS metrics collector",
  "Create backend/app/services/oasis_metrics.py — collects and aggregates simulation metrics. "
  "Track per-round: agent sentiment scores, interaction count, decision count, consensus level, information spread. "
  "Track per-agent: total messages, avg sentiment, influence score (how often others reference them), "
  "decision participation rate, opinion change count. "
  "Track overall: simulation convergence (are opinions stabilizing?), polarization index, "
  "information cascade detection, coalition formation. "
  "Store metrics in a MetricsCollector class with `record_round(round_data)` and `get_summary()` methods. "
  "Export metrics as time-series data suitable for charting.")

t(26, "Create OASIS demo mode fallback",
  "Create backend/app/services/oasis_demo.py — generates realistic mock simulation data when OASIS/LLM is unavailable. "
  "DemoSimulator class that mimics the OasisOrchestrator interface but uses pre-generated data. "
  "Generate 10 rounds of realistic interactions with: "
  "- Message content from templates with variable substitution (agent name, product, metric values). "
  "- Sentiment scores following a natural arc (start neutral, diverge, reconverge). "
  "- Decision points at rounds 3, 6, 9 with realistic outcomes. "
  "- Metric progressions that tell a coherent story. "
  "The demo mode should be indistinguishable from real simulation in the frontend. "
  "Activate automatically when no LLM_API_KEY is configured.")

t(26, "Wire OASIS into simulation API endpoints",
  "Update backend/app/api/simulation.py to use the OASIS orchestrator for real simulations. "
  "POST /api/simulation/start — check if LLM available: use OasisOrchestrator if yes, DemoSimulator if no. "
  "GET /api/simulation/<id>/round/<n> — get specific round results from orchestrator. "
  "POST /api/simulation/<id>/pause — pause running simulation. "
  "POST /api/simulation/<id>/resume — resume paused simulation. "
  "GET /api/simulation/<id>/metrics — get MetricsCollector summary. "
  "Add 'mode' field to simulation response: 'oasis' or 'demo' so frontend can display which mode is active. "
  "Handle concurrent simulations with a simulation registry (dict[id, orchestrator]).")

# ═══════════════════════════════════════════════════════
# GROUP 27: Zep Cloud GraphRAG (8 tasks)
# ═══════════════════════════════════════════════════════
t(27, "Install and configure Zep Cloud SDK",
  "Add zep-cloud to backend/requirements.txt if not present. "
  "Create backend/app/services/zep_config.py: "
  "1) Import from zep_cloud.client import AsyncZep. "
  "2) Create ZepConfig dataclass: api_key, project_name, default_collection. "
  "3) Create `get_zep_client()` singleton that returns configured AsyncZep client. "
  "4) Create `is_zep_available()` that checks if ZEP_API_KEY is set and client can connect. "
  "5) Add connection test endpoint helper: try client.memory.get() with a test session. "
  "6) Handle missing ZEP_API_KEY gracefully — log info message, return None from get_zep_client(). "
  "Test: `python -c 'from zep_cloud.client import AsyncZep; print(\"Zep SDK OK\")'`.")

t(27, "Create Zep entity extraction service",
  "Create backend/app/services/zep_entity_extractor.py that extracts entities from simulation interactions. "
  "EntityExtractor class with: "
  "1) `extract_from_message(message, agent_name)` — uses Zep's built-in entity extraction to identify: "
  "   people, companies, products, amounts, dates, sentiments mentioned in agent messages. "
  "2) `extract_from_round(round_data)` — processes all messages in a simulation round. "
  "3) `build_entity_map(simulation_id)` — builds a complete entity map from all rounds. "
  "Entity types: Person, Company, Product, Metric, Decision, Risk, Opportunity. "
  "Each entity has: name, type, first_mentioned_round, mention_count, associated_agents, sentiment_context. "
  "When Zep unavailable, use a regex-based fallback that extracts named entities from templates.")

t(27, "Create Zep graph memory service",
  "Create backend/app/services/zep_graph_memory.py that builds and queries the knowledge graph. "
  "GraphMemoryService class with: "
  "1) `add_episode(session_id, messages)` — adds simulation conversation to Zep memory. "
  "2) `build_graph(session_id)` — triggers Zep's graph construction from episodes. "
  "3) `query_graph(query, filters)` — searches the knowledge graph with natural language. "
  "4) `get_entity_relationships(entity_name)` — returns all relationships for an entity. "
  "5) `get_community_summary(session_id)` — returns Zep's community detection summary. "
  "6) `get_temporal_facts(session_id, time_range)` — returns facts from a specific time window. "
  "Map simulation rounds to Zep episodes. Each agent message becomes a memory entry. "
  "When Zep unavailable, return mock graph data with pre-built entity relationships.")

t(27, "Create Zep-powered knowledge graph API",
  "Add new endpoints to backend/app/api/graph.py (existing Blueprint): "
  "GET /api/graph/entities — list entities from Zep graph with type filter. "
  "GET /api/graph/entities/<name>/relationships — entity's relationships. "
  "GET /api/graph/search — natural language search over knowledge graph. "
  "GET /api/graph/communities — detected communities/clusters. "
  "GET /api/graph/temporal — temporal facts with time range filter. "
  "GET /api/graph/stats — graph statistics: entity count, relationship count, community count. "
  "Each endpoint checks is_zep_available() and returns mock data if Zep is not configured. "
  "Add 'source' field to responses: 'zep' or 'mock'.")

t(27, "Build knowledge graph visualization component",
  "Create frontend/src/components/graph/KnowledgeGraphViz.vue — D3.js force-directed graph of Zep entities. "
  "Nodes: entities, colored by type (Person=blue, Company=green, Product=purple, Metric=orange). "
  "Edges: relationships, labeled with relationship type. Edge thickness by mention count. "
  "Node size proportional to mention count. Add zoom/pan with D3 zoom behavior. "
  "On node click: show entity details panel (name, type, mentions, relationships, sentiment context). "
  "On edge click: show relationship details. "
  "Add physics controls: charge strength, link distance sliders. "
  "Filter by entity type with toggleable checkboxes. Search by entity name.")

t(27, "Build temporal knowledge timeline component",
  "Create frontend/src/components/graph/TemporalTimeline.vue — D3.js timeline of knowledge graph facts. "
  "X-axis: simulation rounds/time. Y-axis: entity categories. "
  "Plot facts as dots on the timeline, color-coded by type (new entity=blue, relationship formed=green, "
  "opinion changed=yellow, decision made=red). "
  "Connect related facts with lines. Add tooltip showing fact details on hover. "
  "Add playback control: play/pause/speed that animates facts appearing over time. "
  "Show cumulative entity count and relationship count as area chart below the timeline.")

t(27, "Build community detection visualization",
  "Create frontend/src/components/graph/CommunityView.vue — visualization of detected agent communities. "
  "Use D3.js to draw community clusters as grouped nodes within dashed-border containers. "
  "Each community has a label (auto-generated from shared topics). "
  "Nodes within community colored by role. Inter-community edges shown as thinner, lighter lines. "
  "Show community summary: member count, key topics, sentiment, cohesion score. "
  "Add ability to expand/collapse communities. Animate community formation over rounds. "
  "When Zep provides community detection, use that; otherwise, use simple clustering based on interaction frequency.")

t(27, "Build graph search interface component",
  "Create frontend/src/components/graph/GraphSearch.vue — natural language search over the knowledge graph. "
  "Search input with autocomplete suggestions (entity names, common queries). "
  "Results displayed as: matching entities with relationship context, matching facts with timestamps, "
  "matching communities with member lists. "
  "Each result type has a distinct card format. Click result to highlight in KnowledgeGraphViz. "
  "Example queries: 'Which agents discussed pricing?', 'What decisions were made about the product launch?', "
  "'Show relationships between Sales and Marketing agents'. "
  "Use the /api/graph/search endpoint. Show 'Powered by Zep' or 'Demo mode' badge based on source.")

# ═══════════════════════════════════════════════════════
# GROUP 28: Real Multi-Agent Simulation Runner (8 tasks)
# ═══════════════════════════════════════════════════════
t(28, "Create simulation scenario templates",
  "Create backend/app/services/scenario_templates.py with pre-built simulation scenarios for GTM demos. "
  "Each template: name, description, agent_configs (roles + personas), environment_type, num_rounds, constraints. "
  "Templates: "
  "1) 'Pipeline Review' — Sales team reviews Q4 pipeline, debates deal priorities. 4 agents, 6 rounds. "
  "2) 'Competitive Response' — Team reacts to competitor price cut. 5 agents, 8 rounds. "
  "3) 'Product Launch GTM' — Cross-functional team plans go-to-market. 6 agents, 10 rounds. "
  "4) 'Churn Prevention' — CS + Sales + Product discuss at-risk accounts. 4 agents, 6 rounds. "
  "5) 'Budget Allocation' — Leadership allocates marketing budget across channels. 5 agents, 8 rounds. "
  "6) 'MRR Reconciliation Investigation' — Finance + Ops investigate billing discrepancies. 4 agents, 6 rounds. "
  "Each template uses real Intercom product names and realistic GTM scenarios.")

t(28, "Build simulation execution engine",
  "Create backend/app/services/simulation_engine.py — the core simulation execution loop. "
  "SimulationEngine class: "
  "1) `prepare(template_or_custom)` — configures agents and environment from template or custom config. "
  "2) `execute_round(round_num)` — runs one round: determine agent order, process each agent's turn, "
  "   collect interactions, update environment state, record metrics. "
  "3) `execute_all()` — runs all rounds with yield between rounds for streaming. "
  "Agent turn: agent receives context (environment state + recent messages + their memory), "
  "generates response via LLM, response is parsed for actions (message, decision, data_request). "
  "Between rounds: update sentiment scores, check for consensus, evaluate stopping conditions. "
  "Store full execution history in memory for replay. "
  "Thread-safe execution using threading.Lock for concurrent simulation access.")

t(28, "Create simulation state manager",
  "Create backend/app/services/simulation_state.py — manages simulation lifecycle and state. "
  "SimulationStateManager class (module-level singleton): "
  "1) `create_simulation(config)` → simulation_id. "
  "2) `get_simulation(id)` → SimulationState object. "
  "3) `list_simulations()` → all simulations with status. "
  "4) `delete_simulation(id)` → cleanup. "
  "SimulationState: id, status (created/running/paused/completed/failed), config, engine reference, "
  "current_round, total_rounds, created_at, started_at, completed_at, error_message. "
  "Persist simulation results to JSON files in backend/data/simulations/ for replay. "
  "Limit concurrent running simulations to 3 (configurable). Queue excess requests.")

t(28, "Create agent prompt engineering module",
  "Create backend/app/services/agent_prompts.py — LLM prompt templates for OASIS agents. "
  "Define structured prompts that produce parseable agent responses: "
  "System prompt template: 'You are {name}, a {role} at Intercom. {personality}. {expertise}. "
  "You are in a {scenario_type} meeting. {constraints}. Respond in character.' "
  "Turn prompt template: 'Current discussion: {recent_messages}. Environment: {state}. "
  "Your memory: {memories}. What do you say or decide? Format: THOUGHT: (internal reasoning) "
  "MESSAGE: (what you say to others) DECISION: (any decision you make, or NONE) SENTIMENT: (1-10 scale).' "
  "Parse responses to extract structured data. Handle malformed LLM responses gracefully. "
  "Support all three providers with provider-specific optimizations (Claude uses XML tags, GPT uses JSON mode).")

t(28, "Build real-time simulation progress API",
  "Update backend/app/api/simulation.py with enhanced endpoints for real simulation progress: "
  "GET /api/simulation/<id>/status — current status, round progress (3/10), elapsed time. "
  "GET /api/simulation/<id>/stream — Server-Sent Events (SSE) endpoint streaming round completions. "
  "Each SSE event: {round: N, agents_acted: [...], messages: [...], metrics: {...}, timestamp: ISO}. "
  "GET /api/simulation/<id>/replay — full simulation history for replay (all rounds, all interactions). "
  "GET /api/simulation/<id>/agent/<agent_id> — specific agent's full history (messages, decisions, sentiment arc). "
  "Add proper SSE headers (Content-Type: text/event-stream, Cache-Control: no-cache). "
  "Handle client disconnection gracefully.")

t(28, "Build simulation control panel Vue component",
  "Create frontend/src/components/simulation/SimulationControls.vue — controls for running simulations. "
  "Start section: template selector dropdown, agent count slider (2-8), round count slider (4-20), "
  "LLM provider selector (auto/anthropic/openai/gemini), Start button. "
  "Running section: progress bar (round X of Y), elapsed time, current agent acting, "
  "Pause/Resume button, Stop button. "
  "Show 'OASIS Mode' badge (green) or 'Demo Mode' badge (yellow) based on backend response. "
  "Real-time update via EventSource connection to the SSE endpoint. "
  "Disable start button while a simulation is running.")

t(28, "Build simulation replay viewer component",
  "Create frontend/src/components/simulation/ReplayViewer.vue — replay completed simulations round by round. "
  "Transport controls: play/pause, speed (0.5x, 1x, 2x, 4x), step forward/back, jump to round. "
  "Timeline scrubber showing round markers. Current round highlighted. "
  "Main view: agent messages appearing in chat-bubble format as replay progresses. "
  "Side panel: agent sentiment chart updating in real-time with replay. "
  "Bottom: metric charts (interaction count, consensus level) updating with replay position. "
  "Use requestAnimationFrame for smooth playback. Emit events for synchronized chart updates.")

t(28, "Build simulation comparison component",
  "Create frontend/src/components/simulation/SimulationComparison.vue — side-by-side comparison of two simulation runs. "
  "Left/right panels each showing a simulation's results. "
  "Sync controls: lock round navigation (both panels advance together). "
  "Comparison metrics: overlay charts showing both simulations' metrics on the same axes. "
  "Difference highlighting: where outcomes diverged between simulations. "
  "Use case: compare same scenario with different agent compositions or LLM providers. "
  "Dropdown selectors for choosing which two simulations to compare. "
  "Show summary table: metric, sim A value, sim B value, difference, winner.")

# ═══════════════════════════════════════════════════════
# GROUP 29: Agent Memory Persistence (8 tasks)
# ═══════════════════════════════════════════════════════
t(29, "Create agent memory abstraction layer",
  "Create backend/app/services/agent_memory.py — abstraction over Zep for agent memory. "
  "AgentMemory class: "
  "1) `store_message(agent_id, session_id, role, content, metadata)` — stores message in agent's memory. "
  "2) `get_history(agent_id, session_id, last_n)` — retrieves recent messages. "
  "3) `search_memory(agent_id, query, limit)` — semantic search over agent's past interactions. "
  "4) `get_facts(agent_id)` — returns extracted facts about the agent from Zep. "
  "5) `clear_memory(agent_id, session_id)` — resets agent's memory. "
  "When Zep available: use Zep memory API with sessions mapped to simulation IDs. "
  "When Zep unavailable: use in-memory dict with simple keyword search fallback. "
  "Memory is per-agent, per-simulation (agents don't share memories unless explicitly transferred).")

t(29, "Implement temporal memory with Zep",
  "Create backend/app/services/zep_temporal_memory.py — leverages Zep's temporal memory features. "
  "TemporalMemory class: "
  "1) `add_episode(session_id, messages, timestamp)` — adds timestamped conversation episode. "
  "2) `query_at_time(session_id, query, before_timestamp)` — retrieves facts known at a specific time. "
  "3) `get_memory_evolution(session_id, entity)` — shows how knowledge about an entity changed over time. "
  "4) `get_contradictions(session_id)` — identifies contradictory facts in memory. "
  "Use Zep's temporal fact extraction to track: when agents learned information, "
  "when opinions changed, when decisions were made. "
  "Enable 'time travel' — reconstruct what an agent knew at any simulation round. "
  "Mock fallback: return chronologically ordered facts from in-memory store.")

t(29, "Build cross-simulation memory transfer",
  "Create backend/app/services/memory_transfer.py — allows agents to carry memories between simulations. "
  "MemoryTransfer class: "
  "1) `export_agent_memory(agent_id, simulation_id)` → serialized memory bundle. "
  "2) `import_agent_memory(agent_id, simulation_id, memory_bundle)` — loads memories into new simulation. "
  "3) `selective_transfer(agent_id, from_sim, to_sim, filter)` — transfer only specific memory types. "
  "Filters: 'decisions_only', 'relationships_only', 'facts_only', 'all'. "
  "This enables multi-simulation story arcs: agent remembers outcomes of previous simulations. "
  "Add API endpoint: POST /api/simulation/<id>/agents/<agent_id>/import-memory with source simulation ID.")

t(29, "Build agent memory viewer component",
  "Create frontend/src/components/simulation/AgentMemoryView.vue — displays an agent's memory state. "
  "Tabs: Conversation History, Facts & Knowledge, Relationships, Memory Timeline. "
  "Conversation History: chat-style display of all messages the agent sent/received. "
  "Facts & Knowledge: list of extracted facts with confidence scores and source references. "
  "Relationships: mini graph showing this agent's connections to entities and other agents. "
  "Memory Timeline: when the agent learned each fact, with ability to 'time travel'. "
  "Search bar for semantic search over agent's memory. "
  "Show memory source badge: 'Zep' or 'Local'.")

t(29, "Build memory diff visualization",
  "Create frontend/src/components/simulation/MemoryDiff.vue — shows how agent memory changed between rounds. "
  "Two-column diff view: 'Before Round X' vs 'After Round X'. "
  "Highlight: new facts (green), updated facts (yellow), contradicted facts (red). "
  "Round selector slider to pick which transition to examine. "
  "Summary stats: facts added, facts updated, facts contradicted, net knowledge growth. "
  "Useful for understanding what each round contributed to agent knowledge.")

t(29, "Build agent knowledge graph component",
  "Create frontend/src/components/simulation/AgentKnowledgeGraph.vue — per-agent knowledge as a mini graph. "
  "Center node: the agent. Connected nodes: entities the agent knows about. "
  "Edge labels: relationship type (knows_about, made_decision_about, disagrees_with, supports). "
  "Node color: entity type. Edge color: sentiment (green=positive, red=negative, gray=neutral). "
  "Animate graph growing over simulation rounds (slider control). "
  "D3.js force-directed layout with collision detection. "
  "Click entity to see all agent's facts about it.")

t(29, "Create memory persistence API endpoints",
  "Add to backend/app/api/simulation.py: "
  "GET /api/simulation/<id>/agents/<agent_id>/memory — full memory dump for an agent. "
  "GET /api/simulation/<id>/agents/<agent_id>/memory/search?q=query — semantic memory search. "
  "GET /api/simulation/<id>/agents/<agent_id>/memory/facts — extracted facts with confidence. "
  "GET /api/simulation/<id>/agents/<agent_id>/memory/timeline — temporal memory evolution. "
  "GET /api/simulation/<id>/agents/<agent_id>/memory/diff?round=N — memory diff at round N. "
  "POST /api/simulation/<id>/agents/<agent_id>/memory/transfer — import memories from another simulation. "
  "All endpoints fall back to in-memory data when Zep unavailable.")

t(29, "Build memory configuration panel",
  "Create frontend/src/components/simulation/MemoryConfig.vue — configuration for agent memory behavior. "
  "Settings: memory window size (how many past rounds to include in context), "
  "memory search depth (max results from semantic search), "
  "fact extraction aggressiveness (low=only explicit, medium=inferred, high=speculative), "
  "cross-simulation memory (enable/disable carrying memories forward). "
  "Show current Zep connection status with test button. "
  "Show memory usage stats: total facts stored, total episodes, graph size. "
  "Save settings to simulation config. Display in simulation setup wizard.")

# ═══════════════════════════════════════════════════════
# GROUP 30: ReportAgent with Tool Use (8 tasks)
# ═══════════════════════════════════════════════════════
t(30, "Create ReportAgent tool definitions",
  "Create backend/app/services/report_tools.py — tools available to the ReportAgent for data analysis. "
  "Define tools as function schemas (OpenAI function-calling format for compatibility): "
  "1) `query_simulation_data(simulation_id, metric, time_range)` — fetches specific simulation metrics. "
  "2) `analyze_sentiment_trend(simulation_id, agent_ids)` — computes sentiment statistics. "
  "3) `identify_key_decisions(simulation_id)` — extracts decisions from simulation history. "
  "4) `compare_agent_behaviors(simulation_id, agent_ids)` — comparative agent analysis. "
  "5) `generate_chart_data(chart_type, data_query)` — prepares data for specific chart types. "
  "6) `search_knowledge_graph(query)` — searches Zep graph for relevant information. "
  "7) `calculate_gtm_metrics(metric_name, parameters)` — computes GTM-specific calculations. "
  "Each tool has clear parameter schemas and return type definitions.")

t(30, "Build ReportAgent execution engine",
  "Create backend/app/services/report_agent_engine.py — ReACT-pattern agent that writes analysis reports. "
  "ReportAgentEngine class: "
  "1) `generate_report(simulation_id, report_type, custom_prompt)` — main entry point. "
  "2) Uses ReACT loop: Thought → Action → Observation → repeat until report complete. "
  "3) Agent decides which tools to call based on report requirements. "
  "4) Compiles observations into structured report sections. "
  "5) Generates executive summary, detailed findings, recommendations. "
  "Report types: 'executive_summary', 'detailed_analysis', 'agent_comparison', 'decision_audit', 'custom'. "
  "Max 10 tool calls per report to prevent runaway loops. "
  "Track token usage and tool call history for transparency. "
  "Fallback: when LLM unavailable, generate template-based report from raw data.")

t(30, "Create report templates and formatting",
  "Create backend/app/services/report_templates.py — Markdown templates for different report types. "
  "Templates use Jinja2-style placeholders filled by ReportAgent: "
  "Executive Summary: title, date, key findings (3-5 bullets), metrics table, recommendation. "
  "Detailed Analysis: executive summary + per-round breakdown + agent analysis + decision timeline + appendix. "
  "Agent Comparison: side-by-side agent stats table + personality analysis + influence ranking. "
  "Decision Audit: chronological decision list + rationale + dissenting opinions + outcomes. "
  "Each template outputs clean Markdown that can be rendered in the frontend. "
  "Add chart placeholders: `{{chart:sentiment_trend}}`, `{{chart:agent_comparison}}` that frontend renders as actual charts.")

t(30, "Build report generation API",
  "Update backend/app/api/report.py Blueprint: "
  "POST /api/reports/generate — start report generation (async, returns report_id). "
  "Body: {simulation_id, report_type, custom_prompt, include_charts: bool}. "
  "GET /api/reports/<id>/status — generation progress (pending/generating/complete/failed). "
  "GET /api/reports/<id> — full report content (Markdown + chart data). "
  "GET /api/reports — list all generated reports with metadata. "
  "DELETE /api/reports/<id> — delete a report. "
  "GET /api/reports/<id>/tool-calls — transparency log of tool calls the agent made. "
  "Use threading to run report generation asynchronously. Return immediately with report_id.")

t(30, "Build report viewer Vue component",
  "Create frontend/src/components/report/ReportViewer.vue — renders generated reports. "
  "Parse Markdown content and render with proper formatting (use a markdown renderer library). "
  "Replace chart placeholders ({{chart:...}}) with actual D3.js chart components. "
  "Add table of contents sidebar generated from heading structure. "
  "Support print/export: add print-friendly CSS styles. "
  "Show report metadata header: title, date, simulation reference, generation time. "
  "Add 'Regenerate' button to create a new version. "
  "Show generation transparency: expandable section showing tool calls the agent made.")

t(30, "Build report generation wizard component",
  "Create frontend/src/components/report/ReportWizard.vue — step-by-step wizard for generating reports. "
  "Step 1: Select simulation (dropdown of completed simulations). "
  "Step 2: Select report type (cards with descriptions for each type). "
  "Step 3: Customize (optional custom prompt, select which sections to include, chart preferences). "
  "Step 4: Generate — show progress with real-time status updates. "
  "Step 5: Review — show generated report with ReportViewer. "
  "Stepper component at top showing current step. Back/Next navigation. "
  "Save report preferences for next time.")

t(30, "Build tool call transparency component",
  "Create frontend/src/components/report/ToolCallLog.vue — shows the ReportAgent's reasoning process. "
  "Display the ReACT loop: Thought (agent's reasoning), Action (tool called), Observation (tool result). "
  "Each step in a collapsible card. Color-code: thoughts in blue, actions in purple, observations in green. "
  "Show tool call parameters and return values. Track timing per step. "
  "Summary at top: total tool calls, total tokens used, generation time. "
  "This provides transparency into how the AI generated the report — important for trust.")

t(30, "Update report view with new components",
  "Update frontend/src/views/ReportView.vue to integrate new report generation features. "
  "Add 'Generate New Report' button that opens ReportWizard as a modal or slide-over. "
  "Show list of previously generated reports with metadata (date, type, simulation, quality score). "
  "Click report to open in ReportViewer. "
  "Add report comparison: select two reports to view side-by-side. "
  "Add export options: download as Markdown, copy to clipboard, print. "
  "Show ReportAgent status badge: 'AI-Powered' (green) or 'Template' (yellow) mode.")

# ═══════════════════════════════════════════════════════
# GROUP 31: Real-Time Simulation Streaming (5 tasks)
# ═══════════════════════════════════════════════════════
t(31, "Implement WebSocket server for simulation streaming",
  "Create backend/app/services/websocket_manager.py — WebSocket support for real-time simulation updates. "
  "Use flask-socketio library (add to requirements.txt). "
  "WebSocketManager class: "
  "1) `emit_round_update(simulation_id, round_data)` — broadcast round completion to connected clients. "
  "2) `emit_agent_message(simulation_id, agent_id, message)` — stream individual agent messages as they arrive. "
  "3) `emit_metric_update(simulation_id, metrics)` — stream metric changes. "
  "4) `emit_status_change(simulation_id, status)` — stream simulation status changes. "
  "Events: 'round_complete', 'agent_message', 'metric_update', 'simulation_status', 'error'. "
  "Handle connection/disconnection. Room-based: clients join simulation_id room. "
  "Update backend/run.py to use socketio.run() instead of app.run().")

t(31, "Build WebSocket client composable",
  "Create frontend/src/composables/useWebSocket.js — Vue composable for WebSocket connections. "
  "Uses socket.io-client (install via pnpm). "
  "Exports: connect(simulationId), disconnect(), onRoundComplete(callback), onAgentMessage(callback), "
  "onMetricUpdate(callback), onStatusChange(callback), connected (ref), error (ref). "
  "Auto-reconnect on disconnect with exponential backoff. "
  "Clean up listeners on component unmount. "
  "Fallback to SSE polling if WebSocket connection fails. "
  "Use the same URL as the API client base URL.")

t(31, "Build live simulation feed component",
  "Create frontend/src/components/simulation/LiveFeed.vue — real-time message feed during simulation. "
  "Messages appear as they stream in from WebSocket, not waiting for full round completion. "
  "Each message: agent avatar/icon, agent name, message content, timestamp, sentiment badge. "
  "Auto-scroll to bottom as new messages arrive (with 'scroll to latest' button if user scrolled up). "
  "Show typing indicator when an agent is processing (between message events). "
  "Group messages by round with round dividers. "
  "Add message reactions: thumbs up/down that agents might reference in later rounds. "
  "Smooth animation for new messages sliding in from bottom.")

t(31, "Build live metrics dashboard component",
  "Create frontend/src/components/simulation/LiveMetrics.vue — real-time updating charts during simulation. "
  "4 mini charts that update as metric_update events stream in: "
  "1) Sentiment trend — line chart with one line per agent, updating each round. "
  "2) Interaction volume — bar chart showing messages per round. "
  "3) Consensus gauge — circular gauge showing group agreement level. "
  "4) Information spread — network diagram showing who has received what information. "
  "Charts animate smoothly between updates using D3 transitions. "
  "Show 'LIVE' indicator badge when simulation is running.")

t(31, "Build simulation workspace layout",
  "Update frontend/src/views/SimulationWorkspaceView.vue to integrate real-time components. "
  "Layout during active simulation: "
  "Left panel (60%): LiveFeed showing agent messages in real-time. "
  "Right panel (40%): Split into SimulationControls (top 30%), LiveMetrics (bottom 70%). "
  "Bottom bar: simulation progress (round X of Y), elapsed time, agent status indicators. "
  "When simulation completes, transition to review mode: ReplayViewer replaces LiveFeed, "
  "full metrics replace LiveMetrics, report generation button appears. "
  "Use the WebSocket composable for all real-time data. "
  "Responsive: stack panels vertically on mobile.")

# ═══════════════════════════════════════════════════════
# GROUP 32: Agent Persona Generation from Zep Graph (5 tasks)
# ═══════════════════════════════════════════════════════
t(32, "Create persona generator from Zep graph data",
  "Create backend/app/services/persona_from_graph.py — generates agent personas from knowledge graph. "
  "PersonaGenerator class: "
  "1) `generate_from_graph(role, graph_context)` — creates a rich persona using Zep graph entities. "
  "   Extracts: relevant companies, products, market conditions, competitor info from graph. "
  "   Incorporates: real GTM data (accounts, pipeline, revenue) into persona's knowledge. "
  "2) `enhance_persona(base_persona, simulation_context)` — adds simulation-specific context. "
  "3) `generate_team(scenario, num_agents)` — creates a balanced team with complementary personas. "
  "Personas include: name, title, department, personality traits, domain expertise areas, "
  "biases (e.g., 'tends to overestimate conversion rates'), known facts (from graph), goals. "
  "When Zep unavailable, generate from pre-built persona templates with randomized traits.")

t(32, "Build persona customization API",
  "Add endpoints to backend/app/api/simulation.py: "
  "GET /api/agents/personas — list available persona templates. "
  "POST /api/agents/personas/generate — generate personas from graph + scenario. "
  "Body: {scenario_type, num_agents, role_distribution, personality_diversity}. "
  "GET /api/agents/personas/<id> — full persona details. "
  "PUT /api/agents/personas/<id> — customize a generated persona. "
  "POST /api/agents/personas/<id>/clone — clone and modify a persona. "
  "Return personas with 'source' field: 'zep_graph', 'template', 'custom'.")

t(32, "Build persona card Vue component",
  "Create frontend/src/components/simulation/PersonaCard.vue — visual card representing an agent persona. "
  "Show: agent name (generated), title, department badge, personality radar chart (5 traits), "
  "expertise tags, bias indicator, avatar (generated initials with background color based on department). "
  "Personality radar chart using D3.js: analytical, creative, assertive, empathetic, risk-tolerant. "
  "Click to expand: full persona details, known facts, goals, history from previous simulations. "
  "Edit button to customize persona fields. "
  "Compact mode for use in simulation setup (just name, role, key trait).")

t(32, "Build team composition editor component",
  "Create frontend/src/components/simulation/TeamComposer.vue — drag-and-drop team builder. "
  "Left panel: available persona pool (filterable by role, personality type). "
  "Right panel: current team slots (empty slots shown as dashed outlines). "
  "Drag personas from pool to team slots. Remove by dragging back or clicking X. "
  "Team balance indicators: role coverage (sales, marketing, CS, product, finance), "
  "personality diversity score, expertise coverage. "
  "Warnings: 'No sales perspective' if no sales agent, 'Low diversity' if all similar personalities. "
  "Auto-generate button: fill empty slots with recommended agents based on scenario. "
  "Save team compositions as templates for reuse.")

t(32, "Build persona generation wizard",
  "Create frontend/src/components/simulation/PersonaWizard.vue — step wizard for AI-generated personas. "
  "Step 1: Select scenario type → auto-suggest role composition. "
  "Step 2: Configure generation — personality diversity slider, expertise focus areas, graph context toggle. "
  "Step 3: Generate — show loading state, then display generated personas as PersonaCards. "
  "Step 4: Customize — edit any persona, swap out, regenerate individuals. "
  "Step 5: Confirm team → proceed to simulation setup. "
  "Show 'Powered by Zep Knowledge Graph' when graph data enriches personas. "
  "Show generation metadata: which graph entities influenced each persona.")

# ═══════════════════════════════════════════════════════
# GROUP 33: Graceful Fallback to Mock (5 tasks)
# ═══════════════════════════════════════════════════════
t(33, "Create unified service availability checker",
  "Create backend/app/services/availability.py — centralized check for all external service dependencies. "
  "ServiceAvailability class (singleton): "
  "1) `check_all()` → {llm: {available, provider, model}, zep: {available, features}, oasis: {available, version}}. "
  "2) `check_llm()` → tests LLM provider connection with a minimal API call. Cache result for 60 seconds. "
  "3) `check_zep()` → tests Zep Cloud connection. Cache result for 60 seconds. "
  "4) `get_mode()` → 'full' (all services), 'partial' (some services), 'demo' (no external services). "
  "Add endpoint: GET /api/system/status that returns full availability info. "
  "Log availability changes. Emit event when service availability changes.")

t(33, "Create graceful degradation middleware",
  "Create backend/app/middleware/degradation.py — middleware that automatically degrades features when services unavailable. "
  "Before each request, check service availability (from cached results). "
  "Add to Flask g object: g.mode ('full'/'partial'/'demo'), g.available_services (set). "
  "Each Blueprint endpoint can check g.mode to decide whether to use real or mock data. "
  "Add response header X-Service-Mode: full|partial|demo so frontend knows which mode is active. "
  "Log when degradation occurs with reason. "
  "Create decorator @requires_service('llm') that returns 503 if service unavailable, "
  "or @degrades_gracefully('llm') that falls back to mock.")

t(33, "Build comprehensive mock data layer",
  "Create backend/app/services/mock_data.py — centralized mock data for all features. "
  "MockDataProvider class that provides mock responses for every API endpoint: "
  "1) Simulation mock: pre-generated 10-round simulation with 4 agents (from existing demo data). "
  "2) Graph mock: pre-built knowledge graph with 20 entities and 30 relationships. "
  "3) Report mock: pre-generated executive summary report. "
  "4) Memory mock: pre-built agent memory with facts and timeline. "
  "5) GTM data mocks: all salesforce, cpq, pipeline, revenue, orders, reconciliation data. "
  "Mock data should be internally consistent (same accounts referenced across features). "
  "Load from JSON fixtures in backend/data/fixtures/ directory. "
  "Generate fixtures once and commit to repo for deterministic demo experience.")

t(33, "Build service status indicator Vue component",
  "Create frontend/src/components/common/ServiceStatus.vue — shows current service connectivity. "
  "Compact mode (for navbar): colored dot (green=full, yellow=partial, red=demo) with tooltip. "
  "Expanded mode (for settings page): card per service (LLM, Zep, OASIS) with: "
  "status indicator, provider name, last checked timestamp, test connection button. "
  "Auto-refresh status every 60 seconds. Animate transitions between states. "
  "Show 'Demo Mode' banner at top of page when in demo mode with message: "
  "'Running in demo mode — set API keys in Settings for full functionality'. "
  "Add to AppNav.vue in compact mode. Add to SettingsView.vue in expanded mode.")

t(33, "Build demo mode onboarding overlay",
  "Create frontend/src/components/common/DemoModeOverlay.vue — helpful overlay shown in demo mode. "
  "Semi-transparent overlay on features that use mock data, with a small 'Demo Data' badge. "
  "On first visit, show a welcome modal explaining: "
  "'You are running in demo mode. All data is simulated. To enable real AI-powered features: "
  "1) Add your LLM API key in Settings, 2) Add your Zep API key for knowledge graph features.' "
  "Add 'Don't show again' checkbox that persists to localStorage. "
  "Badge click shows tooltip: 'This data is simulated. Configure API keys for real data.' "
  "Use a subtle yellow tint for demo mode badges — not intrusive but visible.")

# ═══════════════════════════════════════════════════════
# GROUP 34: Network Topology Views (8 tasks)
# ═══════════════════════════════════════════════════════
t(34, "Create agent interaction graph data processor",
  "Create backend/app/services/interaction_graph.py — processes simulation data into network graph format. "
  "InteractionGraphBuilder class: "
  "1) `build_from_simulation(simulation_id)` → {nodes: [...], edges: [...]}. "
  "Nodes: agents with attributes (role, avg_sentiment, message_count, influence_score). "
  "Edges: interactions between agents with attributes (message_count, avg_sentiment, topics). "
  "2) `build_temporal_graph(simulation_id, round)` → graph state at specific round. "
  "3) `compute_centrality(graph)` → betweenness, closeness, degree centrality per node. "
  "4) `detect_clusters(graph)` → community detection using Louvain method (implement simple version). "
  "Add API endpoints: GET /api/simulation/<id>/network and GET /api/simulation/<id>/network/round/<n>.")

t(34, "Build agent network force graph component",
  "Create frontend/src/components/visualization/AgentNetworkGraph.vue — D3.js force-directed graph. "
  "Nodes: agents as circles. Size by influence score. Color by role/department. "
  "Edges: interactions. Width by message count. Color by average sentiment (green to red gradient). "
  "Edge labels (on hover): message count, primary topics. "
  "Node labels: agent name, role. Show avatar initials inside circle. "
  "Physics: D3 force simulation with charge, link, center, collision forces. "
  "Interactive: drag nodes, zoom/pan, hover tooltips, click to focus. "
  "Controls panel: charge strength, link distance, show labels toggle, edge filter (min messages).")

t(34, "Build adjacency matrix heatmap component",
  "Create frontend/src/components/visualization/AdjacencyMatrix.vue — D3.js matrix showing all agent interactions. "
  "Rows and columns: agents. Cell color: interaction intensity (white=none, light blue=few, dark blue=many). "
  "Cell click shows interaction details (messages exchanged, sentiment, topics). "
  "Sort options: alphabetical, by cluster, by influence. "
  "Add row/column totals showing total interactions per agent. "
  "Diagonal cells show agent's total activity. "
  "Responsive sizing based on number of agents.")

t(34, "Build information flow animation component",
  "Create frontend/src/components/visualization/InformationFlow.vue — animated visualization of information cascade. "
  "Show how information spreads through the agent network over simulation rounds. "
  "Each piece of information (fact, decision, opinion) represented as a colored particle. "
  "Particles travel along edges from sender to receiver, timing based on round. "
  "Speed control: slow/medium/fast. Round counter. Play/pause. "
  "Show which agents have received each piece of information at current time. "
  "Use D3.js with requestAnimationFrame for smooth animation. "
  "Legend: particle colors by information type (fact=blue, decision=red, opinion=yellow).")

t(34, "Build centrality analysis component",
  "Create frontend/src/components/visualization/CentralityAnalysis.vue — multi-chart centrality view. "
  "Bar chart: agents ranked by centrality score. Toggle between betweenness, closeness, degree. "
  "Radar chart: overlay all three centrality measures for selected agent. "
  "Network graph: nodes sized by selected centrality measure. "
  "Insight text: auto-generated description of who is most central and why. "
  "Example: 'Marketing Manager has highest betweenness centrality — they bridge Sales and Product conversations.' "
  "Use D3.js for all charts. Responsive layout.")

t(34, "Build cluster visualization component",
  "Create frontend/src/components/visualization/ClusterView.vue — community detection visualization. "
  "D3.js force graph with nodes grouped into detected clusters. "
  "Cluster boundaries shown as convex hulls with semi-transparent fill colors. "
  "Cluster labels showing auto-generated descriptions (e.g., 'Revenue-focused group', 'Product advocates'). "
  "Inter-cluster edges shown as thinner lines. Intra-cluster edges thicker. "
  "Summary panel: cluster count, sizes, cohesion scores, key topics per cluster. "
  "Allow manual cluster assignment (drag node between clusters).")

t(34, "Build communication pattern timeline",
  "Create frontend/src/components/visualization/CommPatternTimeline.vue — shows communication patterns over time. "
  "X-axis: simulation rounds. Y-axis: agent pairs. "
  "Marks at intersection of round and pair when communication occurred. "
  "Mark size: message count. Mark color: sentiment. "
  "Highlight patterns: regular communicators (consistent marks), burst communicators (clustered marks), "
  "one-time interactions (single marks). "
  "Add summary: busiest round, most talkative agent, most common pair. "
  "D3.js scatter plot with custom marks.")

t(34, "Create Network Analysis view",
  "Create frontend/src/views/NetworkAnalysisView.vue — dedicated network analysis page. "
  "Accessible from simulation results as 'Network Analysis' tab. "
  "Layout: AgentNetworkGraph (main, 2/3), CentralityAnalysis (side, 1/3). "
  "Below: two-column — AdjacencyMatrix (left), ClusterView (right). "
  "Below: full-width InformationFlow animation + CommPatternTimeline. "
  "Controls: round selector to view network at different points in simulation. "
  "Add to simulation workspace as a tab alongside LiveFeed and other views.")

# ═══════════════════════════════════════════════════════
# GROUP 35: Animated Flow Diagrams (8 tasks)
# ═══════════════════════════════════════════════════════
t(35, "Build data flow animation engine",
  "Create frontend/src/composables/useFlowAnimation.js — Vue composable for managing flow animations. "
  "State: playing (boolean), speed (0.5-4x), currentTime (number), duration (number). "
  "Methods: play(), pause(), setSpeed(speed), seek(time), onFrame(callback). "
  "Uses requestAnimationFrame internally. Emits frame events at 60fps. "
  "Supports multiple synchronized animations (chart A and chart B move together). "
  "Auto-pause when component not visible (IntersectionObserver). "
  "Cleanup on unmount. Provide/inject pattern for child components.")

t(35, "Build animated pipeline flow component",
  "Create frontend/src/components/visualization/PipelineFlow.vue — animated GTM pipeline. "
  "Horizontal flow: Lead → MQL → SQL → SAO → Proposal → Won/Lost. "
  "Animated dots flow through stages, representing individual leads/opportunities. "
  "Dot speed varies by time-in-stage. Dots accumulate at bottlenecks. "
  "Lost dots fall off the bottom with a red trail. Won dots celebrate with a green pulse. "
  "Stage gates with conversion rate labels. Counter per stage showing current count. "
  "Use the flow animation composable. D3.js for rendering. SVG-based for crisp animation.")

t(35, "Build animated revenue waterfall component",
  "Create frontend/src/components/visualization/AnimatedWaterfall.vue — animated revenue bridge. "
  "Bars grow from left to right over time: Starting MRR → +New → +Expansion → -Contraction → -Churn → End. "
  "Each bar animates from zero to full height. Positive bars grow up (green), negative grow down (red). "
  "Running total line animates along the top of the waterfall. "
  "Numbers count up with easing. Connector lines draw between bars. "
  "Use the flow animation composable for synchronized timing.")

t(35, "Build animated Sankey flow component",
  "Create frontend/src/components/visualization/AnimatedSankey.vue — animated Sankey diagram with flowing particles. "
  "Nodes: pipeline stages or process steps. Links: transitions between stages. "
  "Animated particles flow along links, density proportional to volume. "
  "Particle color matches the source node. Particles merge at destination. "
  "Link width transitions smoothly when data updates. "
  "Use d3-sankey for layout, custom animation for particles. "
  "Responsive: recalculates layout on container resize.")

t(35, "Build animated org chart with information flow",
  "Create frontend/src/components/visualization/OrgInfoFlow.vue — org chart showing information flowing between teams. "
  "Tree layout: CEO → VP Sales + VP Marketing + VP CS + VP Product. Each VP has team members. "
  "Animated arrows showing information flow: reports flow up, directives flow down, cross-team collaboration flows horizontally. "
  "Arrow thickness: information volume. Arrow color: information type (data=blue, decision=red, feedback=green). "
  "Show bottlenecks: when information piles up at a node, show a warning indicator. "
  "Click node to see what information is passing through. "
  "Timeline control to show flow at different time points.")

t(35, "Build animated deal lifecycle component",
  "Create frontend/src/components/visualization/DealLifecycle.vue — animated visualization of a single deal's journey. "
  "Horizontal timeline with stage milestones. Deal 'token' moves through stages. "
  "At each stage: show key events (meeting, proposal sent, negotiation, approval). "
  "Branch points: where the deal could have gone differently (competitor entered, budget challenge). "
  "Side panel: running commentary of what happened at each stage. "
  "Auto-play through the lifecycle, or click stages to jump. "
  "Multiple deals can be compared by stacking timelines.")

t(35, "Build animated metric counter component",
  "Create frontend/src/components/visualization/AnimatedCounter.vue — reusable animated number counter. "
  "Props: targetValue, duration, prefix ($, etc.), suffix (%, etc.), decimals. "
  "Animates from 0 (or previous value) to target with easing. "
  "Large display format for dashboard KPI cards. "
  "Color transition: start gray, end in brand blue (or red if negative trend). "
  "Optional sparkline that draws as the counter animates. "
  "Uses requestAnimationFrame. Triggers animation on mount or when targetValue changes. "
  "Format large numbers: 1,234,567 → $1.2M.")

t(35, "Create Animated Visualizations showcase view",
  "Create frontend/src/views/VisualizationsShowcaseView.vue — a page showcasing all animated visualizations. "
  "Grid layout showing each visualization in its own card with title and description. "
  "Each card has a 'Play' button to start the animation. 'View Full' expands to full-screen. "
  "Add route: { path: '/visualizations', name: 'Visualizations', component: VisualizationsShowcaseView }. "
  "This page serves double duty: demo showcase for the presentation and a development gallery. "
  "Add to AppNav.vue with an eye/play icon. "
  "Page title: 'Visualization Gallery' subtitle: 'Animated data storytelling for GTM operations'.")

# ═══════════════════════════════════════════════════════
# GROUP 36: CHECKPOINT (1 task)
# ═══════════════════════════════════════════════════════
t(36, "CHECKPOINT: Verify app builds and runs after OASIS and visualization integration",
  "Run comprehensive build and smoke test: "
  "1) cd frontend && pnpm install && pnpm build — verify no build errors. "
  "2) cd frontend && pnpm lint — verify no linting errors. "
  "3) cd backend && pip install -r requirements.txt — verify all new dependencies install. "
  "4) Verify OASIS imports work: python -c 'from app.services.oasis_orchestrator import OasisOrchestrator; print(\"OK\")'. "
  "5) Verify Zep imports work: python -c 'from app.services.zep_graph_memory import GraphMemoryService; print(\"OK\")'. "
  "6) Verify all new Blueprints registered in backend/app/api/__init__.py. "
  "7) Verify all new Vue routes in frontend/src/router/index.js. "
  "8) Verify WebSocket setup: python -c 'from app.services.websocket_manager import WebSocketManager; print(\"OK\")'. "
  "9) Check for circular imports by importing the app factory. "
  "10) Verify demo mode works: set no API keys and confirm mock data endpoints return data. "
  "Fix any issues found. Create docs/checkpoint-group-36.md with results.")

# ═══════════════════════════════════════════════════════
# GROUP 37: Dashboard Builder (10 tasks)
# ═══════════════════════════════════════════════════════
t(37, "Create dashboard configuration data model",
  "Create backend/app/models/dashboard.py with dataclasses: "
  "DashboardConfig (id, name, description, widgets: list[WidgetConfig], layout: list[LayoutItem], "
  "created_by, created_at, updated_at, is_default), "
  "WidgetConfig (id, type: str, title: str, data_source: str, config: dict, refresh_interval_seconds: int), "
  "LayoutItem (widget_id, x, y, width, height, min_width, min_height). "
  "Widget types: 'kpi_card', 'line_chart', 'bar_chart', 'donut_chart', 'table', 'funnel', 'gauge', 'text', 'activity_feed'. "
  "Data sources: 'revenue', 'pipeline', 'salesforce', 'cpq', 'orders', 'simulation', 'reconciliation'. "
  "Add factory methods for default dashboard configurations.")

t(37, "Create dashboard persistence API",
  "Create backend/app/api/dashboards.py as a Flask Blueprint: "
  "GET /api/dashboards — list saved dashboards. "
  "POST /api/dashboards — create new dashboard from config. "
  "GET /api/dashboards/<id> — get dashboard with full widget and layout config. "
  "PUT /api/dashboards/<id> — update dashboard (name, widgets, layout). "
  "DELETE /api/dashboards/<id> — delete dashboard. "
  "POST /api/dashboards/<id>/duplicate — clone a dashboard. "
  "GET /api/dashboards/default — get the default dashboard config. "
  "Persist to JSON files in backend/data/dashboards/. Register Blueprint.")

t(37, "Build widget registry",
  "Create frontend/src/components/dashboard/WidgetRegistry.js — registry of all available widget types. "
  "Export a map of widget_type → { component, defaultConfig, icon, label, description, supportedDataSources }. "
  "Widget types: KpiCardWidget, LineChartWidget, BarChartWidget, DonutChartWidget, TableWidget, "
  "FunnelWidget, GaugeWidget, TextWidget, ActivityFeedWidget. "
  "Each widget component accepts standard props: { config, data, loading, error, onConfigChange }. "
  "Registry enables dynamic rendering: `<component :is=\"registry[widget.type].component\" />`.")

t(37, "Build KPI card widget component",
  "Create frontend/src/components/dashboard/widgets/KpiCardWidget.vue — configurable KPI card. "
  "Config: data_source, metric_name, label, prefix, suffix, show_trend, show_sparkline, color. "
  "Displays: large value, label, trend arrow (up/down with percentage), optional 6-period sparkline. "
  "Edit mode: form to configure all options. Preview mode: rendered card. "
  "Supports all data sources — fetches the configured metric from the appropriate store. "
  "Color options: auto (based on trend), or fixed brand color.")

t(37, "Build chart widgets (line, bar, donut)",
  "Create frontend/src/components/dashboard/widgets/LineChartWidget.vue, BarChartWidget.vue, DonutChartWidget.vue. "
  "Each uses D3.js v7 with consistent styling. "
  "Config: data_source, metrics (array), time_range, colors, show_legend, show_labels. "
  "Line chart: multiple lines, hover crosshair, legend. "
  "Bar chart: single or grouped bars, horizontal/vertical orientation. "
  "Donut chart: segments with labels, center text showing total. "
  "All charts: responsive to container size, animated on mount, configurable in edit mode. "
  "Edit mode: form with metric selector, time range, color pickers.")

t(37, "Build table and text widgets",
  "Create frontend/src/components/dashboard/widgets/TableWidget.vue and TextWidget.vue. "
  "Table widget: data_source, columns config (which fields to show), sort, pagination, row limit. "
  "Renders sortable table with configurable columns. Supports formatting (currency, date, percentage). "
  "Text widget: markdown content, font size, alignment. "
  "Useful for dashboard titles, notes, annotations. Edit with a simple markdown editor. "
  "Both widgets follow the standard widget props interface.")

t(37, "Build drag-and-drop grid layout",
  "Create frontend/src/components/dashboard/DashboardGrid.vue — drag-and-drop grid layout using CSS Grid. "
  "Grid: 12 columns, auto rows. Widgets placed by grid coordinates (x, y, width, height). "
  "Drag to reposition widgets. Resize by dragging edges/corners. "
  "Snap to grid. Show placement guidelines while dragging. Prevent overlap. "
  "Use a drag-and-drop library (vue-grid-layout or implement with native drag events). Install via pnpm. "
  "Edit mode: show grid lines, handles on widgets, add/remove buttons. "
  "View mode: clean layout without edit chrome.")

t(37, "Build widget picker panel",
  "Create frontend/src/components/dashboard/WidgetPicker.vue — panel for adding widgets to dashboard. "
  "Opens as a slide-over from the right side. "
  "Shows all available widget types from WidgetRegistry as cards with icon, label, description. "
  "Click to add widget to dashboard (placed in next available position). "
  "Category grouping: Charts, Cards, Tables, Other. Search filter. "
  "Preview of each widget type with sample data. "
  "After adding, auto-open widget configuration panel.")

t(37, "Build dashboard Pinia store",
  "Create frontend/src/stores/dashboards.js — manages dashboard state. "
  "State: dashboards (array), activeDashboard (object), editMode (boolean), loading, error. "
  "Actions: fetchDashboards(), fetchDashboard(id), saveDashboard(config), deleteDashboard(id), "
  "setEditMode(bool), addWidget(widgetConfig), removeWidget(widgetId), updateWidgetConfig(widgetId, config), "
  "updateLayout(layoutItems), duplicateDashboard(id). "
  "Getters: widgetConfigs, layoutItems, isDirty (unsaved changes), widgetCount. "
  "API client: frontend/src/api/dashboards.js with matching functions.")

t(37, "Create Dashboard Builder view",
  "Create frontend/src/views/DashboardBuilderView.vue — the dashboard builder page. "
  "Toolbar: dashboard name (editable), Save button, Edit/View toggle, Add Widget button, "
  "Dashboard selector dropdown, New Dashboard button, Delete button. "
  "Main area: DashboardGrid with all configured widgets. "
  "Edit mode: WidgetPicker slide-over, grid handles, widget config panels. "
  "View mode: clean presentation of the dashboard. "
  "Add route: { path: '/dashboards', name: 'Dashboards', component: DashboardBuilderView }. "
  "Add route: { path: '/dashboards/:id', name: 'DashboardDetail', component: DashboardBuilderView }. "
  "Nav item with layout-grid icon.")

# ═══════════════════════════════════════════════════════
# GROUP 38: Timeline Scrubber (8 tasks)
# ═══════════════════════════════════════════════════════
t(38, "Build timeline scrubber composable",
  "Create frontend/src/composables/useTimelineScrubber.js — Vue composable for synchronized timeline control. "
  "State: currentPosition (0-1 normalized), isPlaying, playbackSpeed, duration, marks (event positions). "
  "Methods: play(), pause(), togglePlay(), seek(position), stepForward(), stepBack(), setSpeed(multiplier). "
  "Events: onPositionChange(callback), onPlay(callback), onPause(callback). "
  "Provide/inject pattern so all child components can synchronize to the same timeline. "
  "Keyboard shortcuts: Space (play/pause), Arrow Left/Right (step), +/- (speed). "
  "Auto-calculate duration from data range.")

t(38, "Build timeline scrubber UI component",
  "Create frontend/src/components/timeline/TimelineScrubber.vue — the visual timeline control bar. "
  "Horizontal bar with: progress indicator, draggable playhead, event markers (colored dots at notable events). "
  "Below bar: timestamp labels, play/pause button, speed selector (0.5x, 1x, 2x, 4x), step buttons. "
  "Above bar: current time/round display. "
  "Hover over bar: tooltip showing timestamp at cursor position. "
  "Event markers: colored by type (decision=red, milestone=green, interaction=blue). Click marker to jump there. "
  "Smooth playhead animation during playback. Responsive to container width.")

t(38, "Build synchronized chart wrapper component",
  "Create frontend/src/components/timeline/SyncedChart.vue — wrapper that connects any chart to the timeline. "
  "Props: chartComponent (the actual chart), timeField (data field to sync on), highlightMode ('point'|'range'|'crosshair'). "
  "Renders the chart component and overlays a position indicator: "
  "- 'point': highlights the data point at current timeline position. "
  "- 'range': shades everything before current position. "
  "- 'crosshair': vertical line at current position. "
  "Uses the timeline composable inject to stay synced. "
  "Bidirectional: clicking on the chart also updates the timeline position.")

t(38, "Build timeline event markers component",
  "Create frontend/src/components/timeline/EventMarkers.vue — shows notable events on the timeline. "
  "Extracts events from simulation data: decisions, sentiment peaks/valleys, consensus moments, conflicts. "
  "Renders as clickable icons above the scrubber bar. "
  "Hover: tooltip with event details. Click: jump timeline to that position and show event detail panel. "
  "Category filtering: toggle which event types to show. "
  "Density indicator: when many events cluster, show a count badge instead of individual markers.")

t(38, "Build snapshot comparison component",
  "Create frontend/src/components/timeline/SnapshotComparison.vue — compare state at two timeline points. "
  "Two position pickers: 'Compare Point A at [time] with Point B at [time]'. "
  "Side-by-side view showing: metrics at point A vs point B, agent sentiments, network state. "
  "Diff highlighting: what changed between the two points (green=new, red=removed, yellow=changed). "
  "Summary statistics: total changes, biggest change, most affected agent. "
  "Preset comparisons: 'First vs Last', 'Before vs After Decision X'.")

t(38, "Build timeline annotations component",
  "Create frontend/src/components/timeline/TimelineAnnotations.vue — user-addable annotations on the timeline. "
  "Click any point on the timeline to add a note (stored locally in component state or Pinia). "
  "Annotations appear as small flag icons on the scrubber bar. "
  "Click to view/edit annotation text. Delete button per annotation. "
  "Export annotations as part of report data. Import annotations from shared configurations. "
  "Use for demo narration: pre-add annotations explaining what's happening at key moments.")

t(38, "Build multi-metric synchronized view component",
  "Create frontend/src/components/timeline/MultiMetricView.vue — stacked synchronized charts. "
  "Multiple chart rows, all synchronized to the same timeline scrubber: "
  "Row 1: Agent sentiment lines. Row 2: Interaction volume bars. Row 3: Consensus gauge. "
  "All rows share the same X-axis (handled by timeline scrubber). "
  "Crosshair line moves vertically across all rows simultaneously. "
  "Each row has its own Y-axis and can be individually toggled. "
  "Compact mode: sparkline versions. Expanded mode: full charts.")

t(38, "Integrate timeline scrubber into simulation workspace",
  "Update frontend/src/views/SimulationWorkspaceView.vue to include the timeline scrubber. "
  "Add TimelineScrubber as a fixed bar at the bottom of the simulation workspace. "
  "Wrap existing simulation charts (sentiment, interactions, etc.) in SyncedChart wrappers. "
  "Add EventMarkers above the scrubber. "
  "In replay mode: timeline controls the replay position (replaces ReplayViewer transport controls). "
  "In live mode: timeline shows completed rounds and auto-advances. "
  "Add MultiMetricView as an alternative to individual chart panels. "
  "The timeline becomes the central navigation element for simulation data.")

# ═══════════════════════════════════════════════════════
# GROUP 39: Advanced D3 Charts (10 tasks)
# ═══════════════════════════════════════════════════════
t(39, "Build radar chart component",
  "Create frontend/src/components/charts/RadarChart.vue — reusable D3.js radar/spider chart. "
  "Props: data (array of {label, values: {seriesName: value}}), maxValue, levels (grid circles), showLegend. "
  "Multiple overlapping polygons for comparing series (e.g., Agent A vs Agent B personality traits). "
  "Grid circles with value labels. Axis labels at each spoke. "
  "Tooltip on hover: axis name, all series values at that axis. "
  "Color per series from brand palette. Legend with toggleable series. "
  "Animated mount: polygons expand from center. Responsive to container size.")

t(39, "Build parallel coordinates chart component",
  "Create frontend/src/components/charts/ParallelCoordinates.vue — D3.js parallel coordinates plot. "
  "Props: data (array of objects), dimensions (array of axis configs), colorBy (field name). "
  "Each vertical axis is a dimension. Lines connect data points across all dimensions. "
  "Line color based on a categorical field (e.g., segment, outcome). "
  "Brushable axes: drag to select range on any axis, filter lines accordingly. "
  "Axis reordering: drag axis labels to reorder. "
  "Highlighted line on hover with all other lines dimmed. "
  "Use for: comparing agents across multiple metrics, comparing accounts across dimensions.")

t(39, "Build chord diagram component",
  "Create frontend/src/components/charts/ChordDiagram.vue — D3.js chord diagram. "
  "Props: matrix (NxN flow matrix), labels (array of names), colors (array). "
  "Arcs around the circle for each entity. Chords connecting entities with flow thickness. "
  "Hover arc: highlight all chords connected to that entity. Hover chord: show flow value. "
  "Tooltip with exact values. Legend if color-coded by type. "
  "Use for: agent-to-agent communication volume, data flow between systems. "
  "Animated mount: chords grow from zero. Responsive.")

t(39, "Build sunburst chart component",
  "Create frontend/src/components/charts/SunburstChart.vue — D3.js hierarchical sunburst. "
  "Props: data (tree structure with value at leaves), colorScheme, centerLabel. "
  "Concentric rings showing hierarchy: inner ring = top level, outer = leaves. "
  "Arc size proportional to value. Click to zoom into a segment (becomes new center). "
  "Breadcrumb trail showing current zoom path. Back button to zoom out. "
  "Tooltip on hover: name, value, percentage of parent. "
  "Use for: account revenue by industry → plan → size, pipeline by stage → owner → product. "
  "Animated transitions when zooming.")

t(39, "Build streamgraph component",
  "Create frontend/src/components/charts/StreamGraph.vue — D3.js streamgraph (stacked area with flowing shape). "
  "Props: data (time series with multiple categories), colorScheme, interpolation. "
  "Smooth flowing shape showing how category proportions change over time. "
  "Hover: highlight single stream, show value and percentage. "
  "Legend with toggleable categories. Click category to isolate. "
  "Use for: topic evolution over simulation rounds, revenue mix over time. "
  "Use d3.stackOffsetWiggle for aesthetic baseline. Animated mount.")

t(39, "Build bullet chart component",
  "Create frontend/src/components/charts/BulletChart.vue — D3.js bullet chart for KPI targets. "
  "Props: metrics (array of {label, actual, target, ranges: [poor, ok, good]}). "
  "Each metric as a horizontal bar: gray range bands, black bar for actual, red marker for target. "
  "Compact format: multiple bullet charts stacked vertically. "
  "Use for: KPI target achievement (quota attainment, pipeline coverage, NRR target). "
  "Color actual bar: red if below poor threshold, yellow if in ok range, green if in good range. "
  "Responsive with proper label truncation.")

t(39, "Build calendar heatmap component",
  "Create frontend/src/components/charts/CalendarHeatmap.vue — GitHub-style contribution calendar. "
  "Props: data (array of {date, value}), colorScheme, monthsToShow, tooltipFormatter. "
  "Grid of small squares: each day is a square. Color intensity by value. "
  "Month labels on top. Day-of-week labels on left. "
  "Hover: tooltip with date and value. Click: emit event with date for filtering. "
  "Use for: daily deal activity, daily sync job status, daily simulation runs. "
  "Color scale: white (no activity) to dark blue (high activity). "
  "Responsive: scroll horizontally if not enough width.")

t(39, "Build small multiples chart component",
  "Create frontend/src/components/charts/SmallMultiples.vue — D3.js small multiples layout. "
  "Props: data (array of datasets), chartType ('line'|'bar'|'area'), columns, sharedYAxis. "
  "Renders the same chart type for each dataset in a grid layout. "
  "All charts share the same scale when sharedYAxis=true for easy comparison. "
  "Individual chart hover shows value. Cross-chart hover highlights same X position across all charts. "
  "Use for: comparing metrics across agents, comparing funnel shapes across months. "
  "Grid layout adapts to number of datasets. Title for each small chart.")

t(39, "Build chart theme and utility library",
  "Create frontend/src/lib/chartUtils.js — shared utilities for all D3 charts. "
  "Exports: brandColorScale (categorical), sentimentColorScale (diverging green-red), "
  "quantitativeColorScale (sequential blue), formatCurrency, formatPercentage, formatNumber, "
  "responsiveResize (handles window resize for D3 charts), createTooltip (standard tooltip creator), "
  "axisFormatter (consistent axis label formatting), chartMargins (standard margin convention). "
  "Brand palette: #2068FF (primary), #050505 (navy), #ff5600 (orange), #A0F (accent), plus 6 additional chart colors. "
  "All chart components should import from this shared library.")

t(39, "Create Charts Gallery view",
  "Create a section in the existing VisualizationsShowcaseView.vue for the advanced chart gallery. "
  "Or extend the page to include: 'Advanced Charts' section with one example of each chart type: "
  "Radar (agent personality comparison), Parallel Coords (account multi-dimensional analysis), "
  "Chord (agent communication flow), Sunburst (revenue hierarchy), Stream (topic evolution), "
  "Bullet (KPI targets), Calendar (activity heatmap), Small Multiples (monthly comparisons). "
  "Each chart has a brief description and sample data. Interactive — users can explore. "
  "This serves as both a demo gallery and a component reference.")

# ═══════════════════════════════════════════════════════
# GROUP 40: Comparative Analytics (8 tasks)
# ═══════════════════════════════════════════════════════
t(40, "Create comparison data service",
  "Create backend/app/services/comparison_service.py — service for comparing simulations side by side. "
  "ComparisonService class: "
  "1) `compare_simulations(sim_id_a, sim_id_b)` → structured comparison across all metrics. "
  "2) `compare_agents(sim_id, agent_id_a, agent_id_b)` → agent-level comparison. "
  "3) `compare_scenarios(scenario_type, sim_ids)` → compare multiple runs of same scenario. "
  "4) `compute_statistical_significance(metric_a, metric_b)` → basic stat test for meaningful difference. "
  "Return ComparisonResult: {dimensions: [{name, sim_a_value, sim_b_value, difference, winner, significant}]}. "
  "Add API endpoint: GET /api/simulations/compare?ids=a,b")

t(40, "Build side-by-side comparison layout component",
  "Create frontend/src/components/comparison/ComparisonLayout.vue — split-screen comparison view. "
  "Left panel: Simulation A. Right panel: Simulation B. "
  "Header: simulation selectors (dropdowns), swap button, sync toggle. "
  "Sync toggle: when on, scrolling/interacting in one panel mirrors in the other. "
  "Divider bar: draggable to resize panels. Double-click to reset to 50/50. "
  "Each panel renders the same set of charts/metrics for its simulation. "
  "Difference overlay: toggle to show only where A and B differ.")

t(40, "Build comparison metrics table component",
  "Create frontend/src/components/comparison/ComparisonTable.vue — metrics comparison table. "
  "Columns: Metric, Simulation A, Simulation B, Difference, Winner, Statistical Significance. "
  "Rows: all comparable metrics (sentiment, consensus, decisions, agent engagement, etc.). "
  "Color-code winner column: A=blue, B=orange, Tie=gray. "
  "Significant differences highlighted with bold. "
  "Sortable by any column. Grouped by category (Engagement, Sentiment, Outcomes, etc.). "
  "Summary row: overall comparison score (how many metrics each simulation 'won').")

t(40, "Build comparative chart overlays",
  "Create frontend/src/components/comparison/ChartOverlay.vue — overlay two datasets on one chart. "
  "Props: chartType ('line'|'bar'|'area'), dataA, dataB, labelA, labelB. "
  "Renders both datasets on the same axes with different colors (blue for A, orange for B). "
  "Toggle buttons: show A only, show B only, show both, show difference. "
  "'Difference' mode: chart shows the delta between A and B values. "
  "Use for: overlaying sentiment trends, comparing pipeline progressions. "
  "Shared tooltip showing both values on hover. D3.js based.")

t(40, "Build A/B scenario builder component",
  "Create frontend/src/components/comparison/AbScenarioBuilder.vue — set up A/B comparison experiments. "
  "Select base scenario. Choose variable to change: LLM provider, agent count, personality distribution, "
  "round count, temperature setting. "
  "Configure A variant and B variant (the single changed parameter). "
  "Run both simulations in parallel with a 'Run A/B Test' button. "
  "Progress bar for each simulation. When both complete, auto-navigate to comparison view. "
  "Save A/B test configurations for repeatability.")

t(40, "Build comparison radar chart component",
  "Create frontend/src/components/comparison/ComparisonRadar.vue — radar chart showing two simulations. "
  "Dimensions: overall sentiment, consensus reached, decision quality, agent engagement, "
  "information spread, outcome satisfaction. "
  "Two overlapping polygons (blue=A, orange=B). "
  "Click dimension label to see detailed breakdown of that dimension's scoring. "
  "Summary text: 'Simulation A excels at X, while Simulation B performs better on Y.' "
  "Auto-generated from comparison service data.")

t(40, "Build comparison timeline component",
  "Create frontend/src/components/comparison/ComparisonTimeline.vue — synchronized dual timeline. "
  "Two stacked timelines (A on top, B on bottom) with shared X-axis. "
  "Events plotted on each timeline at the round they occurred. "
  "Visual links between similar events in A and B (e.g., both reached a decision at round 5 vs 7). "
  "Highlight divergence points: where outcomes differed. "
  "Shared scrubber control that moves both timelines together. "
  "Color-coded events matching the A/B color scheme.")

t(40, "Create Comparison view",
  "Create frontend/src/views/ComparisonView.vue — the comparison analytics page. "
  "Layout: ComparisonLayout containing: "
  "Top: ComparisonTable showing overall metrics comparison. "
  "Middle: ComparisonRadar (left 1/3) + ChartOverlay (right 2/3) showing selected metric over time. "
  "Bottom: ComparisonTimeline (full width). "
  "Sidebar: AbScenarioBuilder for setting up new comparisons. "
  "Add route: { path: '/comparison', name: 'Comparison', component: ComparisonView }. "
  "Accessible from simulation results via 'Compare' button. Also direct nav access.")

# ═══════════════════════════════════════════════════════
# GROUP 41: Mini-map + Activity Feed (8 tasks)
# ═══════════════════════════════════════════════════════
t(41, "Build navigation mini-map component",
  "Create frontend/src/components/common/NavigationMiniMap.vue — a mini-map showing system overview. "
  "Small rectangular overview in bottom-right corner showing all GTM data dimensions. "
  "Dots/icons: revenue (green), pipeline (blue), orders (orange), accounts (purple). "
  "Dot size: proportional to metric magnitude. Dot brightness: recency of activity. "
  "Click a dot to navigate to that view. Current page highlighted with a box outline. "
  "Collapsible: click toggle to expand/collapse. Remember state in localStorage. "
  "Use SVG for crisp rendering at small sizes. z-index above other content.")

t(41, "Build global activity feed service",
  "Create backend/app/services/activity_feed.py — aggregates activity across all GTM domains. "
  "ActivityFeedService class: "
  "1) `get_recent(limit, types, since)` → list of activity items. "
  "Activity types: deal_update, lead_scored, churn_risk, sync_complete, simulation_finished, "
  "report_generated, reconciliation_alert, order_provisioned, pipeline_milestone. "
  "Each activity: id, type, title, description, timestamp, severity (info|warning|critical), related_entity. "
  "Generate 50 realistic activities spread over last 24 hours using data from all generator services. "
  "Add API endpoint: GET /api/activity?limit=20&types=deal_update,churn_risk&since=ISO_DATE")

t(41, "Build global activity feed component",
  "Create frontend/src/components/common/GlobalActivityFeed.vue — real-time activity feed sidebar. "
  "Renders as a slide-out panel from the right edge, triggered by a bell icon in navbar. "
  "Each activity item: type icon, title, description, timestamp (relative), severity badge. "
  "Critical items: red background with pulsing dot. Warning: yellow highlight. Info: normal style. "
  "Category filter tabs: All, Deals, Leads, Risk, System. "
  "Unread count badge on the bell icon. Mark as read on view. "
  "Auto-refresh every 30 seconds. Smooth animations for new items. "
  "Maximum height with scrollable content.")

t(41, "Build notification toast system",
  "Create frontend/src/components/common/NotificationToast.vue — toast notification system. "
  "Types: success (green), warning (yellow), error (red), info (blue). "
  "Appears in top-right corner. Auto-dismiss after 5 seconds (configurable). "
  "Click to dismiss. Optional action button (e.g., 'View Details'). "
  "Stack multiple toasts vertically. Animate in from right, fade out. "
  "Create frontend/src/composables/useNotifications.js composable: "
  "notify({title, message, type, duration, action}). Inject anywhere in the app. "
  "Update existing components to use this system for feedback messages.")

t(41, "Build breadcrumb navigation component",
  "Create frontend/src/components/common/Breadcrumbs.vue — hierarchical breadcrumb navigation. "
  "Auto-generates breadcrumbs from current route path and router meta fields. "
  "Example: Home > GTM Dashboard > Revenue > Account Detail. "
  "Last item is current page (not clickable). Others are links. "
  "Separator: chevron icon. Responsive: collapse middle items on mobile with '...' ellipsis. "
  "Add meta.breadcrumb to all routes in router/index.js. "
  "Place at top of main content area in the app layout.")

t(41, "Build quick search/command palette component",
  "Create frontend/src/components/common/CommandPalette.vue — Cmd+K style search palette. "
  "Opens with Ctrl/Cmd+K keyboard shortcut. "
  "Search across: page names (navigate), accounts (go to account), simulations, reports, metrics. "
  "Sections: Navigation (pages), Data (accounts, opportunities), Actions (create simulation, generate report). "
  "Fuzzy search with highlighting of matched characters. "
  "Keyboard navigation: arrow keys to select, Enter to execute, Escape to close. "
  "Recent searches shown by default. Popular actions pinned at top. "
  "Use overlay with semi-transparent backdrop. Smooth animation open/close.")

t(41, "Build system status bar component",
  "Create frontend/src/components/common/SystemStatusBar.vue — thin status bar at the very bottom of the app. "
  "Shows: current data mode (Full/Partial/Demo), active simulation count, last data refresh time, "
  "WebSocket connection status (green dot = connected), API response time (avg last 10 requests). "
  "Compact single-line format, 24px height, monospace font for data. "
  "Expandable on click: shows detailed system info (version, API endpoint, feature flags). "
  "Background color subtle: green tint for healthy, yellow for degraded, red for issues. "
  "Only visible in development mode or when user enables it in settings.")

t(41, "Integrate mini-map and activity feed into app layout",
  "Update the main app layout (frontend/src/App.vue or layout component) to include: "
  "1) NavigationMiniMap in bottom-right corner (persistent, collapsible). "
  "2) GlobalActivityFeed triggered by bell icon in AppNav.vue (slide-out panel). "
  "3) Breadcrumbs at top of main content area. "
  "4) NotificationToast provider wrapping the app. "
  "5) CommandPalette overlay (Cmd+K activated). "
  "6) SystemStatusBar at the very bottom (toggle in settings). "
  "Ensure z-index ordering: palette > activity feed > toasts > mini-map > status bar. "
  "Update AppNav.vue: add bell icon with unread count, add Cmd+K hint in search area.")

# Write output
if __name__ == "__main__":
    print(f"Generated {len(NEW_TASKS)} tasks for groups 26-41")
    with open("tmp/tasks_26_41.json", "w") as f:
        json.dump(NEW_TASKS, f, indent=2)
    print(f"Saved to tmp/tasks_26_41.json")
