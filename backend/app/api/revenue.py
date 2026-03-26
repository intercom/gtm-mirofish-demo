"""
Revenue Analytics API — customer revenue data and cohort retention.
All endpoints return deterministic demo data so the dashboard works without external dependencies.
"""

import hashlib
from flask import Blueprint, jsonify, request

revenue_bp = Blueprint('revenue', __name__, url_prefix='/api/revenue')

DEMO_CUSTOMERS = [
    {"id": "c01", "name": "Meridian Health Systems", "mrr": 84500, "planTier": "Expert", "industry": "Healthcare", "segment": "Enterprise", "healthScore": "A", "seats": 1200, "churnRisk": "low"},
    {"id": "c02", "name": "NovaPay Technologies", "mrr": 67200, "planTier": "Expert", "industry": "Fintech", "segment": "Enterprise", "healthScore": "A", "seats": 980, "churnRisk": "low"},
    {"id": "c03", "name": "CloudCart Commerce", "mrr": 52800, "planTier": "Expert", "industry": "E-commerce", "segment": "Enterprise", "healthScore": "B", "seats": 750, "churnRisk": "low"},
    {"id": "c04", "name": "Vantage Analytics", "mrr": 48300, "planTier": "Expert", "industry": "SaaS", "segment": "Enterprise", "healthScore": "A", "seats": 620, "churnRisk": "low"},
    {"id": "c05", "name": "TrustBank Financial", "mrr": 41900, "planTier": "Expert", "industry": "Fintech", "segment": "Enterprise", "healthScore": "B", "seats": 540, "churnRisk": "medium"},
    {"id": "c06", "name": "Apex Logistics", "mrr": 38100, "planTier": "Advanced", "industry": "Logistics", "segment": "Mid-Market", "healthScore": "A", "seats": 410, "churnRisk": "low"},
    {"id": "c07", "name": "PulseMedia Group", "mrr": 34600, "planTier": "Advanced", "industry": "Media", "segment": "Mid-Market", "healthScore": "B", "seats": 380, "churnRisk": "low"},
    {"id": "c08", "name": "Greenline Insurance", "mrr": 31200, "planTier": "Advanced", "industry": "Fintech", "segment": "Mid-Market", "healthScore": "A", "seats": 350, "churnRisk": "low"},
    {"id": "c09", "name": "DataForge Solutions", "mrr": 28500, "planTier": "Advanced", "industry": "SaaS", "segment": "Mid-Market", "healthScore": "B", "seats": 300, "churnRisk": "medium"},
    {"id": "c10", "name": "UrbanShift Retail", "mrr": 25400, "planTier": "Advanced", "industry": "E-commerce", "segment": "Mid-Market", "healthScore": "C", "seats": 280, "churnRisk": "medium"},
    {"id": "c11", "name": "MedCore Diagnostics", "mrr": 22100, "planTier": "Advanced", "industry": "Healthcare", "segment": "Mid-Market", "healthScore": "A", "seats": 250, "churnRisk": "low"},
    {"id": "c12", "name": "Streamline HR", "mrr": 19800, "planTier": "Advanced", "industry": "SaaS", "segment": "Mid-Market", "healthScore": "B", "seats": 220, "churnRisk": "low"},
    {"id": "c13", "name": "ByteScale Cloud", "mrr": 17500, "planTier": "Advanced", "industry": "SaaS", "segment": "Mid-Market", "healthScore": "C", "seats": 190, "churnRisk": "medium"},
    {"id": "c14", "name": "QuickShip Express", "mrr": 15200, "planTier": "Advanced", "industry": "Logistics", "segment": "Mid-Market", "healthScore": "B", "seats": 160, "churnRisk": "low"},
    {"id": "c15", "name": "FreshCart Grocery", "mrr": 13800, "planTier": "Essential", "industry": "E-commerce", "segment": "SMB", "healthScore": "B", "seats": 140, "churnRisk": "medium"},
    {"id": "c16", "name": "PixelForge Studios", "mrr": 12100, "planTier": "Essential", "industry": "Media", "segment": "SMB", "healthScore": "A", "seats": 120, "churnRisk": "low"},
    {"id": "c17", "name": "ClearView Optics", "mrr": 10500, "planTier": "Essential", "industry": "Healthcare", "segment": "SMB", "healthScore": "C", "seats": 95, "churnRisk": "medium"},
    {"id": "c18", "name": "LedgerPro Accounting", "mrr": 8900, "planTier": "Essential", "industry": "Fintech", "segment": "SMB", "healthScore": "B", "seats": 80, "churnRisk": "low"},
    {"id": "c19", "name": "NimbusNet Hosting", "mrr": 7600, "planTier": "Essential", "industry": "SaaS", "segment": "SMB", "healthScore": "D", "seats": 65, "churnRisk": "high"},
    {"id": "c20", "name": "BrightPath Education", "mrr": 6400, "planTier": "Essential", "industry": "Media", "segment": "SMB", "healthScore": "B", "seats": 55, "churnRisk": "low"},
    {"id": "c21", "name": "TrackPoint Delivery", "mrr": 5200, "planTier": "Essential", "industry": "Logistics", "segment": "SMB", "healthScore": "C", "seats": 48, "churnRisk": "medium"},
    {"id": "c22", "name": "VitalCare Clinics", "mrr": 4500, "planTier": "Essential", "industry": "Healthcare", "segment": "SMB", "healthScore": "B", "seats": 40, "churnRisk": "low"},
    {"id": "c23", "name": "ShopSphere Online", "mrr": 3800, "planTier": "Essential", "industry": "E-commerce", "segment": "SMB", "healthScore": "C", "seats": 35, "churnRisk": "medium"},
    {"id": "c24", "name": "CodeBridge Dev Tools", "mrr": 3200, "planTier": "Essential", "industry": "SaaS", "segment": "SMB", "healthScore": "A", "seats": 28, "churnRisk": "low"},
    {"id": "c25", "name": "RapidRoute Freight", "mrr": 2700, "planTier": "Essential", "industry": "Logistics", "segment": "SMB", "healthScore": "D", "seats": 22, "churnRisk": "high"},
    {"id": "c26", "name": "WellSpring Therapy", "mrr": 2100, "planTier": "Essential", "industry": "Healthcare", "segment": "SMB", "healthScore": "B", "seats": 18, "churnRisk": "low"},
    {"id": "c27", "name": "CoinTrack Analytics", "mrr": 1800, "planTier": "Essential", "industry": "Fintech", "segment": "SMB", "healthScore": "C", "seats": 15, "churnRisk": "medium"},
    {"id": "c28", "name": "SnapContent Media", "mrr": 1400, "planTier": "Essential", "industry": "Media", "segment": "SMB", "healthScore": "B", "seats": 12, "churnRisk": "low"},
    {"id": "c29", "name": "TinyCart Marketplace", "mrr": 950, "planTier": "Essential", "industry": "E-commerce", "segment": "SMB", "healthScore": "D", "seats": 8, "churnRisk": "high"},
    {"id": "c30", "name": "FlexiBooks Startup", "mrr": 650, "planTier": "Essential", "industry": "SaaS", "segment": "SMB", "healthScore": "C", "seats": 5, "churnRisk": "medium"},
]

MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _seed_float(seed_str, low=0.0, high=1.0):
    """Deterministic pseudo-random float from a string seed."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return low + (h / 0xFFFFFFFF) * (high - low)


def _generate_cohort_retention(months=12):
    """Generate a realistic 12x12 cohort retention matrix.

    Each row is a signup cohort (month). Column 0 is always 100%.
    Later columns show retention with natural decay plus occasional expansion.
    Newer cohorts have fewer data points (None for future months).
    """
    current_month_index = 11  # December = most recent complete month

    cohorts = []
    for row in range(months):
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


@revenue_bp.route('/customers', methods=['GET'])
def get_customers():
    """Return customer revenue data for treemap visualization."""
    group_by = request.args.get('groupBy', 'industry')
    customers = DEMO_CUSTOMERS

    total_mrr = sum(c['mrr'] for c in customers)
    total_arr = total_mrr * 12

    return jsonify({
        'success': True,
        'data': {
            'customers': customers,
            'summary': {
                'totalMrr': total_mrr,
                'totalArr': total_arr,
                'customerCount': len(customers),
                'groupBy': group_by,
            },
        },
    })


@revenue_bp.route('/cohort', methods=['GET'])
def get_cohort_retention():
    """Return cohort retention matrix for heatmap visualization."""
    months = request.args.get('months', 12, type=int)
    months = max(1, min(12, months))
    data = _generate_cohort_retention(months)
    return jsonify(data)
