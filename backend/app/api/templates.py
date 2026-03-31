"""
Scenario Template API
CRUD operations for GTM simulation scenario templates,
plus template-based simulation creation and rating.

Templates are stored as JSON files in backend/data/templates/.
"""

import json
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.templates')

templates_bp = Blueprint('templates', __name__, url_prefix='/api/v1/templates')

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '../../data/templates')

VALID_CATEGORIES = [
    'GTM Strategy',
    'Pipeline Management',
    'Competitive Response',
    'Revenue Operations',
    'Customer Success',
    'Product Launch',
    'Team Dynamics',
]

VALID_DIFFICULTIES = ['easy', 'medium', 'hard']


def _ensure_dir():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def _template_path(template_id):
    return os.path.join(TEMPLATES_DIR, f'{template_id}.json')


def _load(template_id):
    path = _template_path(template_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _save(template_id, data):
    _ensure_dir()
    with open(_template_path(template_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_all():
    _ensure_dir()
    templates = []
    for filename in sorted(os.listdir(TEMPLATES_DIR)):
        if not filename.endswith('.json'):
            continue
        path = os.path.join(TEMPLATES_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                templates.append(json.load(f))
        except json.JSONDecodeError:
            logger.warning(f'Invalid JSON in {filename}, skipping')
    return templates


def _summary(template):
    return {
        'id': template.get('id'),
        'name': template.get('name', ''),
        'description': template.get('description', ''),
        'category': template.get('category', ''),
        'difficulty': template.get('difficulty', 'medium'),
        'recommended_agents': template.get('recommended_agents', 5),
        'recommended_rounds': template.get('recommended_rounds', 8),
        'tags': template.get('tags', []),
        'author': template.get('author', ''),
        'created_at': template.get('created_at', ''),
        'usage_count': template.get('usage_count', 0),
        'avg_rating': template.get('avg_rating', 0),
    }


def _sanitize_id(name):
    slug = name.lower().replace(' ', '_').replace('-', '_')
    return ''.join(c for c in slug if c.isalnum() or c == '_')


# ──────────────────────────── List & Categories ────────────────────────────


@templates_bp.route('', methods=['GET'])
def list_templates():
    """
    List scenario templates with optional filtering.

    Query params:
        category — filter by category name
        tag      — filter by tag
        search   — case-insensitive search in name and description
    """
    templates = _load_all()

    category = request.args.get('category')
    if category:
        templates = [t for t in templates if t.get('category') == category]

    tag = request.args.get('tag')
    if tag:
        templates = [t for t in templates if tag in t.get('tags', [])]

    search = request.args.get('search', '').strip().lower()
    if search:
        templates = [
            t for t in templates
            if search in t.get('name', '').lower()
            or search in t.get('description', '').lower()
        ]

    return jsonify({
        'templates': [_summary(t) for t in templates],
        'total': len(templates),
    })


@templates_bp.route('/categories', methods=['GET'])
def list_categories():
    """List categories with template counts."""
    templates = _load_all()
    counts = {}
    for t in templates:
        cat = t.get('category', 'Uncategorized')
        counts[cat] = counts.get(cat, 0) + 1

    categories = [
        {'name': name, 'count': counts.get(name, 0)}
        for name in VALID_CATEGORIES
    ]
    for cat, count in counts.items():
        if cat not in VALID_CATEGORIES:
            categories.append({'name': cat, 'count': count})

    return jsonify({'categories': categories})


# ──────────────────────────── CRUD ─────────────────────────────────────────


@templates_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get full template details."""
    template = _load(template_id)
    if not template:
        return jsonify({'error': f'Template {template_id} not found'}), 404
    return jsonify(template)


@templates_bp.route('', methods=['POST'])
def create_template():
    """
    Create a custom scenario template.

    Required: name
    Optional: description, category, difficulty, recommended_agents,
              recommended_rounds, agent_roles, environment_config,
              initial_state, objectives, tags, author
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    template_id = data.get('id') or _sanitize_id(name)
    if _load(template_id):
        return jsonify({'error': f'Template {template_id} already exists'}), 409

    difficulty = data.get('difficulty', 'medium')
    if difficulty not in VALID_DIFFICULTIES:
        return jsonify({'error': f'difficulty must be one of: {VALID_DIFFICULTIES}'}), 400

    now = datetime.now(timezone.utc).isoformat()

    template = {
        'id': template_id,
        'name': name,
        'description': data.get('description', ''),
        'category': data.get('category', 'GTM Strategy'),
        'difficulty': difficulty,
        'recommended_agents': data.get('recommended_agents', 5),
        'recommended_rounds': data.get('recommended_rounds', 8),
        'agent_roles': data.get('agent_roles', []),
        'environment_config': data.get('environment_config', {}),
        'initial_state': data.get('initial_state', {}),
        'objectives': data.get('objectives', []),
        'tags': data.get('tags', []),
        'author': data.get('author', 'custom'),
        'created_at': now,
        'usage_count': 0,
        'avg_rating': 0,
        'ratings': [],
    }

    _save(template_id, template)
    logger.info(f'Created template: {template_id}')
    return jsonify(template), 201


@templates_bp.route('/<template_id>', methods=['PUT'])
def update_template(template_id):
    """Update an existing template. Only provided fields are changed."""
    template = _load(template_id)
    if not template:
        return jsonify({'error': f'Template {template_id} not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'difficulty' in data and data['difficulty'] not in VALID_DIFFICULTIES:
        return jsonify({'error': f'difficulty must be one of: {VALID_DIFFICULTIES}'}), 400

    updatable = [
        'name', 'description', 'category', 'difficulty',
        'recommended_agents', 'recommended_rounds', 'agent_roles',
        'environment_config', 'initial_state', 'objectives', 'tags', 'author',
    ]
    for field in updatable:
        if field in data:
            template[field] = data[field]

    template['updated_at'] = datetime.now(timezone.utc).isoformat()
    _save(template_id, template)
    logger.info(f'Updated template: {template_id}')
    return jsonify(template)


@templates_bp.route('/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template."""
    path = _template_path(template_id)
    if not os.path.exists(path):
        return jsonify({'error': f'Template {template_id} not found'}), 404

    os.remove(path)
    logger.info(f'Deleted template: {template_id}')
    return jsonify({'success': True, 'id': template_id})


# ──────────────────────────── Use & Rate ───────────────────────────────────


@templates_bp.route('/<template_id>/use', methods=['POST'])
def use_template(template_id):
    """
    Create a simulation from a template.

    Increments usage_count and returns the template's simulation config
    that the frontend can pass to the simulation start endpoint.

    Optional body fields override template defaults:
        agent_roles, recommended_agents, recommended_rounds,
        environment_config
    """
    template = _load(template_id)
    if not template:
        return jsonify({'error': f'Template {template_id} not found'}), 404

    template['usage_count'] = template.get('usage_count', 0) + 1
    _save(template_id, template)

    overrides = request.get_json() or {}

    env_config = {**template.get('environment_config', {})}
    if overrides.get('environment_config'):
        env_config.update(overrides['environment_config'])

    sim_config = {
        'template_id': template_id,
        'name': template.get('name', ''),
        'agent_roles': overrides.get('agent_roles', template.get('agent_roles', [])),
        'recommended_agents': overrides.get('recommended_agents', template.get('recommended_agents', 5)),
        'recommended_rounds': overrides.get('recommended_rounds', template.get('recommended_rounds', 8)),
        'environment_config': env_config,
        'initial_state': template.get('initial_state', {}),
        'objectives': template.get('objectives', []),
    }

    logger.info(f'Template {template_id} used (count: {template["usage_count"]})')

    return jsonify({
        'success': True,
        'simulation_config': sim_config,
        'usage_count': template['usage_count'],
    })


@templates_bp.route('/<template_id>/rate', methods=['POST'])
def rate_template(template_id):
    """
    Rate a template from 1 to 5.

    Body: { "rating": 4 }
    """
    template = _load(template_id)
    if not template:
        return jsonify({'error': f'Template {template_id} not found'}), 404

    data = request.get_json()
    if not data or 'rating' not in data:
        return jsonify({'error': 'rating is required'}), 400

    rating = data['rating']
    if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
        return jsonify({'error': 'rating must be between 1 and 5'}), 400

    if 'ratings' not in template:
        template['ratings'] = []

    template['ratings'].append({
        'rating': rating,
        'rated_at': datetime.now(timezone.utc).isoformat(),
    })

    all_ratings = [r['rating'] for r in template['ratings']]
    template['avg_rating'] = round(sum(all_ratings) / len(all_ratings), 2)

    _save(template_id, template)
    logger.info(f'Template {template_id} rated {rating} (avg: {template["avg_rating"]})')

    return jsonify({
        'success': True,
        'avg_rating': template['avg_rating'],
        'total_ratings': len(template['ratings']),
    })
