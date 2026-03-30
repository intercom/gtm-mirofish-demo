"""
Interactive Tutorial API
Serves tutorial catalog, step content, and tracks user progress.
All endpoints work in demo mode without LLM keys.
"""

from flask import Blueprint, jsonify, request

tutorials_bp = Blueprint('tutorials', __name__, url_prefix='/api/v1/tutorials')

# Tutorial catalog — served from memory (no DB dependency)
TUTORIAL_CATALOG = [
    {
        'id': 'welcome',
        'title': 'Welcome to MiroFish',
        'description': 'Get oriented with the platform — navigation, key features, and your first simulation.',
        'category': 'getting-started',
        'difficulty': 'beginner',
        'estimatedMinutes': 3,
        'icon': 'compass',
        'steps': [
            {
                'id': 'nav-overview',
                'title': 'Navigation',
                'content': 'Use the navigation bar to move between the landing page, your simulations list, and settings.',
                'target': '[data-tutorial="nav"]',
                'position': 'bottom',
                'action': None,
            },
            {
                'id': 'scenarios-intro',
                'title': 'Scenario Templates',
                'content': 'Start from pre-built GTM scenarios like Pipeline Review, Competitive Response, or Product Launch.',
                'target': '[data-tutorial="scenarios"]',
                'position': 'bottom',
                'action': None,
            },
            {
                'id': 'simulations-intro',
                'title': 'Your Simulations',
                'content': 'View and manage all your GTM simulations. Each tracks its status, agents, and results.',
                'target': '[data-tutorial="simulations"]',
                'position': 'bottom',
                'action': None,
            },
            {
                'id': 'settings-intro',
                'title': 'Settings',
                'content': 'Configure your LLM provider (Claude, GPT-4, Gemini), API keys, and simulation defaults.',
                'target': '[data-tutorial="settings"]',
                'position': 'bottom',
                'action': None,
            },
        ],
    },
    {
        'id': 'first-simulation',
        'title': 'Run Your First Simulation',
        'description': 'Walk through the full simulation lifecycle — from picking a scenario to generating a report.',
        'category': 'getting-started',
        'difficulty': 'beginner',
        'estimatedMinutes': 5,
        'icon': 'play-circle',
        'steps': [
            {
                'id': 'pick-scenario',
                'title': 'Pick a Scenario',
                'content': 'Navigate to Scenarios and choose "Pipeline Review". This seeds a cross-functional GTM team.',
                'target': None,
                'position': 'center',
                'action': {'type': 'navigate', 'route': '/scenarios'},
            },
            {
                'id': 'review-agents',
                'title': 'Review Agent Personas',
                'content': 'Each agent has a role (Sales VP, CS Lead) and personality traits that influence how they interact.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'launch-sim',
                'title': 'Launch the Simulation',
                'content': 'Click "Start Simulation" to begin. OASIS agents will converse for multiple rounds, forming opinions.',
                'target': None,
                'position': 'center',
                'action': {'type': 'click', 'selector': '[data-tutorial="start-sim"]'},
            },
            {
                'id': 'observe-rounds',
                'title': 'Watch the Simulation',
                'content': 'Observe sentiment shifts and coalition formation in real-time as agents debate priorities.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'view-results',
                'title': 'Explore Results',
                'content': 'Check the sentiment timeline, influence network, and coalition graph in your workspace.',
                'target': None,
                'position': 'center',
                'action': None,
            },
        ],
    },
    {
        'id': 'knowledge-graph',
        'title': 'Understanding the Knowledge Graph',
        'description': 'Learn how seed text becomes structured entities and relationships that power simulations.',
        'category': 'concepts',
        'difficulty': 'intermediate',
        'estimatedMinutes': 4,
        'icon': 'share-2',
        'steps': [
            {
                'id': 'what-is-kg',
                'title': 'What is a Knowledge Graph?',
                'content': 'The knowledge graph extracts entities (people, companies, products) and relationships from your seed text using an LLM. Zep stores these as nodes and edges.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'seed-text',
                'title': 'Seed Text',
                'content': 'Seed text is the starting scenario description. It should describe market context, key players, competitive landscape, and customer dynamics.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'entity-extraction',
                'title': 'Entity Extraction',
                'content': 'The LLM identifies named entities and their attributes — roles, sentiments, domain expertise — to build agent personas.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'graph-viz',
                'title': 'Visualizing the Graph',
                'content': 'Navigate to the Knowledge Graph view to explore nodes (entities) and edges (relationships) with interactive D3 visualizations.',
                'target': None,
                'position': 'center',
                'action': {'type': 'navigate', 'route': '/knowledge-graph'},
            },
        ],
    },
    {
        'id': 'reading-results',
        'title': 'Reading Simulation Results',
        'description': 'Interpret sentiment timelines, influence networks, and coalition maps to extract strategic insights.',
        'category': 'concepts',
        'difficulty': 'intermediate',
        'estimatedMinutes': 6,
        'icon': 'bar-chart-2',
        'steps': [
            {
                'id': 'sentiment-timeline',
                'title': 'Sentiment Timeline',
                'content': 'Tracks how each agent\'s sentiment evolves over simulation rounds. Rising lines indicate growing support; falling lines signal resistance.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'influence-network',
                'title': 'Influence Network',
                'content': 'A directed graph showing how agents influence each other. Thicker edges mean stronger persuasion — key for identifying power brokers.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'coalition-map',
                'title': 'Coalition Detection',
                'content': 'Clusters of aligned agents reveal likely allies or blockers in a deal — surfacing political dynamics invisible in traditional pipeline tools.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'engagement-heatmap',
                'title': 'Engagement Heatmap',
                'content': 'A matrix showing agent activity intensity across rounds. Hot cells indicate activity bursts — useful for timing stakeholder outreach.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'competitive-mentions',
                'title': 'Competitive Mentions',
                'content': 'Tracks competitor name frequency and sentiment in agent conversations — surfaces which competitors are top-of-mind.',
                'target': None,
                'position': 'center',
                'action': None,
            },
        ],
    },
    {
        'id': 'advanced-scenarios',
        'title': 'Advanced Scenario Design',
        'description': 'Create custom scenarios with branching, what-if analysis, and persona customization.',
        'category': 'advanced',
        'difficulty': 'advanced',
        'estimatedMinutes': 8,
        'icon': 'git-branch',
        'steps': [
            {
                'id': 'custom-seed',
                'title': 'Custom Seed Text',
                'content': 'Write your own seed text describing a specific deal, market shift, or competitive scenario. The more detailed, the richer the simulation.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'persona-tuning',
                'title': 'Persona Tuning',
                'content': 'Adjust agent personality traits (openness, agreeableness, assertiveness) to model specific stakeholder archetypes.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'what-if',
                'title': 'What-If Analysis',
                'content': 'Run alternative branches by changing variables — swap a competitor, adjust sentiment, or introduce a new stakeholder mid-simulation.',
                'target': None,
                'position': 'center',
                'action': None,
            },
            {
                'id': 'branching',
                'title': 'Scenario Branching',
                'content': 'Create multiple branches from the same seed data with different parameters. Compare outcomes to A/B test GTM approaches.',
                'target': None,
                'position': 'center',
                'action': None,
            },
        ],
    },
]

