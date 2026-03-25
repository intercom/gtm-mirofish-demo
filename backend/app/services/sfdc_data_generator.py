"""
Salesforce demo data generator.
Produces deterministic, realistic CRM data for GTM simulation demos.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Module-level cache — generated once, served from memory thereafter
_cache: Dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

INDUSTRIES = ["Technology", "Finance", "Healthcare", "Retail", "Education"]

PLAN_TIERS = ["Essential", "Advanced", "Expert"]

OPPORTUNITY_STAGES = [
    "Prospecting", "Discovery", "Proposal",
    "Negotiation", "Closed Won", "Closed Lost",
]

LEAD_STATUSES = ["New", "Contacted", "Qualified", "Converted", "Disqualified"]

LEAD_SOURCES = [
    "Website", "Webinar", "Referral", "Outbound",
    "Partner", "Event", "Content Download", "Free Trial",
]

TITLES = [
    "VP of Sales", "Director of CS", "CTO", "Head of Support",
    "VP of Engineering", "Director of Product", "COO",
    "Head of Growth", "Director of Marketing", "VP of Operations",
    "Chief Revenue Officer", "IT Director", "Head of Partnerships",
    "Director of Customer Success", "VP of Customer Experience",
]

FIRST_NAMES = [
    "James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert",
    "Ashley", "William", "Amanda", "Daniel", "Megan", "Christopher",
    "Lauren", "Matthew", "Rachel", "Andrew", "Nicole", "Joshua", "Stephanie",
    "Brian", "Priya", "Carlos", "Wei", "Fatima", "Kenji", "Olga",
    "Aarav", "Mei", "Diego", "Aisha", "Ravi", "Yuki", "Sofia",
    "Omar", "Lena", "Tariq", "Ingrid", "Jin", "Elena",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas",
    "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Patel", "Chen", "Kumar", "Nakamura", "Ali", "Sato", "Ivanova",
    "Sharma", "Zhang", "Lopez", "Hassan", "Gupta", "Tanaka", "Fernandez",
    "Nielsen", "Volkov", "Park", "Johansson", "Kim", "Rossi",
]

COMPANY_PREFIXES = [
    "Apex", "Summit", "Vertex", "Nexus", "Pulse", "Orbit", "Forge",
    "Nova", "Crest", "Vibe", "Flux", "Zen", "Prism", "Lumen",
    "Atlas", "Echo", "Drift", "Hive", "Arc", "Core", "Sync",
    "Bolt", "Peak", "Dash", "Grid", "Loop", "Spark", "Wave",
    "Slate", "Bloom", "Harbor", "Ridge", "Fern", "Pine", "Cedar",
]

COMPANY_SUFFIXES = [
    "Systems", "Labs", "Analytics", "Software", "Cloud", "Digital",
    "Technologies", "Solutions", "AI", "Data", "Health", "Finance",
    "Payments", "Platform", "Commerce", "Security", "Insights", "Logic",
    "Works", "IO", "HQ", "Stack", "Base", "Hub", "Corp",
]

OPPORTUNITY_TYPES = ["New Business", "Expansion", "Renewal"]

# Stage → probability mapping
STAGE_PROBABILITY = {
    "Prospecting": 10,
    "Discovery": 25,
    "Proposal": 50,
    "Negotiation": 75,
    "Closed Won": 100,
    "Closed Lost": 0,
}

OWNER_NAMES = [
    "Alex Rivera", "Jordan Chen", "Taylor Kim", "Morgan Patel",
    "Casey Wright", "Jamie Brooks", "Drew Foster", "Quinn Nakamura",
]


def _make_id(rng: random.Random) -> str:
    return uuid.UUID(int=rng.getrandbits(128), version=4).hex[:18]


def _make_date(rng: random.Random, start_days_ago: int, end_days_ago: int) -> str:
    """Return an ISO date string between start_days_ago and end_days_ago before today."""
    base = datetime(2026, 3, 24)
    delta = rng.randint(end_days_ago, start_days_ago)
    return (base - timedelta(days=delta)).strftime("%Y-%m-%d")


def _make_future_date(rng: random.Random, min_days: int, max_days: int) -> str:
    base = datetime(2026, 3, 24)
    delta = rng.randint(min_days, max_days)
    return (base + timedelta(days=delta)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def _generate_accounts(rng: random.Random) -> List[Dict]:
    accounts = []
    used_names: set = set()

    for i in range(50):
        while True:
            name = f"{rng.choice(COMPANY_PREFIXES)} {rng.choice(COMPANY_SUFFIXES)}"
            if name not in used_names:
                used_names.add(name)
                break

        industry = INDUSTRIES[i % len(INDUSTRIES)]
        tier = rng.choice(PLAN_TIERS)
        arr = round(rng.uniform(10_000, 500_000), -2)  # rounded to nearest $100
        health = rng.randint(1, 100)

        accounts.append({
            "id": _make_id(rng),
            "name": name,
            "industry": industry,
            "arr": arr,
            "plan_tier": tier,
            "health_score": health,
            "owner": rng.choice(OWNER_NAMES),
            "created_date": _make_date(rng, 730, 30),
            "renewal_date": _make_future_date(rng, 30, 365),
        })

    return accounts


def _generate_contacts(rng: random.Random, accounts: List[Dict]) -> List[Dict]:
    contacts = []
    for acct in accounts:
        count = rng.randint(1, 3)
        for _ in range(count):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            domain = acct["name"].lower().replace(" ", "") + ".com"
            contacts.append({
                "id": _make_id(rng),
                "first_name": first,
                "last_name": last,
                "email": f"{first.lower()}.{last.lower()}@{domain}",
                "account_id": acct["id"],
                "account_name": acct["name"],
                "title": rng.choice(TITLES),
                "role": rng.choice(["Decision Maker", "Influencer", "Champion", "End User"]),
                "last_activity": _make_date(rng, 60, 0),
            })
    return contacts


def _generate_opportunities(rng: random.Random, accounts: List[Dict]) -> List[Dict]:
    opps = []
    stage_weights = [20, 15, 15, 15, 20, 15]  # distribution across stages

    for i in range(30):
        acct = rng.choice(accounts)
        stage = rng.choices(OPPORTUNITY_STAGES, weights=stage_weights, k=1)[0]
        amount = round(rng.uniform(5_000, 300_000), -2)
        opp_type = rng.choice(OPPORTUNITY_TYPES)

        if stage in ("Closed Won", "Closed Lost"):
            close_date = _make_date(rng, 90, 0)
        else:
            close_date = _make_future_date(rng, 14, 180)

        opps.append({
            "id": _make_id(rng),
            "name": f"{acct['name']} — {opp_type}",
            "account_id": acct["id"],
            "account_name": acct["name"],
            "stage": stage,
            "amount": amount,
            "close_date": close_date,
            "probability": STAGE_PROBABILITY[stage],
            "owner": rng.choice(OWNER_NAMES),
            "type": opp_type,
        })

    return opps


def _generate_leads(rng: random.Random) -> List[Dict]:
    leads = []
    status_weights = [25, 25, 20, 15, 15]  # distribution across statuses

    for _ in range(40):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        company = f"{rng.choice(COMPANY_PREFIXES)} {rng.choice(COMPANY_SUFFIXES)}"
        status = rng.choices(LEAD_STATUSES, weights=status_weights, k=1)[0]

        leads.append({
            "id": _make_id(rng),
            "first_name": first,
            "last_name": last,
            "email": f"{first.lower()}.{last.lower()}@{company.lower().replace(' ', '')}.com",
            "company": company,
            "status": status,
            "source": rng.choice(LEAD_SOURCES),
            "score": rng.randint(1, 100),
            "owner": rng.choice(OWNER_NAMES),
        })

    return leads


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all(seed: int = 42) -> Dict[str, Any]:
    """
    Generate the full Salesforce demo dataset.

    Returns cached data on subsequent calls with the same seed.
    """
    cache_key = f"sfdc_{seed}"
    if cache_key in _cache:
        return _cache[cache_key]

    rng = random.Random(seed)

    accounts = _generate_accounts(rng)
    contacts = _generate_contacts(rng, accounts)
    opportunities = _generate_opportunities(rng, accounts)
    leads = _generate_leads(rng)

    data = {
        "accounts": accounts,
        "contacts": contacts,
        "opportunities": opportunities,
        "leads": leads,
    }

    _cache[cache_key] = data
    return data


def get_accounts(
    seed: int = 42,
    industry: Optional[str] = None,
    tier: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """Return paginated, optionally filtered accounts."""
    items = generate_all(seed)["accounts"]
    if industry:
        items = [a for a in items if a["industry"].lower() == industry.lower()]
    if tier:
        items = [a for a in items if a["plan_tier"].lower() == tier.lower()]
    return _paginate(items, page, per_page)


def get_account(account_id: str, seed: int = 42) -> Optional[Dict[str, Any]]:
    """Return a single account with its related contacts and opportunities."""
    data = generate_all(seed)
    acct = next((a for a in data["accounts"] if a["id"] == account_id), None)
    if not acct:
        return None
    return {
        **acct,
        "contacts": [c for c in data["contacts"] if c["account_id"] == account_id],
        "opportunities": [o for o in data["opportunities"] if o["account_id"] == account_id],
    }


def get_contacts(
    seed: int = 42,
    account_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """Return paginated contacts, optionally filtered by account."""
    items = generate_all(seed)["contacts"]
    if account_id:
        items = [c for c in items if c["account_id"] == account_id]
    return _paginate(items, page, per_page)


def get_opportunities(
    seed: int = 42,
    stage: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """Return paginated opportunities, optionally filtered by stage."""
    items = generate_all(seed)["opportunities"]
    if stage:
        items = [o for o in items if o["stage"].lower() == stage.lower()]
    return _paginate(items, page, per_page)


def get_leads(
    seed: int = 42,
    status: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """Return paginated leads, optionally filtered by status/source."""
    items = generate_all(seed)["leads"]
    if status:
        items = [l for l in items if l["status"].lower() == status.lower()]
    if source:
        items = [l for l in items if l["source"].lower() == source.lower()]
    return _paginate(items, page, per_page)


def get_stats(seed: int = 42) -> Dict[str, Any]:
    """Aggregate CRM statistics."""
    data = generate_all(seed)
    accounts = data["accounts"]
    opps = data["opportunities"]
    leads = data["leads"]

    total_arr = sum(a["arr"] for a in accounts)
    avg_health = round(sum(a["health_score"] for a in accounts) / len(accounts), 1)

    open_stages = {"Prospecting", "Discovery", "Proposal", "Negotiation"}
    pipeline_value = sum(o["amount"] for o in opps if o["stage"] in open_stages)

    converted = sum(1 for l in leads if l["status"] == "Converted")
    lead_conversion_rate = round(converted / len(leads) * 100, 1) if leads else 0

    return {
        "total_accounts": len(accounts),
        "total_arr": round(total_arr, 2),
        "avg_health_score": avg_health,
        "pipeline_value": round(pipeline_value, 2),
        "lead_conversion_rate": lead_conversion_rate,
        "total_opportunities": len(opps),
        "total_leads": len(leads),
        "total_contacts": len(data["contacts"]),
        "accounts_by_industry": _count_by(accounts, "industry"),
        "accounts_by_tier": _count_by(accounts, "plan_tier"),
        "opportunities_by_stage": _count_by(opps, "stage"),
        "leads_by_status": _count_by(leads, "status"),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paginate(items: List[Dict], page: int, per_page: int) -> Dict[str, Any]:
    page = max(1, page)
    per_page = max(1, min(per_page, 100))
    total = len(items)
    start = (page - 1) * per_page
    return {
        "data": items[start : start + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def _count_by(items: List[Dict], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        val = item.get(key, "Unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts
