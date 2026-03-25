"""
Custom Agent CRUD API
Manage custom simulation agent configurations.
"""

import traceback

from flask import Blueprint, jsonify, request

from ..models.custom_agent import (
    CustomAgentConfig,
    CustomAgentManager,
    COMMUNICATION_STYLES,
)
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.agents')

agents_bp = Blueprint('agents', __name__, url_prefix='/api/agents')


# ── Pre-built GTM agent templates ──────────────────────────────────

AGENT_TEMPLATES = [
    {
        "id": "tpl_vp_sales",
        "name": "VP of Sales",
        "role": "VP of Sales",
        "department": "Sales",
        "personality": {"analytical": 65, "creative": 40, "assertive": 85, "empathetic": 45, "risk_tolerant": 70},
        "expertise_areas": ["Enterprise Sales", "Pipeline Management", "Revenue Operations"],
        "communication_style": "formal",
        "biases": ["Optimism bias"],
        "goals": ["Hit quarterly revenue target", "Expand enterprise pipeline"],
        "backstory": "15-year sales veteran who built a $50M ARR segment from scratch.",
        "avatar_color": "#2068FF",
    },
    {
        "id": "tpl_marketing_dir",
        "name": "Marketing Director",
        "role": "Director of Marketing",
        "department": "Marketing",
        "personality": {"analytical": 55, "creative": 80, "assertive": 60, "empathetic": 65, "risk_tolerant": 60},
        "expertise_areas": ["Growth Marketing", "Marketing Strategy", "Data Analytics"],
        "communication_style": "storytelling",
        "biases": ["Confirmation bias"],
        "goals": ["Increase MQL volume 30%", "Improve brand awareness"],
        "backstory": "Former agency creative who transitioned to B2B SaaS demand gen.",
        "avatar_color": "#ff5600",
    },
    {
        "id": "tpl_cs_manager",
        "name": "Customer Success Manager",
        "role": "Senior CSM",
        "department": "Customer Success",
        "personality": {"analytical": 50, "creative": 45, "assertive": 40, "empathetic": 90, "risk_tolerant": 30},
        "expertise_areas": ["Customer Retention", "Product Strategy", "Competitive Analysis"],
        "communication_style": "diplomatic",
        "biases": ["Status quo bias"],
        "goals": ["Reduce churn below 5%", "Increase NPS to 60+"],
        "backstory": "Joined from the customer side; deeply understands user pain points.",
        "avatar_color": "#10B981",
    },
    {
        "id": "tpl_product_manager",
        "name": "Product Manager",
        "role": "Senior Product Manager",
        "department": "Product",
        "personality": {"analytical": 80, "creative": 70, "assertive": 55, "empathetic": 60, "risk_tolerant": 55},
        "expertise_areas": ["Product Strategy", "Data Analytics", "Competitive Analysis"],
        "communication_style": "data_driven",
        "biases": ["Anchoring"],
        "goals": ["Ship v2 roadmap on time", "Increase feature adoption 25%"],
        "backstory": "Ex-engineer who moved to product to bridge the tech-business gap.",
        "avatar_color": "#8B5CF6",
    },
    {
        "id": "tpl_rev_ops",
        "name": "Revenue Operations Analyst",
        "role": "RevOps Analyst",
        "department": "Finance",
        "personality": {"analytical": 95, "creative": 30, "assertive": 45, "empathetic": 35, "risk_tolerant": 25},
        "expertise_areas": ["Revenue Operations", "Financial Planning", "Data Analytics"],
        "communication_style": "data_driven",
        "biases": ["Recency bias"],
        "goals": ["Unify GTM data model", "Reduce forecast error to <10%"],
        "backstory": "Data-first operator obsessed with pipeline hygiene and forecasting accuracy.",
        "avatar_color": "#F59E0B",
    },
    {
        "id": "tpl_sdr_lead",
        "name": "SDR Team Lead",
        "role": "SDR Team Lead",
        "department": "Sales",
        "personality": {"analytical": 45, "creative": 60, "assertive": 75, "empathetic": 55, "risk_tolerant": 65},
        "expertise_areas": ["Enterprise Sales", "Growth Marketing", "Pipeline Management"],
        "communication_style": "casual",
        "biases": ["Optimism bias"],
        "goals": ["Book 200 meetings/quarter", "Ramp new reps in 30 days"],
        "backstory": "Top-performing SDR promoted to lead; energetic and competitive.",
        "avatar_color": "#EC4899",
    },
]


# ── Endpoints ──────────────────────────────────────────────────────

