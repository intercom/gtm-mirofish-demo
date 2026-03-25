"""
Revenue Analytics API
Serves customer revenue data for treemap and analytics visualizations.
Always returns demo data — no LLM key required.
"""

from flask import Blueprint, jsonify, request

revenue_bp = Blueprint('revenue', __name__, url_prefix='/api/v1/revenue')

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
