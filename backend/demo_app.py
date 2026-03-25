"""
MiroFish Demo Backend — Lightweight mock Flask server.

Serves realistic, pre-built demo data for all frontend endpoints so the app
can run without the heavy camel-ai / PyTorch production backend.  Total
image size drops from ~5.8 GB to ~150 MB.
"""

import json
import logging
import math
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

# Load .env from project root (one level up from backend/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
load_dotenv(override=True)

from llm_client import chat_completion  # noqa: E402

log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

SCENARIOS_DIR = Path(__file__).parent / "gtm_scenarios"

# ---------------------------------------------------------------------------
# In-memory state tracking for progressive endpoints
# ---------------------------------------------------------------------------
_graph_tasks: dict = {}     # task_id -> {"start": float}
_simulations: dict = {}     # sim_id  -> {"start": float}
_reports: dict = {}         # report_id -> {"start": float, "sim_id": str}

_BASE_GRAPH_BUILD_SECONDS = 6
_BASE_SIMULATION_RUN_SECONDS = 35
_BASE_REPORT_GEN_SECONDS = 18
TOTAL_ROUNDS = 144

_demo_speed = float(os.environ.get("DEMO_SPEED", "1.0"))


def _speed():
    return max(0.1, _demo_speed)


def GRAPH_BUILD_SECONDS():
    return _BASE_GRAPH_BUILD_SECONDS / _speed()


def SIMULATION_RUN_SECONDS():
    return _BASE_SIMULATION_RUN_SECONDS / _speed()


def REPORT_GEN_SECONDS():
    return _BASE_REPORT_GEN_SECONDS / _speed()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data):
    return jsonify({"success": True, "data": data})


def _err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


def _elapsed(store, key):
    entry = store.get(key)
    if not entry:
        return 0.0
    return time.time() - entry["start"]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "mode": "demo"})


# ---------------------------------------------------------------------------
# GTM Scenarios
# ---------------------------------------------------------------------------

def _load_scenarios():
    scenarios = []
    for p in sorted(SCENARIOS_DIR.glob("*.json")):
        with open(p) as f:
            scenarios.append(json.load(f))
    return scenarios


@app.route("/api/gtm/scenarios")
def list_scenarios():
    return jsonify({"scenarios": _load_scenarios()})


@app.route("/api/gtm/scenarios/<scenario_id>")
def get_scenario(scenario_id):
    for s in _load_scenarios():
        if s["id"] == scenario_id:
            return jsonify(s)
    return _err("Scenario not found", 404)


@app.route("/api/gtm/scenarios/<scenario_id>/seed-text")
def get_seed_text(scenario_id):
    for s in _load_scenarios():
        if s["id"] == scenario_id:
            return _ok({"seed_text": s.get("seed_text", "")})
    return _err("Scenario not found", 404)


@app.route("/api/gtm/seed-data/<data_type>")
def get_seed_data(data_type):
    samples = {
        "companies": [
            {"name": "Acme SaaS", "size": "500-1000", "industry": "SaaS"},
            {"name": "MedFirst Health", "size": "1000-2000", "industry": "Healthcare"},
            {"name": "PayStream Financial", "size": "200-500", "industry": "Fintech"},
            {"name": "ShopNova", "size": "500-1000", "industry": "E-commerce"},
            {"name": "CloudOps Inc", "size": "1000-2000", "industry": "SaaS"},
        ],
        "personas": [
            {"name": "Sarah Chen", "title": "VP of Support", "company": "Acme SaaS"},
            {"name": "Marcus Johnson", "title": "CX Director", "company": "MedFirst Health"},
            {"name": "Priya Patel", "title": "Head of Operations", "company": "PayStream Financial"},
            {"name": "David Kim", "title": "IT Leader", "company": "ShopNova"},
            {"name": "Rachel Torres", "title": "VP of Support", "company": "CloudOps Inc"},
        ],
    }
    return _ok(samples.get(data_type, []))


# ---------------------------------------------------------------------------
# Graph API
# ---------------------------------------------------------------------------

@app.route("/api/graph/build", methods=["POST"])
def graph_build():
    task_id = f"demo-graph-{int(time.time()) % 100000:05d}"
    _graph_tasks[task_id] = {"start": time.time()}
    return jsonify({"success": True, "task_id": task_id, "status": "building"})


@app.route("/api/graph/task/<task_id>")
def graph_task(task_id):
    if task_id not in _graph_tasks:
        _graph_tasks[task_id] = {"start": time.time()}

    elapsed = _elapsed(_graph_tasks, task_id)
    pct = min(100, int(elapsed / GRAPH_BUILD_SECONDS() * 100))

    if pct >= 100:
        return _ok({
            "status": "completed",
            "progress": 100,
            "message": "Knowledge graph built successfully",
            "result": {"graph_id": task_id},
        })

    messages = [
        (0, "Parsing seed document..."),
        (15, "Extracting entities and relationships..."),
        (35, "Building persona nodes..."),
        (55, "Mapping topic clusters..."),
        (75, "Computing relationship weights..."),
        (90, "Finalizing graph structure..."),
    ]
    msg = "Initializing..."
    for threshold, m in messages:
        if pct >= threshold:
            msg = m

    return _ok({
        "status": "building",
        "progress": pct,
        "message": msg,
    })


@app.route("/api/graph/data/<graph_id>")
def graph_data(graph_id):
    nodes, edges = _build_knowledge_graph()
    return _ok({
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    })


