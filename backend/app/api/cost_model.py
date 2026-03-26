"""
Cost Model API
Optimization and scenario management for GTM campaign cost modeling.
"""

from flask import Blueprint, jsonify, request

cost_model_bp = Blueprint('cost_model', __name__, url_prefix='/api/v1/campaigns/cost-model')

# Default channel definitions used when no data is provided
DEFAULT_CHANNELS = [
    {'id': 'paid_search', 'name': 'Paid Search', 'budget': 25000, 'cpl': 85, 'conversionRate': 0.12},
    {'id': 'paid_social', 'name': 'Paid Social', 'budget': 20000, 'cpl': 65, 'conversionRate': 0.08},
    {'id': 'events', 'name': 'Events', 'budget': 30000, 'cpl': 150, 'conversionRate': 0.22},
    {'id': 'partner', 'name': 'Partner', 'budget': 15000, 'cpl': 45, 'conversionRate': 0.18},
    {'id': 'email', 'name': 'Email', 'budget': 5000, 'cpl': 12, 'conversionRate': 0.06},
    {'id': 'content_seo', 'name': 'Content / SEO', 'budget': 10000, 'cpl': 35, 'conversionRate': 0.10},
]

# Funnel stage conversion rates (lead → MQL → SQL → closed won)
DEFAULT_FUNNEL = {
    'leadToMql': 0.35,
    'mqlToSql': 0.40,
    'sqlToClose': 0.25,
    'avgDealSize': 42000,
}

# In-memory scenario store (demo-only; resets on restart)
_saved_scenarios = {}


def _compute_funnel(channels, funnel):
    """Compute full funnel metrics from channel inputs."""
    results = []
    total_budget = 0
    total_leads = 0
    total_mqls = 0
    total_sqls = 0
    total_closed = 0

    for ch in channels:
        budget = max(ch.get('budget', 0), 0)
        cpl = max(ch.get('cpl', 1), 1)
        conv = min(max(ch.get('conversionRate', 0), 0), 1)

        leads = budget / cpl
        mqls = leads * funnel['leadToMql'] * (1 + conv)
        sqls = mqls * funnel['mqlToSql']
        closed = sqls * funnel['sqlToClose']

        total_budget += budget
        total_leads += leads
        total_mqls += mqls
        total_sqls += sqls
        total_closed += closed

        results.append({
            'id': ch.get('id', ''),
            'name': ch.get('name', ''),
            'budget': round(budget, 2),
            'leads': round(leads, 1),
            'mqls': round(mqls, 1),
            'sqls': round(sqls, 1),
            'closed': round(closed, 2),
        })

    total_revenue = total_closed * funnel['avgDealSize']
    roi = ((total_revenue - total_budget) / total_budget * 100) if total_budget > 0 else 0

    return {
        'channels': results,
        'totals': {
            'budget': round(total_budget, 2),
            'leads': round(total_leads, 1),
            'mqls': round(total_mqls, 1),
            'sqls': round(total_sqls, 1),
            'closed': round(total_closed, 2),
            'revenue': round(total_revenue, 2),
            'roi': round(roi, 1),
        },
    }


def _optimize_allocation(total_budget, channels, funnel):
    """
    Greedy optimization: allocate budget proportionally to each channel's
    revenue-per-dollar efficiency, respecting a minimum 5% floor per channel.
    """
    min_pct = 0.05
    n = len(channels)
    floor = total_budget * min_pct

    efficiencies = []
    for ch in channels:
        cpl = max(ch.get('cpl', 1), 1)
        conv = min(max(ch.get('conversionRate', 0), 0), 1)
        leads_per_dollar = 1.0 / cpl
        mqls_per_lead = funnel['leadToMql'] * (1 + conv)
        revenue_per_dollar = (
            leads_per_dollar
            * mqls_per_lead
            * funnel['mqlToSql']
            * funnel['sqlToClose']
            * funnel['avgDealSize']
        )
        efficiencies.append(revenue_per_dollar)

    total_eff = sum(efficiencies) or 1
    remaining = total_budget - floor * n

    optimized = []
    for i, ch in enumerate(channels):
        share = floor + remaining * (efficiencies[i] / total_eff)
        optimized.append({
            **ch,
            'budget': round(share, 2),
        })

    return optimized


@cost_model_bp.route('/calculate', methods=['POST'])
def calculate():
    """Compute funnel predictions from channel inputs."""
    data = request.get_json() or {}
    channels = data.get('channels', DEFAULT_CHANNELS)
    funnel = {**DEFAULT_FUNNEL, **data.get('funnel', {})}
    result = _compute_funnel(channels, funnel)
    return jsonify({'success': True, 'data': result})


@cost_model_bp.route('/optimize', methods=['POST'])
def optimize():
    """Return optimized budget allocation for maximum ROI."""
    data = request.get_json() or {}
    channels = data.get('channels', DEFAULT_CHANNELS)
    funnel = {**DEFAULT_FUNNEL, **data.get('funnel', {})}
    total_budget = data.get('totalBudget')

    if total_budget is None:
        total_budget = sum(ch.get('budget', 0) for ch in channels)

    optimized_channels = _optimize_allocation(total_budget, channels, funnel)
    result = _compute_funnel(optimized_channels, funnel)
    return jsonify({'success': True, 'data': result})


@cost_model_bp.route('/defaults', methods=['GET'])
def defaults():
    """Return default channel and funnel configuration."""
    return jsonify({
        'success': True,
        'data': {
            'channels': DEFAULT_CHANNELS,
            'funnel': DEFAULT_FUNNEL,
        },
    })


@cost_model_bp.route('/scenarios', methods=['GET'])
def list_scenarios():
    """List saved cost model scenarios."""
    return jsonify({
        'success': True,
        'data': list(_saved_scenarios.values()),
    })


@cost_model_bp.route('/scenarios', methods=['POST'])
def save_scenario():
    """Save a named cost model scenario."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Scenario name is required'}), 400

    import time
    scenario_id = f"scen_{int(time.time() * 1000)}"
    scenario = {
        'id': scenario_id,
        'name': name,
        'channels': data.get('channels', []),
        'funnel': data.get('funnel', DEFAULT_FUNNEL),
        'createdAt': time.time(),
    }
    _saved_scenarios[scenario_id] = scenario
    return jsonify({'success': True, 'data': scenario}), 201


@cost_model_bp.route('/scenarios/<scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    """Delete a saved scenario."""
    if scenario_id in _saved_scenarios:
        del _saved_scenarios[scenario_id]
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Scenario not found'}), 404
