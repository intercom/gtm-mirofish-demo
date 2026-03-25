"""
Reconciliation API routes
Provides discrepancy distribution data for revenue reconciliation analysis.
"""

from flask import jsonify

from . import reconciliation_bp
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.reconciliation')

# Pre-built demo data for discrepancy distribution histogram
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


@reconciliation_bp.route('/api/v1/reconciliation/discrepancy-distribution', methods=['GET'])
def get_discrepancy_distribution():
    """
    Get discrepancy distribution data for histogram visualization.

    Query params:
        simulation_id: optional simulation context

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