def _build_knowledge_graph():
    personas = [
        ("Sarah Chen, VP Support @ Acme SaaS", "Persona", "Decision-maker evaluating AI-first support. Currently on Zendesk, frustrated with resolution times and escalation queues."),
        ("Marcus Johnson, CX Director @ MedFirst Health", "Persona", "Healthcare CX leader focused on HIPAA-compliant customer interactions. Evaluates tools through compliance lens first."),
        ("Priya Patel, Head of Ops @ PayStream Financial", "Persona", "Fintech operations leader managing 200-person support team. Obsessed with cost-per-ticket metrics."),
        ("David Kim, IT Leader @ ShopNova", "Persona", "E-commerce IT decision-maker. Prioritizes API integrations and Shopify/Salesforce ecosystem fit."),
        ("Rachel Torres, VP Support @ CloudOps Inc", "Persona", "Enterprise support leader at 2,000-employee SaaS. Champions AI-augmented agents over full automation."),
        ("James Wright, CX Director @ Retail Plus", "Persona", "Retail CX director managing holiday surge planning. Seasonal volume spikes are top concern."),
        ("Anika Sharma, Head of Support Engineering @ DevStack", "Persona", "Technical support leader with strong opinions on chatbot accuracy. Has failed Zendesk AI deployment in past."),
        ("Tom O'Brien, VP Customer Success @ GrowthLoop", "Persona", "Post-sale leader focused on NPS and expansion revenue. Sees support as retention lever."),
        ("Elena Vasquez, Director of Digital @ HealthBridge", "Persona", "Digital transformation leader in healthcare. Evaluating omnichannel patient communication."),
        ("Michael Chang, Head of Operations @ FinEdge", "Persona", "Operations leader at fintech startup. Budget-conscious, looking for 10x efficiency gains."),
        ("Lisa Park, VP CX @ TravelNow", "Persona", "Travel industry CX leader dealing with high-volume, emotionally-charged interactions."),
        ("Robert Williams, IT Director @ EduSpark", "Persona", "EdTech IT leader evaluating student-facing support automation."),
        ("Sofia Martinez, Support Manager @ QuickShip", "Persona", "Mid-market support manager. Hands-on, evaluates tools by agent adoption rate."),
        ("Nathan Lee, CTO @ DataPulse Analytics", "Persona", "Technical founder who builds internal tooling. Skeptical of vendor lock-in."),
        ("Catherine Hayes, CFO @ ScaleUp Corp", "Persona", "Finance leader evaluating support tool ROI. Focused on cost reduction and headcount efficiency."),
    ]

    topics = [
        ("AI-First Support Resolution", "Topic", "Using LLM-powered agents to resolve customer issues without human intervention. Fin agent handles Tier 1 autonomously."),
        ("Zendesk Migration Pain", "Topic", "Common friction points when migrating from Zendesk: ticket history, macros, agent workflows, and reporting dependencies."),
        ("Fin Agent Deployment", "Topic", "Intercom's Fin AI agent — deployment timeline, training requirements, accuracy benchmarks, and resolution rate targets."),
        ("ROI-Driven Messaging", "Topic", "Positioning support automation through cost savings: reduce cost-per-ticket by 40-60%, handle 10x volume without hiring."),
        ("Speed-to-Value Positioning", "Topic", "Deploy in weeks not months messaging. Contrast with 6-month Zendesk AI setup cycles."),
        ("Competitive Displacement Strategy", "Topic", "Targeting Zendesk, Freshdesk, and HubSpot Service Hub customers with migration-focused campaigns."),
        ("Support Cost Optimization", "Topic", "Metrics and strategies for reducing support overhead: automation rate, deflection, first-contact resolution."),
        ("Omnichannel Customer Communication", "Topic", "Unified messaging across email, chat, social, and phone. Intercom Messenger as the hub."),
        ("AI Accuracy and Trust", "Topic", "Customer concerns about chatbot hallucination, incorrect answers, and brand risk from AI responses."),
        ("Agent Augmentation vs Replacement", "Topic", "Two philosophies: AI fully replacing Tier 1 agents vs. AI augmenting human agents with suggested responses."),
        ("Compliance and Data Security", "Topic", "HIPAA, SOC2, GDPR requirements for customer support tools. Healthcare and fintech are particularly sensitive."),
        ("Email Personalization at Scale", "Topic", "AI-generated personalized outreach: tone matching, pain-point targeting, and engagement optimization."),
        ("Outbound Cadence Optimization", "Topic", "Optimal email sequence timing, follow-up intervals, and channel mix for B2B SaaS outbound."),
        ("Spam Perception Risk", "Topic", "How aggressive subject lines and competitive displacement messaging can trigger spam filters or negative brand perception."),
        ("Expansion Revenue through Support", "Topic", "Using support interactions to identify upsell opportunities and drive net revenue retention."),
        ("Support Team Retention", "Topic", "How AI tools affect support agent job satisfaction, career growth, and turnover rates."),
        ("Self-Service Knowledge Base", "Topic", "Building and maintaining help centers that reduce ticket volume. Integration with AI for smart article suggestions."),
        ("Customer Sentiment Analysis", "Topic", "Real-time analysis of customer mood during support interactions to trigger escalation or retention plays."),
        ("Platform Integration Ecosystem", "Topic", "Salesforce, HubSpot, Shopify, Slack integrations. API extensibility and marketplace app availability."),
        ("Proactive Support Strategy", "Topic", "Anticipating customer issues before they arise using product usage signals and predictive models."),
    ]

    relationships = [
        ("Zendesk-to-Intercom Migration Path", "Relationship", "Structured migration process: data export, workflow mapping, agent training, go-live. Average 4-6 weeks."),
        ("AI Pilot Program Structure", "Relationship", "Phased rollout: 10% traffic -> 25% -> 50% -> 100%. Measure resolution rate and CSAT at each gate."),
        ("Competitive Evaluation Framework", "Relationship", "Head-to-head comparison methodology for support platforms: features, pricing, integration, AI capability, support."),
        ("Champion-CFO Alignment", "Relationship", "Internal selling motion: CX champion builds business case, CFO approves based on ROI and headcount impact."),
        ("Support-to-Sales Handoff", "Relationship", "Process for routing expansion signals from support interactions to account management team."),
        ("Vendor Lock-in Concerns", "Relationship", "Technical and contractual barriers to switching support platforms. Data portability and API dependency risks."),
        ("Budget Approval Cycle", "Relationship", "Enterprise procurement timeline: tech eval (4 weeks) -> security review (2 weeks) -> legal (2 weeks) -> sign-off (1 week)."),
        ("Team Adoption Resistance", "Relationship", "Change management challenges when introducing new tools. Agent training, workflow disruption, and productivity dip."),
        ("Multi-Stakeholder Decision", "Relationship", "Support tool purchases involve CX, IT, Finance, and Security teams. Average 4.2 stakeholders in buying committee."),
        ("AI Trust Building Process", "Relationship", "Steps to earn organizational trust in AI: pilot with low-risk tickets, build confidence with metrics, expand scope gradually."),
    ]

    companies = [
        ("Acme SaaS", "Company", "Mid-market SaaS company, 800 employees. Currently on Zendesk Suite Enterprise. $18K/mo support tool spend."),
        ("MedFirst Health", "Company", "Healthcare technology provider, 1,500 employees. HIPAA requirements dominate all vendor evaluations."),
        ("PayStream Financial", "Company", "Series C fintech, 400 employees. Rapid growth creating support scaling challenges. Currently on Freshdesk."),
        ("ShopNova", "Company", "E-commerce platform, 700 employees. High-volume seasonal support. Shopify ecosystem dependency."),
        ("CloudOps Inc", "Company", "Enterprise SaaS, 2,000 employees. Complex B2B support needs. Evaluating Intercom for technical support automation."),
        ("GrowthLoop", "Company", "Growth-stage SaaS, 300 employees. Customer success-driven model. Support is a retention lever."),
        ("HealthBridge", "Company", "Digital health platform, 1,200 employees. Patient-facing communication needs. HIPAA and accessibility requirements."),
        ("FinEdge", "Company", "Early-stage fintech, 150 employees. Lean team needs maximum automation. Budget is primary constraint."),
        ("TravelNow", "Company", "Online travel agency, 900 employees. Emotional support interactions require nuanced AI responses."),
        ("DataPulse Analytics", "Company", "Data analytics startup, 200 employees. API-first culture, builds custom integrations for everything."),
    ]

    all_entities = []
    for i, (name, label, summary) in enumerate(personas, start=1):
        all_entities.append({
            "uuid": str(i),
            "name": name,
            "labels": ["Entity", label],
            "summary": summary,
            "attributes": {"type": label.lower()},
        })
    offset = len(all_entities)
    for i, (name, label, summary) in enumerate(topics, start=offset + 1):
        all_entities.append({
            "uuid": str(i),
            "name": name,
            "labels": ["Entity", label],
            "summary": summary,
            "attributes": {"type": label.lower()},
        })
    offset = len(all_entities)
    for i, (name, label, summary) in enumerate(relationships, start=offset + 1):
        all_entities.append({
            "uuid": str(i),
            "name": name,
            "labels": ["Entity", label],
            "summary": summary,
            "attributes": {"type": label.lower()},
        })
    offset = len(all_entities)
    for i, (name, label, summary) in enumerate(companies, start=offset + 1):
        all_entities.append({
            "uuid": str(i),
            "name": name,
            "labels": ["Entity", label],
            "summary": summary,
            "attributes": {"type": label.lower()},
        })

    num_nodes = len(all_entities)

    edge_defs = [
        ("1", "16", "evaluates", "Sarah Chen is evaluating AI-first support to replace Zendesk at Acme SaaS."),
        ("1", "17", "experiencing", "Sarah Chen's team experiences significant Zendesk migration pain points."),
        ("1", "18", "pilots", "Sarah Chen is running a Fin agent pilot with 10% of support traffic."),
        ("1", "46", "works_at", "Sarah Chen is VP Support at Acme SaaS."),
        ("2", "26", "requires", "Marcus Johnson requires HIPAA compliance for all support tooling."),
        ("2", "23", "manages", "Marcus Johnson manages omnichannel communication across MedFirst channels."),
        ("2", "47", "works_at", "Marcus Johnson is CX Director at MedFirst Health."),
        ("3", "22", "focuses_on", "Priya Patel focuses on support cost optimization metrics."),
        ("3", "19", "responds_to", "Priya Patel responds strongly to ROI-driven messaging."),
        ("3", "48", "works_at", "Priya Patel is Head of Operations at PayStream Financial."),
        ("4", "34", "prioritizes", "David Kim prioritizes platform integration ecosystem fit."),
        ("4", "49", "works_at", "David Kim is IT Leader at ShopNova."),
        ("4", "24", "skeptical_of", "David Kim is skeptical of AI accuracy claims without proof."),
        ("5", "25", "champions", "Rachel Torres champions agent augmentation over full replacement."),
        ("5", "18", "evaluates", "Rachel Torres evaluates Fin for enterprise technical support."),
        ("5", "50", "works_at", "Rachel Torres is VP Support at CloudOps Inc."),
        ("6", "16", "seeks", "James Wright seeks AI support for seasonal volume management."),
        ("6", "22", "measures", "James Wright measures success by cost-per-ticket reduction."),
        ("7", "24", "concerns_about", "Anika Sharma has deep concerns about AI accuracy from past failures."),
        ("7", "18", "testing", "Anika Sharma is testing Fin with controlled traffic after Zendesk AI failure."),
        ("8", "30", "leverages", "Tom O'Brien leverages support interactions to drive expansion revenue."),
        ("8", "51", "works_at", "Tom O'Brien is VP Customer Success at GrowthLoop."),
        ("9", "23", "implements", "Elena Vasquez is implementing omnichannel patient communication."),
        ("9", "26", "bound_by", "Elena Vasquez is bound by HIPAA and accessibility requirements."),
        ("9", "52", "works_at", "Elena Vasquez works at HealthBridge."),
        ("10", "22", "optimizes", "Michael Chang optimizes for maximum automation on lean budget."),
        ("10", "53", "works_at", "Michael Chang is Head of Operations at FinEdge."),
        ("11", "33", "uses", "Lisa Park uses customer sentiment analysis for escalation."),
        ("11", "25", "prefers", "Lisa Park prefers AI augmentation for emotionally-charged travel interactions."),
        ("12", "32", "builds", "Robert Williams builds self-service knowledge base for student support."),
        ("13", "31", "measures_by", "Sofia Martinez measures tool success by support team adoption rate."),
        ("14", "34", "evaluates", "Nathan Lee evaluates platforms by API extensibility and data portability."),
        ("14", "41", "wary_of", "Nathan Lee is wary of vendor lock-in with proprietary platforms."),
        ("15", "19", "driven_by", "Catherine Hayes is driven by ROI and headcount efficiency metrics."),
        ("15", "42", "oversees", "Catherine Hayes oversees budget approval cycle for support tools."),
        ("16", "18", "enables", "AI-first support resolution is the core value prop of Fin agent deployment."),
        ("17", "21", "drives", "Zendesk migration pain drives competitive displacement strategy opportunities."),
        ("18", "20", "validates", "Successful Fin deployment validates speed-to-value positioning."),
        ("19", "15", "persuades", "ROI-driven messaging is the primary lever for persuading CFOs."),
        ("20", "17", "contrasts_with", "Speed-to-value positioning contrasts with slow Zendesk migration experiences."),
        ("21", "17", "targets", "Competitive displacement strategy directly targets Zendesk migration pain."),
        ("22", "16", "achieved_through", "Support cost optimization is achieved through AI-first resolution."),
        ("23", "18", "integrates_with", "Omnichannel communication integrates with Fin for unified AI responses."),
        ("24", "37", "mitigated_by", "AI accuracy concerns are mitigated by structured pilot programs."),
        ("25", "31", "improves", "Agent augmentation approach improves support team retention and satisfaction."),
        ("26", "52", "critical_for", "Compliance and data security is critical for HealthBridge operations."),
        ("27", "28", "informs", "Email personalization results inform outbound cadence optimization strategies."),
        ("28", "29", "must_avoid", "Outbound cadence must carefully avoid spam perception risk."),
        ("29", "21", "constrains", "Spam perception risk constrains how aggressive competitive displacement messaging can be."),
        ("30", "40", "flows_through", "Expansion revenue flows through support-to-sales handoff process."),
        ("32", "16", "reduces_need_for", "Self-service knowledge base reduces need for AI-first agent resolution."),
        ("33", "35", "enhances", "Customer sentiment analysis enhances proactive support strategy."),
        ("34", "41", "influences", "Platform integration ecosystem strength influences vendor lock-in concerns."),
        ("35", "33", "powered_by", "Proactive support strategy is powered by customer sentiment analysis."),
        ("36", "37", "structured_as", "Zen-to-Intercom migration follows AI pilot program structure."),
        ("37", "39", "builds_toward", "AI pilot program builds toward champion-CFO alignment with metrics."),
        ("38", "21", "informs", "Competitive evaluation framework informs competitive displacement strategy."),
        ("39", "42", "requires", "Champion-CFO alignment requires navigating budget approval cycle."),
        ("40", "30", "captures", "Support-to-sales handoff captures expansion revenue opportunities."),
        ("41", "14", "concerns", "Vendor lock-in concerns are top-of-mind for technical founders like Nathan Lee."),
        ("42", "44", "involves", "Budget approval cycle involves multi-stakeholder decision process."),
        ("43", "7", "affects", "Team adoption resistance affects technical leaders like Anika Sharma."),
        ("44", "42", "complicates", "Multi-stakeholder decisions complicate budget approval cycles."),
        ("45", "37", "essential_for", "AI trust building process is essential for successful pilot programs."),
        ("46", "17", "experiencing", "Acme SaaS is experiencing Zendesk migration pain firsthand."),
        ("47", "26", "requires", "MedFirst Health requires strict HIPAA compliance for all tools."),
        ("48", "22", "needs", "PayStream Financial needs aggressive support cost optimization."),
        ("49", "34", "depends_on", "ShopNova depends on Shopify ecosystem integration."),
        ("50", "25", "culture_of", "CloudOps Inc has a culture of agent augmentation over replacement."),
        ("51", "30", "model_of", "GrowthLoop's model centers on expansion revenue from existing customers."),
        ("52", "26", "mandates", "HealthBridge mandates HIPAA and accessibility in all patient-facing tools."),
        ("53", "22", "constrained_by", "FinEdge is constrained by lean budget for support tooling."),
        ("54", "11", "worries_about", "TravelNow worries about AI handling emotionally-charged customer interactions."),
        ("10", "20", "attracted_to", "Michael Chang is attracted to speed-to-value messaging for lean deployment."),
        ("13", "43", "experiences", "Sofia Martinez experiences team adoption resistance when rolling out new tools."),
        ("6", "54", "seasonal_at", "James Wright manages seasonal volume spikes at Retail Plus."),
        ("8", "33", "analyzes", "Tom O'Brien analyzes customer sentiment to identify expansion signals."),
        ("12", "16", "explores", "Robert Williams explores AI-first support for student-facing automation."),
        ("15", "44", "navigates", "Catherine Hayes navigates multi-stakeholder decisions for tool purchases."),
        ("11", "54", "works_at", "Lisa Park is VP CX at TravelNow."),
        ("14", "55", "works_at", "Nathan Lee is CTO at DataPulse Analytics."),
        ("9", "47", "works_at", "Elena Vasquez is Director of Digital at HealthBridge."),
    ]

    edges = []
    for i, (src, tgt, name, fact) in enumerate(edge_defs, start=1):
        if int(src) <= num_nodes and int(tgt) <= num_nodes:
            edges.append({
                "uuid": f"e{i}",
                "source_node_uuid": src,
                "target_node_uuid": tgt,
                "name": name,
                "fact": fact,
            })

    return all_entities, edges


# ---------------------------------------------------------------------------
# Simulation API
# ---------------------------------------------------------------------------

