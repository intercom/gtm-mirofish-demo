"""
Reconciliation API Blueprint
Three-way MRR reconciliation: Salesforce vs Billing (Stripe) vs Snowflake mart.
Provides runs, discrepancies, per-account history, resolution, rules, stats, trend data,
and discrepancy distribution histogram.
"""

import hashlib
import random
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.reconciliation')

reconciliation_bp = Blueprint(
    'reconciliation', __name__, url_prefix='/api/v1/reconciliation'
)

# ---------------------------------------------------------------------------
# In-memory resolution store (persists for app lifetime)
# ---------------------------------------------------------------------------
_resolutions = {}  # record_id -> {resolution_notes, resolved_by, resolved_at}

# ---------------------------------------------------------------------------
# Mock data helpers — deterministic, seeded by account/run id
# ---------------------------------------------------------------------------

_ACCOUNT_NAMES = [
    'Acme Corp', 'Globex Industries', 'Initech Solutions', 'Umbrella Inc',
    'Stark Enterprises', 'Wayne Industries', 'Cyberdyne Systems', 'Tyrell Corp',
    'Soylent Corp', 'Massive Dynamic', 'Oscorp Technologies', 'LexCorp',
    'Aperture Science', 'Black Mesa Research', 'Weyland-Yutani',
    'Rekall Inc', 'Nakatomi Trading', 'Prestige Worldwide', 'Pied Piper',
    'Hooli', 'Aviato', 'Bachmanity Capital', 'Raviga Capital', 'Endframe',
    'Nucleus', 'Intersite', 'Cloudbase Analytics', 'DataStream Ltd',
    'SyncWave Systems', 'BrightPath AI',
]

_DISCREPANCY_TYPES = ['amount_mismatch', 'missing_in_source', 'timing_lag', 'currency_rounding']

_RULES = [
    {'id': 'rule-1', 'name': 'Amount tolerance', 'description': 'Allow up to $5 difference across sources', 'check_type': 'absolute_threshold', 'threshold': 5.0, 'action': 'auto_resolve'},
    {'id': 'rule-2', 'name': 'Percentage tolerance', 'description': 'Allow up to 1% relative difference', 'check_type': 'percentage_threshold', 'threshold': 1.0, 'action': 'auto_resolve'},
    {'id': 'rule-3', 'name': 'Missing record check', 'description': 'Flag accounts present in one source but not others', 'check_type': 'existence', 'threshold': 0, 'action': 'flag'},
    {'id': 'rule-4', 'name': 'Currency normalization', 'description': 'Normalize multi-currency values to USD before comparison', 'check_type': 'currency', 'threshold': 0, 'action': 'auto_resolve'},
    {'id': 'rule-5', 'name': 'Timing window', 'description': 'Allow 48h lag between source updates', 'check_type': 'timing', 'threshold': 48, 'action': 'auto_resolve'},
    {'id': 'rule-6', 'name': 'Large discrepancy escalation', 'description': 'Escalate discrepancies over $1000', 'check_type': 'absolute_threshold', 'threshold': 1000.0, 'action': 'escalate'},
    {'id': 'rule-7', 'name': 'Duplicate detection', 'description': 'Flag potential duplicate account records', 'check_type': 'duplicate', 'threshold': 0, 'action': 'flag'},
    {'id': 'rule-8', 'name': 'Stale data check', 'description': 'Flag sources not updated in 7+ days', 'check_type': 'freshness', 'threshold': 168, 'action': 'flag'},
    {'id': 'rule-9', 'name': 'Negative MRR guard', 'description': 'Flag any negative MRR values as data errors', 'check_type': 'range', 'threshold': 0, 'action': 'escalate'},
    {'id': 'rule-10', 'name': 'Churn mismatch detection', 'description': 'Flag accounts churned in one source but active in another', 'check_type': 'status', 'threshold': 0, 'action': 'flag'},
]

NUM_ACCOUNTS = 200


def _seed_rng(seed_str):
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


