"""
Salesforce demo data generator.
Generates realistic B2B SaaS CRM data with seed-based deterministic randomness.
Data is cached in-memory after first generation.
"""

import random
from typing import Dict, List, Any

from ..models.salesforce import Account, Opportunity, Contact, Lead

_cache: Dict[str, Any] = {}

SEED = 42

COMPANY_NAMES = [
    "TechFlow Systems", "DataVault Inc", "CloudPeak Software", "NexGen Analytics",
    "Quantum Health", "FinServe Pro", "EduSync Platform", "RetailEdge AI",
    "MediCore Solutions", "GreenGrid Energy", "CyberShield Corp", "PayWave Digital",
    "LearnBridge Co", "SupplyChain360", "InsureTech Global", "AgriData Labs",
    "PropTech Ventures", "TravelMind AI", "FoodChain Systems", "AutoPilot SaaS",
    "BioGenix Labs", "LegalFlow Inc", "BuildSmart Tech", "MediaPulse AI",
    "SportsTech Pro", "PharmaLink Cloud", "LogiTrack Systems", "HireWell Platform",
    "WealthPath Analytics", "CleanTech Solutions", "AeroSpace Data", "PetCare Digital",
    "FashionForward AI", "GameStack Studios", "MusicStream Pro", "CryptoVault Inc",
    "SolarWave Energy", "RoboFleet Systems", "NeuroTech AI", "OceanData Labs",
    "UrbanPlan Software", "FitTech Global", "EcoTrack Systems", "DroneLogix Corp",
    "SmartFactory AI", "CodeBridge Platform", "EventPulse Inc", "FarmTech Digital",
    "ClimateSense AI", "VoiceBox Systems",
]

INDUSTRIES = ["Technology", "Finance", "Healthcare", "Retail", "Education"]

PLAN_TIERS = ["Essential", "Advanced", "Expert"]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]

OWNERS = [
    "Sarah Chen", "Marcus Johnson", "Emily Rodriguez", "David Kim",
    "Rachel Patel", "James O'Brien", "Lisa Nakamura", "Tom Fischer",
]

FIRST_NAMES = [
    "Alex", "Jordan", "Casey", "Morgan", "Taylor", "Riley", "Avery", "Quinn",
    "Cameron", "Drew", "Jamie", "Skyler", "Parker", "Reese", "Dakota", "Hayden",
    "Blake", "Finley", "Rowan", "Sage", "Kai", "River", "Phoenix", "Emery",
    "Arden", "Marlowe", "Ellis", "Lennox", "Ainsley", "Sutton",
]

LAST_NAMES = [
    "Anderson", "Brooks", "Carter", "Davis", "Edwards", "Foster", "Garcia",
    "Hayes", "Ibrahim", "Jensen", "Khan", "Lee", "Martinez", "Nguyen",
    "O'Sullivan", "Park", "Quinn", "Rivera", "Singh", "Thompson",
    "Ueda", "Vasquez", "Williams", "Xu", "Yang", "Zhang",
]

TITLES = [
    "VP of Sales", "Director of Customer Success", "CTO", "Head of Product",
    "VP of Engineering", "Director of Marketing", "COO", "Head of Operations",
    "VP of Business Development", "Director of IT", "Chief Revenue Officer",
    "Head of Growth", "VP of Customer Experience",
]

ROLES = ["Decision Maker", "Influencer", "Champion", "End User", "Executive Sponsor"]

OPP_STAGES = ["Prospecting", "Discovery", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
OPP_STAGE_PROB = {"Prospecting": 10, "Discovery": 25, "Proposal": 50, "Negotiation": 75, "Closed Won": 100, "Closed Lost": 0}

LEAD_STATUSES = ["New", "Contacted", "Qualified", "Converted", "Disqualified"]
LEAD_SOURCES = ["Website", "Referral", "Conference", "Outbound", "Partner", "Webinar", "Content Download"]


def _generate_date(rng: random.Random, year: int, month_start: int = 1, month_end: int = 12) -> str:
    month = rng.randint(month_start, month_end)
    day = rng.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def _generate_accounts(rng: random.Random) -> List[Account]:
    accounts = []
    for i, name in enumerate(COMPANY_NAMES):
        acc = Account(
            id=f"ACC-{i + 1:04d}",
            name=name,
            industry=rng.choice(INDUSTRIES),
            arr=round(rng.uniform(10_000, 500_000), 2),
            plan_tier=rng.choice(PLAN_TIERS),
            health_score=rng.randint(1, 100),
            owner=rng.choice(OWNERS),
            created_date=_generate_date(rng, rng.choice([2023, 2024])),
            renewal_date=_generate_date(rng, 2026, 1, 12),
            employee_count=rng.choice([50, 100, 250, 500, 1000, 2500, 5000, 10000]),
            website=f"https://www.{name.lower().replace(' ', '').replace("'", '')}.com",
            region=rng.choice(REGIONS),
        )
        accounts.append(acc)
    return accounts


def _generate_contacts(rng: random.Random, accounts: List[Account]) -> List[Contact]:
    contacts = []
    idx = 0
    for acc in accounts:
        count = rng.randint(1, 3)
        for _ in range(count):
            first = rng.choice(FIRST_NAMES)
            last = rng.choice(LAST_NAMES)
            domain = acc.name.lower().replace(" ", "").replace("'", "")
            contacts.append(Contact(
                id=f"CON-{idx + 1:04d}",
                first_name=first,
                last_name=last,
                email=f"{first.lower()}.{last.lower()}@{domain}.com",
                account_id=acc.id,
                title=rng.choice(TITLES),
                role=rng.choice(ROLES),
                last_activity=_generate_date(rng, 2025, 1, 12),
            ))
            idx += 1
    return contacts


def _generate_opportunities(rng: random.Random, accounts: List[Account]) -> List[Opportunity]:
    opportunities = []
    opp_types = ["New Business", "Expansion", "Renewal"]
    selected = rng.sample(accounts, min(30, len(accounts)))
    for i, acc in enumerate(selected):
        stage = rng.choice(OPP_STAGES)
        opportunities.append(Opportunity(
            id=f"OPP-{i + 1:04d}",
            name=f"{acc.name} — {rng.choice(opp_types)}",
            account_id=acc.id,
            stage=stage,
            amount=round(rng.uniform(5_000, 250_000), 2),
            close_date=_generate_date(rng, rng.choice([2025, 2026])),
            probability=OPP_STAGE_PROB[stage],
            owner=rng.choice(OWNERS),
            type=rng.choice(opp_types),
            created_date=_generate_date(rng, 2025, 1, 6),
        ))
    return opportunities


def _generate_leads(rng: random.Random) -> List[Lead]:
    leads = []
    for i in range(40):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        company = rng.choice(COMPANY_NAMES[:20]) + " (prospect)"
        status = rng.choice(LEAD_STATUSES)
        leads.append(Lead(
            id=f"LEAD-{i + 1:04d}",
            first_name=first,
            last_name=last,
            email=f"{first.lower()}.{last.lower()}@example.com",
            company=company,
            status=status,
            source=rng.choice(LEAD_SOURCES),
            score=rng.randint(1, 100),
            owner=rng.choice(OWNERS),
            created_date=_generate_date(rng, 2025, 1, 12),
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