@app.route("/api/simulation/create", methods=["POST"])
def sim_create():
    sim_id = f"demo-sim-{int(time.time()) % 100000:05d}"
    _simulations[sim_id] = {"start": time.time()}
    return _ok({"simulation_id": sim_id, "status": "created"})


@app.route("/api/simulation/prepare", methods=["POST"])
def sim_prepare():
    body = request.get_json(silent=True) or {}
    sim_id = body.get("simulation_id", list(_simulations.keys())[-1] if _simulations else "demo-sim-00001")
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}
    return _ok({"simulation_id": sim_id, "status": "prepared"})


@app.route("/api/simulation/start", methods=["POST"])
def sim_start():
    body = request.get_json(silent=True) or {}
    sim_id = body.get("simulation_id", list(_simulations.keys())[-1] if _simulations else "demo-sim-00001")
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}
    else:
        _simulations[sim_id]["start"] = time.time()
    return _ok({"status": "running"})


@app.route("/api/simulation/<sim_id>/run-status")
def sim_run_status(sim_id):
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}

    elapsed = _elapsed(_simulations, sim_id)
    pct = min(100, elapsed / SIMULATION_RUN_SECONDS() * 100)
    current_round = min(TOTAL_ROUNDS, int(pct / 100 * TOTAL_ROUNDS))
    completed = pct >= 100

    base_actions = int(current_round * 8.5)
    twitter_actions = int(base_actions * 0.55)
    reddit_actions = base_actions - twitter_actions

    runner_status = "completed" if completed else "running"

    return _ok({
        "runner_status": runner_status,
        "progress_percent": min(100, int(pct)),
        "current_round": current_round,
        "total_rounds": TOTAL_ROUNDS,
        "total_actions_count": base_actions,
        "twitter_actions_count": twitter_actions,
        "reddit_actions_count": reddit_actions,
        "twitter_current_round": current_round,
        "reddit_current_round": max(0, current_round - 2),
        "twitter_completed": completed,
        "reddit_completed": completed,
        "simulated_hours": round(current_round * 0.5, 1),
        "total_simulation_hours": 72,
    })


@app.route("/api/simulation/<sim_id>/run-status/detail")
def sim_run_status_detail(sim_id):
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}

    elapsed = _elapsed(_simulations, sim_id)
    pct = min(100, elapsed / SIMULATION_RUN_SECONDS() * 100)
    current_round = max(1, min(TOTAL_ROUNDS, int(pct / 100 * TOTAL_ROUNDS)))

    actions = _generate_agent_actions(current_round)
    return _ok({
        "recent_actions": actions,
        "all_actions": actions,
    })


