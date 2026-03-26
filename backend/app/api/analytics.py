"""
Analytics API routes — cohort analysis, attribution, segment performance.
"""

import hashlib
import math
from flask import Blueprint, request, jsonify

from ..utils.logger import get_logger

logger = get_logger('mirofish.api.analytics')

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')


# ---------------------------------------------------------------------------
# Shared seed helpers
# ---------------------------------------------------------------------------

def _seed(text):
    """Return a stable float 0-1 from a string, for deterministic demo data."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _seed_float(seed_str, min_val=0.0, max_val=1.0):
    """Deterministic pseudo-random float from a seed string."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    normalized = (h % 10000) / 10000.0
    return min_val + normalized * (max_val - min_val)


def _vary(base, seed_str, spread=0.15):
    """Return base ± spread, seeded deterministically."""
    return round(base + ((_seed(seed_str) - 0.5) * 2 * spread * base), 1)


# ===========================================================================
# Cohort Analysis
# ===========================================================================

def _generate_cohort_data(dimension='signup_date', metric='retention_rate'):
    """Generate deterministic cohort analysis data."""

    dimension_labels = {
        'signup_date': [
            'Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025',
            'May 2025', 'Jun 2025', 'Jul 2025', 'Aug 2025',
            'Sep 2025', 'Oct 2025', 'Nov 2025', 'Dec 2025',
        ],
        'plan_tier': ['Free', 'Starter', 'Pro', 'Enterprise'],
        'source_channel': [
            'Organic Search', 'Paid Search', 'Social Media',
            'Referral', 'Direct', 'Email Campaign',
        ],
        'region': [
            'North America', 'Europe', 'Asia Pacific',
            'Latin America', 'Middle East & Africa',
        ],
    }

    cohort_sizes_base = {
        'signup_date': [120, 145, 132, 158, 170, 165, 180, 195, 188, 210, 225, 240],
        'plan_tier': [450, 320, 180, 60],
        'source_channel': [280, 190, 150, 120, 160, 110],
        'region': [380, 280, 200, 90, 60],
    }

    labels = dimension_labels.get(dimension, dimension_labels['signup_date'])
    sizes = cohort_sizes_base.get(dimension, cohort_sizes_base['signup_date'])

    periods = 12
    period_labels = [f'Month {i}' for i in range(periods)]

    base_curves = {
        'retention_rate': lambda m, seed: max(
            15.0, 100.0 * math.exp(-0.08 * m) + _seed_float(seed, -5, 5)
        ),
        'expansion_rate': lambda m, seed: max(
            0.0, 2.0 + m * 1.5 + _seed_float(seed, -2, 3)
        ),
        'churn_rate': lambda m, seed: max(
            1.0, 12.0 * math.exp(-0.15 * m) + _seed_float(seed, -2, 3)
        ),
        'lifetime_value': lambda m, seed: round(
            50 + m * 45 + _seed_float(seed, -20, 30), 0
        ),
    }

    curve_fn = base_curves.get(metric, base_curves['retention_rate'])

    heatmap = []
    cohort_curves = []
    for i, label in enumerate(labels):
        row = []
        curve_points = []
        for m in range(periods):
            seed = f"{dimension}:{label}:{metric}:{m}"
            val = round(curve_fn(m, seed), 1)
            if metric == 'retention_rate' and m == 0:
                val = 100.0
            row.append(val)
            curve_points.append({'period': m, 'label': period_labels[m], 'value': val})
        heatmap.append(row)
        cohort_curves.append({
            'cohort': label,
            'size': sizes[i] if i < len(sizes) else 100,
            'points': curve_points,
        })

    final_values = [heatmap[i][-1] for i in range(len(labels))]
    avg_values = [round(sum(row) / len(row), 1) for row in heatmap]

    best_idx = avg_values.index(max(avg_values))
    worst_idx = avg_values.index(min(avg_values))

    best_avg = avg_values[best_idx]
    worst_avg = avg_values[worst_idx]
    diff = round(best_avg - worst_avg, 1)
    significant = diff > 10.0

    summary = {
        'best_cohort': {
            'label': labels[best_idx],
            'average': best_avg,
            'final_value': final_values[best_idx],
        },
        'worst_cohort': {
            'label': labels[worst_idx],
            'average': worst_avg,
            'final_value': final_values[worst_idx],
        },
        'difference': diff,
        'statistically_significant': significant,
        'overall_average': round(sum(avg_values) / len(avg_values), 1),
    }

    metric_ranges = {
        'retention_rate': {'min': 0, 'max': 100, 'low_color': '#ef4444', 'high_color': '#009900'},
        'expansion_rate': {'min': 0, 'max': 25, 'low_color': '#f5f5f5', 'high_color': '#2068FF'},
        'churn_rate': {'min': 0, 'max': 20, 'low_color': '#009900', 'high_color': '#ef4444'},
        'lifetime_value': {'min': 0, 'max': 600, 'low_color': '#f5f5f5', 'high_color': '#ff5600'},
    }

    return {
        'dimension': dimension,
        'metric': metric,
        'cohorts': labels,
        'periods': period_labels,
        'cohort_sizes': sizes[:len(labels)],
        'heatmap': heatmap,
        'curves': cohort_curves,
        'summary': summary,
        'color_scale': metric_ranges.get(metric, metric_ranges['retention_rate']),
    }