def _generate_records(run_id, run_index):
    """Generate reconciliation records for a single run.

    run_index 0 = oldest, 3 = newest.  Discrepancy rate improves over time
    to simulate a trend of data quality improvement.
    """
    rng = _seed_rng(f'recon-run-{run_id}')
    base_discrep_rate = 0.18 - (run_index * 0.02)  # 18% → 12%

    records = []
    for i in range(NUM_ACCOUNTS):
        acct_id = f'acct-{i + 1:04d}'
        acct_name = _ACCOUNT_NAMES[i % len(_ACCOUNT_NAMES)]
        if i >= len(_ACCOUNT_NAMES):
            acct_name = f'{acct_name} #{i // len(_ACCOUNT_NAMES) + 1}'

        base_mrr = round(rng.uniform(500, 50000), 2)

        roll = rng.random()
        if roll > base_discrep_rate:
            # Matched — all three sources agree
            sf_mrr = billing_mrr = snowflake_mrr = base_mrr
            status = 'matched'
            disc_type = None
        elif roll > base_discrep_rate * 0.35:
            # Small discrepancy (<$100)
            sf_mrr = base_mrr
            billing_mrr = round(base_mrr + rng.uniform(-100, 100), 2)
            snowflake_mrr = round(base_mrr + rng.uniform(-50, 50), 2)
            status = 'discrepancy'
            disc_type = rng.choice(['timing_lag', 'currency_rounding'])
        elif roll > base_discrep_rate * 0.12:
            # Moderate discrepancy ($100-$1000)
            sf_mrr = base_mrr
            billing_mrr = round(base_mrr + rng.choice([-1, 1]) * rng.uniform(100, 1000), 2)
            snowflake_mrr = round(base_mrr + rng.choice([-1, 1]) * rng.uniform(50, 500), 2)
            status = 'discrepancy'
            disc_type = rng.choice(['amount_mismatch', 'missing_in_source'])
        else:
            # Large discrepancy (>$1000)
            sf_mrr = base_mrr
            billing_mrr = round(base_mrr + rng.choice([-1, 1]) * rng.uniform(1000, 5000), 2)
            snowflake_mrr = round(base_mrr + rng.choice([-1, 1]) * rng.uniform(500, 3000), 2)
            status = 'discrepancy'
            disc_type = 'amount_mismatch'

        record_id = f'{run_id}-{acct_id}'
        resolution = _resolutions.get(record_id)
        if resolution:
            status = 'resolved'

        records.append({
            'record_id': record_id,
            'account_id': acct_id,
            'account_name': acct_name,
            'sf_mrr': sf_mrr,
            'billing_mrr': billing_mrr,
            'snowflake_mrr': snowflake_mrr,
            'sf_vs_billing_diff': round(sf_mrr - billing_mrr, 2),
            'sf_vs_snowflake_diff': round(sf_mrr - snowflake_mrr, 2),
            'billing_vs_snowflake_diff': round(billing_mrr - snowflake_mrr, 2),
            'status': status,
            'discrepancy_type': disc_type,
            'resolution_notes': resolution.get('resolution_notes') if resolution else None,
        })

    return records


def _generate_runs():
    """Generate 4 weekly reconciliation runs with improving trend."""
    now = datetime(2026, 3, 24, 8, 0, 0)
    runs = []
    for i in range(4):
        run_date = now - timedelta(weeks=3 - i)
        run_id = f'run-{i + 1:03d}'
        records = _generate_records(run_id, i)

        matched = sum(1 for r in records if r['status'] in ('matched', 'resolved'))
        discrepancies = [r for r in records if r['status'] == 'discrepancy']
        disc_values = [
            abs(r['sf_vs_billing_diff']) + abs(r['sf_vs_snowflake_diff'])
            for r in discrepancies
        ]

        runs.append({
            'id': run_id,
            'run_date': run_date.isoformat(),
            'total_accounts': NUM_ACCOUNTS,
            'matched_count': matched,
            'discrepancy_count': len(discrepancies),
            'total_discrepancy_value': round(sum(disc_values), 2) if disc_values else 0,
            'largest_discrepancy': round(max(disc_values), 2) if disc_values else 0,
            'avg_discrepancy': round(sum(disc_values) / len(disc_values), 2) if disc_values else 0,
            'run_duration_seconds': _seed_rng(run_id).randint(45, 180),
        })

    return runs


