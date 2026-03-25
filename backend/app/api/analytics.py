"""
Analytics API — anomaly detection across GTM metrics.

Uses Z-score based anomaly detection on time-series data.
Supports demo/mock mode when no real metrics source is configured.
"""

import hashlib
import math
import random
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger

logger = get_logger("mirofish.api.analytics")

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")

# ── Metric definitions ──────────────────────────────────────────────────

METRIC_DEFS = {
    "revenue": {
        "label": "Revenue",
        "metrics": [
            {"key": "mrr", "label": "MRR", "unit": "$", "baseline": 125000, "noise": 3000},
            {"key": "arr", "label": "ARR", "unit": "$", "baseline": 1500000, "noise": 25000},
            {"key": "expansion_revenue", "label": "Expansion Revenue", "unit": "$", "baseline": 18000, "noise": 4000},
            {"key": "churn_revenue", "label": "Churn Revenue", "unit": "$", "baseline": 8000, "noise": 2000},
        ],
    },
    "pipeline": {
        "label": "Pipeline",
        "metrics": [
            {"key": "deal_velocity", "label": "Deal Velocity", "unit": "days", "baseline": 32, "noise": 4},
            {"key": "conversion_rate", "label": "Conversion Rate", "unit": "%", "baseline": 24, "noise": 3},
            {"key": "new_opps", "label": "New Opportunities", "unit": "", "baseline": 85, "noise": 12},
            {"key": "pipeline_value", "label": "Pipeline Value", "unit": "$", "baseline": 450000, "noise": 45000},
        ],
    },
    "sync": {
        "label": "Data Sync",
        "metrics": [
            {"key": "sync_success_rate", "label": "Sync Success Rate", "unit": "%", "baseline": 98.5, "noise": 0.8},
            {"key": "sync_latency", "label": "Sync Latency", "unit": "ms", "baseline": 240, "noise": 50},
            {"key": "records_synced", "label": "Records Synced", "unit": "", "baseline": 15000, "noise": 2000},
        ],
    },
    "billing": {
        "label": "Billing",
        "metrics": [
            {"key": "payment_failure_rate", "label": "Payment Failure Rate", "unit": "%", "baseline": 2.1, "noise": 0.6},
            {"key": "invoice_count", "label": "Invoices Sent", "unit": "", "baseline": 320, "noise": 30},
            {"key": "overdue_amount", "label": "Overdue Amount", "unit": "$", "baseline": 12000, "noise": 3500},
        ],
    },
}

ANOMALY_THRESHOLD = 2.0  # Z-score threshold for anomaly detection


def _seed_for_date(date_str):
    """Deterministic seed from a date string."""
    return int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)


def _generate_timeseries(metric_def, days=90, seed_base=0):
    """Generate a deterministic time-series with injected anomalies."""
    rng = random.Random(seed_base + hash(metric_def["key"]))
    baseline = metric_def["baseline"]
    noise = metric_def["noise"]
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)

    # Pre-select 3-5 anomaly injection points
    num_anomalies = rng.randint(3, 5)
    anomaly_days = sorted(rng.sample(range(5, days - 2), num_anomalies))

    values = []
    for i in range(days):
        date = start + timedelta(days=i)
        # Normal variation + slight trend
        trend = baseline * 0.0005 * i
        val = baseline + trend + rng.gauss(0, noise)

        # Inject anomalies: spike or drop
        if i in anomaly_days:
            direction = rng.choice([-1, 1])
            magnitude = rng.uniform(3.0, 5.5) * noise
            val += direction * magnitude

        values.append({"date": date.isoformat(), "value": round(val, 2)})

    return values


def _detect_anomalies(values, metric_def, category):
    """Z-score based anomaly detection on a value series."""
    if len(values) < 5:
        return []

    nums = [v["value"] for v in values]
    mean = sum(nums) / len(nums)
    variance = sum((x - mean) ** 2 for x in nums) / len(nums)
    std = math.sqrt(variance) if variance > 0 else 1.0

    anomalies = []
    for i, point in enumerate(values):
        z = (point["value"] - mean) / std
        if abs(z) >= ANOMALY_THRESHOLD:
            deviation_pct = ((point["value"] - mean) / mean) * 100 if mean != 0 else 0
            anomalies.append({
                "id": f"{metric_def['key']}_{point['date']}",
                "category": category,
                "metric": metric_def["key"],
                "metric_label": metric_def["label"],
                "date": point["date"],
                "expected": round(mean, 2),
                "actual": point["value"],
                "deviation": round(deviation_pct, 1),
                "z_score": round(z, 2),
                "severity": "critical" if abs(z) >= 4.0 else "high" if abs(z) >= 3.0 else "medium",
                "direction": "spike" if z > 0 else "drop",
            })

    return anomalies


@analytics_bp.route("/anomalies", methods=["GET"])
def get_anomalies():
    """
    GET /api/v1/analytics/anomalies

    Query params:
      - days: lookback window (default 90, max 365)
      - category: filter by category (revenue|pipeline|sync|billing)
      - severity: filter by severity (critical|high|medium)

    Returns detected anomalies with Z-score metadata, timeseries for
    heatmap rendering, and summary statistics.
    """
    days = min(request.args.get("days", 90, type=int), 365)
    cat_filter = request.args.get("category")
    sev_filter = request.args.get("severity")

    all_anomalies = []
    heatmap = {}  # category -> metric_key -> [{date, z_score}]
    timeseries = {}  # metric_key -> [{date, value}]

    seed_base = _seed_for_date(datetime.utcnow().date().isoformat())

    for cat_key, cat_def in METRIC_DEFS.items():
        if cat_filter and cat_key != cat_filter:
            continue
        heatmap[cat_key] = {}
        for mdef in cat_def["metrics"]:
            series = _generate_timeseries(mdef, days=days, seed_base=seed_base)
            timeseries[mdef["key"]] = series

            detected = _detect_anomalies(series, mdef, cat_key)
            if sev_filter:
                detected = [a for a in detected if a["severity"] == sev_filter]
            all_anomalies.extend(detected)

            # Build heatmap row for this metric
            nums = [v["value"] for v in series]
            mean = sum(nums) / len(nums)
            variance = sum((x - mean) ** 2 for x in nums) / len(nums)
            std = math.sqrt(variance) if variance > 0 else 1.0
            heatmap[cat_key][mdef["key"]] = [
                {"date": v["date"], "z_score": round((v["value"] - mean) / std, 2)}
                for v in series
            ]

    # Sort by absolute Z-score descending (most surprising first)
    all_anomalies.sort(key=lambda a: abs(a["z_score"]), reverse=True)

    # Summary stats
    summary = {
        "total": len(all_anomalies),
        "critical": sum(1 for a in all_anomalies if a["severity"] == "critical"),
        "high": sum(1 for a in all_anomalies if a["severity"] == "high"),
        "medium": sum(1 for a in all_anomalies if a["severity"] == "medium"),
        "by_category": {},
    }
    for cat_key in METRIC_DEFS:
        cat_anomalies = [a for a in all_anomalies if a["category"] == cat_key]
        summary["by_category"][cat_key] = len(cat_anomalies)

    return jsonify({
        "success": True,
        "data": {
            "anomalies": all_anomalies,
            "heatmap": heatmap,
            "timeseries": timeseries,
            "summary": summary,
            "meta": {
                "days": days,
                "threshold": ANOMALY_THRESHOLD,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    })
