"""
Data Pipeline API
Connector health and sync status for the pipeline dashboard.
"""

import hashlib
import random
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify

data_pipeline_bp = Blueprint('data_pipeline', __name__, url_prefix='/api/v1/pipeline')

# GTM-relevant connector definitions
CONNECTORS = [
    {
        'id': 'salesforce-crm',
        'name': 'Salesforce CRM',
        'source': 'Salesforce',
        'destination': 'Snowflake',
        'icon_color': '#00A1E0',
    },
    {
        'id': 'stripe-payments',
        'name': 'Stripe Payments',
        'source': 'Stripe',
        'destination': 'BigQuery',
        'icon_color': '#635BFF',
    },
    {
        'id': 'hubspot-marketing',
        'name': 'HubSpot Marketing',
        'source': 'HubSpot',
        'destination': 'Snowflake',
        'icon_color': '#FF7A59',
    },
    {
        'id': 'zendesk-support',
        'name': 'Zendesk Support',
        'source': 'Zendesk',
        'destination': 'Redshift',
        'icon_color': '#17494D',
    },
    {
        'id': 'marketo-automation',
        'name': 'Marketo',
        'source': 'Marketo',
        'destination': 'Snowflake',
        'icon_color': '#5C4C9F',
    },
    {
        'id': 'intercom-conversations',
        'name': 'Intercom',
        'source': 'Intercom',
        'destination': 'BigQuery',
        'icon_color': '#2068FF',
    },
]


def _seed_rng(connector_id, salt=''):
    """Deterministic RNG seeded by connector id so data is stable across calls."""
    h = hashlib.md5(f'{connector_id}{salt}'.encode()).hexdigest()
    return random.Random(int(h, 16))


def _generate_connector_health(connector, now):
    """Generate realistic mock health data for a single connector."""
    rng = _seed_rng(connector['id'], now.strftime('%Y-%m-%d'))

    # Sparkline: 7 days of sync outcomes (1=success, 0=fail)
    fail_rate = rng.uniform(0.0, 0.15)
    sparkline = [0 if rng.random() < fail_rate else 1 for _ in range(7)]

    # Force at least one pattern — most connectors are mostly healthy
    if sum(sparkline) < 5:
        sparkline[rng.randint(0, 6)] = 1

    successes_30d = rng.randint(25, 30)
    total_30d = 30
    success_rate = round(successes_30d / total_30d, 3)

    avg_rows = rng.randint(800, 45000)
    avg_duration = rng.randint(30, 300)

    # Last sync info
    minutes_ago = rng.randint(5, 180)
    last_sync_time = now - timedelta(minutes=minutes_ago)
    last_sync_ok = sparkline[-1] == 1

    # Overall status derived from recent history
    recent_failures = sparkline[-3:].count(0)
    if recent_failures >= 2:
        status = 'error'
    elif recent_failures == 1:
        status = 'warning'
    else:
        status = 'healthy'

    return {
        'id': connector['id'],
        'name': connector['name'],
        'source': connector['source'],
        'destination': connector['destination'],
        'icon_color': connector['icon_color'],
        'status': status,
        'last_sync': {
            'status': 'success' if last_sync_ok else 'failed',
            'timestamp': last_sync_time.isoformat(),
            'rows_synced': avg_rows + rng.randint(-200, 500) if last_sync_ok else 0,
            'duration_seconds': avg_duration + rng.randint(-10, 30),
        },
        'stats': {
            'success_rate_30d': success_rate,
            'avg_rows_per_sync': avg_rows,
            'avg_duration_seconds': avg_duration,
        },
        'sparkline': sparkline,
    }


@data_pipeline_bp.route('/connectors', methods=['GET'])
def list_connectors():
    """Return health data for all sync connectors (demo/mock data)."""
    now = datetime.now(timezone.utc)
    connectors = [_generate_connector_health(c, now) for c in CONNECTORS]
    return jsonify({'connectors': connectors})
