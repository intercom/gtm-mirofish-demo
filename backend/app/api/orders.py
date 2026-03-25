"""
Order-to-Cash API Blueprint
Endpoints for order lifecycle, provisioning status, and billing records.
Generates deterministic demo data when no external data source is configured.
"""

import hashlib
import random
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

orders_bp = Blueprint('orders', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
# Demo data generation (deterministic, cached)
# ---------------------------------------------------------------------------

_cache = {}

PROVISIONING_STEPS = [
    'license_validation',
    'entitlement_setup',
    'workspace_config',
    'billing_setup',
    'activation',
]

ACCOUNT_NAMES = [
    'Acme Corp', 'TechFlow Inc', 'Meridian Health', 'Pinnacle Solutions',
    'Cascade Media', 'Vertex Analytics', 'Horizon Labs', 'Atlas Logistics',
    'Summit Financial', 'Polaris Education', 'NovaTech', 'BrightPath',
    'CloudNine SaaS', 'DataVault', 'StreamLine Ops', 'ClearView HR',
    'Apex Digital', 'BlueSky Retail', 'CoreStack', 'Dynamo Energy',
]

PRODUCT_CATALOG = [
    {'sku': 'INT-SUPPORT-PRO', 'name': 'Intercom Support Pro', 'unit_price': 2400},
    {'sku': 'INT-ENGAGE-STD', 'name': 'Intercom Engage Standard', 'unit_price': 1800},
    {'sku': 'INT-CONVERT-ENT', 'name': 'Intercom Convert Enterprise', 'unit_price': 4200},
    {'sku': 'INT-PLATFORM-BAS', 'name': 'Intercom Platform Basic', 'unit_price': 1200},
    {'sku': 'INT-AI-ADDON', 'name': 'Fin AI Copilot Add-on', 'unit_price': 600},
]

VALIDATION_CHECKS = [
    {'field': 'product_compatibility', 'category': 'Product Validation'},
    {'field': 'license_capacity', 'category': 'Product Validation'},
    {'field': 'discount_threshold', 'category': 'Pricing Validation'},
    {'field': 'margin_floor', 'category': 'Pricing Validation'},
    {'field': 'contract_term_limit', 'category': 'Contract Validation'},
    {'field': 'auto_renewal_clause', 'category': 'Contract Validation'},
    {'field': 'data_residency', 'category': 'Compliance'},
    {'field': 'export_control', 'category': 'Compliance'},
]


def _seed_rng(seed_str):
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


def _generate_orders():
    """Generate 50 deterministic demo orders with full lifecycle data."""
    if 'orders' in _cache:
        return _cache['orders']

    rng = _seed_rng('otc-demo-v1')
    base_date = datetime(2026, 1, 5)
    orders = []

    for i in range(50):
        order_id = f'ORD-{1000 + i}'
        quote_id = f'QTE-{2000 + i}'
        account_idx = i % len(ACCOUNT_NAMES)
        account_id = f'ACC-{3000 + account_idx}'
        account_name = ACCOUNT_NAMES[account_idx]

        created = base_date + timedelta(days=rng.randint(0, 70), hours=rng.randint(8, 17))

        # Line items (1-3 products)
        num_items = rng.randint(1, 3)
        items = []
        chosen = rng.sample(PRODUCT_CATALOG, num_items)
        for prod in chosen:
            qty = rng.randint(1, 5) * 10
            items.append({
                'sku': prod['sku'],
                'name': prod['name'],
                'quantity': qty,
                'unit_price': prod['unit_price'],
                'total': qty * prod['unit_price'],
            })
        total = sum(it['total'] for it in items)

        # Determine outcome: 95% success, 3% provisioning fail, 2% billing warning
        roll = rng.random()
        if roll < 0.03:
            outcome = 'provisioning_failed'
        elif roll < 0.05:
            outcome = 'billing_warning'
        else:
            outcome = 'success'

        # Provisioning steps
        prov_steps = []
        activation_time = None
        for step_idx, step_name in enumerate(PROVISIONING_STEPS):
            step_start = created + timedelta(hours=2 + step_idx * rng.randint(4, 12))
            if outcome == 'provisioning_failed' and step_idx == rng.randint(1, 3):
                prov_steps.append({
                    'order_id': order_id,
                    'step_name': step_name,
                    'status': 'failed',
                    'started_at': step_start.isoformat(),
                    'completed_at': (step_start + timedelta(minutes=rng.randint(1, 5))).isoformat(),
                    'error_message': rng.choice([
                        'Entitlement service timeout after 30s',
                        'License pool exhausted for SKU',
                        'Workspace provisioning quota exceeded',
                        'Billing account validation failed — missing payment method',
                    ]),
                })
                # Remaining steps stay pending
                for remaining in PROVISIONING_STEPS[step_idx + 1:]:
                    prov_steps.append({
                        'order_id': order_id,
                        'step_name': remaining,
                        'status': 'pending',
                        'started_at': None,
                        'completed_at': None,
                        'error_message': None,
                    })
                break
            else:
                completed = step_start + timedelta(minutes=rng.randint(1, 30))
                prov_steps.append({
                    'order_id': order_id,
                    'step_name': step_name,
                    'status': 'success',
                    'started_at': step_start.isoformat(),
                    'completed_at': completed.isoformat(),
                    'error_message': None,
                })
                if step_idx == len(PROVISIONING_STEPS) - 1:
                    activation_time = completed

        # Order status
        if outcome == 'provisioning_failed':
            status = 'Failed'
            activated_date = None
        elif outcome == 'billing_warning':
            status = 'Active'
            activated_date = activation_time.isoformat() if activation_time else None
        else:
            status = 'Active'
            activated_date = activation_time.isoformat() if activation_time else None

        # Validation results
        validations = []
        for vc in VALIDATION_CHECKS:
            v_roll = rng.random()
            if outcome == 'provisioning_failed' and vc['field'] == 'license_capacity' and rng.random() < 0.4:
                v_status = 'warning'
                v_msg = 'License capacity near limit — review before scaling'
            elif v_roll < 0.90:
                v_status = 'pass'
                v_msg = f'{vc["field"].replace("_", " ").title()} check passed'
            elif v_roll < 0.96:
                v_status = 'warning'
                v_msg = rng.choice([
                    'Discount exceeds standard threshold — manager approval obtained',
                    'Non-standard contract term — legal review completed',
                    'Data residency region requires additional DPA',
                ])
            else:
                v_status = 'fail'
                v_msg = rng.choice([
                    'Product bundle incompatibility detected',
                    'Margin below minimum floor — escalation required',
                    'Export control restriction for selected region',
                ])

            validations.append({
                'order_id': order_id,
                'field': vc['field'],
                'category': vc['category'],
                'status': v_status,
                'message': v_msg,
            })

        # Billing records (monthly invoices for active orders)
        billing = []
        if status == 'Active' and activation_time:
            billing_start = activation_time.replace(day=1, hour=0, minute=0, second=0)
            for m in range(rng.randint(1, 3)):
                period_start = billing_start + timedelta(days=30 * m)
                period_end = period_start + timedelta(days=29)
                inv_num = f'INV-{5000 + i * 10 + m}'

                b_roll = rng.random()
                if outcome == 'billing_warning' and m == 0:
                    b_status = 'overdue'
                elif b_roll < 0.90:
                    b_status = 'paid'
                elif b_roll < 0.95:
                    b_status = 'pending'
                elif b_roll < 0.98:
                    b_status = 'overdue'
                else:
                    b_status = 'failed'

                billing.append({
                    'id': inv_num,
                    'order_id': order_id,
                    'account_id': account_id,
                    'account_name': account_name,
                    'amount': total,
                    'period_start': period_start.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d'),
                    'status': b_status,
                    'invoice_number': inv_num,
                })

        order = {
            'id': order_id,
            'quote_id': quote_id,
            'account_id': account_id,
            'account_name': account_name,
            'status': status,
            'total': total,
            'line_items': items,
            'created_date': created.isoformat(),
            'activated_date': activated_date,
            'provisioning_steps': prov_steps,
            'validation_results': validations,
            'billing_records': billing,
        }
        orders.append(order)

    _cache['orders'] = orders
    return orders


def _get_order(order_id):
    orders = _generate_orders()
    for o in orders:
        if o['id'] == order_id:
            return o
    return None


def _all_billing():
    """Flatten billing records from all orders."""
    if 'billing' in _cache:
        return _cache['billing']
    records = []
    for o in _generate_orders():
        records.extend(o['billing_records'])
    _cache['billing'] = records
    return records


# ---------------------------------------------------------------------------
# Order endpoints
# ---------------------------------------------------------------------------

@orders_bp.route('/orders', methods=['GET'])
def list_orders():
    """List orders with optional status filter and pagination."""
    status_filter = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    orders = _generate_orders()
    if status_filter:
        orders = [o for o in orders if o['status'].lower() == status_filter.lower()]

    total = len(orders)
    start = (page - 1) * per_page
    page_orders = orders[start:start + per_page]

    # Strip heavy nested data from list response
    slim = []
    for o in page_orders:
        slim.append({
            'id': o['id'],
            'quote_id': o['quote_id'],
            'account_id': o['account_id'],
            'account_name': o['account_name'],
            'status': o['status'],
            'total': o['total'],
            'created_date': o['created_date'],
            'activated_date': o['activated_date'],
            'line_item_count': len(o['line_items']),
        })

    return jsonify({
        'orders': slim,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@orders_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get a single order with provisioning steps, validation results, and billing."""
    order = _get_order(order_id)
    if not order:
        return jsonify({'error': f'Order {order_id} not found'}), 404
    return jsonify(order)


@orders_bp.route('/orders/<order_id>/timeline', methods=['GET'])
def get_order_timeline(order_id):
    """Chronological timeline of all events for an order."""
    order = _get_order(order_id)
    if not order:
        return jsonify({'error': f'Order {order_id} not found'}), 404

    events = []

    # Order created
    events.append({
        'timestamp': order['created_date'],
        'event': 'Order Created',
        'status': 'success',
        'detail': f'Order {order_id} created from quote {order["quote_id"]}',
    })

    # Validation
    val_results = order['validation_results']
    failures = [v for v in val_results if v['status'] == 'fail']
    warnings = [v for v in val_results if v['status'] == 'warning']
    created_dt = datetime.fromisoformat(order['created_date'])

    events.append({
        'timestamp': (created_dt + timedelta(hours=1)).isoformat(),
        'event': 'Validation Started',
        'status': 'success',
        'detail': f'Running {len(val_results)} validation checks',
    })

    if failures:
        events.append({
            'timestamp': (created_dt + timedelta(hours=1, minutes=30)).isoformat(),
            'event': 'Validation Complete',
            'status': 'warning',
            'detail': f'{len(failures)} failures, {len(warnings)} warnings',
        })
    else:
        events.append({
            'timestamp': (created_dt + timedelta(hours=1, minutes=30)).isoformat(),
            'event': 'Validation Complete',
            'status': 'success',
            'detail': f'All checks passed ({len(warnings)} warnings)' if warnings
                      else 'All checks passed',
        })

    # Provisioning steps
    for step in order['provisioning_steps']:
        if step['started_at']:
            events.append({
                'timestamp': step['started_at'],
                'event': f'Provisioning: {step["step_name"].replace("_", " ").title()}',
                'status': step['status'],
                'detail': step['error_message'] or 'Completed successfully',
            })

    # Activation
    if order['activated_date']:
        events.append({
            'timestamp': order['activated_date'],
            'event': 'Order Activated',
            'status': 'success',
            'detail': 'Order is now active and billing has started',
        })

    # Billing events
    for bill in order['billing_records']:
        events.append({
            'timestamp': bill['period_start'] + 'T00:00:00',
            'event': f'Invoice {bill["invoice_number"]}',
            'status': 'success' if bill['status'] == 'paid'
                      else ('failed' if bill['status'] in ('overdue', 'failed') else 'pending'),
            'detail': f'${bill["amount"]:,.2f} — {bill["status"]}',
        })

    events.sort(key=lambda e: e['timestamp'])

    return jsonify({
        'order_id': order_id,
        'events': events,
    })


@orders_bp.route('/orders/<order_id>/retry-provisioning', methods=['POST'])
def retry_provisioning(order_id):
    """Retry a failed provisioning step (demo: always succeeds)."""
    order = _get_order(order_id)
    if not order:
        return jsonify({'error': f'Order {order_id} not found'}), 404

    failed = [s for s in order['provisioning_steps'] if s['status'] == 'failed']
    if not failed:
        return jsonify({'error': 'No failed provisioning steps to retry'}), 400

    # In demo mode, mark the failed step as success and advance pending steps
    now = datetime.utcnow().isoformat()
    for step in order['provisioning_steps']:
        if step['status'] == 'failed':
            step['status'] = 'success'
            step['error_message'] = None
            step['completed_at'] = now
        elif step['status'] == 'pending':
            step['status'] = 'success'
            step['started_at'] = now
            step['completed_at'] = now

    order['status'] = 'Active'
    order['activated_date'] = now

    return jsonify({
        'success': True,
        'order_id': order_id,
        'message': 'Provisioning retry succeeded',
        'new_status': order['status'],
    })


# ---------------------------------------------------------------------------
# Billing endpoints
# ---------------------------------------------------------------------------

@orders_bp.route('/billing', methods=['GET'])
def list_billing():
    """Billing records with optional status filter and date range."""
    status_filter = request.args.get('status')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    records = list(_all_billing())

    if status_filter:
        records = [r for r in records if r['status'].lower() == status_filter.lower()]
    if date_from:
        records = [r for r in records if r['period_start'] >= date_from]
    if date_to:
        records = [r for r in records if r['period_end'] <= date_to]

    total = len(records)
    start = (page - 1) * per_page
    page_records = records[start:start + per_page]

    return jsonify({
        'records': page_records,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@orders_bp.route('/billing/summary', methods=['GET'])
def billing_summary():
    """Billing KPIs: total invoiced, collected, collection rate, overdue."""
    records = _all_billing()

    total_invoiced = sum(r['amount'] for r in records)
    total_collected = sum(r['amount'] for r in records if r['status'] == 'paid')
    total_overdue = sum(r['amount'] for r in records if r['status'] == 'overdue')
    total_pending = sum(r['amount'] for r in records if r['status'] == 'pending')
    total_failed = sum(r['amount'] for r in records if r['status'] == 'failed')

    collection_rate = (total_collected / total_invoiced * 100) if total_invoiced else 0

    by_status = {}
    for r in records:
        by_status.setdefault(r['status'], {'count': 0, 'amount': 0})
        by_status[r['status']]['count'] += 1
        by_status[r['status']]['amount'] += r['amount']

    return jsonify({
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_overdue': total_overdue,
        'total_pending': total_pending,
        'total_failed': total_failed,
        'collection_rate': round(collection_rate, 2),
        'invoice_count': len(records),
        'by_status': by_status,
    })
