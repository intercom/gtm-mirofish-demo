"""
CPQ (Configure Price Quote) API Blueprint
Serves Intercom product catalog, quotes, and pricing analytics.
Works in demo/mock mode with deterministic seed data when no external
data source is configured.
"""

import hashlib
import math
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger('mirofish.api.cpq')

cpq_bp = Blueprint('cpq', __name__, url_prefix='/api/v1/cpq')

# ---------------------------------------------------------------------------
# Demo data helpers
# ---------------------------------------------------------------------------

PRODUCTS = [
    {
        'id': 'prod-001',
        'name': 'Essential',
        'code': 'INTRCOM-ESS',
        'family': 'Platform',
        'unit_price': 39.00,
        'billing_frequency': 'monthly',
        'description': 'Core customer messaging platform for startups and small businesses.',
        'is_active': True,
        'popular': False,
        'features': ['Shared Inbox', 'Basic Ticketing', 'Help Center', 'Email Support'],
    },
    {
        'id': 'prod-002',
        'name': 'Advanced',
        'code': 'INTRCOM-ADV',
        'family': 'Platform',
        'unit_price': 99.00,
        'billing_frequency': 'monthly',
        'description': 'Automation and AI features for growing support teams.',
        'is_active': True,
        'popular': True,
        'features': ['Fin AI Agent', 'Custom Bots', 'Workflows', 'Team Inbox', 'SLA Rules'],
    },
    {
        'id': 'prod-003',
        'name': 'Expert',
        'code': 'INTRCOM-EXP',
        'family': 'Platform',
        'unit_price': 139.00,
        'billing_frequency': 'monthly',
        'description': 'Enterprise-grade collaboration, security, and reporting.',
        'is_active': True,
        'popular': False,
        'features': ['Workload Management', 'SSO/SAML', 'Custom Roles', 'Dedicated CSM', 'Priority Support'],
    },
    {
        'id': 'prod-004',
        'name': 'Fin AI Agent',
        'code': 'INTRCOM-FIN',
        'family': 'AI',
        'unit_price': 0.99,
        'billing_frequency': 'per_resolution',
        'description': 'AI-powered customer support agent that resolves issues autonomously.',
        'is_active': True,
        'popular': False,
        'features': ['Auto-Resolution', 'Multi-Language', 'Content Suggestions', 'Handoff to Human'],
    },
    {
        'id': 'prod-005',
        'name': 'Proactive Support',
        'code': 'INTRCOM-PRO',
        'family': 'Add-on',
        'unit_price': 499.00,
        'billing_frequency': 'monthly',
        'description': 'Targeted messaging and onboarding tours to reduce inbound volume.',
        'is_active': True,
        'popular': False,
        'features': ['Targeted Messages', 'Product Tours', 'Banners', 'Behavioral Triggers'],
    },
    {
        'id': 'prod-006',
        'name': 'Help Center',
        'code': 'INTRCOM-HC',
        'family': 'Add-on',
        'unit_price': 0.00,
        'billing_frequency': 'monthly',
        'description': 'Self-serve knowledge base included with all plans.',
        'is_active': True,
        'popular': False,
        'features': ['Knowledge Base', 'Article Search', 'Custom Branding'],
    },
]

_PRODUCT_MAP = {p['id']: p for p in PRODUCTS}

_ACCOUNT_NAMES = [
    'Acme Corp', 'TechFlow Inc', 'DataVault Systems', 'Cloudbridge IO',
    'NovaPay', 'FinStar Analytics', 'ShipRight Logistics', 'Pixel Labs',
    'GreenGrid Energy', 'MedConnect Health', 'EduPath Learning',
    'RetailSync', 'SafeNet Cyber', 'BuildRight Construction', 'UrbanBite',
    'StreamLine Media', 'AgriTech Solutions', 'TravelNest', 'InsurePlus',
    'LegalEdge',
]

