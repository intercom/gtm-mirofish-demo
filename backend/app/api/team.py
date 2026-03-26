"""
Team Composition API
Serves persona pool data for the team composer and provides
auto-generate recommendations based on scenario requirements.
"""

import json
import os

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.team')

team_bp = Blueprint('team', __name__, url_prefix='/api/gtm/team')

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')

ROLE_CATEGORY_MAP = {
    'VP of Support': 'cs',
    'CX Director': 'cs',
    'CX Leader': 'cs',
    'Support Manager': 'cs',
    'IT Leader': 'product',
    'Technical Evaluator': 'product',
    'Product Manager': 'product',
    'End User': 'product',
    'Head of Operations': 'operations',
    'VP Operations': 'operations',
    'CFO': 'finance',
    'Decision Maker': 'executive',
    'Champion': 'sales',
    'Sales Director': 'sales',
    'Marketing VP': 'marketing',
    'Growth Lead': 'marketing',
    'Blocker': 'risk',
}

PERSONALITY_MAP = {
    'strategic, data-driven, time-constrained': 'analytical',
    'detail-oriented, quality-focused, collaborative': 'collaborative',
    'technical, risk-aware, process-oriented': 'cautious',
    'pragmatic, metrics-driven, efficiency-focused': 'pragmatic',
}

CATEGORIES = ['sales', 'marketing', 'cs', 'product', 'finance']

# Extended persona pool beyond what's in seed data
EXTENDED_PERSONAS = [
    {
        'role': 'Sales Director',
        'seniority': 'director',
        'category': 'sales',
        'personality': 'assertive',
        'priorities': ['pipeline growth', 'deal velocity', 'competitive positioning'],
        'concerns': ['quota impact during transition', 'CRM integration'],
        'decision_authority': 'influencer',
        'communication_style': 'assertive, results-oriented, competitive',
    },
    {
        'role': 'Marketing VP',
        'seniority': 'executive',
        'category': 'marketing',
        'personality': 'creative',
        'priorities': ['demand generation', 'brand positioning', 'campaign ROI'],
        'concerns': ['message consistency', 'channel attribution'],
        'decision_authority': 'influencer',
        'communication_style': 'creative, brand-conscious, data-informed',
    },
    {
        'role': 'Growth Lead',
        'seniority': 'manager',
        'category': 'marketing',
        'personality': 'experimental',
        'priorities': ['user acquisition', 'activation rates', 'experimentation velocity'],
        'concerns': ['scalability', 'measurement accuracy'],
        'decision_authority': 'influencer',
        'communication_style': 'experimental, metrics-focused, fast-moving',
    },
    {
        'role': 'CFO',
        'seniority': 'executive',
        'category': 'finance',
        'personality': 'analytical',
        'priorities': ['cost control', 'ROI', 'budget forecasting'],
        'concerns': ['hidden costs', 'contract terms', 'long-term TCO'],
        'decision_authority': 'final_approver',
        'communication_style': 'numbers-driven, risk-aware, bottom-line focused',
    },
    {
        'role': 'Decision Maker',
        'seniority': 'executive',
        'category': 'executive',
        'personality': 'strategic',
        'priorities': ['strategic alignment', 'competitive advantage', 'organizational readiness'],
        'concerns': ['change management', 'stakeholder buy-in'],
        'decision_authority': 'final_approver',
        'communication_style': 'strategic, vision-oriented, decisive',
    },
    {
        'role': 'Champion',
        'seniority': 'manager',
        'category': 'sales',
        'personality': 'enthusiastic',
        'priorities': ['product adoption', 'internal advocacy', 'quick wins'],
        'concerns': ['losing credibility if product underperforms'],
        'decision_authority': 'influencer',
        'communication_style': 'enthusiastic, persuasive, relationship-driven',
    },
    {
        'role': 'End User',
        'seniority': 'individual',
        'category': 'product',
        'personality': 'practical',
        'priorities': ['ease of use', 'daily workflow efficiency', 'reliability'],
        'concerns': ['learning curve', 'workflow disruption'],
        'decision_authority': 'end_user',
        'communication_style': 'practical, feature-focused, experience-driven',
    },
    {
        'role': 'Blocker',
        'seniority': 'director',
        'category': 'risk',
        'personality': 'cautious',
        'priorities': ['risk mitigation', 'compliance', 'status quo stability'],
        'concerns': ['everything'],
        'decision_authority': 'technical_veto',
        'communication_style': 'skeptical, risk-focused, detail-oriented',
    },
]


