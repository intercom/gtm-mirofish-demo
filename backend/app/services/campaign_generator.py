"""
Campaign ROI data generator.

Produces 15 realistic Intercom-relevant marketing campaigns with full
funnel metrics (leads → MQL → SQL → opportunity → closed-won), cost
breakdowns, and multi-touch attribution data.

All data is deterministic (seeded RNG) so repeated calls return
consistent results.
"""

import random
from typing import Dict, Any, List, Tuple

from ..models.campaign import Campaign, CampaignCostBreakdown, CampaignAttribution

# Seed for deterministic output across calls
_RNG_SEED = 42

# Default average deal size by campaign type (Intercom mid-market context)
_AVG_DEAL_SIZE = {
    "paid": 18_000,
    "organic": 14_000,
    "event": 22_000,
    "email": 12_000,
    "partner": 28_000,
}

# Default conversion-rate ranges by campaign type: (min, max) for each stage
_CONVERSION_RATES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "paid": {
        "lead_to_mql": (0.25, 0.35),
        "mql_to_sql": (0.30, 0.40),
        "sql_to_won": (0.15, 0.25),
    },
    "organic": {
        "lead_to_mql": (0.15, 0.22),
        "mql_to_sql": (0.25, 0.35),
        "sql_to_won": (0.12, 0.20),
    },
    "event": {
        "lead_to_mql": (0.28, 0.38),
        "mql_to_sql": (0.25, 0.35),
        "sql_to_won": (0.10, 0.18),
    },
    "email": {
        "lead_to_mql": (0.20, 0.30),
        "mql_to_sql": (0.28, 0.38),
        "sql_to_won": (0.15, 0.25),
    },
    "partner": {
        "lead_to_mql": (0.35, 0.40),
        "mql_to_sql": (0.40, 0.50),
        "sql_to_won": (0.25, 0.35),
    },
}

# Per-campaign overrides for conversion rates and deal size.
# Keyed by campaign index (0-based). Allows modeling the reality that
# e.g. Product Hunt signups convert much worse than partner referrals.
_CAMPAIGN_OVERRIDES: Dict[int, Dict[str, Any]] = {
    # Blog Content: early-stage top-of-funnel, long sales cycle → negative ROI
    3: {
        "rates": {
            "lead_to_mql": (0.05, 0.08),
            "mql_to_sql": (0.15, 0.22),
            "sql_to_won": (0.10, 0.15),
        },
        "avg_deal": 8_000,
    },
    # Product Hunt Launch: huge lead volume but mostly curiosity signups
    5: {
        "rates": {
            "lead_to_mql": (0.05, 0.08),
            "mql_to_sql": (0.20, 0.30),
            "sql_to_won": (0.15, 0.22),
        },
        "avg_deal": 10_000,
    },
    # SaaStr Trade Show: expensive badge scans, low conversion → negative ROI
    6: {
        "rates": {
            "lead_to_mql": (0.20, 0.28),
            "mql_to_sql": (0.18, 0.25),
            "sql_to_won": (0.10, 0.15),
        },
        "avg_deal": 20_000,
    },
    # Customer Advocacy: small volume but decent quality
    9: {
        "rates": {
            "lead_to_mql": (0.25, 0.35),
            "mql_to_sql": (0.30, 0.40),
            "sql_to_won": (0.18, 0.28),
        },
        "avg_deal": 16_000,
    },
    # Intercom Summit: better than generic trade show but still expensive
    12: {
        "rates": {
            "lead_to_mql": (0.32, 0.40),
            "mql_to_sql": (0.28, 0.38),
            "sql_to_won": (0.14, 0.20),
        },
        "avg_deal": 24_000,
    },
}

# Cost breakdown templates: maps campaign type → list of (cost_type, weight)
_COST_BREAKDOWN_TEMPLATES: Dict[str, List[Tuple[str, float]]] = {
    "paid": [
        ("ad_spend", 0.65),
        ("tools", 0.10),
        ("content", 0.10),
        ("labor", 0.15),
    ],
    "organic": [
        ("content", 0.45),
        ("tools", 0.15),
        ("labor", 0.40),
    ],
    "event": [
        ("events", 0.55),
        ("content", 0.10),
        ("labor", 0.25),
        ("tools", 0.10),
    ],
    "email": [
        ("tools", 0.20),
        ("content", 0.30),
        ("labor", 0.50),
    ],
    "partner": [
        ("labor", 0.40),
        ("content", 0.15),
        ("events", 0.20),
        ("tools", 0.25),
    ],
}

