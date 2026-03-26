"""
MiroFish Demo Backend — Lightweight mock Flask server.

Serves realistic, pre-built demo data for all frontend endpoints so the app
can run without the heavy camel-ai / PyTorch production backend.  Total
image size drops from ~5.8 GB to ~150 MB.

Routes are organized into Flask Blueprints under app/api/demo/.
"""

import os
import random
import sys
import importlib.util as _ilu
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
load_dotenv(override=True)

# Add backend/ to sys.path for llm_client, and app/api/ for the demo package.
# Importing as "from demo import ..." avoids loading the production app/__init__.py.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _backend_dir)
sys.path.insert(0, os.path.join(_backend_dir, "app", "api"))

from data.demo_preset.loader import (   # noqa: E402
    get_dashboard,
    get_preset_report_id,
    get_preset_sim_id,
    get_report as get_preset_report,
    get_simulation as get_preset_simulation,
    is_demo_preset_enabled,
)

from flask import Flask, jsonify, request
from flask_cors import CORS

from demo import (                       # noqa: E402
    register_demo_blueprints,
    _graph_tasks,
    _simulations,
    _reports,
)

app = Flask(__name__)
CORS(app)
register_demo_blueprints(app)

_preset_loaded: bool = False  # True when demo preset data is active

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data):
    return jsonify({"success": True, "data": data})


def _err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


# ---------------------------------------------------------------------------
# What-If Analysis API
# ---------------------------------------------------------------------------

_spec = _ilu.spec_from_file_location(
    "whatif_engine", Path(__file__).parent / "app/services/whatif_engine.py",
)
_whatif_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_whatif_mod)
WhatIfEngine = _whatif_mod.WhatIfEngine

_whatif_engine = WhatIfEngine()


@app.route("/api/v1/whatif/scenarios", methods=["POST"])
def whatif_create_scenario():
    """Create a what-if scenario variant from a base with modifications."""
    body = request.get_json(silent=True) or {}
    base_id = body.get("base_scenario_id")
    modifications = body.get("modifications", [])
    label = body.get("label", "")

    if not modifications:
        return _err("At least one modification is required")

    try:
        scenario = _whatif_engine.create_scenario(base_id, modifications, label)
        return _ok(scenario.to_dict())
    except Exception as e:
        return _err(str(e))


@app.route("/api/v1/whatif/scenarios", methods=["GET"])
def whatif_list_scenarios():
    """List all what-if scenarios."""
    scenarios = _whatif_engine.list_scenarios()
    return _ok({"scenarios": [s.to_dict() for s in scenarios]})


@app.route("/api/v1/whatif/scenarios/<scenario_id>")
def whatif_get_scenario(scenario_id):
    """Get a specific what-if scenario."""
    scenario = _whatif_engine.get_scenario(scenario_id)
    if not scenario:
        return _err("Scenario not found", 404)
    return _ok(scenario.to_dict())


@app.route("/api/v1/whatif/scenarios/<scenario_id>/run", methods=["POST"])
def whatif_run_scenario(scenario_id):
    """Run a what-if scenario and return results."""
    try:
        results = _whatif_engine.run_scenario(scenario_id)
        return _ok(results.to_dict())
    except ValueError as e:
        return _err(str(e), 404)
    except Exception as e:
        return _err(str(e))


@app.route("/api/v1/whatif/scenarios/<scenario_id>/results")
def whatif_get_results(scenario_id):
    """Get results for a previously-run scenario."""
    results = _whatif_engine.get_results(scenario_id)
    if not results:
        return _err("No results found. Run the scenario first.", 404)
    return _ok(results.to_dict())


@app.route("/api/v1/whatif/compare", methods=["POST"])
def whatif_compare():
    """Compare a variant to its base scenario."""
    body = request.get_json(silent=True) or {}
    base_id = body.get("base_id", "")
    variant_id = body.get("variant_id", "")

    if not base_id or not variant_id:
        return _err("Both base_id and variant_id are required")

    try:
        comparison = _whatif_engine.compare_to_base(base_id, variant_id)
        return _ok(comparison.to_dict())
    except ValueError as e:
        return _err(str(e), 404)


