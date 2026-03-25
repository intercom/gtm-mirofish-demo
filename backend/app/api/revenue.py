"""
Revenue metrics API — cohort retention and revenue analytics.
All endpoints return deterministic demo data so the dashboard works without external dependencies.
"""

import hashlib
from flask import Blueprint, jsonify, request

revenue_bp = Blueprint('revenue', __name__, url_prefix='/api/revenue')

MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _seed_float(seed_str, low=0.0, high=1.0):
    """Deterministic pseudo-random float from a string seed."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return low + (h / 0xFFFFFFFF) * (high - low)


def _generate_cohort_retention(months=12):
    """Generate a realistic 12×12 cohort retention matrix.

    Each row is a signup cohort (month). Column 0 is always 100%.
    Later columns show retention with natural decay plus occasional expansion.
    Newer cohorts have fewer data points (None for future months).
    """
    current_month_index = 11  # December = most recent complete month

    cohorts = []
    for row in range(months):
        cohort_label = MONTH_LABELS[row]
        months_of_data = current_month_index - row + 1
        retention_row = []

        base_rate = 0.93 + _seed_float(f'base-{row}', -0.04, 0.04)

        for col in range(months):
            if col == 0:
                retention_row.append(100.0)
            elif col < months_of_data:
                decay = base_rate ** col
                noise = _seed_float(f'noise-{row}-{col}', -0.03, 0.03)
                expansion = _seed_float(f'expand-{row}-{col}', 0, 0.02) if col <= 3 else 0
                value = round((decay + noise + expansion) * 100, 1)
                value = max(40.0, min(120.0, value))
                retention_row.append(value)
            else:
                retention_row.append(None)

        cohorts.append(retention_row)

    row_averages = []
    for row in cohorts:
        vals = [v for v in row if v is not None]
        row_averages.append(round(sum(vals) / len(vals), 1) if vals else None)

    col_averages = []
    for col in range(months):
        vals = [cohorts[r][col] for r in range(months) if cohorts[r][col] is not None]
        col_averages.append(round(sum(vals) / len(vals), 1) if vals else None)

    return {
        'cohorts': MONTH_LABELS[:months],
        'months': [f'M{i}' for i in range(months)],
        'values': cohorts,
        'row_averages': row_averages,
        'column_averages': col_averages,
    }


@revenue_bp.route('/cohort', methods=['GET'])
def get_cohort_retention():
    """Return cohort retention matrix for heatmap visualization."""
    months = request.args.get('months', 12, type=int)
    months = max(1, min(12, months))
    data = _generate_cohort_retention(months)
    return jsonify(data)