@analytics_bp.route('/cohorts', methods=['GET'])
def get_cohort_data():
    """
    Get cohort analysis data.

    Query params:
        dimension: signup_date | plan_tier | source_channel | region
        metric: retention_rate | expansion_rate | churn_rate | lifetime_value
    """
    try:
        dimension = request.args.get('dimension', 'signup_date')
        metric = request.args.get('metric', 'retention_rate')

        valid_dimensions = ['signup_date', 'plan_tier', 'source_channel', 'region']
        valid_metrics = ['retention_rate', 'expansion_rate', 'churn_rate', 'lifetime_value']

        if dimension not in valid_dimensions:
            return jsonify({
                'success': False,
                'error': f'Invalid dimension. Must be one of: {valid_dimensions}',
            }), 400

        if metric not in valid_metrics:
            return jsonify({
                'success': False,
                'error': f'Invalid metric. Must be one of: {valid_metrics}',
            }), 400

        data = _generate_cohort_data(dimension=dimension, metric=metric)

        return jsonify({
            'success': True,
            'data': data,
        })

    except Exception as e:
        logger.error(f"Cohort analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


@analytics_bp.route('/cohorts/compare', methods=['GET'])
def compare_cohorts():
    """
    Compare two specific cohorts head-to-head.

    Query params:
        dimension: signup_date | plan_tier | source_channel | region
        metric: retention_rate | expansion_rate | churn_rate | lifetime_value
        cohort_a: index of first cohort (0-based)
        cohort_b: index of second cohort (0-based)
    """
    try:
        dimension = request.args.get('dimension', 'signup_date')
        metric = request.args.get('metric', 'retention_rate')
        cohort_a = request.args.get('cohort_a', 0, type=int)
        cohort_b = request.args.get('cohort_b', 1, type=int)

        data = _generate_cohort_data(dimension=dimension, metric=metric)

        num_cohorts = len(data['cohorts'])
        if cohort_a < 0 or cohort_a >= num_cohorts or cohort_b < 0 or cohort_b >= num_cohorts:
            return jsonify({
                'success': False,
                'error': f'Cohort indices must be between 0 and {num_cohorts - 1}',
            }), 400

        curve_a = data['curves'][cohort_a]
        curve_b = data['curves'][cohort_b]

        deltas = []
        for pa, pb in zip(curve_a['points'], curve_b['points']):
            deltas.append({
                'period': pa['period'],
                'label': pa['label'],
                'value_a': pa['value'],
                'value_b': pb['value'],
                'delta': round(pa['value'] - pb['value'], 1),
            })

        avg_a = round(sum(p['value'] for p in curve_a['points']) / len(curve_a['points']), 1)
        avg_b = round(sum(p['value'] for p in curve_b['points']) / len(curve_b['points']), 1)

        return jsonify({
            'success': True,
            'data': {
                'cohort_a': curve_a,
                'cohort_b': curve_b,
                'deltas': deltas,
                'avg_a': avg_a,
                'avg_b': avg_b,
                'winner': curve_a['cohort'] if avg_a >= avg_b else curve_b['cohort'],
            },
        })

    except Exception as e:
        logger.error(f"Cohort comparison failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# ===========================================================================
# Segment Performance
# ===========================================================================

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

METRIC_BASELINES = {
    'mrr': 4200,
    'nrr': 112,
    'churn_rate': 4.5,
    'expansion_rate': 18,
    'csat': 4.2,
}

METRIC_HIGHER_IS_BETTER = {
    'mrr': True,
    'nrr': True,
    'churn_rate': False,
    'expansion_rate': True,
    'csat': True,
}

METRIC_SPREADS = {
    'mrr': 0.45,
    'nrr': 0.08,
    'churn_rate': 0.5,
    'expansion_rate': 0.35,
    'csat': 0.12,
}

DEMO_ACCOUNTS = [
    'Acme Corp', 'TechFlow Inc', 'DataPulse', 'CloudNova', 'BrightPath',
    'NexGen Solutions', 'Quantum Labs', 'PeakVenture', 'SwiftOps', 'CoreStack',
    'Luminary AI', 'Meridian Systems', 'TrueScale', 'VeloCity', 'ArcLight',
]


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
                drift = (i - 2.5) * 0.02 * base
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