def _generate_trend_data(months=24, seed=42):
    """Generate deterministic reconciliation trend data showing improvement over time."""
    rng = random.Random(seed)
    base_date = datetime(2024, 4, 1)
    runs = []

    annotations = {
        5: 'Auto-matching rules deployed',
        11: 'Billing system migration',
        17: 'ML discrepancy classifier launched',
    }

    for i in range(months):
        run_date = base_date + timedelta(days=30 * i)

        progress = i / (months - 1)
        base_match = 87.5 + progress * 10.5
        match_rate = round(min(99.2, base_match + rng.uniform(-1.5, 1.5)), 1)

        base_value = 245000 * (1 - progress * 0.78)
        discrepancy_value = round(max(8000, base_value + rng.uniform(-15000, 15000)), 0)

        base_count = int(185 * (1 - progress * 0.72))
        discrepancy_count = max(12, base_count + rng.randint(-15, 15))

        run = {
            'date': run_date.strftime('%Y-%m-%d'),
            'matchRate': match_rate,
            'discrepancyValue': discrepancy_value,
            'discrepancyCount': discrepancy_count,
            'totalAccounts': 4200 + rng.randint(-50, 100),
        }
        if i in annotations:
            run['annotation'] = annotations[i]

        runs.append(run)

    return runs


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@reconciliation_bp.route('/runs', methods=['GET'])
def list_runs():
    """List all reconciliation runs with summary stats."""
    runs = _generate_runs()
    return jsonify({'runs': runs})


