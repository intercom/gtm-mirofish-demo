"""
Salesforce CRM API Blueprint.
Serves paginated, filterable demo CRM data (accounts, opportunities,
contacts, leads) generated deterministically for the GTM demo.
"""

import traceback
from typing import List, Any

from flask import Blueprint, jsonify, request

from ..services.sfdc_data_generator import get_data
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.salesforce')

salesforce_bp = Blueprint('salesforce', __name__, url_prefix='/api/v1/salesforce')


def _paginate(items: List[Any], page: int, per_page: int) -> dict:
    """Apply pagination to a list and return the standard envelope."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "data": [item.to_dict() for item in items[start:end]],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@salesforce_bp.route('/accounts', methods=['GET'])
def list_accounts():
    """List accounts with pagination and optional filters."""
    try:
        data = get_data()
        accounts = list(data["accounts"])

        industry = request.args.get('industry')
        if industry:
            accounts = [a for a in accounts if a.industry.lower() == industry.lower()]

        tier = request.args.get('tier')
        if tier:
            accounts = [a for a in accounts if a.plan_tier.lower() == tier.lower()]

        region = request.args.get('region')
        if region:
            accounts = [a for a in accounts if a.region.lower() == region.lower()]

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        return jsonify(_paginate(accounts, page, per_page))
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@salesforce_bp.route('/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    """Get a single account with its related contacts and opportunities."""
    try:
        data = get_data()
        account = next((a for a in data["accounts"] if a.id == account_id), None)
        if not account:
            return jsonify({"success": False, "error": f"Account {account_id} not found"}), 404

        contacts = [c.to_dict() for c in data["contacts"] if c.account_id == account_id]
        opportunities = [o.to_dict() for o in data["opportunities"] if o.account_id == account_id]

        result = account.to_dict()
        result["contacts"] = contacts
        result["opportunities"] = opportunities
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@salesforce_bp.route('/opportunities', methods=['GET'])
def list_opportunities():
    """List opportunities with pagination and optional filters."""
    try:
        data = get_data()
        opps = list(data["opportunities"])

        stage = request.args.get('stage')
        if stage:
            opps = [o for o in opps if o.stage.lower() == stage.lower()]

        account_id = request.args.get('account_id')
        if account_id:
            opps = [o for o in opps if o.account_id == account_id]

        close_after = request.args.get('close_after')
        if close_after:
            opps = [o for o in opps if o.close_date >= close_after]

        close_before = request.args.get('close_before')
        if close_before:
            opps = [o for o in opps if o.close_date <= close_before]

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        return jsonify(_paginate(opps, page, per_page))
    except Exception as e:
        logger.error(f"Error listing opportunities: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@salesforce_bp.route('/contacts', methods=['GET'])
def list_contacts():
    """List contacts with pagination and optional account filter."""
    try:
        data = get_data()
        contacts = list(data["contacts"])

        account_id = request.args.get('account_id')
        if account_id:
            contacts = [c for c in contacts if c.account_id == account_id]

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        return jsonify(_paginate(contacts, page, per_page))
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@salesforce_bp.route('/leads', methods=['GET'])
def list_leads():
    """List leads with pagination and optional filters."""
    try:
        data = get_data()
        leads = list(data["leads"])

        status = request.args.get('status')
        if status:
            leads = [l for l in leads if l.status.lower() == status.lower()]

        source = request.args.get('source')
        if source:
            leads = [l for l in leads if l.source.lower() == source.lower()]

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        return jsonify(_paginate(leads, page, per_page))
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@salesforce_bp.route('/stats', methods=['GET'])
def get_stats():
    """Aggregate stats across all Salesforce data."""
    try:
        data = get_data()
        accounts = data["accounts"]
        opportunities = data["opportunities"]
        leads = data["leads"]

        total_arr = sum(a.arr for a in accounts)
        avg_health = sum(a.health_score for a in accounts) / len(accounts) if accounts else 0

        open_stages = {"Prospecting", "Discovery", "Proposal", "Negotiation"}
        pipeline_value = sum(o.amount for o in opportunities if o.stage in open_stages)

        converted = sum(1 for l in leads if l.status == "Converted")
        total_non_new = sum(1 for l in leads if l.status != "New")
        lead_conversion_rate = (converted / total_non_new * 100) if total_non_new else 0

        stage_counts = {}
        for o in opportunities:
            stage_counts[o.stage] = stage_counts.get(o.stage, 0) + 1

        tier_counts = {}
        for a in accounts:
            tier_counts[a.plan_tier] = tier_counts.get(a.plan_tier, 0) + 1

        return jsonify({
            "success": True,
            "data": {
                "total_accounts": len(accounts),
                "total_arr": round(total_arr, 2),
                "avg_health_score": round(avg_health, 1),
                "pipeline_value": round(pipeline_value, 2),
                "lead_conversion_rate": round(lead_conversion_rate, 1),
                "total_opportunities": len(opportunities),
                "total_contacts": len(data["contacts"]),
                "total_leads": len(leads),
                "opportunities_by_stage": stage_counts,
                "accounts_by_tier": tier_counts,
            },
        })
    except Exception as e:
        logger.error(f"Error computing stats: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500
