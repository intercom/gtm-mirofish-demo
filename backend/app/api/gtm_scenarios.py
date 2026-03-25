"""
GTM Scenario API
Serves pre-built GTM simulation scenario templates and seed data,
and provides a unified simulation endpoint that bridges the frontend
ScenarioBuilder with the backend ontology/graph pipeline.
"""

import hashlib
import json
import os
import re
import traceback
import threading

from flask import Blueprint, jsonify, request, make_response, Response

from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..services.scenario_templates import ScenarioTemplateService
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

logger = get_logger('mirofish.gtm')

gtm_bp = Blueprint('gtm', __name__, url_prefix='/api/gtm')

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_scenarios')
SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')


def _load_json(filepath):
    """Load a JSON file, return None if not found."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _file_etag(filepath):
    """Generate an ETag from a file's mtime and size."""
    stat = os.stat(filepath)
    raw = f"{filepath}:{stat.st_mtime_ns}:{stat.st_size}"
    return hashlib.md5(raw.encode()).hexdigest()


def _dir_etag(dirpath, ext='.json'):
    """Generate an ETag from all matching files' mtimes in a directory."""
    parts = []
    if os.path.isdir(dirpath):
        for name in sorted(os.listdir(dirpath)):
            if name.endswith(ext):
                fp = os.path.join(dirpath, name)
                stat = os.stat(fp)
                parts.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")
    raw = "|".join(parts)
    return hashlib.md5(raw.encode()).hexdigest()


def _check_etag(etag):
    """Check If-None-Match header; return a 304 response if it matches."""
    if_none_match = request.headers.get('If-None-Match', '').strip()
    if if_none_match and if_none_match == f'"{etag}"':
        resp = make_response('', 304)
        resp.headers['ETag'] = f'"{etag}"'
        return resp
    return None


def _json_response(data, etag, max_age=300):
    """Build a JSON response with ETag and Cache-Control headers."""
    resp = jsonify(data)
    resp.headers['ETag'] = f'"{etag}"'
    resp.headers['Cache-Control'] = f'public, max-age={max_age}'
    return resp


@gtm_bp.route('/scenarios', methods=['GET'])
def list_scenarios():
    """List all available GTM scenario templates."""
    etag = _dir_etag(SCENARIOS_DIR)
    cached = _check_etag(etag)
    if cached:
        return cached

    scenarios = []
    if os.path.exists(SCENARIOS_DIR):
        for filename in sorted(os.listdir(SCENARIOS_DIR)):
            if filename.endswith('.json'):
                data = _load_json(os.path.join(SCENARIOS_DIR, filename))
                if data:
                    scenarios.append({
                        'id': data.get('id', filename.replace('.json', '')),
                        'name': data.get('name', ''),
                        'description': data.get('description', ''),
                        'category': data.get('category', 'general'),
                        'icon': data.get('icon', ''),
                    })
    return _json_response({'scenarios': scenarios}, etag)


@gtm_bp.route('/scenarios/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    """Get a specific scenario template with full configuration."""
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    if not os.path.exists(filepath):
        return jsonify({'error': f'Scenario {scenario_id} not found'}), 404

    etag = _file_etag(filepath)
    cached = _check_etag(etag)
    if cached:
        return cached

    data = _load_json(filepath)
    return _json_response(data, etag)


@gtm_bp.route('/seed-data/<data_type>', methods=['GET'])
def get_seed_data(data_type):
    """Get GTM seed data by type (account_profiles, signal_definitions, etc.)."""
    filepath = os.path.join(SEED_DATA_DIR, f'{data_type}.json')
    if not os.path.exists(filepath):
        return jsonify({'error': f'Seed data {data_type} not found'}), 404

    etag = _file_etag(filepath)
    cached = _check_etag(etag)
    if cached:
        return cached

    data = _load_json(filepath)
    return _json_response(data, etag)


@gtm_bp.route('/scenarios/<scenario_id>/seed-text', methods=['GET'])
def get_scenario_seed_text(scenario_id):
    """Get the seed text for a scenario, ready to paste into graph building."""
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    if not os.path.exists(filepath):
        return jsonify({'error': 'Seed text not found'}), 404

    etag = _file_etag(filepath)
    cached = _check_etag(etag)
    if cached:
        return cached

    data = _load_json(filepath)
    if data and 'seed_text' in data:
        return _json_response({'seed_text': data['seed_text']}, etag)
    return jsonify({'error': 'Seed text not found'}), 404


@gtm_bp.route('/scenarios/<scenario_id>/export', methods=['GET'])
def export_scenario(scenario_id):
    """Export a scenario as a downloadable JSON file."""
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    data = _load_json(filepath)
    if not data:
        return jsonify({'error': f'Scenario {scenario_id} not found'}), 404

    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    return Response(
        json_bytes,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename="{scenario_id}.json"',
        },
    )