_STATUSES = ['Draft', 'Review', 'Approved', 'Rejected']
_STATUS_WEIGHTS = [0.30, 0.20, 0.30, 0.20]


def _seed_int(seed_str: str, mod: int) -> int:
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    return h % mod


def _seed_float(seed_str: str) -> float:
    return (_seed_int(seed_str, 10000)) / 10000.0


def _pick_status(seed_str: str) -> str:
    val = _seed_float(seed_str)
    cumulative = 0.0
    for status, weight in zip(_STATUSES, _STATUS_WEIGHTS):
        cumulative += weight
        if val < cumulative:
            return status
    return _STATUSES[-1]


def _generate_quotes():
    """Generate 20 deterministic demo quotes with line items."""
    quotes = []
    base_date = datetime(2026, 1, 15)

    for i in range(20):
        qid = f'Q-2026-{1001 + i}'
        seed = f'quote-{i}'
        account = _ACCOUNT_NAMES[i % len(_ACCOUNT_NAMES)]
        status = _pick_status(seed)
        created = base_date + timedelta(days=_seed_int(f'{seed}-date', 60))
        expiry = created + timedelta(days=30)

        num_lines = 2 + _seed_int(f'{seed}-lines', 4)
        lines = []
        total_price = 0.0
        total_list = 0.0

        used_products = set()
        for li in range(num_lines):
            lseed = f'{seed}-line-{li}'
            prod_idx = _seed_int(lseed, len(PRODUCTS))
            while PRODUCTS[prod_idx]['id'] in used_products and len(used_products) < len(PRODUCTS):
                prod_idx = (prod_idx + 1) % len(PRODUCTS)
            used_products.add(PRODUCTS[prod_idx]['id'])
            product = PRODUCTS[prod_idx]

            if product['billing_frequency'] == 'per_resolution':
                quantity = 500 + _seed_int(f'{lseed}-qty', 9500)
            else:
                quantity = 5 + _seed_int(f'{lseed}-qty', 496)

            discount_pct = round(_seed_float(f'{lseed}-disc') * 25, 1)
            term_months = 12 if _seed_float(f'{lseed}-term') < 0.6 else 24

            list_subtotal = product['unit_price'] * quantity * term_months
            net = round(list_subtotal * (1 - discount_pct / 100), 2)
            total_list += list_subtotal
            total_price += net

            lines.append({
                'id': f'{qid}-LI-{li + 1}',
                'quote_id': qid,
                'product_id': product['id'],
                'product_name': product['name'],
                'quantity': quantity,
                'list_price': product['unit_price'],
                'discount_pct': discount_pct,
                'net_price': net,
                'subscription_term_months': term_months,
            })

        discount_pct_overall = round(
            (1 - total_price / total_list) * 100, 1
        ) if total_list > 0 else 0.0

        reject_reason = None
        if status == 'Rejected':
            reasons = [
                'Discount exceeds approval threshold',
                'Budget constraints — defer to next quarter',
                'Competitor offer accepted',
                'Non-standard terms require legal review',
            ]
            reject_reason = reasons[_seed_int(f'{seed}-reason', len(reasons))]

        quotes.append({
            'id': qid,
            'opportunity_id': f'OPP-{2001 + i}',
            'account_name': account,
            'status': status,
            'total_price': round(total_price, 2),
            'discount_pct': discount_pct_overall,
            'created_date': created.strftime('%Y-%m-%d'),
            'expiry_date': expiry.strftime('%Y-%m-%d'),
            'line_items': lines,
            'reject_reason': reject_reason,
        })

    return quotes


_quotes_cache = None


def _get_quotes():
    global _quotes_cache
    if _quotes_cache is None:
        _quotes_cache = _generate_quotes()
    return _quotes_cache


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@cpq_bp.route('/products', methods=['GET'])
def list_products():
    """List all products, optionally filtered by family."""
    family = request.args.get('family')
    results = PRODUCTS
    if family:
        results = [p for p in results if p['family'].lower() == family.lower()]
    families = sorted(set(p['family'] for p in PRODUCTS))
    return jsonify({'products': results, 'families': families, 'total': len(results)})


@cpq_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Return a single product by ID."""
    product = _PRODUCT_MAP.get(product_id)
    if not product:
        return jsonify({'error': f'Product not found: {product_id}'}), 404
    return jsonify(product)


@cpq_bp.route('/quotes', methods=['GET'])
def list_quotes():
    """List quotes with optional status filter and pagination."""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    page_size = min(max(page_size, 1), 50)

    quotes = _get_quotes()

    if status:
        quotes = [q for q in quotes if q['status'].lower() == status.lower()]

    total = len(quotes)
    total_pages = max(1, math.ceil(total / page_size))
    page = min(max(page, 1), total_pages)
    start = (page - 1) * page_size
    page_items = quotes[start:start + page_size]

    summaries = []
    for q in page_items:
        summaries.append({
            'id': q['id'],
            'opportunity_id': q['opportunity_id'],
            'account_name': q['account_name'],
            'status': q['status'],
            'total_price': q['total_price'],
            'discount_pct': q['discount_pct'],
            'created_date': q['created_date'],
            'expiry_date': q['expiry_date'],
            'product_count': len(q['line_items']),
        })

    return jsonify({
        'quotes': summaries,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    })


@cpq_bp.route('/quotes/<quote_id>', methods=['GET'])
def get_quote(quote_id):
    """Get a single quote with all line items and calculated totals."""
    for q in _get_quotes():
        if q['id'] == quote_id:
            subtotal = sum(
                li['list_price'] * li['quantity'] * li['subscription_term_months']
                for li in q['line_items']
            )
            return jsonify({
                **q,
                'subtotal': round(subtotal, 2),
                'total_discount_amount': round(subtotal - q['total_price'], 2),
            })
    return jsonify({'error': f'Quote {quote_id} not found'}), 404


@cpq_bp.route('/quotes/<quote_id>/pdf-preview', methods=['GET'])
def quote_pdf_preview(quote_id):
    """Return an HTML representation of a quote suitable for PDF rendering."""
    quote = None
    for q in _get_quotes():
        if q['id'] == quote_id:
            quote = q
            break

    if not quote:
        return jsonify({'error': f'Quote {quote_id} not found'}), 404

    subtotal = sum(
        li['list_price'] * li['quantity'] * li['subscription_term_months']
        for li in quote['line_items']
    )
    discount_amount = subtotal - quote['total_price']

    rows = ''
    for li in quote['line_items']:
        line_list = li['list_price'] * li['quantity'] * li['subscription_term_months']
        rows += (
            f"<tr>"
            f"<td>{li['product_name']}</td>"
            f"<td style='text-align:right'>{li['quantity']}</td>"
            f"<td style='text-align:right'>${li['list_price']:,.2f}</td>"
            f"<td style='text-align:right'>{li['discount_pct']}%</td>"
            f"<td style='text-align:right'>{li['subscription_term_months']}mo</td>"
            f"<td style='text-align:right'>${line_list:,.2f}</td>"
            f"<td style='text-align:right'>${li['net_price']:,.2f}</td>"
            f"</tr>"
        )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Quote {quote['id']}</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;margin:40px;color:#1a1a1a}}
h1{{color:#050505;font-size:24px}}
.meta{{color:#555;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{padding:8px 12px;border-bottom:1px solid #e5e5e5;text-align:left}}
th{{background:#f5f5f5;font-weight:600}}
.totals{{margin-top:16px;text-align:right}}
.totals .total{{font-size:20px;font-weight:700;color:#2068FF}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;font-weight:600}}
.badge-Draft{{background:#e5e7eb;color:#374151}}
.badge-Review{{background:#fef3c7;color:#92400e}}
.badge-Approved{{background:#d1fae5;color:#065f46}}
.badge-Rejected{{background:#fee2e2;color:#991b1b}}
</style></head>
<body>
<h1>Quote {quote['id']}</h1>
<div class="meta">
  <strong>Account:</strong> {quote['account_name']}<br>
  <strong>Status:</strong> <span class="badge badge-{quote['status']}">{quote['status']}</span><br>
  <strong>Created:</strong> {quote['created_date']} &nbsp;|&nbsp;
  <strong>Expires:</strong> {quote['expiry_date']}
</div>
<table>
<thead><tr>
  <th>Product</th><th style="text-align:right">Qty</th>
  <th style="text-align:right">Unit Price</th><th style="text-align:right">Discount</th>
  <th style="text-align:right">Term</th><th style="text-align:right">List Total</th>
  <th style="text-align:right">Net Price</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="totals">
  <div>Subtotal: ${subtotal:,.2f}</div>
  <div>Discount: -${discount_amount:,.2f}</div>
  <div class="total">Total: ${quote['total_price']:,.2f}</div>
</div>
</body></html>"""

    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@cpq_bp.route('/quotes/<quote_id>/approve', methods=['POST'])