def _generate_agent_actions(current_round):
    agents = [
        ("Sarah Chen", "VP Support @ Acme SaaS"),
        ("Marcus Johnson", "CX Director @ MedFirst"),
        ("Priya Patel", "Head of Ops @ PayStream"),
        ("David Kim", "IT Leader @ ShopNova"),
        ("Rachel Torres", "VP Support @ CloudOps"),
        ("James Wright", "CX Director @ Retail Plus"),
        ("Anika Sharma", "Support Eng Lead @ DevStack"),
        ("Tom O'Brien", "VP CS @ GrowthLoop"),
        ("Elena Vasquez", "Dir Digital @ HealthBridge"),
        ("Michael Chang", "Head of Ops @ FinEdge"),
        ("Lisa Park", "VP CX @ TravelNow"),
        ("Sofia Martinez", "Support Mgr @ QuickShip"),
        ("Nathan Lee", "CTO @ DataPulse"),
        ("Catherine Hayes", "CFO @ ScaleUp Corp"),
        ("Robert Williams", "IT Director @ EduSpark"),
    ]

    action_templates = [
        ("CREATE_POST", "twitter", [
            "Just evaluated @interaboratory's Fin AI agent — resolved 47% of our Tier 1 tickets in the pilot. Zendesk's AI Answer Bot never cracked 20%. The difference is night and day.",
            "Hot take: any support team still manually routing tickets in 2026 is leaving 40% efficiency on the table. AI-first resolution isn't the future, it's the present.",
            "Our team deployed Fin in 3 weeks. THREE WEEKS. Our Zendesk migration took 6 months. Let that sink in.",
            "Ran the numbers: switching to Intercom's Fin agent would save us $280K/yr in support costs. CFO's attention: captured.",
            "The 'AI will replace support agents' narrative is wrong. The right framing is AI handling the repetitive 60% so your agents can do the meaningful 40%.",
            "Just got our Q1 support metrics: 52% AI resolution rate, CSAT actually went UP 8 points. The skeptics on my team are converts now.",
            "Interesting pattern: our Fin deployment handles password resets and billing questions flawlessly, but struggles with nuanced product feedback. Know your automation boundaries.",
            "Comparing support platforms for our 2026 renewal: Intercom's API ecosystem is genuinely impressive. Salesforce, HubSpot, Slack — all native.",
        ]),
        ("CREATE_POST", "reddit", [
            "Our company switched from Zendesk to Intercom 6 months ago. Here's our honest review after processing 150K tickets through Fin AI: resolution rate went from 12% to 48%, CSAT improved 6 points, and we redeployed 3 agents to proactive outreach. AMA.",
            "PSA for anyone evaluating support platforms: request a 30-day pilot with REAL ticket data, not demo scenarios. We caught 4 critical gaps in Zendesk's AI that we would have missed with their canned demo.",
            "Unpopular opinion: the cost-per-ticket metric everyone obsesses over is misleading. What matters is cost-per-RESOLUTION. A $2 ticket that gets reopened 3 times costs $6.",
        ]),
        ("REPLY", "twitter", [
            "Agreed — we saw similar results. The key was starting with high-volume, low-complexity tickets first. Build trust with your team before expanding scope.",
            "This matches our experience. Fin's accuracy on FAQ-type questions is genuinely impressive. The trick is curating your knowledge base before deployment.",
            "Interesting data point. We're seeing 3.2x higher engagement with ROI messaging vs. speed messaging among VP-level personas.",
            "Worth noting: Fin handles intent detection way better than Zendesk's Answer Bot. It actually understands context, not just keyword matching.",
            "We ran a similar analysis. The delta between AI-augmented agents and fully automated resolution is smaller than you'd think — about 8% in our case.",
        ]),
        ("REPLY", "reddit", [
            "Thanks for sharing. What was your knowledge base setup time? We're evaluating Intercom but worried about the content migration effort.",
            "Strong agree on the pilot approach. We did a 2-week pilot with 5% of traffic and caught a critical edge case with our refund workflow that would have been a disaster at full scale.",
            "This resonates. We moved from Freshdesk to Intercom and the AI accuracy difference was the deciding factor. Freshdesk's bot was basically a glorified search engine.",
        ]),
        ("LIKE", "twitter", []),
        ("LIKE", "reddit", []),
        ("REPOST", "twitter", []),
    ]

    rng = random.Random(current_round * 42)
    num_actions = min(15, max(5, current_round // 3))
    actions = []

    for i in range(num_actions):
        agent_name, agent_title = rng.choice(agents)
        action_type, platform, contents = rng.choice(action_templates)
        round_num = max(1, current_round - rng.randint(0, min(5, current_round - 1)))

        action = {
            "agent_id": rng.randint(1, 200),
            "agent_name": f"{agent_name} ({agent_title})",
            "action_type": action_type,
            "platform": platform,
            "round_num": round_num,
            "timestamp": f"2026-01-{15 + round_num // 48:02d}T{(round_num % 48) // 2 + 8:02d}:{(round_num % 2) * 30:02d}:00Z",
            "action_args": {},
        }

        if contents:
            action["action_args"]["content"] = rng.choice(contents)

        actions.append(action)

    actions.sort(key=lambda a: a["round_num"], reverse=True)
    return actions


@app.route("/api/simulation/<sim_id>/timeline")
def sim_timeline(sim_id):
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}

    elapsed = _elapsed(_simulations, sim_id)
    pct = min(100, elapsed / SIMULATION_RUN_SECONDS() * 100)
    current_round = max(1, min(TOTAL_ROUNDS, int(pct / 100 * TOTAL_ROUNDS)))

    timeline = []
    rng = random.Random(12345)
    for r in range(1, current_round + 1):
        base = 3 + math.log(r + 1) * 2.5
        twitter = max(0, int(base * (0.55 + rng.uniform(-0.1, 0.1))))
        reddit = max(0, int(base * (0.45 + rng.uniform(-0.1, 0.1))))
        timeline.append({
            "round_num": r,
            "twitter_actions": twitter,
            "reddit_actions": reddit,
            "total_actions": twitter + reddit,
        })

    return _ok({"timeline": timeline})


@app.route("/api/simulation/<sim_id>")
def sim_get(sim_id):
    return _ok({
        "simulation_id": sim_id,
        "status": "completed" if sim_id in _simulations and _elapsed(_simulations, sim_id) > SIMULATION_RUN_SECONDS() else "running",
        "config": {"total_hours": 72, "minutes_per_round": 30, "platform_mode": "parallel"},
    })


@app.route("/api/simulation/list")
def sim_list():
    return _ok({"simulations": []})


@app.route("/api/simulation/history")
def sim_history():
    return _ok({"history": []})


@app.route("/api/simulation/<sim_id>/actions")
def sim_actions(sim_id):
    return _ok({"actions": _generate_agent_actions(72)})


@app.route("/api/simulation/<sim_id>/agent-stats")
def sim_agent_stats(sim_id):
    return _ok({"stats": []})


@app.route("/api/simulation/<sim_id>/posts")
def sim_posts(sim_id):
    return _ok({"posts": []})


@app.route("/api/simulation/<sim_id>/comments")
def sim_comments(sim_id):
    return _ok({"comments": []})


@app.route("/api/simulation/entities/<graph_id>")
def sim_entities(graph_id):
    nodes, _ = _build_knowledge_graph()
    return _ok({"entities": nodes})


# ---------------------------------------------------------------------------
# Reasoning Transparency API
# ---------------------------------------------------------------------------

AGENTS = [
    ("Sarah Chen", "VP Support @ Acme SaaS"),
    ("Marcus Johnson", "CX Director @ MedFirst"),
    ("Priya Patel", "Head of Ops @ PayStream"),
    ("David Kim", "IT Leader @ ShopNova"),
    ("Rachel Torres", "VP Support @ CloudOps"),
    ("James Wright", "CX Director @ Retail Plus"),
    ("Anika Sharma", "Support Eng Lead @ DevStack"),
    ("Tom O'Brien", "VP CS @ GrowthLoop"),
    ("Elena Vasquez", "Dir Digital @ HealthBridge"),
    ("Michael Chang", "Head of Ops @ FinEdge"),
    ("Lisa Park", "VP CX @ TravelNow"),
    ("Sofia Martinez", "Support Mgr @ QuickShip"),
    ("Nathan Lee", "CTO @ DataPulse"),
    ("Catherine Hayes", "CFO @ ScaleUp Corp"),
    ("Robert Williams", "IT Director @ EduSpark"),
]

_REASONING_TEMPLATES = [
    "Evaluating whether to share our Q1 support metrics publicly. Fin AI resolution rate of {pct}% is significantly above industry average — sharing could attract attention from prospects and validate our positioning.",
    "Weighing competitive response to Zendesk's latest announcement. Our data shows {pct}% improvement in CSAT since switching — direct comparison could be effective but risks appearing combative.",
    "Considering whether cost-per-resolution framing resonates better than speed-to-value. Internal surveys suggest {pct}% of VPs respond more strongly to ROI messaging.",
    "Analyzing the trade-off between AI automation depth and customer satisfaction. Our pilot data shows diminishing returns above {pct}% automation — human escalation paths are critical.",
    "Assessing multi-threading strategy: reaching multiple stakeholders increases conversion {pct}% but risks appearing spammy if not coordinated.",
    "Reviewing whether compliance-first messaging for Healthcare is worth the extra personalization cost. Data shows {pct}% higher engagement when HIPAA is mentioned upfront.",
]

_GOAL_TEMPLATES = [
    "Maximize support team efficiency",
    "Reduce cost per resolution",
    "Improve customer satisfaction scores",
    "Drive AI adoption in support workflows",
    "Build thought leadership in CX space",
    "Evaluate competitive alternatives objectively",
    "Optimize multi-channel support strategy",
    "Scale support operations without proportional headcount",
]

_FACTOR_TEMPLATES = [
    {"name": "ROI impact", "weight": 0.35, "assessment": "High — strong cost savings narrative"},
    {"name": "audience relevance", "weight": 0.25, "assessment": "Medium — resonates with VP-level personas"},
    {"name": "competitive risk", "weight": 0.15, "assessment": "Low — factual, data-driven framing"},
    {"name": "credibility", "weight": 0.15, "assessment": "High — backed by pilot data"},
    {"name": "timing", "weight": 0.10, "assessment": "Good — aligns with Q1 budget planning"},
]


def _agent_id_from_name(name):
    return abs(hash(name)) % 10000


def _generate_round_reasoning(sim_id, round_num):
    rng = random.Random(hash(f"{sim_id}-reasoning-{round_num}"))
    traces = []
    num_agents = rng.randint(3, 8)
    chosen = rng.sample(AGENTS, num_agents)
    for name, title in chosen:
        agent_id = _agent_id_from_name(name)
        tpl = rng.choice(_REASONING_TEMPLATES)
        pct = rng.randint(20, 72)
        goal = rng.choice(_GOAL_TEMPLATES)
        confidence = round(rng.uniform(0.55, 0.95), 2)
        action = rng.choice(["CREATE_POST", "REPLY", "LIKE", "REPOST"])
        traces.append({
            "agent_id": agent_id,
            "agent_name": f"{name} ({title})",
            "round": round_num,
            "reasoning": tpl.format(pct=pct),
            "goal": goal,
            "action_chosen": action,
            "confidence": confidence,
            "factors_considered": [
                {**f, "weight": round(f["weight"] + rng.uniform(-0.05, 0.05), 2)}
                for f in rng.sample(_FACTOR_TEMPLATES, rng.randint(2, 4))
            ],
            "alternatives_rejected": rng.sample(
                ["LIKE", "REPOST", "CREATE_POST", "REPLY", "IGNORE"],
                rng.randint(1, 3),
            ),
        })
    return traces


def _generate_decisions(sim_id):
    rng = random.Random(hash(f"{sim_id}-decisions"))
    decisions = []
    topics = [
        "AI automation vs human touch",
        "Competitive displacement messaging",
        "ROI-first vs feature-first positioning",
        "Multi-threading outreach strategy",
        "Compliance-first messaging for Healthcare",
        "Optimal email cadence timing",
        "Zendesk migration narrative",
        "Fin AI resolution rate claims",
    ]
    for i, topic in enumerate(topics):
        agent_name, agent_title = rng.choice(AGENTS)
        agent_id = _agent_id_from_name(agent_name)
        confidence = round(rng.uniform(0.6, 0.95), 2)
        round_num = rng.randint(1, TOTAL_ROUNDS)
        decisions.append({
            "decision_id": f"dec-{sim_id[:8]}-{i:04d}",
            "agent_id": agent_id,
            "agent_name": f"{agent_name} ({agent_title})",
            "round": round_num,
            "topic": topic,
            "action": rng.choice(["CREATE_POST", "REPLY", "REPOST"]),
            "confidence": confidence,
            "reasoning_summary": rng.choice(_REASONING_TEMPLATES).format(pct=rng.randint(20, 72)),
        })
    return decisions


@app.route("/api/simulation/<sim_id>/round/<int:round_num>/reasoning")
def sim_round_reasoning(sim_id, round_num):
    if round_num < 1 or round_num > TOTAL_ROUNDS:
        return _err(f"Round must be between 1 and {TOTAL_ROUNDS}", 400)
    traces = _generate_round_reasoning(sim_id, round_num)
    return _ok({"simulation_id": sim_id, "round": round_num, "traces": traces})


@app.route("/api/simulation/<sim_id>/agents/<int:agent_id>/reasoning")
def sim_agent_reasoning(sim_id, agent_id):
    rng = random.Random(hash(f"{sim_id}-agent-{agent_id}"))
    agent_match = None
    for name, title in AGENTS:
        if _agent_id_from_name(name) == agent_id:
            agent_match = (name, title)
            break
    if not agent_match:
        return _err("Agent not found", 404)
    name, title = agent_match
    traces = []
    num_rounds = rng.randint(5, 12)
    rounds = sorted(rng.sample(range(1, TOTAL_ROUNDS + 1), num_rounds))
    for r in rounds:
        tpl = rng.choice(_REASONING_TEMPLATES)
        pct = rng.randint(20, 72)
        traces.append({
            "round": r,
            "reasoning": tpl.format(pct=pct),
            "goal": rng.choice(_GOAL_TEMPLATES),
            "action_chosen": rng.choice(["CREATE_POST", "REPLY", "LIKE", "REPOST"]),
            "confidence": round(rng.uniform(0.55, 0.95), 2),
            "factors_considered": [
                {**f, "weight": round(f["weight"] + rng.uniform(-0.05, 0.05), 2)}
                for f in rng.sample(_FACTOR_TEMPLATES, rng.randint(2, 4))
            ],
        })
    return _ok({
        "simulation_id": sim_id,
        "agent_id": agent_id,
        "agent_name": f"{name} ({title})",
        "traces": traces,
    })


@app.route("/api/simulation/<sim_id>/decisions")
def sim_decisions(sim_id):
    decisions = _generate_decisions(sim_id)
    return _ok({"simulation_id": sim_id, "decisions": decisions})


@app.route("/api/simulation/<sim_id>/decisions/<decision_id>/explain")
def sim_decision_explain(sim_id, decision_id):
    decisions = _generate_decisions(sim_id)
    match = next((d for d in decisions if d["decision_id"] == decision_id), None)
    if not match:
        return _err("Decision not found", 404)
    rng = random.Random(hash(f"{sim_id}-explain-{decision_id}"))
    return _ok({
        "decision_id": decision_id,
        "agent_name": match["agent_name"],
        "round": match["round"],
        "topic": match["topic"],
        "action": match["action"],
        "reasoning": match["reasoning_summary"],
        "explanation": {
            "goal": rng.choice(_GOAL_TEMPLATES),
            "factors": [
                {**f, "weight": round(f["weight"] + rng.uniform(-0.05, 0.05), 2)}
                for f in _FACTOR_TEMPLATES
            ],
            "decision_process": (
                f"Agent evaluated {len(_FACTOR_TEMPLATES)} factors against the goal "
                f"of '{rng.choice(_GOAL_TEMPLATES).lower()}'. "
                f"The {match['action']} action scored highest with {match['confidence']:.0%} "
                f"confidence based on weighted factor analysis."
            ),
            "alternatives": [
                {
                    "action": alt,
                    "score": round(rng.uniform(0.2, match["confidence"] - 0.05), 2),
                    "rejection_reason": rng.choice([
                        "Lower expected engagement",
                        "Insufficient data support",
                        "Misaligned with current goal",
                        "Higher competitive risk",
                        "Audience mismatch",
                    ]),
                }
                for alt in rng.sample(["CREATE_POST", "REPLY", "LIKE", "REPOST", "IGNORE"], 2)
                if alt != match["action"]
            ],
        },
    })


@app.route("/api/simulation/<sim_id>/decisions/<decision_id>/counterfactual")
def sim_decision_counterfactual(sim_id, decision_id):
    decisions = _generate_decisions(sim_id)
    match = next((d for d in decisions if d["decision_id"] == decision_id), None)
    if not match:
        return _err("Decision not found", 404)
    rng = random.Random(hash(f"{sim_id}-cf-{decision_id}"))
    alt_actions = [a for a in ["CREATE_POST", "REPLY", "LIKE", "REPOST", "IGNORE"] if a != match["action"]]
    scenarios = []
    for alt in rng.sample(alt_actions, min(3, len(alt_actions))):
        engagement_delta = round(rng.uniform(-30, 15), 1)
        sentiment_delta = round(rng.uniform(-0.3, 0.2), 2)
        scenarios.append({
            "alternative_action": alt,
            "predicted_engagement_delta_pct": engagement_delta,
            "predicted_sentiment_delta": sentiment_delta,
            "cascade_effect": rng.choice([
                "Minimal — isolated impact on immediate thread",
                "Moderate — 2-3 connected agents would shift stance",
                "Significant — could trigger topic-wide sentiment reversal",
            ]),
            "risk_assessment": rng.choice(["low", "medium", "high"]),
            "narrative": (
                f"If the agent had chosen {alt} instead of {match['action']}, "
                f"engagement would have shifted by {engagement_delta:+.1f}% "
                f"with a sentiment change of {sentiment_delta:+.2f}."
            ),
        })
    return _ok({
        "decision_id": decision_id,
        "original_action": match["action"],
        "original_confidence": match["confidence"],
        "counterfactual_scenarios": scenarios,
    })


@app.route("/api/simulation/<sim_id>/argument-map/<topic>")
def sim_argument_map(sim_id, topic):
    rng = random.Random(hash(f"{sim_id}-argmap-{topic}"))
    nodes = []
    edges = []
    positions = [
        {"label": "central_claim", "type": "claim"},
        {"label": "supporting_evidence_1", "type": "evidence"},
        {"label": "supporting_evidence_2", "type": "evidence"},
        {"label": "counterargument_1", "type": "counterargument"},
        {"label": "counterargument_2", "type": "counterargument"},
        {"label": "rebuttal_1", "type": "rebuttal"},
        {"label": "synthesis", "type": "synthesis"},
    ]
    claim_templates = {
        "claim": [
            f"AI-driven support automation delivers measurable ROI for {topic}",
            f"The market is shifting toward {topic} as a competitive differentiator",
            f"Organizations that adopt {topic} early will capture disproportionate market share",
        ],
        "evidence": [
            "Pilot data shows 47% AI resolution rate with Fin agent",
            "CSAT improved 8 points after Intercom deployment",
            "Cost per resolution dropped 40% in first quarter",
            "3-week deployment time vs 6-month legacy migration",
            "Multi-threading outreach increases conversion 4.7x",
        ],
        "counterargument": [
            "AI chatbots still struggle with nuanced product feedback",
            "Migration costs and team disruption offset short-term savings",
            "Customer trust decreases when they know they're talking to a bot",
            "Regulatory requirements in Healthcare limit AI automation scope",
        ],
        "rebuttal": [
            "Human escalation paths preserve quality for complex cases",
            "3-week deployment minimizes disruption window",
            "Transparency about AI involvement actually increases trust per recent studies",
        ],
        "synthesis": [
            f"Balanced approach to {topic}: automate high-volume low-complexity, elevate humans for high-value interactions",
        ],
    }
    for i, pos in enumerate(positions):
        node_type = pos["type"]
        agent_name, agent_title = rng.choice(AGENTS)
        nodes.append({
            "id": f"arg-{i}",
            "type": node_type,
            "content": rng.choice(claim_templates[node_type]),
            "agent_name": f"{agent_name} ({agent_title})",
            "agent_id": _agent_id_from_name(agent_name),
            "confidence": round(rng.uniform(0.5, 0.95), 2),
            "round_introduced": rng.randint(1, TOTAL_ROUNDS),
        })
    edge_defs = [
        ("arg-1", "arg-0", "supports"), ("arg-2", "arg-0", "supports"),
        ("arg-3", "arg-0", "opposes"), ("arg-4", "arg-0", "opposes"),
        ("arg-5", "arg-3", "rebuts"), ("arg-6", "arg-0", "synthesizes"),
    ]
    for src, tgt, rel in edge_defs:
        edges.append({
            "source": src, "target": tgt, "relationship": rel,
            "strength": round(rng.uniform(0.4, 0.95), 2),
        })
    return _ok({
        "simulation_id": sim_id,
        "topic": topic,
        "argument_map": {"nodes": nodes, "edges": edges},
    })


# ---------------------------------------------------------------------------
# Report API
# ---------------------------------------------------------------------------

REPORT_SECTIONS = [
    {
        "section_index": 0,
        "content": """## Executive Summary

This report presents findings from a 72-hour swarm intelligence simulation involving **200 AI agents** representing synthetic buyer personas across SaaS, Healthcare, Fintech, and E-commerce verticals. The simulation tested Intercom's outbound campaign messaging strategy targeting mid-market companies currently using Zendesk.

### Key Findings

- **VP of Support personas showed 3.2x higher engagement with ROI-driven messaging** compared to speed-to-value messaging, with particularly strong response rates among companies spending >$10K/mo on support tooling
- **"Your Zendesk bill is 3x what it should be"** was the highest-performing subject line, achieving a **34.7% simulated open rate** — but triggered spam perception in 8.2% of Healthcare personas due to aggressive competitive framing
- **Healthcare and Fintech verticals require compliance-first messaging** — standard ROI messaging achieved only 12% engagement vs. 31% when HIPAA/SOC2 compliance was mentioned in the first two sentences
- **Optimal email cadence is Day 1 → Day 3 → Day 8 → Day 15** — the standard Day 1 → Day 2 → Day 4 cadence showed 23% higher unsubscribe intent signals
- **Fin AI agent resolution rate claims** (50% automation) were the single most persuasive data point, referenced in 67% of positive engagement signals across all persona types

### Simulation Confidence

| Metric | Value |
|--------|-------|
| Total agent interactions | 12,384 |
| Unique conversation threads | 847 |
| Cross-persona influence events | 234 |
| Simulation convergence score | 0.89 / 1.00 |
| Statistical confidence | 94.2% |

> **Bottom line:** The outbound campaign has strong fundamentals but requires segment-specific message tailoring. A one-size-fits-all approach would underperform by an estimated 40-55% compared to the optimized variant matrix recommended in Chapter 5.""",
    },
    {
        "section_index": 1,
        "content": """## Engagement Analysis

### Engagement by Persona Type

The simulation reveals dramatic differences in how each persona type engages with outbound messaging:

| Persona Type | Open Rate | Reply Rate | Meeting Book Rate | Top Message Trigger |
|-------------|-----------|------------|-------------------|---------------------|
| VP of Support | 38.4% | 12.1% | 4.8% | Cost reduction proof points |
| CX Director | 31.2% | 8.7% | 3.2% | AI resolution rate benchmarks |
| IT Leader | 22.8% | 5.3% | 2.1% | Integration ecosystem details |
| Head of Operations | 35.6% | 10.4% | 4.1% | Efficiency metrics and headcount impact |
| CFO / Finance | 28.9% | 7.8% | 3.6% | ROI calculations with timeframe |

### Engagement by Industry

- **SaaS companies** showed the highest overall engagement (34.2% average open rate), driven by familiarity with the competitive landscape and active tool evaluation cycles
- **Healthcare** had the lowest initial engagement (19.8%) but the **highest conversion-to-meeting rate** (5.1%) when compliance messaging was front-loaded — these buyers are slower to engage but more serious when they do
- **Fintech** personas exhibited strong "comparison shopping" behavior — 73% of engaged fintech personas also researched Freshdesk and HubSpot Service Hub within the simulation, suggesting multi-vendor evaluation is the norm
- **E-commerce** engagement was highly seasonal-dependent — agents simulating Q4 planning cycles showed 2.8x higher engagement than those in steady-state operations

### Engagement by Company Size

| Company Size | Avg Open Rate | Avg Reply Rate | Key Pattern |
|-------------|--------------|----------------|-------------|
| 200-500 employees | 36.1% | 11.2% | Price-sensitive, fast decision cycles |
| 500-1000 employees | 32.4% | 9.8% | Committee-driven, need multiple touches |
| 1000-2000 employees | 27.8% | 7.1% | Security-first, require enterprise features |

### Network Effects

A notable finding: when **3+ personas from the same simulated company** engaged with outbound content, the likelihood of a meeting booking increased by **4.7x**. This suggests that multi-threading (reaching multiple stakeholders at the same company) is significantly more effective than single-contact outreach.

The simulation identified **23 "viral content" events** where one agent's positive engagement triggered interest from connected agents, primarily through simulated internal Slack-like channels. The content that generated these cascade events consistently featured **specific, verifiable metrics** (e.g., "48% AI resolution rate in 30-day pilot") rather than general claims.""",
    },
    {
        "section_index": 2,
        "content": """## Messaging Effectiveness

### Subject Line Performance

All four subject line variants were tested against the full 200-agent population. Results ranked by simulated open rate:

| Rank | Subject Line | Open Rate | Spam Flag Rate | Best Segment |
|------|-------------|-----------|----------------|--------------|
| 1 | "Your Zendesk bill is 3x what it should be" | 34.7% | 8.2% | SaaS VP of Support |
| 2 | "How [Company] cut support costs 40% with AI" | 31.2% | 2.1% | All — safest universal option |
| 3 | "The AI agent your support team actually wants" | 28.9% | 1.4% | CX Directors, Support Managers |
| 4 | "Replace Zendesk in 30 days — here's how" | 24.3% | 11.7% | SaaS IT Leaders only |

**Critical insight:** Subject line #1 has the highest open rate but also the highest spam perception. In Healthcare, the spam flag rate jumps to **14.8%** — this subject line should be **excluded from Healthcare segments entirely**.

Subject line #2 is the recommended default: strong performance across all segments with minimal negative perception. The `[Company]` personalization token increased open rates by an additional 3.2 percentage points when the case study was industry-matched.

### Message Body Analysis

The simulation tested message body variations across three dimensions:

**Tone:**
- **Data-driven tone** outperformed all others across VP and Director personas (+18% engagement vs. casual)
- **Casual tone** performed well with Support Managers and smaller companies but alienated Enterprise buyers (-22%)
- **Consultative tone** was the best performer for IT Leaders who valued being treated as technical peers

**Length:**
- **Short emails (< 100 words)** had the highest open-to-read rate but lowest meeting booking rate
- **Medium emails (100-200 words)** were the optimal length, balancing engagement and conversion
- **Long emails (> 200 words)** were only effective for CFO personas who wanted detailed ROI analysis

**Call-to-Action Style:**
- **Soft ask** ("Would it be useful to see how [similar company] approached this?"): 11.3% reply rate
- **Hard ask** ("Can we schedule 20 minutes this week?"): 7.8% reply rate, but 2.1x higher meeting conversion
- **Question CTA** ("What's your team's biggest support bottleneck right now?"): 14.7% reply rate — highest response rate but lower quality responses

### Competitive Displacement Sensitivity

Mentions of competitor names triggered strong reactions:

- **Zendesk mentions** were well-received by frustrated current users (positive in 64% of interactions) but triggered defensive responses from satisfied Zendesk users (negative in 78%)
- **Freshdesk mentions** were largely neutral — most personas viewed Freshdesk as a lower-tier option and didn't feel defensive
- **HubSpot Service Hub mentions** triggered "already evaluated" fatigue in 34% of personas — many had recently looked at HubSpot and decided against it

**Recommendation:** Lead with value proposition, not competitive displacement. Introduce competitor comparisons only in follow-up emails (email 2 or 3 in sequence) and only when the prospect has shown engagement signals.""",
    },
    {
        "section_index": 3,
        "content": """## Behavioral Patterns

### Temporal Engagement Patterns

The 72-hour simulation revealed distinct behavioral waves:

- **Hours 0-12:** Initial engagement spike. 62% of all first opens occurred within the first 12 simulated hours. VP-level personas opened within 2 hours; Manager-level personas took 6-8 hours on average.
- **Hours 12-36:** "Research phase." Engaged personas spent this period visiting simulated product pages, reading case studies, and discussing internally. **This is when the multi-threading effect is strongest** — reaching a second stakeholder during this window increased conversion 3.1x.
- **Hours 36-56:** Decision crystallization. Personas either moved toward meeting booking or disengaged. The "silent middle" — personas who opened but didn't respond — showed a 23% eventual conversion rate when followed up at Hour 48.
- **Hours 56-72:** Late responders. A surprising 15% of total meetings were booked in this window, primarily from personas who needed internal approval or budget confirmation.

### Persona Behavioral Clusters

The simulation identified five distinct behavioral clusters that cut across job titles:

**Cluster 1: "Rapid Evaluators" (18% of agents)**
- Opened email within 1 hour, clicked through to product page, and either booked or dismissed within 24 hours
- Best reached with: direct CTA, specific metrics, and a clear "next step"
- Over-indexed on: SaaS companies, 200-500 employees

**Cluster 2: "Committee Builders" (24% of agents)**
- Forwarded content to 2-3 internal stakeholders before engaging
- Best reached with: shareable content (case studies, ROI calculators), multi-stakeholder messaging
- Over-indexed on: 500-1000 employee companies, Healthcare

**Cluster 3: "Silent Researchers" (31% of agents)**
- Opened multiple times but never replied to outbound email
- Eventually engaged through a different channel (simulated product page visit, competitor comparison page)
- Best reached with: retargeting-style follow-ups that acknowledge their research behavior

**Cluster 4: "Skeptical Evaluators" (19% of agents)**
- Responded with objections or requests for proof before any positive engagement
- **Most likely to convert once objections are addressed** (34% eventual meeting rate vs. 12% average)
- Best reached with: detailed technical documentation, peer references, and pilot program offers

**Cluster 5: "Passive Observers" (8% of agents)**
- Minimal engagement but remained subscribed. Represent future pipeline for re-engagement campaigns.
- Best reached with: low-frequency, high-value content (quarterly industry reports, benchmark data)

### Objection Mapping

The most common objections by frequency:

1. **"We just renewed our Zendesk contract"** (34% of negative responses) — Counter: offer ROI analysis to build business case for next renewal cycle
2. **"AI chatbots give bad answers"** (28%) — Counter: Fin accuracy benchmarks with comparable company data
3. **"We don't have budget for a migration"** (22%) — Counter: migration cost offset by first-year savings calculation
4. **"We need [specific feature] that you don't have"** (16%) — Counter: feature parity documentation and roadmap

### Network Influence Analysis

Key finding: **8 "influencer" agents** (4% of the population) generated **34% of all positive sentiment cascade events**. These agents shared characteristics:
- Senior titles (VP or Director level)
- At companies with 500+ employees
- Had previously evaluated 2+ support tools
- Engaged with data-driven content (not emotional appeals)

This suggests that identifying and prioritizing "influencer" prospects in real campaigns could dramatically improve campaign ROI.""",
    },
    {
        "section_index": 4,
        "content": """## Recommendations

Based on the simulation findings, we recommend the following prioritized action items:

### Priority 1: Segment-Specific Message Variants (Confidence: 96%)

- **Create 4 industry-specific email variants** instead of one universal template
  - **SaaS:** Lead with Zendesk migration ease and Fin resolution rates
  - **Healthcare:** Lead with HIPAA compliance and patient communication AI
  - **Fintech:** Lead with security certifications and cost-per-ticket metrics
  - **E-commerce:** Lead with seasonal scaling and Shopify integration
- **Expected impact:** 35-45% improvement in overall engagement rate

### Priority 2: Optimize Subject Line Strategy (Confidence: 94%)

- **Default to "How [Company] cut support costs 40% with AI"** as the universal subject line
- **Use "Your Zendesk bill is 3x what it should be"** only for SaaS companies confirmed on Zendesk
- **Never use competitive displacement subject lines** for Healthcare or Fintech segments
- **A/B test "The AI agent your support team actually wants"** for CX Director personas specifically
- **Expected impact:** 8-12% higher open rates with 60% reduction in spam flags

### Priority 3: Revise Email Cadence (Confidence: 91%)

- **Switch from Day 1-2-4 to Day 1-3-8-15 cadence** to reduce unsubscribe pressure
- **Add a "research acknowledgment" touchpoint at Day 5** for prospects who opened but didn't reply — "I noticed you've been exploring [topic] — here's a relevant case study"
- **Introduce multi-threading at Day 3** — reach a second stakeholder at engaged companies
- **Expected impact:** 23% reduction in unsubscribe rate, 18% increase in meeting bookings

### Priority 4: Build "Influencer Prospect" Targeting (Confidence: 87%)

- **Identify real-world equivalents of the 8 influencer archetypes** found in the simulation
- **Characteristics to target:** VP/Director at 500+ employee companies who have evaluated 2+ support tools in the past 18 months
- **Create premium content track** (executive briefings, benchmark reports) for these high-value prospects
- **Expected impact:** 3-4x ROI on outreach to this segment

### Priority 5: Address Top Objections Proactively (Confidence: 85%)

- **Add "contract flexibility" messaging** in Email 2 for the 34% who cite existing contracts
- **Create Fin accuracy benchmark one-pager** for the 28% concerned about AI quality
- **Build an interactive migration cost calculator** for the 22% citing budget constraints
- **Publish feature parity matrix** (Intercom vs. Zendesk vs. Freshdesk) for the 16% with feature concerns
- **Expected impact:** 15-20% improvement in objection-to-engagement conversion

### Implementation Timeline

| Week | Action | Owner |
|------|--------|-------|
| 1 | Create industry-specific email variants | Content team |
| 1 | Implement new subject line strategy | Growth marketing |
| 2 | Update cadence in outbound automation | Marketing ops |
| 2 | Build influencer prospect target list | Sales ops |
| 3 | Create objection-handling collateral | Product marketing |
| 3 | Launch A/B tests with optimized variants | Growth marketing |
| 4 | Analyze first-week results and iterate | All teams |

### Risk Factors

- **Spam filter sensitivity:** Aggressive competitive messaging in subject lines carries brand risk. Monitor deliverability metrics closely in the first 48 hours of any campaign launch.
- **Data freshness:** The simulation used anonymized seed data. Verify that technographic data (who uses Zendesk) is current — stale data was identified as a known issue (25-32% accuracy in Clay enrichment).
- **AI perception gap:** 28% of personas had negative preconceptions about AI chatbots. Leading with "AI agent" framing may backfire — consider "intelligent automation" or "smart support" as alternative positioning.

> **Overall recommendation:** Implement Priorities 1-3 immediately for the next outbound campaign cycle. Priorities 4-5 are medium-term improvements that can be phased in over the following quarter. The simulation predicts a **45-65% improvement in campaign effectiveness** when all five recommendations are implemented versus the current one-size-fits-all approach.""",
    },
]


@app.route("/api/report/generate", methods=["POST"])
def report_generate():
    body = request.get_json(silent=True) or {}
    sim_id = body.get("simulation_id", "demo-sim-00001")
    report_id = f"demo-report-{sim_id.split('-')[-1]}"

    if report_id in _reports and _elapsed(_reports, report_id) > REPORT_GEN_SECONDS():
        return _ok({
            "report_id": report_id,
            "status": "completed",
            "already_generated": True,
        })

    _reports[report_id] = {"start": time.time(), "sim_id": sim_id}
    return _ok({
        "report_id": report_id,
        "status": "generating",
        "already_generated": False,
    })


@app.route("/api/report/generate/status", methods=["POST"])
def report_generate_status():
    body = request.get_json(silent=True) or {}
    report_id = body.get("report_id", "")
    if report_id not in _reports:
        return _err("Report not found", 404)
    elapsed = _elapsed(_reports, report_id)
    pct = min(100, int(elapsed / REPORT_GEN_SECONDS() * 100))
    return _ok({"progress": pct, "status": "completed" if pct >= 100 else "generating"})


@app.route("/api/report/<report_id>/progress")
def report_progress(report_id):
    if report_id not in _reports:
        _reports[report_id] = {"start": time.time(), "sim_id": "unknown"}

    elapsed = _elapsed(_reports, report_id)
    pct = min(100, int(elapsed / REPORT_GEN_SECONDS() * 100))
    total_sections = len(REPORT_SECTIONS)
    completed = min(total_sections, int(pct / 100 * total_sections))

    messages = [
        (0, "Analyzing simulation data..."),
        (20, "Generating executive summary..."),
        (40, "Computing engagement metrics..."),
        (60, "Analyzing messaging effectiveness..."),
        (80, "Synthesizing recommendations..."),
        (95, "Finalizing report..."),
    ]
    msg = "Initializing..."
    for threshold, m in messages:
        if pct >= threshold:
            msg = m

    return _ok({
        "progress": pct,
        "total_sections": total_sections,
        "completed_sections": completed,
        "message": msg,
    })


@app.route("/api/report/<report_id>/sections")
def report_sections(report_id):
    if report_id not in _reports:
        _reports[report_id] = {"start": time.time(), "sim_id": "unknown"}

    elapsed = _elapsed(_reports, report_id)
    pct = min(100, elapsed / REPORT_GEN_SECONDS() * 100)
    total = len(REPORT_SECTIONS)
    visible = min(total, int(pct / 100 * total) + (1 if pct > 5 else 0))

    return _ok({
        "sections": REPORT_SECTIONS[:visible],
        "is_complete": pct >= 100,
    })


@app.route("/api/report/<report_id>/section/<int:section_index>")
def report_section(report_id, section_index):
    if 0 <= section_index < len(REPORT_SECTIONS):
        return _ok(REPORT_SECTIONS[section_index])
    return _err("Section not found", 404)


@app.route("/api/report/<report_id>")
def report_get(report_id):
    return _ok({
        "report_id": report_id,
        "status": "completed",
        "sections": REPORT_SECTIONS,
    })


@app.route("/api/report/by-simulation/<sim_id>")
def report_by_simulation(sim_id):
    report_id = f"demo-report-{sim_id.split('-')[-1]}"
    return _ok({
        "report_id": report_id,
        "status": "completed",
    })


@app.route("/api/report/list")
def report_list():
    return _ok({"reports": []})


@app.route("/api/report/<report_id>/download")
def report_download(report_id):
    full_md = "\n\n---\n\n".join(s["content"] for s in REPORT_SECTIONS)
    return Response(
        full_md,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=mirofish-report-{report_id}.md"},
    )


@app.route("/api/report/check/<sim_id>")
def report_check(sim_id):
    report_id = f"demo-report-{sim_id.split('-')[-1]}"
    if report_id in _reports and _elapsed(_reports, report_id) > REPORT_GEN_SECONDS():
        return _ok({
            "has_report": True,
            "report_id": report_id,
            "report_status": "completed",
        })
    return _ok({
        "has_report": False,
        "report_id": None,
        "report_status": None,
    })


# ---------------------------------------------------------------------------
# Report Agent Logs (stubs for frontend API module)
# ---------------------------------------------------------------------------

@app.route("/api/report/<report_id>/agent-log")
def report_agent_log(report_id):
    return _ok({"logs": []})


@app.route("/api/report/<report_id>/agent-log/stream")
def report_agent_log_stream(report_id):
    return _ok({"logs": []})


@app.route("/api/report/<report_id>/console-log")
def report_console_log(report_id):
    return _ok({"logs": []})


@app.route("/api/report/<report_id>/console-log/stream")
def report_console_log_stream(report_id):
    return _ok({"logs": []})


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------

CHAT_RESPONSES = {
    "subject line": {
        "response": "Based on the simulation data, here's the subject line performance breakdown:\n\n1. \"Your Zendesk bill is 3x what it should be\" — 34.7% open rate (but 8.2% spam flag in Healthcare)\n2. \"How [Company] cut support costs 40% with AI\" — 31.2% open rate (safest universal option)\n3. \"The AI agent your support team actually wants\" — 28.9% open rate (best for CX Directors)\n4. \"Replace Zendesk in 30 days\" — 24.3% open rate (highest spam risk at 11.7%)\n\nThe key insight is that subject line #1 has the highest raw performance but carries brand risk in regulated industries. For a universal campaign, I'd recommend #2 as the default with #1 reserved for confirmed Zendesk accounts in SaaS.",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "subject line performance by open rate and spam flag rate"}, "result": "Analyzed 200 agent interactions across 4 subject line variants. Competitive displacement framing shows highest engagement but also highest negative sentiment in Healthcare (14.8% spam flag) and Fintech (9.1% spam flag)."},
        ],
        "sources": ["Simulation Rounds 1-144", "Agent Engagement Metrics", "Spam Perception Analysis"],
    },
    "persona": {
        "response": "The simulation reveals significant persona-based variation in engagement:\n\n• VP of Support: 38.4% open rate, responds most strongly to ROI-driven messaging with specific cost reduction numbers. They want to see \"40% cost reduction\" not \"significant savings.\"\n\n• CX Director: 31.2% open rate, most engaged by AI resolution rate benchmarks. They care about CSAT impact and agent experience.\n\n• IT Leader: 22.8% open rate — the hardest to engage. They prioritize integration ecosystem details and security certifications. Lead with technical credibility.\n\n• Head of Operations: 35.6% open rate, focused on efficiency metrics and headcount impact. They're running the numbers immediately.\n\n• CFO: 28.9% open rate, responds to detailed ROI calculations with specific timeframes. They need a business case they can present to the board.\n\nThe biggest surprise: VP of Support personas showed 3.2x higher engagement with ROI messaging compared to speed-to-value messaging. We assumed speed would win, but these buyers care more about proving budget impact to their CFO.",
        "tool_calls": [
            {"name": "panorama_search", "arguments": {"query": "persona engagement breakdown by role title"}, "result": "Retrieved engagement data for 5 persona types across 12,384 total interactions. VP of Support and Head of Operations are highest-engagement personas. IT Leaders require the most touches before converting."},
        ],
        "sources": ["Agent Cluster Analysis", "Persona Engagement Matrix", "Cross-Role Comparison Report"],
    },
    "healthcare": {
        "response": "Healthcare is a fascinating segment in this simulation. Here's what the data shows:\n\n• Initial engagement is the LOWEST of all verticals at 19.8% average open rate\n• BUT conversion-to-meeting rate is the HIGHEST at 5.1% — these buyers are slow to engage but very serious when they do\n• HIPAA compliance must be mentioned in the first two sentences or engagement drops to 12%\n• Standard ROI messaging achieves only 12% engagement vs 31% when compliance is front-loaded\n• The subject line \"Your Zendesk bill is 3x what it should be\" triggers a 14.8% spam flag rate in Healthcare — it should be excluded entirely\n\nThe recommended approach for Healthcare: Lead with \"HIPAA-compliant AI-powered support\" positioning, include SOC2 certification badges in email signature, and use the consultative CTA style (\"What are your biggest compliance challenges with your current support tool?\").",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "healthcare vertical engagement patterns and compliance sensitivity"}, "result": "Healthcare personas prioritize compliance verification before evaluating features. 89% of healthcare decision-makers checked for HIPAA documentation within first 3 interactions. Compliance-first messaging improved engagement 2.6x."},
        ],
        "sources": ["Vertical Analysis - Healthcare", "Compliance Sensitivity Index", "HIPAA Messaging A/B Results"],
    },
    "objection": {
        "response": "The simulation identified four primary objection patterns with clear counter-strategies:\n\n1. **\"We just renewed our Zendesk contract\"** (34% of negative responses)\n   → Counter: Don't push for immediate switch. Offer ROI analysis to build business case for next renewal. Plant the seed now, harvest in 6-12 months.\n\n2. **\"AI chatbots give bad answers\"** (28%)\n   → Counter: This is the most convertible objection! Share Fin accuracy benchmarks and offer a controlled pilot. 34% of \"Skeptical Evaluator\" personas who raised this objection eventually booked meetings.\n\n3. **\"We don't have budget for a migration\"** (22%)\n   → Counter: Build an interactive migration cost calculator showing first-year savings offset. The math almost always works in Intercom's favor for companies spending >$5K/mo on support.\n\n4. **\"We need [specific feature] you don't have\"** (16%)\n   → Counter: Feature parity matrix + roadmap. Most gaps are perceived, not real.\n\nKey insight: Skeptical Evaluators (Cluster 4) have the HIGHEST eventual meeting rate at 34%. Don't be discouraged by initial pushback — address it directly with data.",
        "tool_calls": [
            {"name": "panorama_search", "arguments": {"query": "objection frequency and conversion rates by objection type"}, "result": "Mapped 4 primary objection categories across 847 conversation threads. 'AI quality concerns' objection has highest overcome rate (34%) when addressed with specific accuracy benchmarks and pilot program offers."},
        ],
        "sources": ["Objection Mapping Analysis", "Skeptical Evaluator Cluster Study", "Counter-Strategy Effectiveness Report"],
    },
    "roi": {
        "response": "The ROI story from the simulation is compelling:\n\n• **Cost reduction:** Companies spending >$10K/mo on support tools showed the strongest engagement with cost-saving messaging. The \"40% cost reduction\" claim was the most-cited metric in positive engagement signals.\n\n• **Headcount efficiency:** Head of Operations personas responded 3.1x more strongly to \"handle 10x volume without hiring\" than generic efficiency claims. They're doing literal headcount math.\n\n• **Time-to-value:** Deployment speed (\"3 weeks vs 6 months\") was the #2 most persuasive data point after resolution rate claims. But it was most effective for smaller companies (200-500 employees) who can't afford long implementation cycles.\n\n• **AI resolution rate:** Fin's 50% automation claim was referenced in 67% of positive engagement signals. This is the single most powerful metric in the entire messaging arsenal.\n\nThe simulation suggests framing ROI differently by persona:\n- **For VPs:** \"Save $280K/yr and redeploy 3 agents to proactive outreach\"\n- **For CFOs:** \"40% cost reduction with 90-day payback period\"\n- **For Ops leaders:** \"Handle holiday surge without temporary hires\"",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "ROI messaging effectiveness by persona and company size"}, "result": "ROI-driven messaging outperformed speed messaging by 3.2x among VP personas. Cost reduction claims most effective at >$10K/mo spend. Resolution rate (50%) was referenced in 67% of positive engagement signals."},
        ],
        "sources": ["ROI Sensitivity Analysis", "Persona-Specific Messaging Study", "Cost Reduction Impact Model"],
    },
    "cadence": {
        "response": "The simulation revealed a clear winner for email cadence:\n\n**Current cadence (Day 1-2-4):** Triggers \"too aggressive\" perception in 23% of personas. The Day 2 follow-up feels pushy, especially for Enterprise buyers who need time to process.\n\n**Recommended cadence (Day 1-3-8-15):**\n- Day 1: Initial outreach with value proposition\n- Day 3: \"Research acknowledgment\" — acknowledge their evaluation without being pushy\n- Day 8: Case study or social proof relevant to their industry\n- Day 15: Direct ask with specific meeting time offer\n\nThis cadence showed 23% lower unsubscribe intent and 18% higher eventual meeting bookings.\n\n**Critical addition:** Multi-threading at Day 3. When a second stakeholder at the same company was contacted during the \"research phase\" (Hours 12-36), conversion increased 3.1x. The simulation strongly supports reaching multiple buying committee members early.\n\n**Late responder insight:** 15% of meetings were booked in the Day 12-15 window by personas who needed internal approval time. Don't give up after Day 8.",
        "tool_calls": [
            {"name": "insight_forge", "arguments": {"query": "email cadence timing optimization and multi-threading impact"}, "result": "Day 1-3-8-15 cadence outperformed Day 1-2-4 by 18% in meeting bookings with 23% fewer unsubscribes. Multi-threading (2+ contacts at same company) at Day 3 increased conversion 3.1x."},
        ],
        "sources": ["Cadence Optimization Analysis", "Multi-Threading Impact Study", "Temporal Engagement Patterns"],
    },
    "fin": {
        "response": "Fin AI agent data from the simulation:\n\n• **Resolution rate claims are the #1 persuasion lever** — \"50% AI resolution\" was referenced in 67% of positive engagement signals across ALL persona types\n• Agents who received Fin-specific messaging showed 2.4x higher engagement than those who received generic \"AI support\" messaging\n• The most effective Fin proof point was: \"48% resolution rate in 30-day pilot\" — specific, time-bounded, and verifiable\n• IT Leaders specifically asked about Fin's accuracy on technical queries vs. simple FAQ-type questions\n• Healthcare personas needed assurance that Fin could handle HIPAA-sensitive interactions\n\n**Interesting pattern:** Personas who had previously experienced a failed chatbot deployment (Cluster 4: Skeptical Evaluators) were actually MORE likely to engage with Fin messaging when it included accuracy benchmarks and pilot program structure. They want AI to work — they just need proof.\n\nRecommendation: Create a \"Fin Accuracy Report\" one-pager showing resolution rates by ticket category, and include it as an attachment in Email 2 of the sequence.",
        "tool_calls": [
            {"name": "panorama_search", "arguments": {"query": "Fin AI agent perception and engagement metrics across persona types"}, "result": "Fin-specific messaging achieved 2.4x engagement vs generic AI messaging. 50% resolution rate claim was most-cited metric. Skeptical Evaluators showed 34% eventual conversion when provided accuracy benchmarks."},
        ],
        "sources": ["Fin Perception Analysis", "AI Accuracy Benchmark Study", "Pilot Program Engagement Data"],
    },
}

