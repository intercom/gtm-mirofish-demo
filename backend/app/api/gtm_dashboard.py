"""
GTM Dashboard API
Serves mock/demo data for dashboard widgets including top accounts table.
All data is deterministic (seeded) so it's consistent across requests.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

gtm_dashboard_bp = Blueprint('gtm_dashboard', __name__, url_prefix='/api/gtm/dashboard')

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')

# Deterministic company names for demo data
_COMPANY_NAMES = [
    'Acme Corp', 'TechNova', 'CloudSync', 'DataStream', 'FinanceHub',
    'RetailMax', 'HealthBridge', 'EduSpark', 'LogiTrack', 'MediaWave',
    'CyberGuard', 'GreenEnergy', 'BuildRight', 'FoodChain', 'TravelEase',
    'InsureTech', 'AutoDrive', 'PharmaCo', 'AgriSmart', 'SpaceDynamics',
]

_PLANS = ['Starter', 'Growth', 'Professional', 'Enterprise']

_INDUSTRIES = ['SaaS', 'Healthcare', 'Fintech', 'E-commerce', 'Manufacturing',
               'Education', 'Logistics', 'Media', 'Cybersecurity', 'Energy']


def _seed_hash(name, field):
    """Deterministic hash for a company+field pair, returns float 0-1."""
    h = hashlib.md5(f"{name}:{field}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _generate_accounts():
    """Generate 20 deterministic demo account records."""
    accounts = []
    base_date = datetime(2026, 3, 24)

    for i, name in enumerate(_COMPANY_NAMES):
        seed = _seed_hash(name, 'arr')

        arr = int(5000 + seed * 495000)
        arr = round(arr / 1000) * 1000

        plan_idx = min(int(_seed_hash(name, 'plan') * len(_PLANS)), len(_PLANS) - 1)
        plan = _PLANS[plan_idx]

        health = int(10 + _seed_hash(name, 'health') * 90)

        pipeline = int(arr * (0.1 + _seed_hash(name, 'pipeline') * 0.9))
        pipeline = round(pipeline / 1000) * 1000

        days_ago = int(_seed_hash(name, 'activity') * 60)
        last_activity = (base_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        renewal_offset = int(30 + _seed_hash(name, 'renewal') * 335)
        renewal_date = (base_date + timedelta(days=renewal_offset)).strftime('%Y-%m-%d')

        industry_idx = min(int(_seed_hash(name, 'industry') * len(_INDUSTRIES)), len(_INDUSTRIES) - 1)

        accounts.append({
            'rank': i + 1,
            'name': name,
            'arr': arr,
            'plan': plan,
            'health_score': health,
            'pipeline': pipeline,
            'last_activity': last_activity,
            'renewal_date': renewal_date,
            'industry': _INDUSTRIES[industry_idx],
        })

    accounts.sort(key=lambda a: a['arr'], reverse=True)
    for i, acct in enumerate(accounts):
        acct['rank'] = i + 1

    return accounts


@gtm_dashboard_bp.route('/top-accounts', methods=['GET'])
def top_accounts():
    """Return top 20 accounts sorted by ARR (default) for dashboard table."""
    accounts = _generate_accounts()

    sort_by = request.args.get('sort_by', 'arr')
    order = request.args.get('order', 'desc')
    search = request.args.get('search', '').strip().lower()

    if search:
        accounts = [a for a in accounts if search in a['name'].lower()
                    or search in a['industry'].lower()
                    or search in a['plan'].lower()]

    valid_sort_fields = {'arr', 'name', 'health_score', 'pipeline', 'renewal_date', 'last_activity', 'plan', 'rank'}
    if sort_by in valid_sort_fields:
        reverse = order == 'desc'
        accounts.sort(key=lambda a: a.get(sort_by, 0), reverse=reverse)
        for i, acct in enumerate(accounts):
            acct['rank'] = i + 1

    max_arr = max((a['arr'] for a in accounts), default=1)
    total_arr = sum(a['arr'] for a in accounts)
    total_pipeline = sum(a['pipeline'] for a in accounts)

    return jsonify({
        'accounts': accounts,
        'meta': {
            'total': len(accounts),
            'max_arr': max_arr,
            'total_arr': total_arr,
            'total_pipeline': total_pipeline,
        },
    })