# Campaign definitions: (name, type, channel, budget, leads, start, end, status)
_CAMPAIGN_DEFS: List[Tuple[str, str, str, float, int, str, str, str]] = [
    ("LinkedIn Paid — Mid-Market SaaS", "paid", "linkedin", 50_000, 500, "2025-10-01", "2026-03-15", "active"),
    ("Google Ads — Zendesk Competitor", "paid", "google", 80_000, 800, "2025-09-15", "2026-03-25", "active"),
    ("Webinar Series — AI Support Trends", "event", "webinar", 20_000, 200, "2025-11-01", "2026-02-28", "completed"),
    ("Blog Content — Support Automation", "organic", "blog", 15_000, 600, "2025-07-01", "2026-03-25", "active"),
    ("Partner Referral Program", "partner", "referral", 30_000, 150, "2025-08-01", "2026-03-25", "active"),
    ("Product Hunt Launch — Fin AI Agent", "organic", "product_hunt", 5_000, 1_000, "2026-01-15", "2026-01-22", "completed"),
    ("SaaStr Annual Trade Show", "event", "trade_show", 100_000, 300, "2026-02-10", "2026-02-14", "completed"),
    ("Email Nurture — Trial Conversions", "email", "email", 12_000, 450, "2025-10-01", "2026-03-25", "active"),
    ("Facebook Retargeting — Demo Visitors", "paid", "facebook", 25_000, 350, "2025-11-01", "2026-03-25", "active"),
    ("Customer Advocacy — Case Studies", "organic", "case_study", 8_000, 120, "2025-09-01", "2026-03-01", "completed"),
    ("G2 & Capterra Reviews Push", "partner", "review_platform", 18_000, 220, "2025-10-15", "2026-03-15", "active"),
    ("LinkedIn Thought Leadership — CX", "organic", "linkedin_organic", 10_000, 380, "2025-08-01", "2026-03-25", "active"),
    ("Intercom Summit 2026", "event", "conference", 75_000, 500, "2026-03-05", "2026-03-07", "completed"),
    ("Cold Email — Freshdesk Migration", "email", "email", 9_000, 280, "2026-01-01", "2026-03-25", "active"),
    ("HubSpot Integration Co-Marketing", "partner", "co_marketing", 22_000, 180, "2025-12-01", "2026-03-01", "completed"),
]


def _generate_cost_breakdown(
    campaign_id: str,
    campaign_type: str,
    spend: float,
    rng: random.Random,
) -> List[CampaignCostBreakdown]:
    """Split total spend into realistic cost categories."""
    template = _COST_BREAKDOWN_TEMPLATES.get(campaign_type, _COST_BREAKDOWN_TEMPLATES["paid"])
    breakdowns = []
    remaining = spend
    for i, (cost_type, weight) in enumerate(template):
        if i == len(template) - 1:
            amount = remaining
        else:
            jitter = rng.uniform(-0.05, 0.05)
            amount = round(spend * max(0.05, weight + jitter), 2)
            remaining -= amount
        breakdowns.append(CampaignCostBreakdown(
            campaign_id=campaign_id,
            cost_type=cost_type,
            amount=round(max(0, amount), 2),
        ))
    return breakdowns


def _generate_attribution(
    campaign_id: str,
    opportunities: int,
    rng: random.Random,
) -> List[CampaignAttribution]:
    """Generate multi-touch attribution records for campaign opportunities."""
    models = ["first_touch", "last_touch", "linear", "time_decay"]
    attributions = []
    for i in range(opportunities):
        opp_id = f"opp_{campaign_id}_{i:03d}"
        credit_pool = 100.0
        for j, model in enumerate(models):
            if j == len(models) - 1:
                credit = round(credit_pool, 1)
            else:
                credit = round(rng.uniform(15, 40), 1)
                credit_pool -= credit
            attributions.append(CampaignAttribution(
                campaign_id=campaign_id,
                opportunity_id=opp_id,
                attribution_model=model,
                credit_percentage=max(0, credit),
            ))
    return attributions