DEFAULT_CHAT = {
    "response": "That's a great question! Based on the simulation data, here's what I can tell you:\n\nThe 72-hour simulation with 200 AI agents produced 12,384 total interactions across Twitter and Reddit platforms. The key themes that emerged were:\n\n1. **ROI-driven messaging outperforms speed messaging** by 3.2x among senior buyer personas\n2. **Healthcare and Fintech require compliance-first positioning** — standard messaging only achieves 12% engagement vs 31% with compliance front-loaded\n3. **Multi-threading (reaching multiple stakeholders)** increases conversion 4.7x\n4. **Optimal cadence is Day 1-3-8-15** instead of the current Day 1-2-4\n\nYou can ask me about specific topics like:\n- Subject line performance\n- Persona-specific engagement patterns\n- Objection handling strategies\n- ROI messaging optimization\n- Email cadence recommendations\n- Fin AI agent positioning\n- Industry-specific approaches (Healthcare, Fintech, etc.)\n\nWhat would you like to dive deeper into?",
    "tool_calls": [
        {"name": "panorama_search", "arguments": {"query": "simulation overview and key metrics"}, "result": "72-hour simulation, 200 agents, 12,384 interactions, 847 unique threads, 94.2% statistical confidence. Top finding: segment-specific messaging improves engagement 35-45%."},
    ],
    "sources": ["Full Simulation Report", "Executive Summary", "Cross-Section Analysis"],
}