@app.route("/api/v1/whatif/sensitivity", methods=["POST"])
def whatif_sensitivity():
    """Run a parameter sensitivity sweep."""
    body = request.get_json(silent=True) or {}
    base_id = body.get("base_scenario_id")
    parameter = body.get("parameter", "")
    value_range = body.get("value_range", [])

    if not parameter:
        return _err("parameter is required")
    if not value_range or len(value_range) < 2:
        return _err("value_range must contain at least 2 values")

    try:
        result = _whatif_engine.run_sensitivity(base_id, parameter, value_range)
        return _ok(result.to_dict())
    except Exception as e:
        return _err(str(e))


@app.route("/api/v1/whatif/scenarios/<base_id>/variants")
def whatif_get_variants(base_id):
    """Get all variants linked to a base scenario."""
    variants = _whatif_engine.get_variants(base_id)
    return _ok({"variants": [v.to_dict() for v in variants]})


# ---------------------------------------------------------------------------
# Adjacency Matrix API (not in demo blueprint — added for heatmap component)
# ---------------------------------------------------------------------------

@app.route("/api/simulation/<sim_id>/adjacency-matrix")
def sim_adjacency_matrix(sim_id):
    """Return agent-to-agent interaction matrix for heatmap visualization."""
    agents = [
        "Sarah Chen", "Marcus Johnson", "Priya Patel", "David Kim",
        "Rachel Torres", "James Wright", "Anika Sharma", "Tom O'Brien",
        "Elena Vasquez", "Michael Chang", "Lisa Park", "Sofia Martinez",
        "Nathan Lee", "Catherine Hayes", "Robert Williams",
    ]
    n = len(agents)
    rng = random.Random(42)

    # Define clusters: agents in the same cluster interact more
    clusters = [0, 1, 0, 2, 0, 1, 2, 1, 1, 2, 0, 2, 2, 0, 1]

    # Build symmetric interaction counts
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[i][j] = rng.randint(40, 120)
            else:
                same_cluster = clusters[i] == clusters[j]
                base = rng.randint(8, 35) if same_cluster else rng.randint(0, 12)
                matrix[i][j] = base
                matrix[j][i] = base

    # Normalize to 0-1
    flat = [v for row in matrix for v in row]
    max_val = max(flat) or 1
    values = [[round(v / max_val, 3) for v in row] for row in matrix]

    # Row and column totals (sum of off-diagonal interactions)
    row_totals = [sum(matrix[i][j] for j in range(n) if j != i) for i in range(n)]
    col_totals = [sum(matrix[i][j] for i in range(n) if i != j) for j in range(n)]

    # Influence ranking (by total interactions)
    influence_order = sorted(range(n), key=lambda i: row_totals[i], reverse=True)
    # Cluster ordering (group by cluster, then by influence within)
    cluster_order = sorted(range(n), key=lambda i: (clusters[i], -row_totals[i]))

    return _ok({
        "agents": agents,
        "values": values,
        "row_totals": row_totals,
        "col_totals": col_totals,
        "clusters": clusters,
        "sort_orders": {
            "alphabetical": list(range(n)),
            "cluster": cluster_order,
            "influence": influence_order,
        },
    })


# ---------------------------------------------------------------------------
# Demo Preset API
# ---------------------------------------------------------------------------

@app.route("/api/demo-preset")
def demo_preset_status():
    """Check if demo preset is available and/or loaded."""
    return _ok({
        "available": is_demo_preset_enabled(),
        "loaded": _preset_loaded,
        "simulation_id": get_preset_sim_id() if _preset_loaded else None,
        "report_id": get_preset_report_id() if _preset_loaded else None,
    })


