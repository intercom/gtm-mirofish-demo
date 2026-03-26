"""
Agent Memory Persistence & Search API

Endpoints for querying, searching, and managing agent memory
within simulations. Falls back to in-memory mock data when Zep
is unavailable.

Also provides graph-level memory search, agent listing, and topic
extraction for the memory viewer via a separate Blueprint.
"""

import hashlib
import traceback
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from . import simulation_bp
from ..config import Config
from ..services.memory_search import MemorySearchService
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.memory')


# ---------------------------------------------------------------------------
# Deterministic mock-data helpers
# ---------------------------------------------------------------------------

# Persona types matching the GTM simulation agent archetypes
_PERSONA_TYPES = [
    "Sales Rep", "Customer Success Manager", "Product Manager",
    "Marketing Lead", "Solutions Engineer", "VP Sales",
    "Support Lead", "Account Executive", "SDR",
    "RevOps Analyst", "Partner Manager", "Field CTO",
    "Demand Gen", "Customer Advocate", "Growth Lead",
]

_TOPICS = [
    "product-led growth", "customer churn", "pipeline velocity",
    "competitive positioning", "enterprise onboarding",
    "support ticket deflection", "upsell strategy",
    "pricing model", "partner channel", "NPS improvement",
    "self-serve activation", "demo conversion rate",
]

_FACT_TEMPLATES = [
    "{agent} observed that {topic} is trending among enterprise accounts",
    "{agent} believes {topic} should be the top priority for Q2",
    "{agent} noted that competitors are investing heavily in {topic}",
    "{agent} reported a 15% improvement in metrics related to {topic}",
    "{agent} expressed concern about declining {topic} performance",
    "{agent} proposed a new initiative around {topic}",
    "{agent} shared data showing strong correlation between {topic} and retention",
    "{agent} flagged a risk: {topic} may be under-resourced next quarter",
]


def _seed(simulation_id: str, agent_id: str, salt: str = "") -> int:
    """Deterministic seed from IDs so mock data is stable across calls."""
    raw = f"{simulation_id}:{agent_id}:{salt}"
    return int(hashlib.md5(raw.encode()).hexdigest(), 16)


def _pick(items, seed_val: int, index: int = 0):
    """Deterministic pick from a list."""
    return items[(seed_val + index) % len(items)]


def _agent_name(agent_id: str, seed_val: int) -> str:
    first_names = [
        "Alex", "Jordan", "Morgan", "Casey", "Riley",
        "Taylor", "Quinn", "Avery", "Dana", "Blake",
        "Sam", "Jamie", "Drew", "Reese", "Skyler",
    ]
    return _pick(first_names, seed_val)


def _generate_facts(simulation_id: str, agent_id: str, count: int = 8):
    """Generate deterministic mock facts for an agent."""
    s = _seed(simulation_id, agent_id, "facts")
    name = _agent_name(agent_id, s)
    facts = []
    for i in range(count):
        topic = _pick(_TOPICS, s, i)
        template = _pick(_FACT_TEMPLATES, s, i + 3)
        confidence = round(0.55 + ((s + i * 7) % 40) / 100, 2)
        facts.append({
            "id": f"fact_{abs(hash((simulation_id, agent_id, i))) % 10**8:08d}",
            "text": template.format(agent=name, topic=topic),
            "topic": topic,
            "confidence": confidence,
            "source_round": (s + i * 3) % 20 + 1,
            "created_at": (
                datetime(2026, 1, 1) + timedelta(hours=(s + i * 5) % 480)
            ).isoformat(),
        })
    return facts


def _generate_memory_entries(simulation_id: str, agent_id: str, total_rounds: int = 20):
    """Generate a full mock memory dump for an agent."""
    s = _seed(simulation_id, agent_id, "memory")
    name = _agent_name(agent_id, s)
    persona = _pick(_PERSONA_TYPES, s)
    facts = _generate_facts(simulation_id, agent_id)
    interactions = []
    for r in range(1, total_rounds + 1):
        topic = _pick(_TOPICS, s, r)
        interactions.append({
            "round": r,
            "type": _pick(["post", "comment", "reaction", "share"], s, r),
            "topic": topic,
            "content_summary": f"{name} discussed {topic} in round {r}",
            "sentiment": round(-0.3 + ((s + r * 11) % 60) / 50, 2),
        })
    return {
        "agent_id": agent_id,
        "agent_name": name,
        "persona_type": persona,
        "total_facts": len(facts),
        "total_interactions": len(interactions),
        "facts": facts,
        "interactions": interactions,
        "metadata": {
            "simulation_id": simulation_id,
            "memory_source": "mock",
            "last_updated": datetime.utcnow().isoformat(),
        },
    }


