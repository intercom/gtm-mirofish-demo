"""
Revenue API Blueprint
Serves SaaS revenue analytics: metrics, customers, churn, expansion, summary, cohort data,
and ARR trend breakdowns for the GTM dashboard.
All endpoints work in demo/mock mode using the revenue data generator.
"""

from flask import Blueprint, jsonify, request

from ..services.revenue_data_generator import get_revenue_generator
from ..utils.logger import get_logger

logger = get_logger('mirofish.revenue')

revenue_bp = Blueprint('revenue', __name__, url_prefix='/api/revenue')

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


@revenue_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Monthly revenue metrics for last N months. Query: ?months=12"""
    try:
        months = request.args.get('months', 12, type=int)
        months = max(1, min(months, 24))
        gen = get_revenue_generator()
        return jsonify({"success": True, "data": gen.get_metrics(months)})
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@revenue_bp.route('/customers', methods=['GET'])
def get_customers():
    """Customer revenue list with sort/filter. Query: ?plan=Advanced&mrr_min=1000&sort_by=mrr&sort_order=desc&limit=50&offset=0"""
    try:
        gen = get_revenue_generator()
        data = gen.get_customers(
            plan=request.args.get('plan'),
            mrr_min=request.args.get('mrr_min', type=float),
            mrr_max=request.args.get('mrr_max', type=float),
            sort_by=request.args.get('sort_by', 'mrr'),
            sort_order=request.args.get('sort_order', 'desc'),
            limit=request.args.get('limit', 50, type=int),
            offset=request.args.get('offset', 0, type=int),
        )
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@revenue_bp.route('/churn', methods=['GET'])
def get_churn():
    """Churn events with date range and reason filters. Query: ?reason=competitor&date_from=2025-04-01&date_to=2026-03-01"""
    try:
        gen = get_revenue_generator()
        data = gen.get_churn_events(
            reason=request.args.get('reason'),
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
        )
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Error fetching churn events: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@revenue_bp.route('/expansion', methods=['GET'])
def get_expansion():
    """Expansion events with type filter. Query: ?type=upsell&date_from=2025-04-01&date_to=2026-03-01"""
    try:
        gen = get_revenue_generator()
        data = gen.get_expansion_events(
            expansion_type=request.args.get('type'),
            date_from=request.args.get('date_from'),
            date_to=request.args.get('date_to'),
        )
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Error fetching expansion events: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@revenue_bp.route('/summary', methods=['GET'])
def get_summary():
    """Top-level KPIs: current MRR, ARR, growth rate, net retention, gross retention, LTV, CAC."""
    try:
        gen = get_revenue_generator()
        return jsonify({"success": True, "data": gen.get_summary()})
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@revenue_bp.route('/cohort', methods=['GET'])
def get_cohort():
    """Cohort retention analysis by signup month."""
    try:
        gen = get_revenue_generator()
        return jsonify({"success": True, "data": gen.get_cohort_data()})
    except Exception as e:
        logger.error(f"Error fetching cohort data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
