"""
Campaign ROI data generator.
Produces 15 realistic Intercom-relevant campaigns with conversion funnels,
cost breakdowns, and multi-touch attribution data.
"""

import random

from ..models.campaign import Campaign, CampaignCostBreakdown, CampaignAttribution

# Seeded RNG for deterministic output across calls
_rng = random.Random(42)

# Raw campaign definitions
_CAMPAIGN_DEFS = [
    {
        'id': 'camp-linkedin-paid',
        'name': 'LinkedIn Paid Ads — Enterprise ICPs',
        'type': 'paid', 'channel': 'LinkedIn',
        'start_date': '2025-01-15', 'end_date': '2025-06-30',
        'budget': 50000, 'spend_to_date': 47200,
        'leads': 500, 'mql_rate': 0.32, 'sql_rate': 0.40, 'win_rate': 0.22,
        'avg_deal': 42000, 'status': 'active',
        'costs': [('ad_spend', 38000), ('tools', 3200), ('content', 4000), ('labor', 2000)],
    },
    {
        'id': 'camp-google-ads',
        'name': 'Google Ads — Product Keywords',
        'type': 'paid', 'channel': 'Google Ads',
        'start_date': '2025-01-01', 'end_date': '2025-12-31',
        'budget': 80000, 'spend_to_date': 72500,
        'leads': 800, 'mql_rate': 0.28, 'sql_rate': 0.35, 'win_rate': 0.18,
        'avg_deal': 28000, 'status': 'active',
        'costs': [('ad_spend', 62000), ('tools', 4500), ('labor', 6000)],
    },
    {
        'id': 'camp-webinar-series',
        'name': 'Webinar Series — AI in Customer Support',
        'type': 'event', 'channel': 'Webinar',
        'start_date': '2025-02-01', 'end_date': '2025-05-31',
        'budget': 20000, 'spend_to_date': 18500,
        'leads': 200, 'mql_rate': 0.40, 'sql_rate': 0.45, 'win_rate': 0.30,
        'avg_deal': 35000, 'status': 'completed',
        'costs': [('tools', 5000), ('content', 6500), ('labor', 7000)],
    },
    {
        'id': 'camp-blog-content',
        'name': 'Blog Content Program',
        'type': 'organic', 'channel': 'Blog / SEO',
        'start_date': '2025-01-01', 'end_date': '2025-12-31',
        'budget': 15000, 'spend_to_date': 13200,
        'leads': 600, 'mql_rate': 0.25, 'sql_rate': 0.30, 'win_rate': 0.15,
        'avg_deal': 22000, 'status': 'active',
        'costs': [('content', 9000), ('tools', 1200), ('labor', 3000)],
    },
    {
        'id': 'camp-partner-referrals',
        'name': 'Partner Referral Program',
        'type': 'partner', 'channel': 'Partners',
        'start_date': '2025-03-01', 'end_date': '2025-12-31',
        'budget': 30000, 'spend_to_date': 24000,
        'leads': 150, 'mql_rate': 0.55, 'sql_rate': 0.50, 'win_rate': 0.35,
        'avg_deal': 55000, 'status': 'active',
        'costs': [('ad_spend', 12000), ('events', 5000), ('labor', 7000)],
    },
    {
        'id': 'camp-product-hunt',
        'name': 'Product Hunt Launch — Fin AI',
        'type': 'organic', 'channel': 'Product Hunt',
        'start_date': '2025-04-01', 'end_date': '2025-04-07',
        'budget': 5000, 'spend_to_date': 4800,
        'leads': 1000, 'mql_rate': 0.12, 'sql_rate': 0.25, 'win_rate': 0.10,
        'avg_deal': 15000, 'status': 'completed',
        'costs': [('content', 2000), ('labor', 2800)],
    },
    {
        'id': 'camp-trade-show',
        'name': 'SaaStr Annual Trade Show',
        'type': 'event', 'channel': 'Trade Show',
        'start_date': '2025-09-15', 'end_date': '2025-09-18',
        'budget': 100000, 'spend_to_date': 95000,
        'leads': 300, 'mql_rate': 0.35, 'sql_rate': 0.30, 'win_rate': 0.12,
        'avg_deal': 60000, 'status': 'completed',
        'costs': [('events', 65000), ('content', 10000), ('labor', 15000), ('tools', 5000)],
    },
    {
        'id': 'camp-email-nurture',
        'name': 'Email Nurture — Trial-to-Paid',
        'type': 'email', 'channel': 'Email',
        'start_date': '2025-01-01', 'end_date': '2025-12-31',
        'budget': 12000, 'spend_to_date': 9800,
        'leads': 450, 'mql_rate': 0.38, 'sql_rate': 0.42, 'win_rate': 0.28,
        'avg_deal': 18000, 'status': 'active',
        'costs': [('tools', 4800), ('content', 3000), ('labor', 2000)],
    },
    {
        'id': 'camp-g2-review',
        'name': 'G2 Review Campaign',
        'type': 'organic', 'channel': 'G2 / Review Sites',
        'start_date': '2025-02-15', 'end_date': '2025-08-31',
        'budget': 8000, 'spend_to_date': 7200,
        'leads': 180, 'mql_rate': 0.45, 'sql_rate': 0.40, 'win_rate': 0.25,
        'avg_deal': 30000, 'status': 'active',
        'costs': [('tools', 3200), ('content', 2000), ('labor', 2000)],
    },
    {
        'id': 'camp-youtube-tutorials',
        'name': 'YouTube Tutorial Series',
        'type': 'organic', 'channel': 'YouTube',
        'start_date': '2025-03-01', 'end_date': '2025-12-31',
        'budget': 25000, 'spend_to_date': 22000,
        'leads': 350, 'mql_rate': 0.20, 'sql_rate': 0.30, 'win_rate': 0.15,
        'avg_deal': 20000, 'status': 'active',
        'costs': [('content', 14000), ('tools', 3000), ('labor', 5000)],
    },
    {
        'id': 'camp-facebook-retarget',
        'name': 'Facebook Retargeting — Site Visitors',
        'type': 'paid', 'channel': 'Facebook',
        'start_date': '2025-04-01', 'end_date': '2025-09-30',
        'budget': 18000, 'spend_to_date': 16500,
        'leads': 220, 'mql_rate': 0.30, 'sql_rate': 0.35, 'win_rate': 0.20,
        'avg_deal': 25000, 'status': 'active',
        'costs': [('ad_spend', 13500), ('tools', 1500), ('labor', 1500)],
    },
    {
        'id': 'camp-podcast-sponsor',
        'name': 'Podcast Sponsorships — SaaS Shows',
        'type': 'paid', 'channel': 'Podcast',
        'start_date': '2025-02-01', 'end_date': '2025-07-31',
        'budget': 35000, 'spend_to_date': 33000,
        'leads': 120, 'mql_rate': 0.25, 'sql_rate': 0.33, 'win_rate': 0.20,
        'avg_deal': 45000, 'status': 'completed',
        'costs': [('ad_spend', 28000), ('content', 3000), ('labor', 2000)],
    },
    {
        'id': 'camp-customer-advocacy',
        'name': 'Customer Advocacy / Case Studies',
        'type': 'partner', 'channel': 'Customer Stories',
        'start_date': '2025-01-15', 'end_date': '2025-12-31',
        'budget': 10000, 'spend_to_date': 8500,
        'leads': 90, 'mql_rate': 0.50, 'sql_rate': 0.55, 'win_rate': 0.40,
        'avg_deal': 50000, 'status': 'active',
        'costs': [('content', 5000), ('labor', 3500)],
    },
    {
        'id': 'camp-abm-enterprise',
        'name': 'ABM — Fortune 500 Target List',
        'type': 'paid', 'channel': 'ABM / Direct',
        'start_date': '2025-05-01', 'end_date': '2025-11-30',
        'budget': 60000, 'spend_to_date': 45000,
        'leads': 40, 'mql_rate': 0.60, 'sql_rate': 0.50, 'win_rate': 0.25,
        'avg_deal': 120000, 'status': 'active',
        'costs': [('ad_spend', 20000), ('tools', 8000), ('content', 7000), ('labor', 10000)],
    },
    {
        'id': 'camp-community-slack',
        'name': 'Community Slack + Events',
        'type': 'organic', 'channel': 'Community',
        'start_date': '2025-01-01', 'end_date': '2025-12-31',
        'budget': 6000, 'spend_to_date': 5200,
        'leads': 280, 'mql_rate': 0.18, 'sql_rate': 0.28, 'win_rate': 0.12,
        'avg_deal': 16000, 'status': 'active',
        'costs': [('tools', 2200), ('labor', 3000)],
    },
]