_REPORT_CHAT_SYSTEM = """You are MiroFish, an AI research analyst for Intercom's GTM team.

You have access to results from a completed swarm intelligence simulation:
- 200 AI agents representing buyer personas across SaaS, Healthcare, Fintech, and E-commerce
- 72-hour simulation, 144 rounds, running on Twitter and Reddit platforms
- Outbound campaign targeting mid-market companies currently using Zendesk

Key findings you should reference:
- VP of Support personas showed 3.2x higher engagement with ROI-driven messaging vs speed-to-value messaging
- "Your Zendesk bill is 3x what it should be" achieved 34.7% open rate but 8.2% spam flag rate in Healthcare
- Healthcare and Fintech require compliance-first messaging (12% engagement without vs 31% with)
- Optimal email cadence is Day 1-3-8-15 (not Day 1-2-4)
- Fin AI agent 50% resolution rate was the single most persuasive data point (referenced in 67% of positive signals)
- Multi-threading (3+ personas at same company) increases meeting booking 4.7x
- 12,384 total interactions, 847 unique threads, 94.2% statistical confidence
- Subject line "How [Company] cut support costs 40% with AI" is the safest universal option (31.2% open, 2.1% spam)
- "Replace Zendesk in 30 days" had 24.3% open rate but 11.7% spam flag — worst performer
- Data-driven tone outperformed casual tone by 18% among VP/Director personas
- Medium emails (100-200 words) optimal length; short emails have lowest meeting conversion
- Skeptical Evaluators (19% of agents) have the HIGHEST eventual meeting rate (34%) when objections are addressed
- Top objection: "We just renewed our Zendesk contract" (34% of negative responses)
- 8 "influencer" agents (4% of population) generated 34% of positive sentiment cascades

Respond with data-backed insights. Use markdown formatting.
Reference specific metrics and percentages from the simulation data.
Keep responses focused and actionable. If asked about something not in the simulation data, say so honestly."""


@app.route("/api/report/chat", methods=["POST"])
def report_chat():
    body = request.get_json(silent=True) or {}
    question = (body.get("message") or body.get("question") or "")
    chat_history = body.get("chat_history") or []

    # Try LLM first
    llm_messages = [{"role": "system", "content": _REPORT_CHAT_SYSTEM}]
    for msg in chat_history:
        if msg.get("role") in ("user", "assistant"):
            llm_messages.append({"role": msg["role"], "content": msg["content"]})
    llm_messages.append({"role": "user", "content": question})

    llm_response = chat_completion(llm_messages, max_tokens=2048)

    if llm_response:
        return _ok({
            "response": llm_response,
            "tool_calls": [
                {"name": "insight_forge", "arguments": {"query": question[:100]}, "result": "Analyzed simulation data with LLM."},
            ],
            "sources": ["Simulation Report", "Agent Engagement Data", "LLM Analysis"],
        })

    # Fallback: keyword matching
    q_lower = question.lower()
    matched = None
    for keyword, response_data in CHAT_RESPONSES.items():
        if keyword in q_lower:
            matched = response_data
            break

    if not matched:
        matched = DEFAULT_CHAT

    return _ok(matched)


# ---------------------------------------------------------------------------
# Settings API
# ---------------------------------------------------------------------------

@app.route("/api/settings/test-llm", methods=["POST"])
def test_llm():
    return jsonify({
        "ok": True,
        "model": "claude-sonnet-4-20250514",
        "message": "Demo mode — connection simulated",
    })


@app.route("/api/settings/test-zep", methods=["POST"])
def test_zep():
    return jsonify({
        "ok": True,
        "message": "Demo mode — connection simulated",
    })


@app.route("/api/settings/auth-status")
def auth_status():
    return jsonify({"authEnabled": False})


