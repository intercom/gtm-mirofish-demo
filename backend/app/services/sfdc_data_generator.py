"""
Salesforce demo data generator.
Produces deterministic, realistic CRM data for GTM simulation demos.
Data is cached in-memory after first generation.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

from ..models.salesforce import Account, Opportunity, Contact, Lead

_cache: Dict[str, Any] = {}

SEED = 42

INDUSTRIES = ["Technology", "Finance", "Healthcare", "Retail", "Education"]

PLAN_TIERS = ["Essential", "Advanced", "Expert"]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]

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

ROLES = ["Decision Maker", "Influencer", "Champion", "End User", "Executive Sponsor"]

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

STAGE_PROBABILITY = {
    "Prospecting": 10,
    "Discovery": 25,
    "Proposal": 50,
    "Negotiation": 75,
    "Closed Won": 100,
    "Closed Lost": 0,
}

EMPLOYEE_COUNTS = [50, 100, 250, 500, 1000, 2500, 5000, 10000]

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


def _generate_accounts(rng: random.Random) -> List[Account]:
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
        arr = round(rng.uniform(10_000, 500_000), -2)
        health = rng.randint(1, 100)

        accounts.append(Account(
            id=_make_id(rng),
            name=name,
            industry=industry,
            arr=arr,
            plan_tier=tier,
            health_score=health,
            owner=rng.choice(OWNER_NAMES),
            created_date=_make_date(rng, 730, 30),
            renewal_date=_make_future_date(rng, 30, 365),
            employee_count=rng.choice(EMPLOYEE_COUNTS),
            website=f"https://www.{name.lower().replace(' ', '')}.com",
            region=rng.choice(REGIONS),
        ))

    return accounts


def _generate_contacts(rng: random.Random, accounts: List[Account]) -> List[Contact]:
    contacts = []
    for acct in accounts:
        count = rng.randint(1, 3)
        for _ in range(count):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            domain = acct.name.lower().replace(" ", "") + ".com"
            contacts.append(Contact(
                id=_make_id(rng),
                first_name=first,
                last_name=last,
                email=f"{first.lower()}.{last.lower()}@{domain}",
                account_id=acct.id,
                title=rng.choice(TITLES),
                role=rng.choice(ROLES),
                last_activity=_make_date(rng, 60, 0),
            ))
    return contacts


def _generate_opportunities(rng: random.Random, accounts: List[Account]) -> List[Opportunity]:
    opps = []
    stage_weights = [20, 15, 15, 15, 20, 15]

    for _ in range(30):
        acct = rng.choice(accounts)
        stage = rng.choices(OPPORTUNITY_STAGES, weights=stage_weights, k=1)[0]
        amount = round(rng.uniform(5_000, 300_000), -2)
        opp_type = rng.choice(OPPORTUNITY_TYPES)

        if stage in ("Closed Won", "Closed Lost"):
            close_date = _make_date(rng, 90, 0)
        else:
            close_date = _make_future_date(rng, 14, 180)

        opps.append(Opportunity(
            id=_make_id(rng),
            name=f"{acct.name} — {opp_type}",
            account_id=acct.id,
            stage=stage,
            amount=amount,
            close_date=close_date,
            probability=STAGE_PROBABILITY[stage],
            owner=rng.choice(OWNER_NAMES),
            type=opp_type,
            created_date=_make_date(rng, 180, 0),
        ))

    return opps


def _generate_leads(rng: random.Random) -> List[Lead]:
    leads = []
    status_weights = [25, 25, 20, 15, 15]

    for _ in range(40):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        company = f"{rng.choice(COMPANY_PREFIXES)} {rng.choice(COMPANY_SUFFIXES)}"
        status = rng.choices(LEAD_STATUSES, weights=status_weights, k=1)[0]

        leads.append(Lead(
            id=_make_id(rng),
            first_name=first,
            last_name=last,
            email=f"{first.lower()}.{last.lower()}@{company.lower().replace(' ', '')}.com",
            company=company,
            status=status,
            source=rng.choice(LEAD_SOURCES),
            score=rng.randint(1, 100),
            owner=rng.choice(OWNER_NAMES),
            created_date=_make_date(rng, 180, 0),
        ))

    return leads


def get_data() -> Dict[str, List]:
    """Return all generated Salesforce demo data. Cached after first call."""
    if _cache:
        return _cache

    rng = random.Random(SEED)
    accounts = _generate_accounts(rng)
    contacts = _generate_contacts(rng, accounts)
    opportunities = _generate_opportunities(rng, accounts)
    leads = _generate_leads(rng)

    _cache["accounts"] = accounts
    _cache["contacts"] = contacts
    _cache["opportunities"] = opportunities
    _cache["leads"] = leads
    return _cache