# Opportunity IDs for attribution
_OPP_IDS = [f'opp-{i:04d}' for i in range(1, 201)]


def _build_campaign(defn: dict) -> Campaign:
    """Convert a raw definition dict into a fully-computed Campaign."""
    leads = defn['leads']
    mqls = int(leads * defn['mql_rate'])
    sqls = int(mqls * defn['sql_rate'])
    opps = int(sqls * defn['win_rate'])
    closed_won = opps * defn['avg_deal']
    spend = defn['spend_to_date']
    cpl = round(spend / leads, 2) if leads else 0
    cpa = round(spend / opps, 2) if opps else 0
    roi = round((closed_won - spend) / spend * 100, 2) if spend else 0

    cost_breakdown = [
        CampaignCostBreakdown(campaign_id=defn['id'], cost_type=ct, amount=amt)
        for ct, amt in defn['costs']
    ]

    # Generate deterministic attribution records
    rng = random.Random(hash(defn['id']))
    opp_sample = rng.sample(_OPP_IDS, min(opps, len(_OPP_IDS)))
    attributions = []
    for model in ('first_touch', 'last_touch', 'linear', 'time_decay'):
        for opp_id in opp_sample:
            credit = round(rng.uniform(5, 100), 1)
            attributions.append(CampaignAttribution(
                campaign_id=defn['id'],
                opportunity_id=opp_id,
                attribution_model=model,
                credit_percentage=credit,
            ))

    return Campaign(
        id=defn['id'],
        name=defn['name'],
        type=defn['type'],
        channel=defn['channel'],
        start_date=defn['start_date'],
        end_date=defn['end_date'],
        budget=defn['budget'],
        spend_to_date=spend,
        leads_generated=leads,
        mqls=mqls,
        sqls=sqls,
        opportunities=opps,
        closed_won_value=closed_won,
        cpl=cpl,
        cpa=cpa,
        roi_percentage=roi,
        status=defn['status'],
        cost_breakdown=cost_breakdown,
        attributions=attributions,
    )