def _generate_timeline(simulation_id: str, agent_id: str, total_rounds: int = 20):
    """Generate memory evolution over rounds."""
    s = _seed(simulation_id, agent_id, "timeline")
    name = _agent_name(agent_id, s)
    timeline = []
    cumulative_facts = 0
    for r in range(1, total_rounds + 1):
        new_facts = (s + r * 7) % 4
        cumulative_facts += new_facts
        topic = _pick(_TOPICS, s, r)
        timeline.append({
            "round": r,
            "new_facts": new_facts,
            "cumulative_facts": cumulative_facts,
            "dominant_topic": topic,
            "sentiment_shift": round(-0.2 + ((s + r * 13) % 40) / 100, 2),
            "knowledge_growth_rate": round(new_facts / max(cumulative_facts, 1), 3),
        })
    return {
        "agent_id": agent_id,
        "agent_name": name,
        "total_rounds": total_rounds,
        "final_fact_count": cumulative_facts,
        "timeline": timeline,
    }


def _generate_diff(simulation_id: str, agent_id: str, round_num: int):
    """Generate memory diff at a specific round."""
    s = _seed(simulation_id, agent_id, f"diff_{round_num}")
    name = _agent_name(agent_id, s)
    topic = _pick(_TOPICS, s, round_num)

    added = []
    updated = []
    removed = []

    num_added = (s + round_num * 5) % 4
    num_updated = (s + round_num * 3) % 3
    num_removed = (s + round_num * 2) % 2

    for i in range(num_added):
        t = _pick(_TOPICS, s, round_num + i + 10)
        added.append({
            "id": f"fact_new_{round_num}_{i}",
            "text": f"{name} learned about {t} during round {round_num}",
            "topic": t,
            "confidence": round(0.6 + ((s + i) % 35) / 100, 2),
        })

    for i in range(num_updated):
        t = _pick(_TOPICS, s, round_num + i + 20)
        added_conf = round(0.5 + ((s + i + 5) % 30) / 100, 2)
        updated.append({
            "id": f"fact_upd_{round_num}_{i}",
            "text": f"{name}'s understanding of {t} evolved in round {round_num}",
            "topic": t,
            "previous_confidence": added_conf,
            "new_confidence": round(min(added_conf + 0.1, 0.99), 2),
        })

    for i in range(num_removed):
        t = _pick(_TOPICS, s, round_num + i + 30)
        removed.append({
            "id": f"fact_rem_{round_num}_{i}",
            "text": f"{name} contradicted earlier belief about {t}",
            "topic": t,
            "reason": "contradicted_by_new_evidence",
        })

    return {
        "agent_id": agent_id,
        "agent_name": name,
        "round": round_num,
        "summary": {
            "facts_added": len(added),
            "facts_updated": len(updated),
            "facts_removed": len(removed),
            "net_change": len(added) - len(removed),
        },
        "added": added,
        "updated": updated,
        "removed": removed,
    }


# ---------------------------------------------------------------------------
# Zep integration helpers (try Zep first, fall back to mock)
# ---------------------------------------------------------------------------

def _try_zep_memory(graph_id: str, agent_id: str):
    """Attempt to read memory from Zep. Returns None if unavailable."""
    if not Config.ZEP_API_KEY:
        return None
    try:
        from zep_cloud.client import Zep
        client = Zep(api_key=Config.ZEP_API_KEY)
        # Query edges related to this agent in the graph
        result = client.graph.search(
            graph_id=graph_id,
            query=f"agent {agent_id}",
            limit=50,
        )
        if result and hasattr(result, 'edges') and result.edges:
            facts = []
            for edge in result.edges:
                facts.append({
                    "id": getattr(edge, 'uuid', ''),
                    "text": getattr(edge, 'fact', ''),
                    "topic": "zep_extracted",
                    "confidence": 0.85,
                    "created_at": getattr(edge, 'created_at', datetime.utcnow().isoformat()),
                })
            return facts
    except Exception as e:
        logger.warning(f"Zep memory read failed, using fallback: {e}")
    return None


def _try_zep_search(graph_id: str, query: str, limit: int = 10):
    """Attempt semantic search via Zep. Returns None if unavailable."""
    if not Config.ZEP_API_KEY:
        return None
    try:
        from zep_cloud.client import Zep
        client = Zep(api_key=Config.ZEP_API_KEY)
        result = client.graph.search(
            graph_id=graph_id,
            query=query,
            limit=limit,
        )
        if result and hasattr(result, 'edges') and result.edges:
            hits = []
            for edge in result.edges:
                hits.append({
                    "text": getattr(edge, 'fact', ''),
                    "score": 0.8,
                    "source": "zep_semantic",
                })
            return hits
    except Exception as e:
        logger.warning(f"Zep search failed, using fallback: {e}")
    return None


# ---------------------------------------------------------------------------
# Simulation-level agent memory endpoints (attached to simulation_bp)
# ---------------------------------------------------------------------------