@app.route("/api/demo-preset/load", methods=["POST"])
def demo_preset_load():
    """Load demo preset data into in-memory state for a curated presentation."""
    global _preset_loaded

    if not is_demo_preset_enabled():
        return _err("Demo preset not enabled. Set DEMO_PRESET=true in environment.", 403)

    preset_sim = get_preset_simulation()
    preset_report = get_preset_report()
    sim_id = preset_sim["simulation_id"]
    report_id = preset_report["report_id"]

    # Seed in-memory state so existing endpoints serve preset data
    _simulations[sim_id] = {"start": 0}  # start=0 means completed (elapsed > threshold)
    _graph_tasks[f"demo-graph-preset"] = {"start": 0}
    _reports[report_id] = {"start": 0, "sim_id": sim_id}
    _preset_loaded = True

    return _ok({
        "loaded": True,
        "simulation_id": sim_id,
        "status": "completed" if sim_id in _simulations and _elapsed(_simulations, sim_id) > SIMULATION_RUN_SECONDS() else "running",
        "config": {"total_hours": 72, "minutes_per_round": 30, "platform_mode": "parallel"},
        "report_id": report_id,
        "graph_task_id": "demo-graph-preset",
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


@app.route("/api/simulation/<sim_id>/agent-personalities")
def sim_agent_personalities(sim_id):
    import hashlib
    traits = ["confidence", "openness", "risk_aversion", "empathy", "aggressiveness"]
    names = [
        "Sarah Chen, VP Support @ Acme SaaS",
        "Marcus Johnson, CTO @ HealthFirst",
        "Priya Patel, Dir. CX @ FinServe",
        "James O'Brien, Head of Ops @ RetailCo",
        "Elena Rodriguez, VP Product @ CloudSync",
        "David Kim, Support Lead @ EduPlatform",
        "Aisha Williams, CRO @ DataDrive",
        "Tom Fischer, Dir. IT @ MediGroup",
        "Nina Yamamoto, COO @ LogiTech",
        "Carlos Mendez, VP Sales @ InsureTech",
    ]
    agents = []
    for i, name in enumerate(names):
        initial, current = {}, {}
        for trait in traits:
            seed = hashlib.md5(f"{i}-{trait}".encode()).hexdigest()
            base_val = (int(seed[:4], 16) % 60) + 20
            delta = (int(seed[4:8], 16) % 30) - 12
            initial[trait] = base_val
            current[trait] = max(0, min(100, base_val + delta))
        agents.append({
            "agent_id": i,
            "agent_name": name,
            "initial_personality": initial,
            "current_personality": current,
        })
    return _ok({"traits": traits, "agents": agents})


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
# Snapshot Comparison API
# ---------------------------------------------------------------------------

_POSITIVE_WORDS = [
    'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
    'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
    'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
]
_NEGATIVE_WORDS = [
    'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
    'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
    'problem', 'unclear', 'frustrated', 'poor', 'slow', 'lacks',
]


def _score_content(content):
    if not content:
        return 0.0
    lower = content.lower()
    pos = sum(1 for w in _POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in _NEGATIVE_WORDS if w in lower)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def _build_snapshot_at_round(sim_id, target_round):
    """Build a complete simulation state snapshot at a given round."""
    rng = random.Random(12345)
    timeline = []
    total_twitter = 0
    total_reddit = 0
    for r in range(1, target_round + 1):
        base = 3 + math.log(r + 1) * 2.5
        tw = max(0, int(base * (0.55 + rng.uniform(-0.1, 0.1))))
        rd = max(0, int(base * (0.45 + rng.uniform(-0.1, 0.1))))
        total_twitter += tw
        total_reddit += rd
        timeline.append({"round_num": r, "twitter_actions": tw, "reddit_actions": rd})

    total_actions = total_twitter + total_reddit

    # Generate cumulative agent activity up to this round
    agents_data = {}
    for r in range(1, target_round + 1):
        actions = _generate_agent_actions(r)
        for a in actions:
            name = a["agent_name"]
            if name not in agents_data:
                agents_data[name] = {
                    "name": name,
                    "actionCount": 0,
                    "sentimentSum": 0.0,
                    "sentimentCount": 0,
                    "twitter": 0,
                    "reddit": 0,
                    "firstRound": r,
                    "lastRound": r,
                }
            entry = agents_data[name]
            entry["actionCount"] += 1
            entry["lastRound"] = max(entry["lastRound"], r)
            if a["platform"] == "twitter":
                entry["twitter"] += 1
            else:
                entry["reddit"] += 1
            content = a.get("action_args", {}).get("content", "")
            if content:
                entry["sentimentSum"] += _score_content(content)
                entry["sentimentCount"] += 1

    agents_list = []
    for entry in agents_data.values():
        avg_sent = entry["sentimentSum"] / entry["sentimentCount"] if entry["sentimentCount"] else 0.0
        agents_list.append({
            "name": entry["name"],
            "actionCount": entry["actionCount"],
            "sentiment": round(avg_sent, 3),
            "twitter": entry["twitter"],
            "reddit": entry["reddit"],
            "primaryPlatform": "twitter" if entry["twitter"] >= entry["reddit"] else "reddit",
        })
    agents_list.sort(key=lambda x: x["actionCount"], reverse=True)

    overall_sentiment = 0.0
    if agents_list:
        overall_sentiment = sum(a["sentiment"] for a in agents_list) / len(agents_list)

    return {
        "round": target_round,
        "metrics": {
            "totalActions": total_actions,
            "twitterActions": total_twitter,
            "redditActions": total_reddit,
            "activeAgents": len(agents_list),
        },
        "agents": agents_list[:15],
        "sentimentAvg": round(overall_sentiment, 3),
    }


def _compute_snapshot_diff(snap_a, snap_b):
    """Compute diff between two snapshots."""
    ma, mb = snap_a["metrics"], snap_b["metrics"]
    metric_diff = {}
    for key in ma:
        a_val, b_val = ma[key], mb[key]
        delta = b_val - a_val
        pct = round(delta / a_val * 100, 1) if a_val else 0.0
        metric_diff[key] = {"a": a_val, "b": b_val, "delta": delta, "pctChange": pct}

    # Agent-level changes
    agents_a = {a["name"]: a for a in snap_a["agents"]}
    agents_b = {a["name"]: a for a in snap_b["agents"]}
    all_names = set(agents_a) | set(agents_b)

    new_agents = [agents_b[n] for n in all_names if n not in agents_a]
    removed_agents = [agents_a[n] for n in all_names if n not in agents_b]

    agent_changes = []
    biggest_change = {"description": "No changes", "value": 0}
    most_affected = {"name": "N/A", "totalChange": 0}

    for name in sorted(all_names):
        if name not in agents_a or name not in agents_b:
            continue
        aa, ab = agents_a[name], agents_b[name]
        action_delta = ab["actionCount"] - aa["actionCount"]
        sentiment_delta = round(ab["sentiment"] - aa["sentiment"], 3)
        total_change = abs(action_delta) + abs(sentiment_delta) * 10

        if action_delta != 0:
            agent_changes.append({
                "agent": name,
                "metric": "actionCount",
                "oldValue": aa["actionCount"],
                "newValue": ab["actionCount"],
                "change": action_delta,
            })
        if abs(sentiment_delta) > 0.01:
            agent_changes.append({
                "agent": name,
                "metric": "sentiment",
                "oldValue": aa["sentiment"],
                "newValue": ab["sentiment"],
                "change": sentiment_delta,
            })

        if total_change > most_affected["totalChange"]:
            most_affected = {"name": name, "totalChange": round(total_change, 1)}

    if agent_changes:
        top = max(agent_changes, key=lambda c: abs(c["change"]))
        biggest_change = {
            "description": f"{top['agent']} {top['metric']} changed by {top['change']:+}",
            "value": abs(top["change"]),
        }

    sentiment_delta = round(snap_b["sentimentAvg"] - snap_a["sentimentAvg"], 3)

    return {
        "metrics": metric_diff,
        "agentChanges": agent_changes,
        "newAgents": new_agents,
        "removedAgents": removed_agents,
        "biggestChange": biggest_change,
        "mostAffectedAgent": most_affected,
        "totalChanges": len(agent_changes) + len(new_agents) + len(removed_agents),
        "sentimentDelta": sentiment_delta,
    }


@app.route("/api/simulation/<sim_id>/snapshot/compare")
def sim_snapshot_compare(sim_id):
    round_a = request.args.get("round_a", 1, type=int)
    round_b = request.args.get("round_b", TOTAL_ROUNDS, type=int)
    round_a = max(1, min(TOTAL_ROUNDS, round_a))
    round_b = max(1, min(TOTAL_ROUNDS, round_b))

    snap_a = _build_snapshot_at_round(sim_id, round_a)
    snap_b = _build_snapshot_at_round(sim_id, round_b)
    diff = _compute_snapshot_diff(snap_a, snap_b)

    return _ok({
        "point_a": snap_a,
        "point_b": snap_b,
        "diff": diff,
    })


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
        "graph_task_id": "demo-graph-preset",
    })


