"""
Analytics API — Segment Performance
Returns customer segment performance metrics for the analytics dashboard.
Works in demo/mock mode without any LLM key.
"""

import hashlib

from flask import Blueprint, jsonify, request

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# ---------------------------------------------------------------------------
# Deterministic seed helper
# ---------------------------------------------------------------------------

def _seed(text):
    """Return a stable float 0-1 from a string, for deterministic demo data."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _vary(base, seed_str, spread=0.15):
    """Return base ± spread, seeded deterministically."""
    return round(base + ((_seed(seed_str) - 0.5) * 2 * spread * base), 1)


# ---------------------------------------------------------------------------
# Static segment definitions
# ---------------------------------------------------------------------------

SEGMENT_TYPES = {
    'plan_tier': {
        'label': 'Plan Tier',
        'segments': ['Starter', 'Pro', 'Premium', 'Enterprise'],
    },
    'industry': {
        'label': 'Industry',
        'segments': ['SaaS', 'E-commerce', 'Fintech', 'Healthcare', 'Media'],
    },
    'company_size': {
        'label': 'Company Size',
        'segments': ['1-50', '51-200', '201-1000', '1001-5000', '5000+'],
    },
    'region': {
        'label': 'Region',
        'segments': ['North America', 'Europe', 'APAC', 'LATAM'],
    },
}

METRICS = ['mrr', 'nrr', 'churn_rate', 'expansion_rate', 'csat']

METRIC_LABELS = {
    'mrr': 'Avg MRR ($)',
    'nrr': 'Net Revenue Retention (%)',
    'churn_rate': 'Churn Rate (%)',
    'expansion_rate': 'Expansion Rate (%)',
    'csat': 'CSAT Score',
}

# Baseline values per metric (realistic SaaS benchmarks)
METRIC_BASELINES = {
    'mrr': 4200,
    'nrr': 112,
    'churn_rate': 4.5,
    'expansion_rate': 18,
    'csat': 4.2,
}

# Higher-is-better flag (used for best/worst detection)
METRIC_HIGHER_IS_BETTER = {
    'mrr': True,
    'nrr': True,
    'churn_rate': False,
    'expansion_rate': True,
    'csat': True,
}

# Spread factors per metric (how much variance between segments)
METRIC_SPREADS = {
    'mrr': 0.45,
    'nrr': 0.08,
    'churn_rate': 0.5,
    'expansion_rate': 0.35,
    'csat': 0.12,
}

# Demo accounts per segment
DEMO_ACCOUNTS = [
    'Acme Corp', 'TechFlow Inc', 'DataPulse', 'CloudNova', 'BrightPath',
    'NexGen Solutions', 'Quantum Labs', 'PeakVenture', 'SwiftOps', 'CoreStack',
    'Luminary AI', 'Meridian Systems', 'TrueScale', 'VeloCity', 'ArcLight',
]


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

def _generate_segment_metrics(segment_type):
    """Generate metrics for each segment in a segment type."""
    info = SEGMENT_TYPES[segment_type]
    segments = []

    for seg_name in info['segments']:
        metrics = {}
        for m in METRICS:
            base = METRIC_BASELINES[m]
            spread = METRIC_SPREADS[m]
            metrics[m] = _vary(base, f'{segment_type}:{seg_name}:{m}', spread)

        segments.append({
            'name': seg_name,
            'metrics': metrics,
        })

    # Tag best / worst for each metric
    for m in METRICS:
        values = [(s['name'], s['metrics'][m]) for s in segments]
        higher = METRIC_HIGHER_IS_BETTER[m]
        best = max(values, key=lambda x: x[1]) if higher else min(values, key=lambda x: x[1])
        worst = min(values, key=lambda x: x[1]) if higher else max(values, key=lambda x: x[1])
        for s in segments:
            s.setdefault('tags', {})
            if s['name'] == best[0]:
                s['tags'][m] = 'best'
            elif s['name'] == worst[0]:
                s['tags'][m] = 'worst'

    return segments


def _generate_trend_data(segment_type):
    """Generate 6-month trend data per segment."""
    info = SEGMENT_TYPES[segment_type]
    months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    trends = {}

    for seg_name in info['segments']:
        seg_trend = []
        for i, month in enumerate(months):
            point = {'month': month}
            for m in METRICS:
                base = METRIC_BASELINES[m]
                spread = METRIC_SPREADS[m]
                drift = (i - 2.5) * 0.02 * base  # slight upward drift
                val = _vary(base + drift, f'{segment_type}:{seg_name}:{m}:{month}', spread)
                point[m] = val
            seg_trend.append(point)
        trends[seg_name] = seg_trend

    return {'months': months, 'segments': trends}


def _generate_accounts(segment_type, segment_name):
    """Generate demo accounts for drill-down."""
    accounts = []
    for i, name in enumerate(DEMO_ACCOUNTS):
        seed_key = f'{segment_type}:{segment_name}:{name}'
        accounts.append({
            'name': name,
            'mrr': round(_vary(METRIC_BASELINES['mrr'], seed_key + ':mrr', 0.6)),
            'nrr': _vary(METRIC_BASELINES['nrr'], seed_key + ':nrr', 0.1),
            'churn_risk': round(_seed(seed_key + ':churn') * 100, 1),
            'csat': round(_vary(METRIC_BASELINES['csat'], seed_key + ':csat', 0.15), 1),
            'last_active': f'2026-03-{15 + (i % 11):02d}',
        })
    return accounts


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@analytics_bp.route('/segments', methods=['GET'])
def get_segments():
    """
    GET /api/v1/analytics/segments?type=plan_tier

    Returns segment performance data with metrics, best/worst tags,
    trend data, and metadata.
    """
    segment_type = request.args.get('type', 'plan_tier')

    if segment_type not in SEGMENT_TYPES:
        return jsonify({'error': f'Unknown segment type: {segment_type}'}), 400

    segments = _generate_segment_metrics(segment_type)
    trends = _generate_trend_data(segment_type)

    return jsonify({
        'segment_type': segment_type,
        'label': SEGMENT_TYPES[segment_type]['label'],
        'metrics': METRIC_LABELS,
        'metric_direction': METRIC_HIGHER_IS_BETTER,
        'segments': segments,
        'trends': trends,
    })


@analytics_bp.route('/segments/<segment_type>/<segment_name>/accounts', methods=['GET'])
def get_segment_accounts(segment_type, segment_name):
    """
    GET /api/v1/analytics/segments/plan_tier/Enterprise/accounts

    Returns individual accounts for drill-down.
    """
    if segment_type not in SEGMENT_TYPES:
        return jsonify({'error': f'Unknown segment type: {segment_type}'}), 400

    info = SEGMENT_TYPES[segment_type]
    if segment_name not in info['segments']:
        return jsonify({'error': f'Unknown segment: {segment_name}'}), 404

    accounts = _generate_accounts(segment_type, segment_name)
    return jsonify({
        'segment_type': segment_type,
        'segment_name': segment_name,
        'accounts': accounts,
    })
