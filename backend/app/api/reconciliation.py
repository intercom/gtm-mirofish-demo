"""
Reconciliation API Blueprint
Endpoints for MRR reconciliation trend data (Salesforce vs Billing vs Snowflake).
"""

import random
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

reconciliation_bp = Blueprint('reconciliation', __name__, url_prefix='/api/reconciliation')


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
