"""
Deals API — serves recent deal activity for the dashboard ticker.

Always returns deterministic mock data (no LLM or external data source needed).
The data rotates based on the current hour so the ticker feels dynamic across
page reloads without requiring a database.
"""

import hashlib
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

deals_bp = Blueprint('deals', __name__, url_prefix='/api/deals')

COMPANIES = [
    'Acme Corp', 'TechNova', 'BrightPath', 'CloudScale', 'DataForge',
    'Nexus AI', 'PulseMetrics', 'Stratiform', 'VeloCity', 'ZenithOps',
    'ArcLight', 'BluePeak', 'CoreShift', 'DriftLabs', 'EchoBase',
    'FluxPoint', 'GreenGrid', 'HyperLoop', 'IronClad', 'JetStream',
]

STAGES = ['Discovery', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']

AMOUNTS = [
    12_000, 24_500, 48_000, 67_000, 95_000, 120_000,
    18_750, 35_200, 52_800, 78_300, 145_000, 210_000,
    8_500, 31_000, 56_750, 89_400, 175_000, 42_100,
    15_600, 63_900,
]


def _seed_int(seed_str, mod):
    """Deterministic pseudo-random int from a string seed."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return h % mod


def _generate_deals(count=10):
    """Generate *count* recent deals using the current hour as rotation seed."""
    hour_seed = int(time.time()) // 3600
    deals = []

    for i in range(count):
        seed = f'{hour_seed}-{i}'
        company_idx = _seed_int(seed + '-co', len(COMPANIES))
        amount_idx = _seed_int(seed + '-amt', len(AMOUNTS))
        stage_idx = _seed_int(seed + '-stg', len(STAGES))

        stage = STAGES[stage_idx]
        prev_stage_idx = max(0, stage_idx - 1)

        if stage == 'Closed Won':
            status = 'won'
        elif stage == 'Closed Lost':
            status = 'lost'
        else:
            status = 'advanced'

        minutes_ago = _seed_int(seed + '-min', 120) + 1
        ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)

        deals.append({
            'id': f'deal-{hour_seed}-{i}',
            'company': COMPANIES[company_idx],
            'stage': stage,
            'previous_stage': STAGES[prev_stage_idx],
            'amount': AMOUNTS[amount_idx],
            'status': status,
            'timestamp': ts.isoformat(),
            'minutes_ago': minutes_ago,
        })

    deals.sort(key=lambda d: d['minutes_ago'])
    return deals


@deals_bp.route('/recent', methods=['GET'])
def recent_deals():
    """Return the most recent deal activity for the ticker."""
    count = min(int(request.args.get('count', 10)), 20)
    return jsonify({'deals': _generate_deals(count)})
