"""
Pipeline data generator service.

Generates deterministic demo data for the GTM pipeline analytics:
- 6 months of monthly FunnelSnapshots
- 200 ConversionEvents with timestamps
- Seasonal patterns (Q4 +20%, Q1 -10%)
- Velocity metrics per stage
"""

import hashlib
import random
from datetime import datetime, timedelta
from statistics import median

from ..models.pipeline import (
    PipelineStage, FunnelSnapshot, ConversionEvent, PIPELINE_STAGES,
)

_SEED = 42
_BASE_LEADS_PER_MONTH = 1000
_MONTHS = 6
_CONVERSION_EVENT_COUNT = 200

OWNERS = [
    "Sarah Chen", "Marcus Johnson", "Emily Park", "David Kim",
    "Rachel Torres", "James Wilson", "Aisha Patel", "Tom Harris",
]


def _seasonal_factor(month: int) -> float:
    """Q4 (Oct-Dec) +20% leads, Q1 (Jan-Mar) -10% conversion."""
    if month in (10, 11, 12):
        return 1.20
    if month in (1, 2, 3):
        return 0.90
    return 1.0


def _seeded_rng(seed: int) -> random.Random:
    return random.Random(seed)


def generate_funnel_history(months: int = _MONTHS) -> list[FunnelSnapshot]:
    """Generate monthly funnel snapshots with realistic progression."""
    rng = _seeded_rng(_SEED)
    now = datetime(2026, 3, 1)
    snapshots = []

    for i in range(months):
        dt = now - timedelta(days=30 * (months - 1 - i))
        month_num = dt.month
        season = _seasonal_factor(month_num)

        raw_leads = int(_BASE_LEADS_PER_MONTH * season * rng.uniform(0.90, 1.10))
        stages = []
        current_count = raw_leads
        total_value = 0.0

        for sdef in PIPELINE_STAGES:
            if sdef["name"] == "Closed Lost":
                continue

            deal_value = current_count * rng.uniform(8000, 15000) if sdef["order"] >= 2 else 0.0
            total_value += deal_value

            conv_rate = sdef["conversion_rate"]
            if conv_rate > 0:
                conv_rate *= rng.uniform(0.90, 1.10)

            avg_days = sdef["avg_days"] * rng.uniform(0.85, 1.15) if sdef["avg_days"] > 0 else 0.0

            stages.append(PipelineStage(
                name=sdef["name"],
                order=sdef["order"],
                count=current_count,
                value=round(deal_value, 2),
                conversion_rate_to_next=round(min(conv_rate, 1.0), 4),
                avg_days_in_stage=round(avg_days, 1),
                color=sdef["color"],
            ))

            if conv_rate > 0:
                current_count = int(current_count * conv_rate)

        snapshots.append(FunnelSnapshot(
            timestamp=dt.strftime("%Y-%m-%d"),
            stages=stages,
            total_leads=raw_leads,
            total_revenue=round(total_value, 2),
        ))

    return snapshots


def generate_conversion_events(count: int = _CONVERSION_EVENT_COUNT) -> list[ConversionEvent]:
    """Generate individual lead conversion events across stages."""
    rng = _seeded_rng(_SEED + 1)
    win_stages = [s for s in PIPELINE_STAGES if s["name"] not in ("Closed Won", "Closed Lost")]
    events = []
    base_date = datetime(2025, 10, 1)

    for i in range(count):
        stage_idx = rng.randint(0, len(win_stages) - 2)
        from_stage = win_stages[stage_idx]
        to_stage = win_stages[stage_idx + 1]

        ts = base_date + timedelta(days=rng.randint(0, 180), hours=rng.randint(0, 23))
        duration = max(1, int(from_stage["avg_days"] * rng.uniform(0.5, 2.0)))
        entity_id = hashlib.md5(f"lead-{i}".encode()).hexdigest()[:12]

        events.append(ConversionEvent(
            id=f"evt-{i:04d}",
            entity_id=entity_id,
            from_stage=from_stage["name"],
            to_stage=to_stage["name"],
            timestamp=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            duration_days=duration,
            owner=rng.choice(OWNERS),
        ))

    events.sort(key=lambda e: e.timestamp)
    return events


def compute_velocity_metrics(events: list[ConversionEvent] | None = None) -> list[dict]:
    """Compute avg and median days per stage transition."""
    if events is None:
        events = generate_conversion_events()

    buckets: dict[str, list[int]] = {}
    for evt in events:
        key = f"{evt.from_stage} → {evt.to_stage}"
        buckets.setdefault(key, []).append(evt.duration_days)

    metrics = []
    for transition, durations in buckets.items():
        from_s, to_s = transition.split(" → ")
        metrics.append({
            "from_stage": from_s,
            "to_stage": to_s,
            "avg_days": round(sum(durations) / len(durations), 1),
            "median_days": round(median(durations), 1),
            "min_days": min(durations),
            "max_days": max(durations),
            "count": len(durations),
        })

    metrics.sort(key=lambda m: PIPELINE_STAGES[[s["name"] for s in PIPELINE_STAGES].index(m["from_stage"])]["order"])
    return metrics


def compute_forecast(snapshot: FunnelSnapshot | None = None) -> dict:
    """Simple forecast: current pipeline value × stage probability."""
    if snapshot is None:
        history = generate_funnel_history()
        snapshot = history[-1]

    stage_probs = {
        "Raw Lead": 0.25 * 0.40 * 0.60 * 0.70 * 0.35,
        "MQL": 0.40 * 0.60 * 0.70 * 0.35,
        "SQL": 0.60 * 0.70 * 0.35,
        "SAO": 0.70 * 0.35,
        "Proposal": 0.35,
        "Closed Won": 1.0,
    }

    weighted = 0.0
    unweighted = 0.0
    by_stage = []

    for stage in snapshot.stages:
        prob = stage_probs.get(stage.name, 0)
        w = stage.value * prob
        weighted += w
        unweighted += stage.value
        by_stage.append({
            "stage": stage.name,
            "value": stage.value,
            "probability": round(prob, 4),
            "weighted_value": round(w, 2),
        })

    confidence = 0.15
    return {
        "weighted_forecast": round(weighted, 2),
        "unweighted_total": round(unweighted, 2),
        "best_case": round(weighted * (1 + confidence), 2),
        "expected": round(weighted, 2),
        "worst_case": round(weighted * (1 - confidence), 2),
        "by_stage": by_stage,
        "as_of": snapshot.timestamp,
    }
