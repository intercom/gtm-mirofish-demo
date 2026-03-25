"""
Global Activity Feed Service — aggregates activity across all GTM domains.

Generates realistic demo activities spanning deals, leads, churn risks,
syncs, simulations, reports, reconciliations, orders, and pipeline milestones.
"""

import hashlib
import random
import time
from datetime import datetime, timezone


ACTIVITY_TYPES = [
    "deal_update",
    "lead_scored",
    "churn_risk",
    "sync_complete",
    "simulation_finished",
    "report_generated",
    "reconciliation_alert",
    "order_provisioned",
    "pipeline_milestone",
]

_COMPANIES = [
    "Acme SaaS", "MedFirst Health", "PayStream Financial",
    "ShopNova", "CloudOps Inc", "GrowthLoop", "HealthBridge",
    "FinEdge", "TravelNow", "DataPulse Analytics",
]

_PEOPLE = [
    ("Sarah Chen", "VP of Support"),
    ("Marcus Johnson", "CX Director"),
    ("Priya Patel", "Head of Operations"),
    ("David Kim", "IT Leader"),
    ("Rachel Torres", "VP of Support"),
    ("Tom O'Brien", "VP Customer Success"),
    ("Elena Vasquez", "Director of Digital"),
    ("Michael Chang", "Head of Operations"),
    ("Lisa Park", "VP CX"),
    ("Nathan Lee", "CTO"),
]

_TEMPLATES = {
    "deal_update": [
        {"title": "Deal moved to Negotiation", "desc": "{company} deal ({value}) advanced to negotiation stage by {person}", "severity": "info"},
        {"title": "Deal closed-won", "desc": "{company} signed {value} annual contract — {person} confirmed", "severity": "info"},
        {"title": "Deal at risk — no activity", "desc": "{company} deal stalled for 14 days — last touch by {person}", "severity": "warning"},
        {"title": "Deal value increased", "desc": "{company} expanded scope from {value} to {value_up} — upsell by {person}", "severity": "info"},
    ],
    "lead_scored": [
        {"title": "High-intent lead detected", "desc": "{person} at {company} visited pricing page 3x this week — score: {score}", "severity": "info"},
        {"title": "Lead score spike", "desc": "{company} lead score jumped to {score} after demo request from {person}", "severity": "info"},
        {"title": "MQL threshold reached", "desc": "{person} ({company}) crossed MQL threshold — score: {score}", "severity": "info"},
    ],
    "churn_risk": [
        {"title": "Churn risk elevated", "desc": "{company} usage dropped 40% this month — {person} unresponsive to outreach", "severity": "critical"},
        {"title": "Support ticket surge", "desc": "{company} filed 12 tickets in 48 hours — escalation flagged for {person}", "severity": "warning"},
        {"title": "Contract renewal at risk", "desc": "{company} renewal in 30 days — {person} requested competitor comparison", "severity": "critical"},
    ],
    "sync_complete": [
        {"title": "CRM sync completed", "desc": "Salesforce sync finished — {count} records updated for {company} pipeline", "severity": "info"},
        {"title": "Data enrichment complete", "desc": "Enriched {count} contacts across {company} and 3 other accounts", "severity": "info"},
    ],
    "simulation_finished": [
        {"title": "GTM simulation complete", "desc": "Competitive displacement simulation finished — {count} agent interactions analyzed", "severity": "info"},
        {"title": "Scenario analysis ready", "desc": "Pricing sensitivity simulation for {company} segment completed in {duration}", "severity": "info"},
    ],
    "report_generated": [
        {"title": "Weekly pipeline report ready", "desc": "Pipeline forecast report generated — {value} total weighted pipeline", "severity": "info"},
        {"title": "Churn analysis report", "desc": "Monthly churn risk report ready — {count} accounts flagged across segments", "severity": "warning"},
    ],
    "reconciliation_alert": [
        {"title": "Revenue reconciliation mismatch", "desc": "{company} billing shows ${amount} discrepancy — needs review by {person}", "severity": "warning"},
        {"title": "License count mismatch", "desc": "{company} using {count} seats but contracted for {count_lower} — overage alert", "severity": "warning"},
    ],
    "order_provisioned": [
        {"title": "New account provisioned", "desc": "{company} workspace created — {count} seats activated by {person}", "severity": "info"},
        {"title": "Add-on provisioned", "desc": "Fin AI add-on enabled for {company} — requested by {person}", "severity": "info"},
    ],
    "pipeline_milestone": [
        {"title": "Pipeline target hit", "desc": "Q1 pipeline reached ${amount} — {pct}% of target with 6 weeks remaining", "severity": "info"},
        {"title": "Stage conversion record", "desc": "Discovery-to-demo conversion hit {pct}% this month — best in 4 quarters", "severity": "info"},
        {"title": "New segment pipeline opened", "desc": "Healthcare vertical pipeline opened at ${amount} — {count} qualified opportunities", "severity": "info"},
    ],
}


class ActivityFeedService:
    """Generates and serves a global activity feed across GTM domains."""

    @staticmethod
    def get_recent(limit=20, types=None, since=None):
        """Return recent activity items, optionally filtered.

        Args:
            limit: Max items to return (default 20).
            types: List of activity type strings to include (None = all).
            since: ISO 8601 datetime string — only return activities after this.

        Returns:
            List of activity dicts sorted newest-first.
        """
        activities = ActivityFeedService._generate_activities(count=50)

        if types:
            valid_types = set(types) & set(ACTIVITY_TYPES)
            if valid_types:
                activities = [a for a in activities if a["type"] in valid_types]

        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                since_ts = since_dt.timestamp()
                activities = [a for a in activities if a["_ts"] > since_ts]
            except (ValueError, AttributeError):
                pass

        for a in activities:
            a.pop("_ts", None)

        return activities[:limit]

    @staticmethod
    def _generate_activities(count=50):
        """Generate `count` realistic activities spread over the last 24 hours."""
        now = time.time()
        day_seed = int(now // 3600)
        rng = random.Random(day_seed)

        activities = []
        for i in range(count):
            offset_seconds = rng.uniform(0, 86400)
            ts = now - offset_seconds

            activity_type = rng.choice(ACTIVITY_TYPES)
            templates = _TEMPLATES[activity_type]
            template = rng.choice(templates)

            company = rng.choice(_COMPANIES)
            person_name, person_title = rng.choice(_PEOPLE)

            values = {
                "company": company,
                "person": f"{person_name} ({person_title})",
                "value": f"${rng.randint(20, 500)}K",
                "value_up": f"${rng.randint(500, 900)}K",
                "score": str(rng.randint(72, 98)),
                "count": str(rng.randint(8, 450)),
                "count_lower": str(rng.randint(20, 80)),
                "amount": f"{rng.randint(1, 50) * 100:,}",
                "duration": f"{rng.randint(2, 18)}m {rng.randint(10, 59)}s",
                "pct": str(rng.randint(60, 135)),
            }

            title = template["title"]
            desc = template["desc"].format(**values)

            activity_id = hashlib.md5(
                f"{day_seed}-{i}-{activity_type}".encode()
            ).hexdigest()[:12]

            dt = datetime.fromtimestamp(ts, tz=timezone.utc)

            activities.append({
                "id": f"act_{activity_id}",
                "type": activity_type,
                "title": title,
                "description": desc,
                "timestamp": dt.isoformat(),
                "severity": template["severity"],
                "related_entity": {
                    "type": "company",
                    "name": company,
                },
                "_ts": ts,
            })

        activities.sort(key=lambda a: a["_ts"], reverse=True)
        return activities
