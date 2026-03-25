"""Demo Graph API Blueprint — mock knowledge graph build and retrieval."""

import time

from flask import Blueprint, jsonify, request

from . import (
    _graph_tasks, _ok, _err, _elapsed,
    GRAPH_BUILD_SECONDS,
)

graph_demo_bp = Blueprint('demo_graph', __name__)


@graph_demo_bp.route("/api/graph/build", methods=["POST"])
def graph_build():
    task_id = f"demo-graph-{int(time.time()) % 100000:05d}"
    _graph_tasks[task_id] = {"start": time.time()}
    return jsonify({"success": True, "task_id": task_id, "status": "building"})


@graph_demo_bp.route("/api/graph/task/<task_id>")
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


@graph_demo_bp.route("/api/graph/data/<graph_id>")
def graph_data(graph_id):
    nodes, edges = _build_knowledge_graph()
    return _ok({
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    })


@graph_demo_bp.route("/api/graph/project/<project_id>")
def graph_project(project_id):
    return _ok({"project_id": project_id, "name": "Demo Project", "status": "active"})


@graph_demo_bp.route("/api/graph/project/list")
def graph_project_list():
    return _ok({"projects": []})


@graph_demo_bp.route("/api/graph/project/<project_id>", methods=["DELETE"])
def graph_project_delete(project_id):
    return _ok({"deleted": True})


@graph_demo_bp.route("/api/graph/project/<project_id>/reset", methods=["POST"])
def graph_project_reset(project_id):
    return _ok({"reset": True})


@graph_demo_bp.route("/api/graph/ontology/generate", methods=["POST"])
def graph_ontology_generate():
    return _ok({"ontology": "demo-ontology"})


@graph_demo_bp.route("/api/graph/tasks")
def graph_tasks():
    return _ok({"tasks": []})


@graph_demo_bp.route("/api/graph/delete/<graph_id>", methods=["DELETE"])
def graph_delete(graph_id):
    return _ok({"deleted": True})


# ---------------------------------------------------------------------------
# Knowledge graph data generator
# ---------------------------------------------------------------------------

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