@app.route("/api/demo-preset/simulation")
def demo_preset_simulation():
    """Return full preset simulation data including coalitions and belief changes."""
    if not _preset_loaded:
        return _err("Demo preset not loaded. POST /api/demo-preset/load first.", 400)
    return _ok(get_preset_simulation())


@app.route("/api/demo-preset/report")
def demo_preset_report():
    """Return full preset report data."""
    if not _preset_loaded:
        return _err("Demo preset not loaded. POST /api/demo-preset/load first.", 400)
    return _ok(get_preset_report())


@app.route("/api/demo-preset/dashboard")
def demo_preset_dashboard():
    """Return preset dashboard widget configuration."""
    if not _preset_loaded:
        return _err("Demo preset not loaded. POST /api/demo-preset/load first.", 400)
    return _ok(get_dashboard())


# ---------------------------------------------------------------------------
# Org Chart with Information Flow
# ---------------------------------------------------------------------------

_ORG_TREE = {
    "id": "ceo-1",
    "name": "Sarah Chen",
    "title": "CEO",
    "children": [
        {
            "id": "vp-sales",
            "name": "Marcus Rivera",
            "title": "VP Sales",
            "children": [
                {"id": "sales-1", "name": "Jake Thornton", "title": "Enterprise AE"},
                {"id": "sales-2", "name": "Priya Nair", "title": "Mid-Market AE"},
                {"id": "sales-3", "name": "Tom Liu", "title": "SDR Lead"},
            ],
        },
        {
            "id": "vp-marketing",
            "name": "Aisha Patel",
            "title": "VP Marketing",
            "children": [
                {"id": "mktg-1", "name": "Dylan Park", "title": "Demand Gen"},
                {"id": "mktg-2", "name": "Nina Costa", "title": "Product Marketing"},
                {"id": "mktg-3", "name": "Eli Russo", "title": "Content Lead"},
            ],
        },
        {
            "id": "vp-cs",
            "name": "David Kim",
            "title": "VP Customer Success",
            "children": [
                {"id": "cs-1", "name": "Maria Lopez", "title": "Enterprise CSM"},
                {"id": "cs-2", "name": "Sam Okafor", "title": "Mid-Market CSM"},
                {"id": "cs-3", "name": "Jess Wang", "title": "Support Lead"},
            ],
        },
        {
            "id": "vp-product",
            "name": "Rachel Stein",
            "title": "VP Product",
            "children": [
                {"id": "prod-1", "name": "Arjun Mehta", "title": "PM — Platform"},
                {"id": "prod-2", "name": "Lucy Tran", "title": "PM — AI/ML"},
                {"id": "prod-3", "name": "Chris Novak", "title": "UX Lead"},
            ],
        },
    ],
}