def approve_quote(quote_id):
    """Transition a quote from Review to Approved."""
    for q in _get_quotes():
        if q['id'] == quote_id:
            if q['status'] not in ('Review', 'Draft'):
                return jsonify({
                    'error': f"Cannot approve a quote with status '{q['status']}'"
                }), 400
            q['status'] = 'Approved'
            q['reject_reason'] = None
            logger.info(f'Quote {quote_id} approved')
            return jsonify({'id': quote_id, 'status': 'Approved'})
    return jsonify({'error': f'Quote {quote_id} not found'}), 404


@cpq_bp.route('/quotes/<quote_id>/reject', methods=['POST'])
def reject_quote(quote_id):
    """Transition a quote to Rejected with a reason."""
    data = request.get_json(silent=True) or {}
    reason = data.get('reason', '')

    for q in _get_quotes():
        if q['id'] == quote_id:
            if q['status'] == 'Rejected':
                return jsonify({
                    'error': 'Quote is already rejected'
                }), 400
            q['status'] = 'Rejected'
            q['reject_reason'] = reason or 'No reason provided'
            logger.info(f'Quote {quote_id} rejected: {q["reject_reason"]}')
            return jsonify({
                'id': quote_id,
                'status': 'Rejected',
                'reject_reason': q['reject_reason'],
            })
    return jsonify({'error': f'Quote {quote_id} not found'}), 404


@cpq_bp.route('/stats', methods=['GET'])
def cpq_stats():
    """Aggregate CPQ statistics."""
    quotes = _get_quotes()
    total = len(quotes)

    approved = sum(1 for q in quotes if q['status'] == 'Approved')
    rejected = sum(1 for q in quotes if q['status'] == 'Rejected')
    decided = approved + rejected

    avg_discount = (
        sum(q['discount_pct'] for q in quotes) / total if total else 0.0
    )
    avg_deal_size = (
        sum(q['total_price'] for q in quotes) / total if total else 0.0
    )

    revenue_by_product = {}
    for q in quotes:
        for li in q['line_items']:
            name = li['product_name']
            revenue_by_product[name] = revenue_by_product.get(name, 0.0) + li['net_price']
    revenue_by_product = {k: round(v, 2) for k, v in revenue_by_product.items()}

    status_counts = {}
    for q in quotes:
        status_counts[q['status']] = status_counts.get(q['status'], 0) + 1

    return jsonify({
        'total_quotes': total,
        'approval_rate': round(approved / decided * 100, 1) if decided else 0.0,
        'avg_discount': round(avg_discount, 1),
        'avg_deal_size': round(avg_deal_size, 2),
        'total_pipeline_value': round(sum(q['total_price'] for q in quotes), 2),
        'revenue_by_product': revenue_by_product,
        'status_counts': status_counts,
    })