@reconciliation_bp.route('/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    """Get a single run with all its reconciliation records."""
    runs = _generate_runs()
    run = next((r for r in runs if r['id'] == run_id), None)
    if not run:
        return jsonify({'error': f'Run {run_id} not found'}), 404

    idx = next(i for i, r in enumerate(runs) if r['id'] == run_id)
    records = _generate_records(run_id, idx)
    return jsonify({'run': run, 'records': records})


@reconciliation_bp.route('/current', methods=['GET'])
def current_run():
    """Get the most recent run's results."""
    runs = _generate_runs()
    latest = runs[-1]
    idx = len(runs) - 1
    records = _generate_records(latest['id'], idx)
    return jsonify({'run': latest, 'records': records})


@reconciliation_bp.route('/discrepancies', methods=['GET'])
def list_discrepancies():
    """Return only discrepancy records from the latest run, sorted by magnitude."""
    runs = _generate_runs()
    latest = runs[-1]
    idx = len(runs) - 1
    records = _generate_records(latest['id'], idx)

    discrepancies = [r for r in records if r['status'] == 'discrepancy']
    discrepancies.sort(
        key=lambda r: abs(r['sf_vs_billing_diff']) + abs(r['sf_vs_snowflake_diff']),
        reverse=True,
    )
    return jsonify({
        'run_id': latest['id'],
        'run_date': latest['run_date'],
        'discrepancies': discrepancies,
        'total': len(discrepancies),
    })


@reconciliation_bp.route('/account/<account_id>', methods=['GET'])
def account_history(account_id):
    """Reconciliation history for a specific account across all runs."""
    runs = _generate_runs()
    history = []
    for idx, run in enumerate(runs):
        records = _generate_records(run['id'], idx)
        match = next((r for r in records if r['account_id'] == account_id), None)
        if match:
            history.append({
                'run_id': run['id'],
                'run_date': run['run_date'],
                **match,
            })

    if not history:
        return jsonify({'error': f'Account {account_id} not found'}), 404

    return jsonify({
        'account_id': account_id,
        'account_name': history[0]['account_name'],
        'history': history,
    })


@reconciliation_bp.route('/resolve/<record_id>', methods=['POST'])
def resolve_discrepancy(record_id):
    """Mark a discrepancy as resolved with notes."""
    data = request.get_json() or {}
    notes = data.get('resolution_notes', '').strip()
    if not notes:
        return jsonify({'error': 'resolution_notes is required'}), 400

    _resolutions[record_id] = {
        'resolution_notes': notes,
        'resolved_by': data.get('resolved_by', 'analyst'),
        'resolved_at': datetime.utcnow().isoformat(),
    }
    logger.info(f'Resolved discrepancy {record_id}')

    return jsonify({
        'success': True,
        'record_id': record_id,
        'resolution': _resolutions[record_id],
    })


@reconciliation_bp.route('/rules', methods=['GET'])
def list_rules():
    """Return active reconciliation rules."""
    return jsonify({'rules': _RULES})


@reconciliation_bp.route('/stats', methods=['GET'])
def recon_stats():
    """Overall reconciliation health: match rate, total discrepancy value, trend."""
    runs = _generate_runs()

    trend = []
    for idx, run in enumerate(runs):
        match_rate = round(run['matched_count'] / run['total_accounts'] * 100, 1)
        trend.append({
            'run_id': run['id'],
            'run_date': run['run_date'],
            'match_rate': match_rate,
            'discrepancy_count': run['discrepancy_count'],
            'total_discrepancy_value': run['total_discrepancy_value'],
            'avg_discrepancy': run['avg_discrepancy'],
        })

    latest = runs[-1]
    match_rate = round(latest['matched_count'] / latest['total_accounts'] * 100, 1)

    return jsonify({
        'match_rate': match_rate,
        'total_accounts': latest['total_accounts'],
        'matched_count': latest['matched_count'],
        'discrepancy_count': latest['discrepancy_count'],
        'total_discrepancy_value': latest['total_discrepancy_value'],
        'largest_discrepancy': latest['largest_discrepancy'],
        'avg_discrepancy': latest['avg_discrepancy'],
        'trend': trend,
        'latest_run_date': latest['run_date'],
    })


@reconciliation_bp.route('/trend', methods=['GET'])
def get_trend():
    """Return reconciliation trend data for charting."""
    months = request.args.get('months', 24, type=int)
    months = max(6, min(60, months))
    data = _generate_trend_data(months=months)
    return jsonify({
        'runs': data,
        'target': {'matchRate': 95.0},
    })


# ---------------------------------------------------------------------------
# Discrepancy distribution histogram
# ---------------------------------------------------------------------------

DEMO_DISCREPANCY_DISTRIBUTION = {
    "bins": [
        {
            "range": "$0–$10",
            "min": 0,
            "max": 10,
            "total": 142,
            "by_type": {"timing": 58, "rounding": 61, "missing": 18, "genuine": 5},
        },
        {
            "range": "$10–$50",
            "min": 10,
            "max": 50,
            "total": 98,
            "by_type": {"timing": 34, "rounding": 29, "missing": 24, "genuine": 11},
        },
        {
            "range": "$50–$100",
            "min": 50,
            "max": 100,
            "total": 67,
            "by_type": {"timing": 22, "rounding": 12, "missing": 19, "genuine": 14},
        },
        {
            "range": "$100–$500",
            "min": 100,
            "max": 500,
            "total": 45,
            "by_type": {"timing": 11, "rounding": 5, "missing": 16, "genuine": 13},
        },
        {
            "range": "$500–$1K",
            "min": 500,
            "max": 1000,
            "total": 18,
            "by_type": {"timing": 3, "rounding": 1, "missing": 7, "genuine": 7},
        },
        {
            "range": "$1K+",
            "min": 1000,
            "max": None,
            "total": 8,
            "by_type": {"timing": 1, "rounding": 0, "missing": 3, "genuine": 4},
        },
    ],
    "statistics": {
        "mean": 145.32,
        "median": 42.50,
        "max": 4820.00,
        "stddev": 385.17,
        "total_accounts": 378,
        "total_discrepancies": 378,
    },
}


@reconciliation_bp.route('/discrepancy-distribution', methods=['GET'])
def get_discrepancy_distribution():
    """Get discrepancy distribution data for histogram visualization.

    Returns histogram bins with per-type breakdowns and summary statistics.
    Always returns demo data (no LLM key required).
    """
    try:
        return jsonify({
            "success": True,
            "data": DEMO_DISCREPANCY_DISTRIBUTION,
        })
    except Exception as e:
        logger.error(f"Failed to get discrepancy distribution: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500