REQUIRED_SCENARIO_FIELDS = {'id', 'name', 'seed_text', 'agent_config', 'simulation_config'}
SAFE_ID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,62}$')


@gtm_bp.route('/scenarios/import', methods=['POST'])
def import_scenario():
    """Import a scenario from JSON payload and save to the scenarios directory."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    missing = REQUIRED_SCENARIO_FIELDS - set(data.keys())
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(sorted(missing))}'}), 400

    scenario_id = str(data['id']).strip()
    if not SAFE_ID_RE.match(scenario_id):
        return jsonify({
            'error': 'Invalid scenario id. Use lowercase alphanumeric, hyphens, and underscores only.'
        }), 400

    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    overwritten = os.path.exists(filepath)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"[import] {'Overwritten' if overwritten else 'Created'} scenario: {scenario_id}")

    return jsonify({
        'success': True,
        'scenario': {
            'id': data.get('id'),
            'name': data.get('name', ''),
            'description': data.get('description', ''),
            'category': data.get('category', 'custom'),
            'icon': data.get('icon', 'upload'),
        },
        'overwritten': overwritten,
    }), 201 if not overwritten else 200


# ============== Leaderboard Endpoint ==============

# Score weights for composite ranking
SCORE_WEIGHTS = {
    'sentiment': 0.35,
    'consensus': 0.30,
    'decision_quality': 0.35,
}

MOCK_SCENARIO_NAMES = [
    'Enterprise Onboarding Flow',
    'Competitive Win/Loss Analysis',
    'Pipeline Acceleration Sprint',
    'Churn Risk Triage',
    'Expansion Revenue Strategy',
    'Product-Led Growth Review',
    'Support Escalation Workflow',
    'Quarterly Business Review',
]


def _deterministic_hash(value):
    """Return a stable integer hash from any string."""
    return int(hashlib.md5(value.encode('utf-8')).hexdigest()[:8], 16)


def _compute_run_scores(run):
    """Compute sentiment, consensus, and decision quality scores for a run.

    Uses deterministic seeding from the run ID so scores are stable across
    calls.  Observable metrics (totalActions, totalRounds, agentCount) nudge
    the scores so runs with more activity genuinely score differently.
    """
    seed = _deterministic_hash(run.get('id', str(run.get('timestamp', 0))))
    actions = run.get('totalActions', 0) or 0
    rounds = run.get('totalRounds', 0) or 0
    agents = run.get('agentCount', 0) or 0

    # Sentiment: 0-100
    sentiment_base = ((seed % 40) + 50) / 100
    sentiment_boost = min(actions / 2000, 0.10)
    sentiment = min(round((sentiment_base + sentiment_boost) * 100), 100)

    # Consensus: 0-100
    consensus_base = (((seed * 7) % 35) + 45) / 100
    round_boost = min(rounds / 200, 0.15)
    agent_boost = min(agents / 30, 0.05)
    consensus = min(round((consensus_base + round_boost + agent_boost) * 100), 100)

    # Decision quality: 0-100
    quality_base = (((seed * 13) % 30) + 55) / 100
    density = min((actions / max(rounds, 1)) / 20, 0.10) if actions and rounds else 0
    decision_quality = min(round((quality_base + density) * 100), 100)

    composite = round(
        sentiment * SCORE_WEIGHTS['sentiment']
        + consensus * SCORE_WEIGHTS['consensus']
        + decision_quality * SCORE_WEIGHTS['decision_quality']
    )

    return {
        'sentiment': sentiment,
        'consensus': consensus,
        'decisionQuality': decision_quality,
        'composite': composite,
    }


def _build_mock_leaderboard():
    """Generate a demo leaderboard when no run data is provided."""
    import time
    entries = []
    now = int(time.time() * 1000)
    for i, name in enumerate(MOCK_SCENARIO_NAMES):
        mock_id = f'mock-{i:04d}'
        run = {
            'id': mock_id,
            'scenarioName': name,
            'totalActions': 400 + (i * 137) % 600,
            'totalRounds': 80 + (i * 23) % 64,
            'agentCount': 8 + i % 8,
            'twitterActions': 200 + (i * 71) % 300,
            'redditActions': 100 + (i * 53) % 200,
            'timestamp': now - (i * 86400000),
            'status': 'completed',
            'scenarioId': f'scenario-{i}',
        }
        scores = _compute_run_scores(run)
        entries.append({**run, 'scores': scores})
    entries.sort(key=lambda e: e['scores']['composite'], reverse=True)
    for rank, entry in enumerate(entries, 1):
        entry['rank'] = rank
    return entries


@gtm_bp.route('/scenarios/leaderboard', methods=['POST'])
def scenarios_leaderboard():
    """Score and rank simulation runs.

    Accepts a JSON body with a ``runs`` array of simulation run objects.
    Returns the same runs augmented with ``scores`` and ``rank``.

    When called with an empty or missing ``runs`` array, returns demo data.
    """
    data = request.get_json(silent=True) or {}
    runs = data.get('runs')

    if not runs:
        return jsonify({'success': True, 'data': _build_mock_leaderboard()})

    entries = []
    for run in runs:
        scores = _compute_run_scores(run)
        entries.append({**run, 'scores': scores})

    entries.sort(key=lambda e: e['scores']['composite'], reverse=True)
    for rank, entry in enumerate(entries, 1):
        entry['rank'] = rank

    return jsonify({'success': True, 'data': entries})


# ============== Outcome Mapping ==============

# Pre-built decision→impact data keyed by scenario category.
# Used in demo/mock mode; can be enriched via LLM when a key is configured.
_DEMO_OUTCOMES = {
    'outbound': {
        'scenario_name': 'Outbound Campaign Pre-Testing',
        'decisions': [
            {
                'id': 'sdr_headcount',
                'title': 'Increase SDR headcount by 2',
                'category': 'hiring',
                'impact': {'pipeline_per_month': 200000, 'cost_per_month': 80000},
                'timeline': {
                    'day_30': {'pipeline': 50000, 'cost': 80000},
                    'day_60': {'pipeline': 140000, 'cost': 80000},
                    'day_90': {'pipeline': 200000, 'cost': 80000},
                },
                'roi': 2.5,
                'confidence': 0.72,
            },
            {
                'id': 'competitive_campaign',
                'title': 'Launch competitive comparison campaign',
                'category': 'campaign',
                'impact': {'pipeline_per_month': 75000, 'cost_per_month': 15000},
                'timeline': {
                    'day_30': {'pipeline': 20000, 'cost': 15000},
                    'day_60': {'pipeline': 55000, 'cost': 15000},
                    'day_90': {'pipeline': 75000, 'cost': 15000},
                },
                'roi': 5.0,
                'confidence': 0.65,
            },
            {
                'id': 'subject_line_optimization',
                'title': 'A/B test top-2 subject lines at scale',
                'category': 'optimization',
                'impact': {'pipeline_per_month': 45000, 'cost_per_month': 5000},
                'timeline': {
                    'day_30': {'pipeline': 15000, 'cost': 5000},
                    'day_60': {'pipeline': 35000, 'cost': 5000},
                    'day_90': {'pipeline': 45000, 'cost': 5000},
                },
                'roi': 9.0,
                'confidence': 0.81,
            },
            {
                'id': 'persona_targeting',
                'title': 'Focus outreach on VP Support & CX Director personas',
                'category': 'targeting',
                'impact': {'pipeline_per_month': 120000, 'cost_per_month': 10000},
                'timeline': {
                    'day_30': {'pipeline': 30000, 'cost': 10000},
                    'day_60': {'pipeline': 80000, 'cost': 10000},
                    'day_90': {'pipeline': 120000, 'cost': 10000},
                },
                'roi': 12.0,
                'confidence': 0.78,
            },
        ],
    },
    'pricing': {
        'scenario_name': 'Pricing Change Simulation',
        'decisions': [
            {
                'id': 'grandfather_existing',
                'title': 'Grandfather existing customers for 12 months',
                'category': 'retention',
                'impact': {'pipeline_per_month': 0, 'cost_per_month': 180000},
                'timeline': {
                    'day_30': {'pipeline': 0, 'cost': 180000},
                    'day_60': {'pipeline': 0, 'cost': 180000},
                    'day_90': {'pipeline': 50000, 'cost': 180000},
                },
                'roi': 0.28,
                'confidence': 0.85,
            },
            {
                'id': 'usage_based_repricing',
                'title': 'Migrate to usage-based pricing model',
                'category': 'pricing',
                'impact': {'pipeline_per_month': 320000, 'cost_per_month': 45000},
                'timeline': {
                    'day_30': {'pipeline': 60000, 'cost': 45000},
                    'day_60': {'pipeline': 200000, 'cost': 45000},
                    'day_90': {'pipeline': 320000, 'cost': 45000},
                },
                'roi': 7.1,
                'confidence': 0.58,
            },
            {
                'id': 'churn_prevention',
                'title': 'Proactive outreach to at-risk accounts',
                'category': 'retention',
                'impact': {'pipeline_per_month': 150000, 'cost_per_month': 25000},
                'timeline': {
                    'day_30': {'pipeline': 80000, 'cost': 25000},
                    'day_60': {'pipeline': 130000, 'cost': 25000},
                    'day_90': {'pipeline': 150000, 'cost': 25000},
                },
                'roi': 6.0,
                'confidence': 0.74,
            },
        ],
    },
    'signals': {
        'scenario_name': 'Sales Signal Validation',
        'decisions': [
            {
                'id': 'signal_prioritization',
                'title': 'Reduce signal types from 8 to top-3 predictive',
                'category': 'optimization',
                'impact': {'pipeline_per_month': 95000, 'cost_per_month': 8000},
                'timeline': {
                    'day_30': {'pipeline': 25000, 'cost': 8000},
                    'day_60': {'pipeline': 65000, 'cost': 8000},
                    'day_90': {'pipeline': 95000, 'cost': 8000},
                },
                'roi': 11.9,
                'confidence': 0.71,
            },
            {
                'id': 'slack_consolidation',
                'title': 'Consolidate signal delivery to single Slack channel',
                'category': 'process',
                'impact': {'pipeline_per_month': 40000, 'cost_per_month': 3000},
                'timeline': {
                    'day_30': {'pipeline': 15000, 'cost': 3000},
                    'day_60': {'pipeline': 30000, 'cost': 3000},
                    'day_90': {'pipeline': 40000, 'cost': 3000},
                },
                'roi': 13.3,
                'confidence': 0.82,
            },
            {
                'id': 'rep_enablement',
                'title': 'Add signal context cards with recommended actions',
                'category': 'enablement',
                'impact': {'pipeline_per_month': 110000, 'cost_per_month': 20000},
                'timeline': {
                    'day_30': {'pipeline': 20000, 'cost': 20000},
                    'day_60': {'pipeline': 70000, 'cost': 20000},
                    'day_90': {'pipeline': 110000, 'cost': 20000},
                },
                'roi': 5.5,
                'confidence': 0.67,
            },
        ],
    },
    'personalization': {
        'scenario_name': 'Personalization Strategy',
        'decisions': [
            {
                'id': 'ai_personalization',
                'title': 'Deploy AI-generated email personalization',
                'category': 'automation',
                'impact': {'pipeline_per_month': 160000, 'cost_per_month': 12000},
                'timeline': {
                    'day_30': {'pipeline': 35000, 'cost': 12000},
                    'day_60': {'pipeline': 100000, 'cost': 12000},
                    'day_90': {'pipeline': 160000, 'cost': 12000},
                },
                'roi': 13.3,
                'confidence': 0.69,
            },
            {
                'id': 'segment_playbooks',
                'title': 'Create industry-specific outreach playbooks',
                'category': 'content',
                'impact': {'pipeline_per_month': 85000, 'cost_per_month': 18000},
                'timeline': {
                    'day_30': {'pipeline': 15000, 'cost': 18000},
                    'day_60': {'pipeline': 50000, 'cost': 18000},
                    'day_90': {'pipeline': 85000, 'cost': 18000},
                },
                'roi': 4.7,
                'confidence': 0.73,
            },
        ],
    },
}

# Fallback: generic outcomes for unknown scenario categories
_DEMO_OUTCOMES['general'] = _DEMO_OUTCOMES['outbound']


@gtm_bp.route('/outcomes/<scenario_id>', methods=['GET'])
def get_outcomes(scenario_id):
    """
    Return decision→impact outcome mappings for a scenario.

    Works in demo mode with pre-built data. When an LLM key is configured,
    the endpoint can optionally enrich outcomes (not yet implemented — the
    demo data is sufficient for the visualization component).
    """
    # Try to load the scenario to determine category
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    scenario = _load_json(filepath)

    if scenario:
        category = scenario.get('category', 'general')
    else:
        category = 'general'

    outcomes = _DEMO_OUTCOMES.get(category, _DEMO_OUTCOMES['general'])

    # Compute aggregate totals for the frontend
    decisions = outcomes['decisions']
    total_pipeline = sum(d['impact']['pipeline_per_month'] for d in decisions)
    total_cost = sum(d['impact']['cost_per_month'] for d in decisions)
    avg_roi = (
        sum(d['roi'] for d in decisions) / len(decisions) if decisions else 0
    )

    return jsonify({
        'scenario_id': scenario_id,
        'scenario_name': outcomes['scenario_name'],
        'decisions': decisions,
        'totals': {
            'pipeline_per_month': total_pipeline,
            'cost_per_month': total_cost,
            'net_impact': total_pipeline - total_cost,
            'avg_roi': round(avg_roi, 1),
        },
    })


# ============== Simulation Scenario Templates ==============

@gtm_bp.route('/templates', methods=['GET'])
def list_templates():
    """List all pre-built simulation scenario templates."""
    return jsonify({'templates': ScenarioTemplateService.list_templates()})


@gtm_bp.route('/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a specific simulation scenario template with full configuration."""
    template = ScenarioTemplateService.get_template(template_id)
    if template:
        return jsonify(template.to_dict())
    return jsonify({'error': f'Template {template_id} not found'}), 404


