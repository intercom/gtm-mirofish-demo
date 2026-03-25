"""
CPQ (Configure-Price-Quote) API
Serves Intercom product catalog, quotes, and pricing analytics.
Works in demo/mock mode when no LLM key is configured.
"""

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.cpq')

cpq_bp = Blueprint('cpq', __name__, url_prefix='/api/v1/cpq')

PRODUCTS = [
    {
        "id": "prod_essential",
        "name": "Essential",
        "family": "Support",
        "description": "Foundational customer support with shared inbox, ticketing, and basic automation for small teams.",
        "unit_price": 29,
        "billing_frequency": "per seat/month",
        "popular": False,
        "features": ["Shared Inbox", "Basic Ticketing", "Help Center", "Email Support"],
    },
    {
        "id": "prod_advanced",
        "name": "Advanced",
        "family": "Support",
        "description": "Full-featured support suite with Fin AI agent, custom bots, and advanced workflows for growing teams.",
        "unit_price": 85,
        "billing_frequency": "per seat/month",
        "popular": True,
        "features": ["Fin AI Agent", "Custom Bots", "Workflows", "Team Inbox", "SLA Rules"],
    },
    {
        "id": "prod_expert",
        "name": "Expert",
        "family": "Support",
        "description": "Enterprise-grade support with workload management, SSO/SAML, and dedicated success manager.",
        "unit_price": 132,
        "billing_frequency": "per seat/month",
        "popular": False,
        "features": ["Workload Management", "SSO/SAML", "Custom Roles", "Dedicated CSM", "Priority Support"],
    },
    {
        "id": "prod_fin_ai",
        "name": "Fin AI Agent",
        "family": "AI & Automation",
        "description": "AI-powered resolution engine that autonomously handles customer questions using your help center content.",
        "unit_price": 0.99,
        "billing_frequency": "per resolution",
        "popular": False,
        "features": ["Auto-Resolution", "Multi-Language", "Content Suggestions", "Handoff to Human"],
    },
    {
        "id": "prod_proactive",
        "name": "Proactive Support",
        "family": "AI & Automation",
        "description": "Automated outbound messaging with targeted banners, tooltips, and in-app surveys triggered by user behavior.",
        "unit_price": 49,
        "billing_frequency": "per month",
        "popular": False,
        "features": ["Targeted Messages", "Product Tours", "Banners", "Behavioral Triggers"],
    },
    {
        "id": "prod_messenger",
        "name": "Intercom Messenger",
        "family": "Channels",
        "description": "Customizable in-app messenger with real-time chat, conversation history, and rich media support.",
        "unit_price": 0,
        "billing_frequency": "included",
        "popular": False,
        "features": ["Real-time Chat", "Conversation History", "Rich Media", "Custom Branding"],
    },
    {
        "id": "prod_omnichannel",
        "name": "Omnichannel",
        "family": "Channels",
        "description": "Unified inbox across email, chat, social, and SMS so your team can manage every conversation in one place.",
        "unit_price": 39,
        "billing_frequency": "per seat/month",
        "popular": False,
        "features": ["Email", "SMS", "WhatsApp", "Social Media", "Unified Inbox"],
    },
    {
        "id": "prod_analytics",
        "name": "Analytics & Reporting",
        "family": "Platform",
        "description": "Custom dashboards, CSAT/NPS tracking, team performance metrics, and Fin AI usage insights.",
        "unit_price": 49,
        "billing_frequency": "per month",
        "popular": False,
        "features": ["Custom Dashboards", "CSAT Tracking", "Team Metrics", "Fin Reports"],
    },
]


@cpq_bp.route('/products', methods=['GET'])
def list_products():
    """Return the product catalog, optionally filtered by family or search query."""
    family = request.args.get('family')
    search = request.args.get('search', '').lower()

    results = PRODUCTS
    if family:
        results = [p for p in results if p['family'] == family]
    if search:
        results = [
            p for p in results
            if search in p['name'].lower()
            or search in p['description'].lower()
            or search in p['family'].lower()
        ]

    families = sorted(set(p['family'] for p in PRODUCTS))
    return jsonify({"products": results, "families": families})


@cpq_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Return a single product by ID."""
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({"error": f"Product not found: {product_id}"}), 404
    return jsonify(product)