def _load_seed_personas():
    """Load personas from seed data and enrich with category/personality."""
    filepath = os.path.join(SEED_DATA_DIR, 'persona_templates.json')
    personas = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for p in data.get('personas', []):
            role = p['role']
            persona = {
                **p,
                'category': ROLE_CATEGORY_MAP.get(role, 'other'),
                'personality': PERSONALITY_MAP.get(
                    p.get('communication_style', ''), 'balanced'
                ),
            }
            personas.append(persona)

    # Add extended personas that aren't already in seed data
    seed_roles = {p['role'] for p in personas}
    for ep in EXTENDED_PERSONAS:
        if ep['role'] not in seed_roles:
            personas.append(ep)

    # Assign stable IDs
    for i, p in enumerate(personas):
        p['id'] = f"persona-{p['role'].lower().replace(' ', '-')}"

    return personas


@team_bp.route('/personas', methods=['GET'])
def list_personas():
    """Return the full persona pool with enriched metadata."""
    personas = _load_seed_personas()
    categories = sorted({p['category'] for p in personas})
    personalities = sorted({p['personality'] for p in personas})
    return jsonify({
        'personas': personas,
        'categories': categories,
        'personalities': personalities,
    })


@team_bp.route('/auto-generate', methods=['POST'])
def auto_generate():
    """
    Recommend a team composition based on scenario requirements.

    Request (JSON):
        {
            "team_size": 5,
            "scenario_type": "competitive_displacement",
            "existing_roles": ["VP of Support"]
        }

    Returns a recommended list of persona roles.
    """
    data = request.get_json() or {}
    team_size = min(data.get('team_size', 5), 12)
    existing_roles = set(data.get('existing_roles', []))

    all_personas = _load_seed_personas()
    available = [p for p in all_personas if p['role'] not in existing_roles]

    # Greedy: ensure category coverage first, then fill by diversity
    selected = []
    covered_categories = set()
    covered_personalities = set()

    # Phase 1: one persona per core category
    for cat in CATEGORIES:
        if len(selected) >= team_size:
            break
        candidates = [p for p in available if p['category'] == cat and p['role'] not in {s['role'] for s in selected}]
        if candidates:
            # Prefer personality not yet covered
            pick = next(
                (c for c in candidates if c['personality'] not in covered_personalities),
                candidates[0],
            )
            selected.append(pick)
            covered_categories.add(cat)
            covered_personalities.add(pick['personality'])

    # Phase 2: fill remaining slots with max diversity
    remaining = [p for p in available if p['role'] not in {s['role'] for s in selected}]
    for p in remaining:
        if len(selected) >= team_size:
            break
        if p['personality'] not in covered_personalities:
            selected.append(p)
            covered_personalities.add(p['personality'])

    # Phase 3: fill any remaining with whatever's left
    remaining = [p for p in available if p['role'] not in {s['role'] for s in selected}]
    for p in remaining:
        if len(selected) >= team_size:
            break
        selected.append(p)

    return jsonify({
        'recommended': [p['role'] for p in selected],
        'personas': selected,
    })


@team_bp.route('/templates', methods=['GET'])
def list_templates():
    """List saved team templates (in-memory for demo)."""
    return jsonify({'templates': _templates})


@team_bp.route('/templates', methods=['POST'])
def save_template():
    """Save a team composition as a reusable template."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    roles = data.get('roles', [])
    if not name or not roles:
        return jsonify({'error': 'name and roles are required'}), 400

    template = {
        'id': f"tmpl-{len(_templates) + 1}",
        'name': name,
        'roles': roles,
    }
    _templates.append(template)
    return jsonify(template), 201


# In-memory template storage (demo mode)
_templates = []