@agents_bp.route('', methods=['GET'])
def list_agents():
    """List all saved custom agents."""
    try:
        agents = CustomAgentManager.list_agents()
        return jsonify({
            "success": True,
            "data": [a.to_dict() for a in agents],
        })
    except Exception as e:
        logger.error(f"List agents failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('', methods=['POST'])
def create_agent():
    """Create a new custom agent from config."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "JSON body required"}), 400

        agent = CustomAgentConfig.from_dict(data)
        errors = agent.validate()
        if errors:
            return jsonify({"success": False, "errors": errors}), 422

        created = CustomAgentManager.create(data)
        logger.info(f"Created agent {created.id}: {created.name}")
        return jsonify({"success": True, "data": created.to_dict()}), 201
    except Exception as e:
        logger.error(f"Create agent failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a specific agent's details."""
    agent = CustomAgentManager.get(agent_id)
    if not agent:
        return jsonify({"success": False, "error": f"Agent {agent_id} not found"}), 404
    return jsonify({"success": True, "data": agent.to_dict()})


@agents_bp.route('/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update an existing agent."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "JSON body required"}), 400

        # Validate the merged result
        existing = CustomAgentManager.get(agent_id)
        if not existing:
            return jsonify({"success": False, "error": f"Agent {agent_id} not found"}), 404

        merged = existing.to_dict()
        merged.update(data)
        check = CustomAgentConfig.from_dict(merged)
        errors = check.validate()
        if errors:
            return jsonify({"success": False, "errors": errors}), 422

        updated = CustomAgentManager.update(agent_id, data)
        logger.info(f"Updated agent {agent_id}")
        return jsonify({"success": True, "data": updated.to_dict()})
    except Exception as e:
        logger.error(f"Update agent {agent_id} failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete a custom agent."""
    if CustomAgentManager.delete(agent_id):
        logger.info(f"Deleted agent {agent_id}")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": f"Agent {agent_id} not found"}), 404


@agents_bp.route('/<agent_id>/clone', methods=['POST'])
def clone_agent(agent_id):
    """Clone an existing agent."""
    try:
        cloned = CustomAgentManager.clone(agent_id)
        if not cloned:
            return jsonify({"success": False, "error": f"Agent {agent_id} not found"}), 404
        logger.info(f"Cloned agent {agent_id} -> {cloned.id}")
        return jsonify({"success": True, "data": cloned.to_dict()}), 201
    except Exception as e:
        logger.error(f"Clone agent {agent_id} failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route('/templates', methods=['GET'])
def list_templates():
    """Return pre-built GTM agent templates."""
    return jsonify({"success": True, "data": AGENT_TEMPLATES})


@agents_bp.route('/generate', methods=['POST'])
def generate_agent():
    """AI-generate an agent config from a text description. Falls back to template matching when no LLM key is configured."""
    try:
        data = request.get_json()
        if not data or not data.get('description'):
            return jsonify({"success": False, "error": "description is required"}), 400

        description = data['description'].strip()

        # Try LLM generation first
        if Config.LLM_API_KEY:
            try:
                return _generate_with_llm(description)
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to template: {e}")

        # Fallback: pick best-matching template
        return _generate_from_template(description)

    except Exception as e:
        logger.error(f"Generate agent failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ── Internal helpers ───────────────────────────────────────────────

def _generate_with_llm(description: str):
    """Use the configured LLM to generate an agent config from a description."""
    from ..utils.llm_client import LLMClient

    client = LLMClient()
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert at creating simulation agent personas for GTM (Go-To-Market) operations. "
                "Given a description, generate a JSON agent configuration with these exact fields:\n"
                '{"name": "string", "role": "string", "department": "string", '
                '"personality": {"analytical": 0-100, "creative": 0-100, "assertive": 0-100, "empathetic": 0-100, "risk_tolerant": 0-100}, '
                '"expertise_areas": ["string"], "communication_style": "formal|casual|data_driven|storytelling|diplomatic", '
                '"biases": ["string"], "goals": ["string"], "backstory": "string", "avatar_color": "#hex"}\n'
                "Department should be one of: Sales, Marketing, Customer Success, Product, Finance, Engineering, Executive.\n"
                "Return ONLY the JSON object, no extra text."
            ),
        },
        {"role": "user", "content": description},
    ]
    result = client.chat_json(messages, temperature=0.7)
    return jsonify({"success": True, "data": result, "source": "llm"})


def _generate_from_template(description: str):
    """Match the description to the closest template using keyword overlap."""
    desc_lower = description.lower()

    best_score = -1
    best_template = AGENT_TEMPLATES[0]

    for tpl in AGENT_TEMPLATES:
        score = 0
        keywords = (
            [tpl['name'].lower(), tpl['role'].lower(), tpl['department'].lower()]
            + [e.lower() for e in tpl['expertise_areas']]
        )
        for kw in keywords:
            for word in kw.split():
                if word in desc_lower:
                    score += 1
        if score > best_score:
            best_score = score
            best_template = tpl

    # Return a copy without the template id so frontend treats it as new
    result = {k: v for k, v in best_template.items() if k != 'id'}
    return jsonify({"success": True, "data": result, "source": "template"})