# ============== GTM Context Data ==============

# Per-scenario context data: realistic business metrics for display
# during simulation. Deterministic — no LLM needed.
_SCENARIO_CONTEXT = {
    "outbound_campaign": {
        "revenue": {
            "label": "Revenue",
            "metrics": [
                {"key": "mrr", "label": "MRR", "value": "$4.2M", "trend": "+3.1%"},
                {"key": "arr", "label": "ARR", "value": "$50.4M", "trend": "+18%"},
                {"key": "growth_rate", "label": "MoM Growth", "value": "3.1%", "trend": "+0.4pp"},
                {"key": "nrr", "label": "Net Revenue Retention", "value": "112%", "trend": "+2pp"},
                {"key": "acv", "label": "Avg Contract Value", "value": "$24K", "trend": "+8%"},
            ],
        },
        "pipeline": {
            "label": "Pipeline",
            "metrics": [
                {"key": "total_pipeline", "label": "Total Pipeline", "value": "$18.5M", "trend": "+12%"},
                {"key": "weighted_pipeline", "label": "Weighted Pipeline", "value": "$8.2M", "trend": "+6%"},
                {"key": "open_deals", "label": "Open Deals", "value": "142", "trend": "+15"},
                {"key": "avg_deal_size", "label": "Avg Deal Size", "value": "$130K", "trend": "-3%"},
                {"key": "win_rate", "label": "Win Rate", "value": "28%", "trend": "+1.5pp"},
                {"key": "avg_cycle_days", "label": "Avg Sales Cycle", "value": "45 days", "trend": "-3 days"},
            ],
        },
        "accounts": {
            "label": "Accounts",
            "metrics": [
                {"key": "total_accounts", "label": "Total Accounts", "value": "2,400", "trend": "+180"},
                {"key": "healthy", "label": "Healthy (A/B)", "value": "68%", "trend": "+2pp"},
                {"key": "at_risk", "label": "At Risk (C)", "value": "22%", "trend": "-1pp"},
                {"key": "critical", "label": "Critical (D/F)", "value": "10%", "trend": "-1pp"},
                {"key": "churn_rate", "label": "Monthly Churn", "value": "2.1%", "trend": "-0.3pp"},
                {"key": "expansion_eligible", "label": "Expansion Eligible", "value": "340", "trend": "+45"},
            ],
        },
        "campaigns": {
            "label": "Campaigns",
            "metrics": [
                {"key": "active_campaigns", "label": "Active Campaigns", "value": "8", "trend": "+2"},
                {"key": "total_sent", "label": "Emails Sent (MTD)", "value": "45,200", "trend": "+22%"},
                {"key": "open_rate", "label": "Avg Open Rate", "value": "24.3%", "trend": "+1.8pp"},
                {"key": "click_rate", "label": "Avg Click Rate", "value": "3.2%", "trend": "+0.4pp"},
                {"key": "conversion_rate", "label": "Email Conversion", "value": "1.8%", "trend": "+0.2pp"},
                {"key": "top_campaign", "label": "Top Campaign", "value": "Fin AI Launch", "trend": "32% open"},
            ],
        },
    },
    "pricing_simulation": {
        "revenue": {
            "label": "Revenue",
            "metrics": [
                {"key": "mrr", "label": "MRR", "value": "$4.2M", "trend": "+3.1%"},
                {"key": "arr", "label": "ARR", "value": "$50.4M", "trend": "+18%"},
                {"key": "at_risk_arr", "label": "At-Risk ARR", "value": "$8.1M", "trend": "+$1.2M"},
                {"key": "nrr", "label": "Net Revenue Retention", "value": "112%", "trend": "+2pp"},
                {"key": "avg_contract_value", "label": "Avg Contract Value", "value": "$24K", "trend": "+8%"},
                {"key": "revenue_per_account", "label": "Revenue per Account", "value": "$1,750/mo", "trend": "+5%"},
            ],
        },
        "pipeline": {
            "label": "Pipeline",
            "metrics": [
                {"key": "total_pipeline", "label": "Total Pipeline", "value": "$18.5M", "trend": "+12%"},
                {"key": "renewal_pipeline", "label": "Renewal Pipeline", "value": "$12.3M", "trend": "Q2 renewals"},
                {"key": "expansion_pipeline", "label": "Expansion Pipeline", "value": "$6.2M", "trend": "+18%"},
                {"key": "avg_deal_size", "label": "Avg Deal Size", "value": "$130K", "trend": "-3%"},
                {"key": "win_rate", "label": "Win Rate", "value": "28%", "trend": "+1.5pp"},
            ],
        },
        "accounts": {
            "label": "Accounts",
            "metrics": [
                {"key": "total_accounts", "label": "Total Accounts", "value": "2,400", "trend": "+180"},
                {"key": "smb_accounts", "label": "SMB Segment", "value": "1,440", "trend": "60%"},
                {"key": "midmarket_accounts", "label": "Mid-Market", "value": "720", "trend": "30%"},
                {"key": "enterprise_accounts", "label": "Enterprise", "value": "240", "trend": "10%"},
                {"key": "churn_rate", "label": "Monthly Churn", "value": "2.1%", "trend": "-0.3pp"},
                {"key": "competitor_eval", "label": "Evaluating Competitors", "value": "186", "trend": "+23"},
            ],
        },
        "campaigns": {
            "label": "Campaigns",
            "metrics": [
                {"key": "active_campaigns", "label": "Active Campaigns", "value": "3", "trend": "pricing-focused"},
                {"key": "migration_notices", "label": "Migration Notices Sent", "value": "1,200", "trend": "Phase 1"},
                {"key": "open_rate", "label": "Notice Open Rate", "value": "68%", "trend": "+12pp"},
                {"key": "support_tickets", "label": "Pricing Tickets", "value": "89", "trend": "+34"},
                {"key": "nps_score", "label": "Current NPS", "value": "42", "trend": "-3"},
            ],
        },
    },
    "signal_validation": {
        "revenue": {
            "label": "Revenue",
            "metrics": [
                {"key": "mrr", "label": "MRR", "value": "$4.2M", "trend": "+3.1%"},
                {"key": "arr", "label": "ARR", "value": "$50.4M", "trend": "+18%"},
                {"key": "signal_attributed_arr", "label": "Signal-Attributed ARR", "value": "$6.8M", "trend": "13.5%"},
                {"key": "nrr", "label": "Net Revenue Retention", "value": "112%", "trend": "+2pp"},
            ],
        },
        "pipeline": {
            "label": "Pipeline",
            "metrics": [
                {"key": "total_pipeline", "label": "Total Pipeline", "value": "$18.5M", "trend": "+12%"},
                {"key": "signal_sourced", "label": "Signal-Sourced Pipeline", "value": "$4.1M", "trend": "22%"},
                {"key": "signal_influenced", "label": "Signal-Influenced Deals", "value": "68", "trend": "+12"},
                {"key": "unactioned_signals", "label": "Unactioned Signals", "value": "76%", "trend": "+65pp"},
                {"key": "signal_to_meeting", "label": "Signal → Meeting Rate", "value": "8.3%", "trend": "-2.1pp"},
                {"key": "avg_cycle_days", "label": "Avg Sales Cycle", "value": "45 days", "trend": "-3 days"},
            ],
        },
        "accounts": {
            "label": "Accounts",
            "metrics": [
                {"key": "total_accounts", "label": "Total Accounts", "value": "2,400", "trend": "+180"},
                {"key": "signal_active", "label": "Signal-Active Accounts", "value": "892", "trend": "37%"},
                {"key": "churn_rate", "label": "Monthly Churn", "value": "2.1%", "trend": "-0.3pp"},
                {"key": "expansion_eligible", "label": "Expansion Eligible", "value": "340", "trend": "+45"},
                {"key": "usage_surge", "label": "Usage Surge Accounts", "value": "124", "trend": "+18"},
                {"key": "competitor_research", "label": "Competitor Research", "value": "89", "trend": "+11"},
            ],
        },
        "campaigns": {
            "label": "Campaigns",
            "metrics": [
                {"key": "active_campaigns", "label": "Active Campaigns", "value": "5", "trend": "signal-triggered"},
                {"key": "signal_alerts_today", "label": "Signal Alerts (Today)", "value": "47", "trend": "+8"},
                {"key": "rep_action_rate", "label": "Rep Action Rate", "value": "24%", "trend": "-3pp"},
                {"key": "avg_response_time", "label": "Avg Response Time", "value": "4.2 hrs", "trend": "+0.8 hrs"},
                {"key": "conversion_rate", "label": "Signal Conversion", "value": "11%", "trend": "+1.5pp"},
            ],
        },
    },
    "personalization": {
        "revenue": {
            "label": "Revenue",
            "metrics": [
                {"key": "mrr", "label": "MRR", "value": "$4.2M", "trend": "+3.1%"},
                {"key": "arr", "label": "ARR", "value": "$50.4M", "trend": "+18%"},
                {"key": "outbound_attributed", "label": "Outbound-Attributed ARR", "value": "$3.2M", "trend": "6.3%"},
                {"key": "nrr", "label": "Net Revenue Retention", "value": "112%", "trend": "+2pp"},
            ],
        },
        "pipeline": {
            "label": "Pipeline",
            "metrics": [
                {"key": "total_pipeline", "label": "Total Pipeline", "value": "$18.5M", "trend": "+12%"},
                {"key": "outbound_pipeline", "label": "Outbound Pipeline", "value": "$5.4M", "trend": "+24%"},
                {"key": "open_deals", "label": "Open Deals", "value": "142", "trend": "+15"},
                {"key": "avg_deal_size", "label": "Avg Deal Size", "value": "$130K", "trend": "-3%"},
                {"key": "win_rate", "label": "Win Rate", "value": "28%", "trend": "+1.5pp"},
            ],
        },
        "accounts": {
            "label": "Accounts",
            "metrics": [
                {"key": "total_accounts", "label": "Total Accounts", "value": "2,400", "trend": "+180"},
                {"key": "healthy", "label": "Healthy (A/B)", "value": "68%", "trend": "+2pp"},
                {"key": "churn_rate", "label": "Monthly Churn", "value": "2.1%", "trend": "-0.3pp"},
                {"key": "expansion_eligible", "label": "Expansion Eligible", "value": "340", "trend": "+45"},
                {"key": "email_reachable", "label": "Email-Reachable", "value": "1,920", "trend": "80%"},
            ],
        },
        "campaigns": {
            "label": "Campaigns",
            "metrics": [
                {"key": "active_campaigns", "label": "Active Campaigns", "value": "8", "trend": "+2"},
                {"key": "variants_tested", "label": "Variants Under Test", "value": "10", "trend": "this sprint"},
                {"key": "emails_per_rep", "label": "Emails/Rep/Week", "value": "25", "trend": "target"},
                {"key": "open_rate", "label": "Avg Open Rate", "value": "24.3%", "trend": "+1.8pp"},
                {"key": "ai_score_accuracy", "label": "AI Score Accuracy", "value": "62%", "trend": "baseline"},
                {"key": "top_variant", "label": "Top Variant", "value": "#3 (Casual+Pain)", "trend": "38% open"},
            ],
        },
    },
}

