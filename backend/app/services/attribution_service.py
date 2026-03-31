"""
Attribution analysis service.

Implements multi-touch attribution models (first-touch, last-touch, linear,
time-decay, position-based) and generates demo data for GTM simulations.
"""

import random
from typing import Dict, List, Any, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.attribution')

CHANNELS = ['Paid Search', 'Organic Search', 'Email Campaign', 'LinkedIn Ads',
            'Webinar', 'Content Syndication', 'Direct', 'Referral']

STAGES = ['Awareness', 'Consideration', 'Evaluation', 'Purchase']

OUTCOMES = ['Closed Won', 'Closed Lost', 'Open Pipeline']


def _generate_demo_journeys(count: int = 80) -> List[Dict[str, Any]]:
    """Generate realistic multi-touch customer journeys."""
    rng = random.Random(42)
    journeys = []

    company_prefixes = ['Acme', 'Global', 'Peak', 'Nova', 'Apex', 'Stellar',
                        'Bright', 'Core', 'Edge', 'Pulse']
    company_suffixes = ['Corp', 'Inc', 'Tech', 'Systems', 'Solutions',
                        'Labs', 'Group', 'Digital', 'IO', 'HQ']

    for i in range(count):
        touch_count = rng.randint(2, 6)
        touchpoints = []
        for t in range(touch_count):
            channel = rng.choice(CHANNELS)
            days_before_close = rng.randint(1, 90) if t == touch_count - 1 else rng.randint(
                (touch_count - t) * 10, (touch_count - t) * 20 + 30)
            touchpoints.append({
                'channel': channel,
                'days_before_close': days_before_close,
                'stage': STAGES[min(t * len(STAGES) // touch_count, len(STAGES) - 1)],
            })

        touchpoints.sort(key=lambda x: -x['days_before_close'])

        outcome_roll = rng.random()
        if outcome_roll < 0.45:
            outcome = 'Closed Won'
        elif outcome_roll < 0.75:
            outcome = 'Closed Lost'
        else:
            outcome = 'Open Pipeline'

        deal_value = rng.choice([15000, 25000, 40000, 60000, 85000, 120000])
        if outcome == 'Closed Lost':
            deal_value = int(deal_value * rng.uniform(0.4, 0.8))

        company = f"{rng.choice(company_prefixes)} {rng.choice(company_suffixes)}"
        journeys.append({
            'account': company,
            'deal_value': deal_value,
            'outcome': outcome,
            'touchpoints': touchpoints,
        })

    return journeys


def _apply_first_touch(journeys: List[Dict]) -> Dict[str, float]:
    """100% credit to first touchpoint."""
    credits = {}
    for j in journeys:
        if j['outcome'] != 'Closed Won':
            continue
        ch = j['touchpoints'][0]['channel']
        credits[ch] = credits.get(ch, 0) + j['deal_value']
    return credits


def _apply_last_touch(journeys: List[Dict]) -> Dict[str, float]:
    """100% credit to last touchpoint."""
    credits = {}
    for j in journeys:
        if j['outcome'] != 'Closed Won':
            continue
        ch = j['touchpoints'][-1]['channel']
        credits[ch] = credits.get(ch, 0) + j['deal_value']
    return credits


def _apply_linear(journeys: List[Dict]) -> Dict[str, float]:
    """Equal credit across all touchpoints."""
    credits = {}
    for j in journeys:
        if j['outcome'] != 'Closed Won':
            continue
        share = j['deal_value'] / len(j['touchpoints'])
        for tp in j['touchpoints']:
            credits[tp['channel']] = credits.get(tp['channel'], 0) + share
    return credits


def _apply_time_decay(journeys: List[Dict]) -> Dict[str, float]:
    """More credit to recent touchpoints (half-life = 14 days)."""
    import math
    half_life = 14
    credits = {}
    for j in journeys:
        if j['outcome'] != 'Closed Won':
            continue
        weights = []
        for tp in j['touchpoints']:
            w = math.pow(2, -tp['days_before_close'] / half_life)
            weights.append(w)
        total_w = sum(weights)
        if total_w == 0:
            continue
        for tp, w in zip(j['touchpoints'], weights):
            share = j['deal_value'] * (w / total_w)
            credits[tp['channel']] = credits.get(tp['channel'], 0) + share
    return credits


def _apply_position_based(journeys: List[Dict]) -> Dict[str, float]:
    """40% first, 40% last, 20% split among middle."""
    credits = {}
    for j in journeys:
        if j['outcome'] != 'Closed Won':
            continue
        tps = j['touchpoints']
        n = len(tps)
        for i, tp in enumerate(tps):
            if n == 1:
                share = j['deal_value']
            elif n == 2:
                share = j['deal_value'] * 0.5
            elif i == 0:
                share = j['deal_value'] * 0.4
            elif i == n - 1:
                share = j['deal_value'] * 0.4
            else:
                share = j['deal_value'] * 0.2 / (n - 2)
            credits[tp['channel']] = credits.get(tp['channel'], 0) + share
    return credits


MODEL_FNS = {
    'first_touch': _apply_first_touch,
    'last_touch': _apply_last_touch,
    'linear': _apply_linear,
    'time_decay': _apply_time_decay,
    'position_based': _apply_position_based,
}

MODEL_LABELS = {
    'first_touch': 'First Touch',
    'last_touch': 'Last Touch',
    'linear': 'Linear',
    'time_decay': 'Time Decay',
    'position_based': 'Position-Based',
}


def _build_sankey(journeys: List[Dict]) -> Dict[str, Any]:
    """Build Sankey nodes/links from journeys (channel → stage → outcome)."""
    node_set = set()
    link_counts: Dict[tuple, float] = {}

    for j in journeys:
        first_channel = j['touchpoints'][0]['channel']
        last_stage = j['touchpoints'][-1]['stage']
        outcome = j['outcome']
        val = j['deal_value']

        node_set.update([first_channel, last_stage, outcome])

        key_cs = (first_channel, last_stage)
        link_counts[key_cs] = link_counts.get(key_cs, 0) + val

        key_so = (last_stage, outcome)
        link_counts[key_so] = link_counts.get(key_so, 0) + val

    nodes = sorted(node_set)
    node_index = {n: i for i, n in enumerate(nodes)}

    links = []
    for (src, tgt), value in link_counts.items():
        links.append({
            'source': node_index[src],
            'target': node_index[tgt],
            'value': round(value),
        })

    return {
        'nodes': [{'name': n} for n in nodes],
        'links': links,
    }


def _find_key_insight(model_results: Dict[str, Dict[str, float]]) -> Dict[str, str]:
    """Find the biggest disagreement between attribution models."""
    all_channels = set()
    for credits in model_results.values():
        all_channels.update(credits.keys())

    max_diff = 0
    insight_channel = ''
    high_model = ''
    low_model = ''

    for ch in all_channels:
        values = {m: model_results[m].get(ch, 0) for m in model_results}
        if not values:
            continue
        hi = max(values, key=values.get)
        lo = min(values, key=values.get)
        diff = values[hi] - values[lo]
        if diff > max_diff:
            max_diff = diff
            insight_channel = ch
            high_model = hi
            low_model = lo

    if not insight_channel:
        return {'text': 'All models agree on channel attribution.', 'type': 'neutral'}

    return {
        'text': (
            f"{insight_channel} shows the biggest model disagreement: "
            f"{MODEL_LABELS.get(high_model, high_model)} attributes "
            f"${max_diff:,.0f} more than {MODEL_LABELS.get(low_model, low_model)}."
        ),
        'channel': insight_channel,
        'high_model': high_model,
        'low_model': low_model,
        'difference': round(max_diff),
        'type': 'divergence',
    }


def get_attribution_analysis(simulation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run attribution analysis. Uses demo data when no simulation data is available.
    """
    journeys = _generate_demo_journeys()

    model_results = {}
    for model_id, fn in MODEL_FNS.items():
        raw = fn(journeys)
        model_results[model_id] = {ch: round(v) for ch, v in raw.items()}

    sankey = _build_sankey(journeys)
    insight = _find_key_insight(model_results)

    touchpoint_sequences = []
    won = [j for j in journeys if j['outcome'] == 'Closed Won']
    for j in sorted(won, key=lambda x: -x['deal_value'])[:12]:
        touchpoint_sequences.append({
            'account': j['account'],
            'deal_value': j['deal_value'],
            'touchpoints': [
                {'channel': tp['channel'], 'stage': tp['stage'],
                 'days_before_close': tp['days_before_close']}
                for tp in j['touchpoints']
            ],
        })

    channel_revenue = {}
    for model_id, credits in model_results.items():
        for ch, val in credits.items():
            if ch not in channel_revenue:
                channel_revenue[ch] = {}
            channel_revenue[ch][model_id] = val

    return {
        'sankey': sankey,
        'touchpoint_sequences': touchpoint_sequences,
        'model_results': model_results,
        'model_labels': MODEL_LABELS,
        'channel_revenue': channel_revenue,
        'channels': sorted(set(ch for credits in model_results.values() for ch in credits)),
        'insight': insight,
        'summary': {
            'total_journeys': len(journeys),
            'won_deals': len(won),
            'total_revenue': sum(j['deal_value'] for j in won),
            'avg_touchpoints': round(sum(len(j['touchpoints']) for j in journeys) / len(journeys), 1),
        },
    }