def _build_org_flows(time_point):
    """Generate deterministic information flow edges for a given time point."""
    rng = random.Random(42 + time_point)

    flow_templates = [
        # Reports flowing UP
        {"source": "sales-1", "target": "vp-sales", "type": "data", "label": "Pipeline report", "direction": "up"},
        {"source": "sales-2", "target": "vp-sales", "type": "data", "label": "Deal forecast", "direction": "up"},
        {"source": "sales-3", "target": "vp-sales", "type": "data", "label": "SDR metrics", "direction": "up"},
        {"source": "mktg-1", "target": "vp-marketing", "type": "data", "label": "Campaign results", "direction": "up"},
        {"source": "mktg-2", "target": "vp-marketing", "type": "data", "label": "Win/loss analysis", "direction": "up"},
        {"source": "cs-1", "target": "vp-cs", "type": "feedback", "label": "Customer health", "direction": "up"},
        {"source": "cs-2", "target": "vp-cs", "type": "feedback", "label": "Churn risk alert", "direction": "up"},
        {"source": "cs-3", "target": "vp-cs", "type": "feedback", "label": "Support tickets", "direction": "up"},
        {"source": "prod-1", "target": "vp-product", "type": "data", "label": "Sprint velocity", "direction": "up"},
        {"source": "prod-2", "target": "vp-product", "type": "data", "label": "AI model accuracy", "direction": "up"},
        {"source": "vp-sales", "target": "ceo-1", "type": "data", "label": "Revenue update", "direction": "up"},
        {"source": "vp-marketing", "target": "ceo-1", "type": "data", "label": "MQL pipeline", "direction": "up"},
        {"source": "vp-cs", "target": "ceo-1", "type": "feedback", "label": "NPS trends", "direction": "up"},
        {"source": "vp-product", "target": "ceo-1", "type": "data", "label": "Roadmap status", "direction": "up"},
        # Directives flowing DOWN
        {"source": "ceo-1", "target": "vp-sales", "type": "decision", "label": "Q3 targets", "direction": "down"},
        {"source": "ceo-1", "target": "vp-marketing", "type": "decision", "label": "Budget realloc", "direction": "down"},
        {"source": "ceo-1", "target": "vp-product", "type": "decision", "label": "Priority shift", "direction": "down"},
        {"source": "vp-sales", "target": "sales-1", "type": "decision", "label": "Account focus", "direction": "down"},
        {"source": "vp-marketing", "target": "mktg-1", "type": "decision", "label": "Campaign brief", "direction": "down"},
        {"source": "vp-cs", "target": "cs-1", "type": "decision", "label": "Escalation plan", "direction": "down"},
        {"source": "vp-product", "target": "prod-2", "type": "decision", "label": "AI roadmap", "direction": "down"},
        # Cross-team HORIZONTAL collaboration
        {"source": "vp-sales", "target": "vp-marketing", "type": "data", "label": "Lead quality", "direction": "horizontal"},
        {"source": "vp-marketing", "target": "vp-sales", "type": "data", "label": "Content assets", "direction": "horizontal"},
        {"source": "vp-cs", "target": "vp-product", "type": "feedback", "label": "Feature requests", "direction": "horizontal"},
        {"source": "vp-product", "target": "vp-cs", "type": "data", "label": "Release notes", "direction": "horizontal"},
        {"source": "vp-sales", "target": "vp-cs", "type": "data", "label": "Deal handoff", "direction": "horizontal"},
        {"source": "mktg-2", "target": "sales-1", "type": "data", "label": "Battle cards", "direction": "horizontal"},
        {"source": "cs-1", "target": "prod-1", "type": "feedback", "label": "Bug report", "direction": "horizontal"},
    ]

    active = [f for f in flow_templates if rng.random() < 0.6 + 0.05 * time_point]
    for f in active:
        f["volume"] = rng.randint(1, 10)

    # Bottleneck detection: nodes receiving > threshold inbound flows
    inbound_counts = {}
    for f in active:
        inbound_counts[f["target"]] = inbound_counts.get(f["target"], 0) + f["volume"]
    bottleneck_threshold = 15
    bottlenecks = [nid for nid, vol in inbound_counts.items() if vol >= bottleneck_threshold]

    return active, bottlenecks


@app.route("/api/v1/org-chart")
def org_chart():
    """Return org hierarchy tree, information flows, and bottleneck data."""
    time_point = request.args.get("time", 0, type=int)
    time_point = max(0, min(time_point, 10))
    flows, bottlenecks = _build_org_flows(time_point)
    return _ok({
        "tree": _ORG_TREE,
        "flows": flows,
        "bottlenecks": bottlenecks,
        "time_points": 11,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    if is_demo_preset_enabled():
        # Auto-load preset so the app starts with curated data ready to go
        sim = get_preset_simulation()
        rpt = get_preset_report()
        _simulations[sim["simulation_id"]] = {"start": 0}
        _graph_tasks["demo-graph-preset"] = {"start": 0}
        _reports[rpt["report_id"]] = {"start": 0, "sim_id": sim["simulation_id"]}
        _preset_loaded = True
        print(f"Demo preset loaded: sim={sim['simulation_id']}, report={rpt['report_id']}")

    print(f"MiroFish Demo Backend starting on port {port} (demo mode)")
    app.run(host="0.0.0.0", port=port, debug=debug)