# Default context for unknown scenarios
_DEFAULT_CONTEXT = _SCENARIO_CONTEXT["outbound_campaign"]


@gtm_bp.route('/scenarios/<scenario_id>/context', methods=['GET'])
def get_scenario_context(scenario_id):
    """
    Return GTM business context metrics for a scenario.
    Deterministic data — works without LLM in demo/mock mode.
    """
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    scenario = _load_json(filepath)
    if not scenario:
        return jsonify({'error': f'Scenario {scenario_id} not found'}), 404

    context = _SCENARIO_CONTEXT.get(scenario_id, _DEFAULT_CONTEXT)
    return jsonify({
        'scenario_id': scenario_id,
        'scenario_name': scenario.get('name', ''),
        'sections': context,
    })


# ============== Unified Simulation Endpoint ==============

@gtm_bp.route('/simulate', methods=['POST'])
def simulate():
    """
    Unified GTM simulation endpoint.

    Accepts the frontend's simulation config (seed_text + parameters),
    creates a project, generates ontology, and kicks off async graph
    building -- all in one call.

    Request (JSON):
        {
            "seed_text": "...",               // required
            "agent_count": 200,               // optional, stored as metadata
            "persona_types": [...],           // optional, stored as metadata
            "industries": [...],              // optional, stored as metadata
            "company_sizes": [...],           // optional, stored as metadata
            "regions": [...],                 // optional, stored as metadata
            "duration_hours": 72,             // optional, stored as metadata
            "minutes_per_round": 30,          // optional, stored as metadata
            "platform_mode": "parallel"       // optional, stored as metadata
        }

    Returns:
        {
            "success": true,
            "data": {
                "task_id": "...",
                "project_id": "..."
            }
        }

    The frontend can then poll GET /api/graph/task/<task_id> for progress.
    On completion the task result contains project_id, graph_id, and task_id.
    """
    try:
        data = request.get_json() or {}
        seed_text = data.get('seed_text', '').strip()

        if not seed_text:
            return jsonify({
                "success": False,
                "error": "seed_text is required"
            }), 400

        # Validate Zep key early so we fail fast
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY is not configured"
            }), 500

        # Capture simulation metadata from the frontend config
        sim_metadata = {
            k: data[k] for k in (
                'agent_count', 'persona_types', 'industries',
                'company_sizes', 'regions', 'duration_hours',
                'minutes_per_round', 'platform_mode',
            ) if k in data
        }

        # Create project
        project = ProjectManager.create_project(name="GTM Simulation")
        project.simulation_requirement = seed_text
        project_id = project.project_id
        logger.info(f"[simulate] Created project {project_id}")

        # Save seed_text as extracted text (no file upload needed)
        preprocessed = TextProcessor.preprocess_text(seed_text)
        project.total_text_length = len(preprocessed)
        ProjectManager.save_extracted_text(project_id, preprocessed)

        # Create async task
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            "GTM Simulation",
            metadata={"project_id": project_id, **sim_metadata},
        )

        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)

        # ---- background thread ----
        def _run():
            build_logger = get_logger('mirofish.gtm.build')
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    message="Generating ontology from seed text...",
                    progress=5,
                )

                # 1. Generate ontology
                generator = OntologyGenerator()
                ontology = generator.generate(
                    document_texts=[preprocessed],
                    simulation_requirement=seed_text,
                )

                entity_count = len(ontology.get("entity_types", []))
                edge_count = len(ontology.get("edge_types", []))
                build_logger.info(
                    f"[{task_id}] Ontology generated: "
                    f"{entity_count} entity types, {edge_count} edge types"
                )

                # Persist ontology on the project
                proj = ProjectManager.get_project(project_id)
                proj.ontology = {
                    "entity_types": ontology.get("entity_types", []),
                    "edge_types": ontology.get("edge_types", []),
                }
                proj.analysis_summary = ontology.get("analysis_summary", "")
                proj.status = ProjectStatus.ONTOLOGY_GENERATED
                ProjectManager.save_project(proj)

                task_manager.update_task(
                    task_id,
                    message="Ontology generated. Creating graph...",
                    progress=15,
                )

                # 2. Build graph (mirrors graph.py build_task logic)
                text = ProjectManager.get_extracted_text(project_id)
                chunk_size = proj.chunk_size or Config.DEFAULT_CHUNK_SIZE
                chunk_overlap = proj.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP
                graph_name = proj.name or "GTM Simulation Graph"

                builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)

                # Split text
                chunks = TextProcessor.split_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
                total_chunks = len(chunks)

                task_manager.update_task(
                    task_id,
                    message=f"Text split into {total_chunks} chunks. Creating Zep graph...",
                    progress=20,
                )

                graph_id = builder.create_graph(name=graph_name)

                proj = ProjectManager.get_project(project_id)
                proj.graph_id = graph_id
                proj.status = ProjectStatus.GRAPH_BUILDING
                ProjectManager.save_project(proj)

                # Set ontology on the Zep graph
                task_manager.update_task(task_id, message="Setting ontology...", progress=25)
                builder.set_ontology(graph_id, proj.ontology)

                # Add text batches
                def add_progress_cb(msg, ratio):
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=25 + int(ratio * 35),  # 25-60%
                    )

                task_manager.update_task(
                    task_id,
                    message=f"Adding {total_chunks} text chunks...",
                    progress=25,
                )
                episode_uuids = builder.add_text_batches(
                    graph_id, chunks, batch_size=3, progress_callback=add_progress_cb,
                )

                # Wait for Zep processing
                task_manager.update_task(
                    task_id, message="Waiting for Zep processing...", progress=60,
                )

                def wait_progress_cb(msg, ratio):
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=60 + int(ratio * 30),  # 60-90%
                    )

                builder._wait_for_episodes(episode_uuids, wait_progress_cb)

                # Fetch final graph data
                task_manager.update_task(
                    task_id, message="Fetching graph data...", progress=95,
                )
                graph_data = builder.get_graph_data(graph_id)

                # Mark project complete
                proj = ProjectManager.get_project(project_id)
                proj.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(proj)

                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(
                    f"[{task_id}] Graph complete: graph_id={graph_id}, "
                    f"nodes={node_count}, edges={edge_count}"
                )

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="Simulation graph built successfully",
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "task_id": task_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks,
                    },
                )

            except Exception as e:
                build_logger.error(f"[{task_id}] Simulation failed: {e}")
                build_logger.debug(traceback.format_exc())

                proj = ProjectManager.get_project(project_id)
                if proj:
                    proj.status = ProjectStatus.FAILED
                    proj.error = str(e)
                    ProjectManager.save_project(proj)

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Simulation failed: {e}",
                    error=traceback.format_exc(),
                )

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "task_id": task_id,
                "project_id": project_id,
            },
        })

    except Exception as e:
        logger.error(f"[simulate] Request error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500
