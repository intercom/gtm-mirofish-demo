"""
Analytics API routes — cohort analysis, attribution, segment performance.
"""

import hashlib
import math
from flask import Blueprint, request, jsonify

from ..utils.logger import get_logger

logger = get_logger('mirofish.api.analytics')

analytics_bp = Blueprint('analytics', __name__)


def _seed_float(seed_str, min_val=0.0, max_val=1.0):
    """Deterministic pseudo-random float from a seed string."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    normalized = (h % 10000) / 10000.0
    return min_val + normalized * (max_val - min_val)


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

    # Base decay curve varies by metric
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

    # Compute summary stats
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

    # Color scale hints for the frontend
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


@analytics_bp.route('/api/v1/analytics/cohorts', methods=['GET'])
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


@analytics_bp.route('/api/v1/analytics/cohorts/compare', methods=['GET'])
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