# Module-level cache — built once, reused across requests
_campaigns_cache: list | None = None


def get_campaigns() -> list[Campaign]:
    """Return all generated campaigns (cached)."""
    global _campaigns_cache
    if _campaigns_cache is None:
        _campaigns_cache = [_build_campaign(d) for d in _CAMPAIGN_DEFS]
    return _campaigns_cache


# Aliases expected by the barrel file (services/__init__.py)
generate_campaigns = get_campaigns


def get_campaign_stats() -> dict:
    """Aggregate stats across all campaigns."""
    campaigns = get_campaigns()
    total_spend = sum(c.spend_to_date for c in campaigns)
    total_revenue = sum(c.closed_won_value for c in campaigns)
    return {
        'total_spend': total_spend,
        'total_revenue': total_revenue,
        'overall_roi': round((total_revenue - total_spend) / total_spend * 100, 2) if total_spend else 0,
        'campaign_count': len(campaigns),
    }


def get_roi_comparison() -> list[dict]:
    """All campaigns ranked by ROI percentage (descending)."""
    return sorted(
        [{'id': c.id, 'name': c.name, 'roi_percentage': c.roi_percentage} for c in get_campaigns()],
        key=lambda x: x['roi_percentage'],
        reverse=True,
    )


def get_budget_efficiency() -> list[dict]:
    """Spend efficiency (CPL/CPA) grouped by channel."""
    by_channel: dict[str, dict] = {}
    for c in get_campaigns():
        b = by_channel.setdefault(c.channel, {'spend': 0, 'leads': 0, 'opps': 0})
        b['spend'] += c.spend_to_date
        b['leads'] += c.leads_generated
        b['opps'] += c.opportunities
    return [
        {
            'channel': ch,
            'cpl': round(v['spend'] / v['leads'], 2) if v['leads'] else 0,
            'cpa': round(v['spend'] / v['opps'], 2) if v['opps'] else 0,
        }
        for ch, v in by_channel.items()
    ]