# Category metadata
CATEGORIES = [
    {'id': 'getting-started', 'label': 'Getting Started', 'order': 0},
    {'id': 'concepts', 'label': 'Core Concepts', 'order': 1},
    {'id': 'advanced', 'label': 'Advanced', 'order': 2},
]


@tutorials_bp.route('/', methods=['GET'])
def list_tutorials():
    """List all available tutorials with metadata (no step content)."""
    category = request.args.get('category')
    catalog = []
    for t in TUTORIAL_CATALOG:
        entry = {
            'id': t['id'],
            'title': t['title'],
            'description': t['description'],
            'category': t['category'],
            'difficulty': t['difficulty'],
            'estimatedMinutes': t['estimatedMinutes'],
            'icon': t['icon'],
            'stepCount': len(t['steps']),
        }
        if category and t['category'] != category:
            continue
        catalog.append(entry)
    return jsonify({'success': True, 'data': catalog, 'categories': CATEGORIES})


@tutorials_bp.route('/<tutorial_id>', methods=['GET'])
def get_tutorial(tutorial_id):
    """Get full tutorial content including all steps."""
    for t in TUTORIAL_CATALOG:
        if t['id'] == tutorial_id:
            return jsonify({'success': True, 'data': t})
    return jsonify({'success': False, 'error': f'Tutorial "{tutorial_id}" not found'}), 404


@tutorials_bp.route('/<tutorial_id>/steps/<step_id>/validate', methods=['POST'])
def validate_step(tutorial_id, step_id):
    """Validate that a user completed an interactive step action.

    In demo mode, always returns success. With an LLM, could verify
    actual state (e.g. did the user really navigate to the right page).
    """
    tutorial = next((t for t in TUTORIAL_CATALOG if t['id'] == tutorial_id), None)
    if not tutorial:
        return jsonify({'success': False, 'error': 'Tutorial not found'}), 404

    step = next((s for s in tutorial['steps'] if s['id'] == step_id), None)
    if not step:
        return jsonify({'success': False, 'error': 'Step not found'}), 404

    return jsonify({
        'success': True,
        'data': {
            'valid': True,
            'stepId': step_id,
            'message': 'Step completed successfully.',
        },
    })