# ---------------------------------------------------------------------------
# Graph project stubs (called by frontend graphApi module)
# ---------------------------------------------------------------------------

@app.route("/api/graph/project/<project_id>")
def graph_project(project_id):
    return _ok({"project_id": project_id, "name": "Demo Project", "status": "active"})


@app.route("/api/graph/project/list")
def graph_project_list():
    return _ok({"projects": []})


@app.route("/api/graph/project/<project_id>", methods=["DELETE"])
def graph_project_delete(project_id):
    return _ok({"deleted": True})


@app.route("/api/graph/project/<project_id>/reset", methods=["POST"])
def graph_project_reset(project_id):
    return _ok({"reset": True})


@app.route("/api/graph/ontology/generate", methods=["POST"])
def graph_ontology_generate():
    return _ok({"ontology": "demo-ontology"})


@app.route("/api/graph/tasks")
def graph_tasks():
    return _ok({"tasks": []})


@app.route("/api/graph/delete/<graph_id>", methods=["DELETE"])
def graph_delete(graph_id):
    return _ok({"deleted": True})


# ---------------------------------------------------------------------------
# Simulation stubs (additional endpoints from frontend API module)
# ---------------------------------------------------------------------------

@app.route("/api/simulation/entities/<graph_id>/<entity_uuid>")
def sim_entity(graph_id, entity_uuid):
    return _ok({"uuid": entity_uuid, "name": "Demo Entity"})


@app.route("/api/simulation/entities/<graph_id>/by-type/<entity_type>")
def sim_entities_by_type(graph_id, entity_type):
    return _ok({"entities": []})


@app.route("/api/simulation/prepare/status", methods=["POST"])
def sim_prepare_status():
    return _ok({"status": "prepared"})


@app.route("/api/simulation/stop", methods=["POST"])
def sim_stop():
    return _ok({"status": "stopped"})


@app.route("/api/simulation/<sim_id>/profiles")
def sim_profiles(sim_id):
    return _ok({"profiles": []})


@app.route("/api/simulation/<sim_id>/profiles/realtime")
def sim_profiles_realtime(sim_id):
    return _ok({"profiles": []})


@app.route("/api/simulation/<sim_id>/config")
def sim_config(sim_id):
    return _ok({"config": {"total_hours": 72, "minutes_per_round": 30, "platform_mode": "parallel"}})


@app.route("/api/simulation/<sim_id>/config/realtime")
def sim_config_realtime(sim_id):
    return _ok({"config": {}})


@app.route("/api/simulation/<sim_id>/config/download")
def sim_config_download(sim_id):
    return Response("{}", mimetype="application/json", headers={"Content-Disposition": "attachment; filename=config.json"})


@app.route("/api/simulation/script/<script_name>/download")
def sim_script_download(script_name):
    return Response("", mimetype="text/plain", headers={"Content-Disposition": f"attachment; filename={script_name}"})


@app.route("/api/simulation/generate-profiles", methods=["POST"])
def sim_generate_profiles():
    return _ok({"profiles": []})


_INTERVIEW_RESPONSES = {
    "messaging": "The subject line 'Your Zendesk bill is 3x what it should be' caught my attention immediately — it called out a real pain point. However, the 'Replace Zendesk in 30 days' variant felt too aggressive. I'd respond better to messaging that positions Intercom as a complement or upgrade rather than a rip-and-replace.",
    "pricing": "Cost is a real factor for our team. We're spending $12K/month on Zendesk and the 40% savings claim is compelling. But I need to see a detailed TCO comparison that includes migration costs, training time, and the first 6 months of potential productivity loss.",
    "competition": "We evaluated Freshdesk last quarter and it didn't meet our needs on the AI front. Intercom's Fin agent is genuinely differentiated — the intent understanding is impressive. My concern is whether it handles our edge cases as well as the demo suggests.",
    "objection": "My biggest concern is migration risk. We have 3 years of customer data, 200+ macros, and custom integrations built on Zendesk's API. I need a clear migration playbook with timelines before I can advocate for a switch internally.",
    "engagement": "I engaged mostly on Twitter because that's where I follow industry conversations. I shared the ROI-focused content with my team because those numbers were specific enough to be credible. The generic 'AI is the future' posts didn't resonate — I need concrete evidence.",
    "recommendation": "If I were advising Intercom's GTM team: lead with the cost angle for execs like me, but make sure the technical documentation is solid for our IT team. We won't make a decision without IT sign-off, and they'll dig deep into the API docs.",
}

_INTERVIEW_KEYWORD_MAP = {
    "messaging": ["messag", "subject", "copy", "email", "content", "campaign"],
    "pricing": ["pric", "cost", "budget", "spend", "tco", "roi", "money", "savings"],
    "competition": ["compet", "zendesk", "freshdesk", "rival", "alternative", "versus", "vs"],
    "objection": ["objection", "concern", "risk", "worry", "block", "hesitat", "migrat"],
    "engagement": ["engage", "interact", "action", "click", "share", "platform", "twitter", "reddit"],
    "recommendation": ["recommend", "advice", "suggest", "improv", "next step", "gtm"],
}


def _interview_keyword_fallback(question, agent_role):
    q = question.lower()
    for key, keywords in _INTERVIEW_KEYWORD_MAP.items():
        if any(kw in q for kw in keywords):
            return _INTERVIEW_RESPONSES[key]
    return (
        f"That's a great question. From my perspective as {agent_role or 'a stakeholder'}, "
        "the key factor in any vendor decision is whether the solution genuinely solves a "
        "pain point we have today. I saw some compelling data in the simulation, particularly "
        "around cost efficiency and AI-first resolution. I'd want to see a pilot program "
        "before committing to anything."
    )


def _build_persona_traits(role):
    role_lower = (role or "").lower()
    if "vp" in role_lower or "director" in role_lower:
        return {
            "seniority": "Executive",
            "priorities": "ROI and cost efficiency, team productivity, vendor consolidation",
            "communication_style": "Executive — concise, data-driven, focused on business outcomes",
            "objections": "Migration risk and downtime, contract lock-in concerns, integration complexity",
            "decision_factors": "TCO comparison, peer references, pilot program availability",
        }
    if "it" in role_lower or "engineer" in role_lower or "cto" in role_lower:
        return {
            "seniority": "Technical Leader",
            "priorities": "Security and compliance, API quality and documentation, integration ecosystem",
            "communication_style": "Technical — detail-oriented, skeptical of marketing claims",
            "objections": "Data migration complexity, SSO/SAML requirements, scalability concerns",
            "decision_factors": "Technical documentation, API capabilities, security certifications",
        }
    if "ops" in role_lower or "operations" in role_lower:
        return {
            "seniority": "Operations Leader",
            "priorities": "Process efficiency, cross-team alignment, reporting and analytics",
            "communication_style": "Process-oriented — systematic, focused on workflows and metrics",
            "objections": "Change management overhead, training requirements, workflow disruption",
            "decision_factors": "Implementation timeline, training resources, workflow customization",
        }
    if "cfo" in role_lower or "finance" in role_lower:
        return {
            "seniority": "Finance Executive",
            "priorities": "Cost reduction, headcount efficiency, ROI with clear timeframes",
            "communication_style": "Numbers-focused — needs quantified business case and payback period",
            "objections": "Total cost of ownership uncertainty, hidden fees, switching costs",
            "decision_factors": "ROI calculations, payback period, board-presentable business case",
        }
    return {
        "seniority": "Senior Stakeholder",
        "priorities": "Customer satisfaction, team enablement, platform reliability",
        "communication_style": "Balanced — open to evaluation, values peer recommendations",
        "objections": "Learning curve, feature parity, support responsiveness",
        "decision_factors": "Product demos, case studies, free trial experience",
    }


@app.route("/api/simulation/interview", methods=["POST"])
def sim_interview():
    body = request.get_json(silent=True) or {}
    agent_name = body.get("agent_name", "Agent")
    agent_role = body.get("agent_role", "")
    agent_company = body.get("agent_company", "")
    prompt = body.get("prompt", "")
    chat_history = body.get("chat_history") or []

    traits = _build_persona_traits(agent_role)

    system_prompt = f"""You are {agent_name}, {agent_role}{(' at ' + agent_company) if agent_company else ''}.

Your persona:
- Seniority: {traits['seniority']}
- Priorities: {traits['priorities']}
- Communication style: {traits['communication_style']}
- Likely objections: {traits['objections']}
- Decision factors: {traits['decision_factors']}

You participated in a simulated outbound campaign evaluation where Intercom targeted mid-market companies currently using Zendesk. The simulation ran 200 AI agents for 72 hours across Twitter and Reddit.

Key simulation findings you experienced:
- ROI-driven messaging (40% cost savings) was compelling but you need proof
- Fin AI agent's 50% resolution rate claim was the most persuasive data point
- Subject line "Your Zendesk bill is 3x what it should be" got your attention but felt aggressive
- You engaged on Twitter/Reddit sharing industry perspectives with peers
- Multi-threading (multiple people at your company being contacted) influenced your evaluation

Stay in character. Answer from your professional perspective.
Reference specific data points when relevant.
Be opinionated — you have real preferences and concerns.
Keep responses conversational, 2-4 paragraphs."""

    llm_messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        if msg.get("role") in ("user", "assistant"):
            llm_messages.append({"role": msg["role"], "content": msg["content"]})
    llm_messages.append({"role": "user", "content": prompt})

    llm_response = chat_completion(llm_messages, max_tokens=1024)

    if llm_response:
        return _ok({"response": llm_response})

    # Fallback: keyword matching
    return _ok({"response": _interview_keyword_fallback(prompt, agent_role)})


@app.route("/api/simulation/interview/batch", methods=["POST"])
def sim_interview_batch():
    return _ok({"responses": []})


@app.route("/api/simulation/interview/all", methods=["POST"])
def sim_interview_all():
    return _ok({"responses": []})


@app.route("/api/simulation/interview/history", methods=["POST"])
def sim_interview_history():
    return _ok({"history": []})


@app.route("/api/simulation/env-status", methods=["POST"])
def sim_env_status():
    return _ok({"status": "active"})


@app.route("/api/simulation/close-env", methods=["POST"])
def sim_close_env():
    return _ok({"closed": True})


# ---------------------------------------------------------------------------
# Auth stubs
# ---------------------------------------------------------------------------

@app.route("/api/auth/logout")
def auth_logout():
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Demo Speed Control
# ---------------------------------------------------------------------------

@app.route("/api/demo/speed", methods=["GET", "POST"])
def demo_speed():
    global _demo_speed
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        _demo_speed = max(0.1, float(body.get("speed", 1.0)))
        return _ok({"speed": _demo_speed})
    return _ok({"speed": _demo_speed})


@app.route("/api/demo/skip/<phase>", methods=["POST"])
def demo_skip(phase):
    """Instantly complete a phase by backdating its start time."""
    if phase == "graph":
        for task_id in _graph_tasks:
            _graph_tasks[task_id]["start"] = 0
        return _ok({"skipped": "graph"})
    elif phase == "simulation":
        for sim_id in _simulations:
            _simulations[sim_id]["start"] = 0
        return _ok({"skipped": "simulation"})
    elif phase == "report":
        for report_id in _reports:
            _reports[report_id]["start"] = 0
        return _ok({"skipped": "report"})
    return _err(f"Unknown phase: {phase}")


@app.route("/api/demo/reset", methods=["POST"])
def demo_reset():
    """Clear all in-memory state for a fresh demo."""
    global _demo_speed
    _graph_tasks.clear()
    _simulations.clear()
    _reports.clear()
    _demo_speed = 1.0
    return _ok({"reset": True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"MiroFish Demo Backend starting on port {port} (demo mode)")
    app.run(host="0.0.0.0", port=port, debug=debug)