@simulation_bp.route('/<simulation_id>/agents/<agent_id>/memory', methods=['GET'])
def get_agent_memory(simulation_id: str, agent_id: str):
    """Full memory dump for an agent.

    Tries Zep first for live graph data, falls back to deterministic
    mock data when Zep is unavailable.
    """
    try:
        # Attempt Zep integration
        zep_facts = _try_zep_memory(simulation_id, agent_id)
        if zep_facts is not None:
            s = _seed(simulation_id, agent_id, "memory")
            name = _agent_name(agent_id, s)
            return jsonify({
                "success": True,
                "data": {
                    "agent_id": agent_id,
                    "agent_name": name,
                    "persona_type": _pick(_PERSONA_TYPES, s),
                    "total_facts": len(zep_facts),
                    "facts": zep_facts,
                    "metadata": {
                        "simulation_id": simulation_id,
                        "memory_source": "zep",
                        "last_updated": datetime.utcnow().isoformat(),
                    },
                },
            })

        # Fallback to mock data
        memory = _generate_memory_entries(simulation_id, agent_id)
        return jsonify({
            "success": True,
            "data": memory,
        })

    except Exception as e:
        logger.error(f"Failed to get agent memory: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<agent_id>/memory/search', methods=['GET'])
def search_agent_memory(simulation_id: str, agent_id: str):
    """Semantic memory search for an agent.

    Query params:
        q: search query (required)
        limit: max results (default 10)
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                "success": False,
                "error": "Query parameter 'q' is required",
            }), 400

        limit = request.args.get('limit', 10, type=int)

        # Attempt Zep semantic search
        zep_results = _try_zep_search(simulation_id, query, limit=limit)
        if zep_results is not None:
            return jsonify({
                "success": True,
                "data": {
                    "agent_id": agent_id,
                    "query": query,
                    "source": "zep",
                    "count": len(zep_results),
                    "results": zep_results,
                },
            })

        # Fallback: keyword match against mock facts
        facts = _generate_facts(simulation_id, agent_id, count=20)
        query_lower = query.lower()
        matches = [
            {"text": f["text"], "score": f["confidence"], "source": "keyword_match"}
            for f in facts
            if query_lower in f["text"].lower() or query_lower in f["topic"].lower()
        ]
        # If no keyword match, return top facts by confidence as "fuzzy" results
        if not matches:
            matches = [
                {"text": f["text"], "score": f["confidence"] * 0.5, "source": "fuzzy_fallback"}
                for f in sorted(facts, key=lambda x: x["confidence"], reverse=True)
            ]
        matches = matches[:limit]

        return jsonify({
            "success": True,
            "data": {
                "agent_id": agent_id,
                "query": query,
                "source": "mock",
                "count": len(matches),
                "results": matches,
            },
        })

    except Exception as e:
        logger.error(f"Agent memory search failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<agent_id>/memory/facts', methods=['GET'])
def get_agent_memory_facts(simulation_id: str, agent_id: str):
    """Extracted facts with confidence scores.

    Query params:
        min_confidence: filter by minimum confidence (default 0.0)
        topic: filter by topic keyword
        limit: max results (default 50)
    """
    try:
        min_confidence = request.args.get('min_confidence', 0.0, type=float)
        topic_filter = request.args.get('topic', '').strip().lower()
        limit = request.args.get('limit', 50, type=int)

        # Attempt Zep
        zep_facts = _try_zep_memory(simulation_id, agent_id)
        if zep_facts is not None:
            filtered = [f for f in zep_facts if f.get("confidence", 0) >= min_confidence]
            if topic_filter:
                filtered = [f for f in filtered if topic_filter in f.get("topic", "").lower()]
            return jsonify({
                "success": True,
                "data": {
                    "agent_id": agent_id,
                    "source": "zep",
                    "count": len(filtered[:limit]),
                    "facts": filtered[:limit],
                },
            })

        # Fallback to mock
        facts = _generate_facts(simulation_id, agent_id, count=30)
        filtered = [f for f in facts if f["confidence"] >= min_confidence]
        if topic_filter:
            filtered = [f for f in filtered if topic_filter in f["topic"].lower()]
        filtered = filtered[:limit]

        return jsonify({
            "success": True,
            "data": {
                "agent_id": agent_id,
                "source": "mock",
                "count": len(filtered),
                "facts": filtered,
            },
        })

    except Exception as e:
        logger.error(f"Failed to get agent facts: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<agent_id>/memory/timeline', methods=['GET'])
def get_agent_memory_timeline(simulation_id: str, agent_id: str):
    """Temporal memory evolution across simulation rounds.

    Query params:
        rounds: total rounds to show (default 20)
    """
    try:
        total_rounds = request.args.get('rounds', 20, type=int)
        total_rounds = min(max(total_rounds, 1), 200)

        timeline = _generate_timeline(simulation_id, agent_id, total_rounds)

        return jsonify({
            "success": True,
            "data": timeline,
        })

    except Exception as e:
        logger.error(f"Failed to get memory timeline: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<agent_id>/memory/diff', methods=['GET'])
def get_agent_memory_diff(simulation_id: str, agent_id: str):
    """Memory diff at a specific round — what changed.

    Query params:
        round: round number (required)
    """
    try:
        round_num = request.args.get('round', type=int)
        if round_num is None:
            return jsonify({
                "success": False,
                "error": "Query parameter 'round' is required",
            }), 400

        if round_num < 1:
            return jsonify({
                "success": False,
                "error": "Round must be >= 1",
            }), 400

        diff = _generate_diff(simulation_id, agent_id, round_num)

        return jsonify({
            "success": True,
            "data": diff,
        })

    except Exception as e:
        logger.error(f"Failed to get memory diff: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<agent_id>/memory/transfer', methods=['POST'])
def transfer_agent_memory(simulation_id: str, agent_id: str):
    """Import memories from another simulation into this agent.

    JSON body:
        source_simulation_id: str (required)
        source_agent_id: str (optional, defaults to same agent_id)
        fact_ids: list[str] (optional, import specific facts only)
    """
    try:
        data = request.get_json() or {}
        source_sim = data.get('source_simulation_id')
        if not source_sim:
            return jsonify({
                "success": False,
                "error": "source_simulation_id is required",
            }), 400

        source_agent = data.get('source_agent_id', agent_id)
        fact_ids = data.get('fact_ids')

        # Get source facts (mock or Zep)
        source_facts = _generate_facts(source_sim, source_agent, count=20)
        if fact_ids:
            source_facts = [f for f in source_facts if f["id"] in fact_ids]

        transferred = []
        for fact in source_facts:
            transferred.append({
                "original_id": fact["id"],
                "new_id": f"imported_{fact['id']}",
                "text": fact["text"],
                "topic": fact["topic"],
                "original_confidence": fact["confidence"],
                "transferred_confidence": round(fact["confidence"] * 0.85, 2),
                "source_simulation": source_sim,
                "source_agent": source_agent,
            })

        return jsonify({
            "success": True,
            "data": {
                "agent_id": agent_id,
                "simulation_id": simulation_id,
                "source_simulation_id": source_sim,
                "source_agent_id": source_agent,
                "transferred_count": len(transferred),
                "transferred_facts": transferred,
                "transfer_timestamp": datetime.utcnow().isoformat(),
            },
        })

    except Exception as e:
        logger.error(f"Memory transfer failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ---------------------------------------------------------------------------
# Graph-level memory search endpoints (memory_bp Blueprint)
# ---------------------------------------------------------------------------

memory_bp = Blueprint('memory', __name__)


@memory_bp.route('/api/memory/<graph_id>/search', methods=['POST'])
def search_memories(graph_id: str):
    """
    Search agent memories in the knowledge graph.

    POST body:
        query: str - search text (optional, empty returns all)
        agent_name: str - filter by agent (optional)
        memory_type: str - filter by type: facts|beliefs|decisions (optional)
        sort_by: str - 'relevance' or 'chronological' (default: relevance)
        limit: int - max results (default: 50)
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get('query', '')
        agent_name = data.get('agent_name') or None
        memory_type = data.get('memory_type') or None
        sort_by = data.get('sort_by', 'relevance')
        limit = min(int(data.get('limit', 50)), 200)

        svc = MemorySearchService(graph_id)
        result = svc.search(
            query=query,
            agent_name=agent_name,
            memory_type=memory_type,
            sort_by=sort_by,
            limit=limit,
        )

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@memory_bp.route('/api/memory/<graph_id>/agents', methods=['GET'])
def list_agents(graph_id: str):
    """List agent names available in the knowledge graph."""
    try:
        svc = MemorySearchService(graph_id)
        agents = svc.get_agents()
        return jsonify({'success': True, 'data': agents})

    except Exception as e:
        logger.error(f"List agents failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500


@memory_bp.route('/api/memory/<graph_id>/topics', methods=['GET'])
def get_topics(graph_id: str):
    """
    Get memory topics for word cloud visualization.

    Query params:
        agent_name: str - filter by agent (optional)
        top_n: int - number of topics (default: 30)
    """
    try:
        agent_name = request.args.get('agent_name') or None
        top_n = min(int(request.args.get('top_n', 30)), 100)

        svc = MemorySearchService(graph_id)
        topics = svc.get_topics(agent_name=agent_name, top_n=top_n)

        return jsonify({'success': True, 'data': topics})

    except Exception as e:
        logger.error(f"Get topics failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }), 500
