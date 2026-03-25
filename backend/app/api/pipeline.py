"""
Pipeline Funnel API
Serves GTM pipeline funnel data for dashboard widgets.
Returns mock data when no simulation is active — always works in demo mode.
"""

from flask import Blueprint, jsonify

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/v1/pipeline')

MOCK_FUNNEL_STAGES = [
    {
        "name": "MQL",
        "count": 1284,
        "value": 6420000,
        "color": "#2068FF",
    },
    {
        "name": "SQL",
        "count": 514,
        "value": 3854000,
        "color": "#4D8AFF",
    },
    {
        "name": "Opportunity",
        "count": 308,
        "value": 2772000,
        "color": "#ff5600",
    },
    {
        "name": "Closed Won",
        "count": 108,
        "value": 1620000,
        "color": "#009900",
    },
]


def _compute_conversion_rates(stages):
    """Compute conversion rates between consecutive stages."""
    rates = []
    for i in range(len(stages) - 1):
        current = stages[i]["count"]
        next_count = stages[i + 1]["count"]
        rate = round((next_count / current) * 100, 1) if current else 0
        rates.append({
            "from": stages[i]["name"],
            "to": stages[i + 1]["name"],
            "rate": rate,
        })
    return rates


@pipeline_bp.route('/funnel', methods=['GET'])
def get_funnel():
    """Return current pipeline funnel snapshot with all stages and conversion rates."""
    stages = MOCK_FUNNEL_STAGES
    conversion_rates = _compute_conversion_rates(stages)

    return jsonify({
        "stages": stages,
        "conversion_rates": conversion_rates,
    })