def generate_campaigns() -> Dict[str, Any]:
    """
    Generate 15 realistic Intercom GTM campaigns with full funnel metrics.

    Returns a dict with keys:
        campaigns: list of Campaign dicts
        cost_breakdowns: list of CampaignCostBreakdown dicts
        attributions: list of CampaignAttribution dicts
    """
    rng = random.Random(_RNG_SEED)

    campaigns: List[Campaign] = []
    all_breakdowns: List[CampaignCostBreakdown] = []
    all_attributions: List[CampaignAttribution] = []

    for idx, (name, ctype, channel, budget, leads, start, end, status) in enumerate(_CAMPAIGN_DEFS):
        campaign_id = f"camp_{idx + 1:03d}"
        overrides = _CAMPAIGN_OVERRIDES.get(idx, {})
        rates = overrides.get("rates", _CONVERSION_RATES[ctype])

        # Spend: completed campaigns use ~90-100% of budget, active ~50-80%, planned ~0
        if status == "completed":
            spend_ratio = rng.uniform(0.88, 1.0)
        elif status == "active":
            spend_ratio = rng.uniform(0.50, 0.80)
        else:
            spend_ratio = 0.0
        spend = round(budget * spend_ratio, 2)

        # Funnel conversion with seeded randomness within type ranges
        mql_rate = rng.uniform(*rates["lead_to_mql"])
        sql_rate = rng.uniform(*rates["mql_to_sql"])
        won_rate = rng.uniform(*rates["sql_to_won"])

        mqls = int(leads * mql_rate)
        sqls = int(mqls * sql_rate)
        opportunities = max(1, int(sqls * rng.uniform(0.6, 0.9)))
        raw_won = opportunities * won_rate
        won_deals = max(0, round(raw_won))

        avg_deal = overrides.get("avg_deal", _AVG_DEAL_SIZE[ctype])
        deal_variation = rng.uniform(0.8, 1.3)
        closed_won_value = round(won_deals * avg_deal * deal_variation, 2)

        # Derived metrics
        cpl = round(spend / leads, 2) if leads > 0 else 0
        cpa = round(spend / won_deals, 2) if won_deals > 0 else 0
        roi_pct = round((closed_won_value - spend) / spend * 100, 1) if spend > 0 else 0

        campaign = Campaign(
            id=campaign_id,
            name=name,
            type=ctype,
            channel=channel,
            start_date=start,
            end_date=end,
            budget=budget,
            spend_to_date=spend,
            leads_generated=leads,
            mqls=mqls,
            sqls=sqls,
            opportunities=opportunities,
            closed_won_value=closed_won_value,
            cpl=cpl,
            cpa=cpa,
            roi_percentage=roi_pct,
            status=status,
        )
        campaigns.append(campaign)

        # Cost breakdown
        breakdowns = _generate_cost_breakdown(campaign_id, ctype, spend, rng)
        all_breakdowns.extend(breakdowns)

        # Attribution
        attributions = _generate_attribution(campaign_id, opportunities, rng)
        all_attributions.extend(attributions)

    return {
        "campaigns": [c.to_dict() for c in campaigns],
        "cost_breakdowns": [b.to_dict() for b in all_breakdowns],
        "attributions": [a.to_dict() for a in all_attributions],
    }


def get_campaign_stats(campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate statistics across all campaigns."""
    total_spend = sum(c["spend_to_date"] for c in campaigns)
    total_revenue = sum(c["closed_won_value"] for c in campaigns)
    total_leads = sum(c["leads_generated"] for c in campaigns)

    best = max(campaigns, key=lambda c: c["roi_percentage"])
    worst = min(campaigns, key=lambda c: c["roi_percentage"])

    spend_by_type: Dict[str, float] = {}
    for c in campaigns:
        spend_by_type[c["type"]] = spend_by_type.get(c["type"], 0) + c["spend_to_date"]

    overall_roi = round((total_revenue - total_spend) / total_spend * 100, 1) if total_spend > 0 else 0

    return {
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2),
        "total_leads": total_leads,
        "overall_roi": overall_roi,
        "best_campaign": {"id": best["id"], "name": best["name"], "roi": best["roi_percentage"]},
        "worst_campaign": {"id": worst["id"], "name": worst["name"], "roi": worst["roi_percentage"]},
        "spend_by_type": {k: round(v, 2) for k, v in spend_by_type.items()},
    }


def get_roi_comparison(campaigns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return campaigns ranked by ROI percentage (descending)."""
    return sorted(
        [
            {
                "id": c["id"],
                "name": c["name"],
                "type": c["type"],
                "channel": c["channel"],
                "spend": c["spend_to_date"],
                "revenue": c["closed_won_value"],
                "roi_percentage": c["roi_percentage"],
                "leads": c["leads_generated"],
                "status": c["status"],
            }
            for c in campaigns
        ],
        key=lambda x: x["roi_percentage"],
        reverse=True,
    )


def get_budget_efficiency(campaigns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return per-channel efficiency metrics (CPL, CPA)."""
    by_channel: Dict[str, Dict[str, float]] = {}
    for c in campaigns:
        ch = c["channel"]
        if ch not in by_channel:
            by_channel[ch] = {"spend": 0, "leads": 0, "won_deals": 0, "revenue": 0}
        by_channel[ch]["spend"] += c["spend_to_date"]
        by_channel[ch]["leads"] += c["leads_generated"]
        by_channel[ch]["won_deals"] += c["opportunities"]
        by_channel[ch]["revenue"] += c["closed_won_value"]

    result = []
    for ch, d in by_channel.items():
        result.append({
            "channel": ch,
            "total_spend": round(d["spend"], 2),
            "total_leads": d["leads"],
            "cpl": round(d["spend"] / d["leads"], 2) if d["leads"] > 0 else 0,
            "cpa": round(d["spend"] / d["won_deals"], 2) if d["won_deals"] > 0 else 0,
            "revenue": round(d["revenue"], 2),
        })
    return sorted(result, key=lambda x: x["cpl"])
