"""
Revenue Metrics API
Serves ARR trend data and revenue breakdowns for the GTM dashboard.
Provides demo/mock data when no external data source is configured.
"""

from flask import Blueprint, jsonify, request

revenue_bp = Blueprint('revenue', __name__, url_prefix='/api/v1/revenue')

DEMO_ARR_DATA = [
    {"month": "2025-01", "newBusiness": 80, "expansion": 10, "churn": 5},
    {"month": "2025-02", "newBusiness": 95, "expansion": 18, "churn": 8},
    {"month": "2025-03", "newBusiness": 120, "expansion": 30, "churn": 10},
    {"month": "2025-04", "newBusiness": 150, "expansion": 45, "churn": 12},
    {"month": "2025-05", "newBusiness": 185, "expansion": 60, "churn": 15},
    {"month": "2025-06", "newBusiness": 220, "expansion": 80, "churn": 18},
    {"month": "2025-07", "newBusiness": 260, "expansion": 105, "churn": 22},
    {"month": "2025-08", "newBusiness": 310, "expansion": 130, "churn": 28},
    {"month": "2025-09", "newBusiness": 365, "expansion": 160, "churn": 35},
    {"month": "2025-10", "newBusiness": 420, "expansion": 200, "churn": 40},
    {"month": "2025-11", "newBusiness": 490, "expansion": 245, "churn": 48},
    {"month": "2025-12", "newBusiness": 560, "expansion": 300, "churn": 55},
    {"month": "2026-01", "newBusiness": 640, "expansion": 360, "churn": 62},
    {"month": "2026-02", "newBusiness": 730, "expansion": 430, "churn": 72},
    {"month": "2026-03", "newBusiness": 830, "expansion": 510, "churn": 80},
]


@revenue_bp.route('/arr-trend', methods=['GET'])
def get_arr_trend():
    """Get ARR trend data broken down by new business, expansion, and churn.

    Query params:
        months (int): Number of months to return (default: all)
    """
    months = request.args.get('months', type=int)

    data = DEMO_ARR_DATA
    if months and months > 0:
        data = data[-months:]

    return jsonify({
        "success": True,
        "data": data,
    })
