"""Demo Simulation Blueprint — mock simulation lifecycle and agent interviews."""

import math
import random
import time

from flask import Blueprint, Response, request

from . import (
    _simulations, _ok, _err, _elapsed,
    SIMULATION_RUN_SECONDS, TOTAL_ROUNDS,
)
from .graph import _build_knowledge_graph

from llm_client import chat_completion

simulation_demo_bp = Blueprint('demo_simulation', __name__)


# ---------------------------------------------------------------------------
# Simulation lifecycle
# ---------------------------------------------------------------------------

@simulation_demo_bp.route("/api/simulation/create", methods=["POST"])
def sim_create():
    sim_id = f"demo-sim-{int(time.time()) % 100000:05d}"
    _simulations[sim_id] = {"start": time.time()}
    return _ok({"simulation_id": sim_id, "status": "created"})


@simulation_demo_bp.route("/api/simulation/prepare", methods=["POST"])
def sim_prepare():
    body = request.get_json(silent=True) or {}
    sim_id = body.get("simulation_id", list(_simulations.keys())[-1] if _simulations else "demo-sim-00001")
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}
    return _ok({"simulation_id": sim_id, "status": "prepared"})


@simulation_demo_bp.route("/api/simulation/start", methods=["POST"])
def sim_start():
    body = request.get_json(silent=True) or {}
    sim_id = body.get("simulation_id", list(_simulations.keys())[-1] if _simulations else "demo-sim-00001")
    if sim_id not in _simulations:
        _simulations[sim_id] = {"start": time.time()}
    else:
        _simulations[sim_id]["start"] = time.time()
    return _ok({"status": "running"})


@simulation_demo_bp.route("/api/simulation/<sim_id>/run-status")
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


@simulation_demo_bp.route("/api/simulation/<sim_id>/run-status/detail")
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


@simulation_demo_bp.route("/api/simulation/<sim_id>/timeline")
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


@simulation_demo_bp.route("/api/simulation/<sim_id>")
def sim_get(sim_id):
    return _ok({
        "simulation_id": sim_id,
        "status": "completed" if sim_id in _simulations and _elapsed(_simulations, sim_id) > SIMULATION_RUN_SECONDS() else "running",
        "config": {"total_hours": 72, "minutes_per_round": 30, "platform_mode": "parallel"},
    })


@simulation_demo_bp.route("/api/simulation/list")
def sim_list():
    return _ok({"simulations": []})


@simulation_demo_bp.route("/api/simulation/history")
def sim_history():
    return _ok({"history": []})


@simulation_demo_bp.route("/api/simulation/<sim_id>/actions")
def sim_actions(sim_id):
    return _ok({"actions": _generate_agent_actions(72)})


@simulation_demo_bp.route("/api/simulation/<sim_id>/agent-stats")
def sim_agent_stats(sim_id):
    return _ok({"stats": []})


@simulation_demo_bp.route("/api/simulation/<sim_id>/posts")
def sim_posts(sim_id):
    return _ok({"posts": []})


@simulation_demo_bp.route("/api/simulation/<sim_id>/comments")
def sim_comments(sim_id):
    return _ok({"comments": []})


@simulation_demo_bp.route("/api/simulation/entities/<graph_id>")
def sim_entities(graph_id):
    nodes, _ = _build_knowledge_graph()
    return _ok({"entities": nodes})


@simulation_demo_bp.route("/api/simulation/entities/<graph_id>/<entity_uuid>")
def sim_entity(graph_id, entity_uuid):
    return _ok({"uuid": entity_uuid, "name": "Demo Entity"})


@simulation_demo_bp.route("/api/simulation/entities/<graph_id>/by-type/<entity_type>")
def sim_entities_by_type(graph_id, entity_type):
    return _ok({"entities": []})


@simulation_demo_bp.route("/api/simulation/prepare/status", methods=["POST"])
def sim_prepare_status():
    return _ok({"status": "prepared"})


@simulation_demo_bp.route("/api/simulation/stop", methods=["POST"])
def sim_stop():
    return _ok({"status": "stopped"})


@simulation_demo_bp.route("/api/simulation/<sim_id>/profiles")
def sim_profiles(sim_id):
    return _ok({"profiles": []})


@simulation_demo_bp.route("/api/simulation/<sim_id>/profiles/realtime")
def sim_profiles_realtime(sim_id):
    return _ok({"profiles": []})


@simulation_demo_bp.route("/api/simulation/<sim_id>/config")
def sim_config(sim_id):
    return _ok({"config": {"total_hours": 72, "minutes_per_round": 30, "platform_mode": "parallel"}})


@simulation_demo_bp.route("/api/simulation/<sim_id>/config/realtime")
def sim_config_realtime(sim_id):
    return _ok({"config": {}})


@simulation_demo_bp.route("/api/simulation/<sim_id>/config/download")
def sim_config_download(sim_id):
    return Response("{}", mimetype="application/json", headers={"Content-Disposition": "attachment; filename=config.json"})


@simulation_demo_bp.route("/api/simulation/script/<script_name>/download")
def sim_script_download(script_name):
    return Response("", mimetype="text/plain", headers={"Content-Disposition": f"attachment; filename={script_name}"})


@simulation_demo_bp.route("/api/simulation/generate-profiles", methods=["POST"])
def sim_generate_profiles():
    return _ok({"profiles": []})


# ---------------------------------------------------------------------------
# Agent interviews
# ---------------------------------------------------------------------------

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


@simulation_demo_bp.route("/api/simulation/interview", methods=["POST"])
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

    return _ok({"response": _interview_keyword_fallback(prompt, agent_role)})


@simulation_demo_bp.route("/api/simulation/interview/batch", methods=["POST"])
def sim_interview_batch():
    return _ok({"responses": []})


@simulation_demo_bp.route("/api/simulation/interview/all", methods=["POST"])
def sim_interview_all():
    return _ok({"responses": []})


@simulation_demo_bp.route("/api/simulation/interview/history", methods=["POST"])
def sim_interview_history():
    return _ok({"history": []})


@simulation_demo_bp.route("/api/simulation/env-status", methods=["POST"])
def sim_env_status():
    return _ok({"status": "active"})


@simulation_demo_bp.route("/api/simulation/close-env", methods=["POST"])
def sim_close_env():
    return _ok({"closed": True})


# ---------------------------------------------------------------------------
# Action generator
# ---------------------------------------------------------------------------

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
