"""
Salesforce CRM data models for GTM demo simulation.

Defines core Salesforce objects as dataclasses with serialization
and deterministic sample data generation.
"""

import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


# --- Constants for realistic demo data ---

INDUSTRIES = [
    "Technology", "Finance", "Healthcare", "Retail", "Education",
    "Manufacturing", "Media", "Professional Services", "Real Estate", "Logistics",
]

PLAN_TIERS = ["Essential", "Advanced", "Expert"]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]

OPPORTUNITY_STAGES = [
    "Prospecting", "Discovery", "Proposal", "Negotiation",
    "Closed Won", "Closed Lost",
]

OPPORTUNITY_TYPES = ["New Business", "Expansion", "Renewal"]

LEAD_STATUSES = ["New", "Contacted", "Qualified", "Converted", "Disqualified"]

LEAD_SOURCES = [
    "Website", "Webinar", "Referral", "Outbound", "Event",
    "Content Download", "Product Trial", "Partner",
]

CONTACT_TITLES = [
    "VP of Sales", "Director of Customer Success", "CTO",
    "Head of Support", "VP of Engineering", "Director of Product",
    "Chief Revenue Officer", "Head of Growth", "VP of Marketing",
    "Director of Operations",
]

CONTACT_ROLES = [
    "Decision Maker", "Influencer", "Champion", "End User", "Executive Sponsor",
]

_FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey",
    "Riley", "Quinn", "Avery", "Cameron", "Drew",
    "Jamie", "Reese", "Skyler", "Dakota", "Hayden",
    "Emery", "Rowan", "Sage", "Blake", "Finley",
    "Harper", "Logan", "Parker", "Elliot", "Kendall",
]

_LAST_NAMES = [
    "Chen", "Patel", "O'Brien", "Nakamura", "Rodriguez",
    "Kim", "Johansson", "Martinez", "Williams", "Singh",
    "Thompson", "Garcia", "Lee", "Anderson", "Muller",
    "Ali", "Nguyen", "Brown", "Davis", "Wilson",
]

_COMPANY_PREFIXES = [
    "Apex", "Beacon", "Catalyst", "DataFlow", "Envoy",
    "Fusion", "GridPoint", "Helix", "Intelli", "Jetstream",
    "Keystone", "Luminary", "Meridian", "Nexus", "Orbit",
    "Prism", "Quantum", "Relay", "Summit", "Terraform",
    "Unity", "Vertex", "Wavelength", "Xenon", "Zephyr",
]

_COMPANY_SUFFIXES = [
    "AI", "Labs", "Systems", "Technologies", "Cloud",
    "Analytics", "Solutions", "Software", "Digital", "Inc",
]

_EMAIL_DOMAINS = [
    "apex.io", "beacontech.com", "catalystlabs.co", "dataflow.dev", "envoyai.com",
    "fusioncloud.io", "gridpoint.tech", "helixsys.com", "intellisoft.co", "jetstream.dev",
]

_EMPLOYEE_COUNTS = [50, 100, 250, 500, 1000, 2500, 5000, 10000]


def _seeded_rng(seed: int) -> random.Random:
    """Create a deterministic Random instance from a seed."""
    return random.Random(seed)


def _generate_id(prefix: str, seed: int) -> str:
    """Generate a deterministic ID from prefix and seed."""
    h = hashlib.md5(f"{prefix}:{seed}".encode()).hexdigest()[:12]
    return f"{prefix}_{h}"


def _random_date(rng: random.Random, start_year: int = 2023, end_year: int = 2025) -> str:
    """Generate a random ISO date string within a range."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    dt = start + timedelta(days=rng.randint(0, delta))
    return dt.strftime("%Y-%m-%d")


@dataclass
class Account:
    """Salesforce Account — represents a customer company."""
    id: str
    name: str
    industry: str
    arr: float
    plan_tier: str
    health_score: int
    owner: str
    created_date: str
    renewal_date: str
    employee_count: int = 0
    website: str = ""
    region: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "industry": self.industry,
            "arr": self.arr,
            "plan_tier": self.plan_tier,
            "health_score": self.health_score,
            "owner": self.owner,
            "created_date": self.created_date,
            "renewal_date": self.renewal_date,
            "employee_count": self.employee_count,
            "website": self.website,
            "region": self.region,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            id=data["id"],
            name=data["name"],
            industry=data["industry"],
            arr=data["arr"],
            plan_tier=data["plan_tier"],
            health_score=data["health_score"],
            owner=data["owner"],
            created_date=data["created_date"],
            renewal_date=data["renewal_date"],
            employee_count=data.get("employee_count", 0),
            website=data.get("website", ""),
            region=data.get("region", ""),
        )

    @classmethod
    def create_sample(cls, seed: int = 0) -> "Account":
        rng = _seeded_rng(seed)
        prefix = rng.choice(_COMPANY_PREFIXES)
        suffix = rng.choice(_COMPANY_SUFFIXES)
        owner_first = rng.choice(_FIRST_NAMES)
        owner_last = rng.choice(_LAST_NAMES)
        name = f"{prefix} {suffix}"

        arr_raw = rng.randint(10, 500) * 1000
        return cls(
            id=_generate_id("acct", seed),
            name=name,
            industry=rng.choice(INDUSTRIES),
            arr=float(arr_raw),
            plan_tier=rng.choice(PLAN_TIERS),
            health_score=rng.randint(1, 100),
            owner=f"{owner_first} {owner_last}",
            created_date=_random_date(rng, 2022, 2024),
            renewal_date=_random_date(rng, 2025, 2026),
            employee_count=rng.choice(_EMPLOYEE_COUNTS),
            website=f"https://www.{name.lower().replace(' ', '')}.com",
            region=rng.choice(REGIONS),
        )


@dataclass
class Opportunity:
    """Salesforce Opportunity — represents a deal in the pipeline."""
    id: str
    name: str
    account_id: str
    stage: str
    amount: float
    close_date: str
    probability: int
    owner: str
    type: str
    created_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "account_id": self.account_id,
            "stage": self.stage,
            "amount": self.amount,
            "close_date": self.close_date,
            "probability": self.probability,
            "owner": self.owner,
            "type": self.type,
            "created_date": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Opportunity":
        return cls(
            id=data["id"],
            name=data["name"],
            account_id=data["account_id"],
            stage=data["stage"],
            amount=data["amount"],
            close_date=data["close_date"],
            probability=data["probability"],
            owner=data["owner"],
            type=data["type"],
            created_date=data.get("created_date", ""),
        )

    @classmethod
    def create_sample(cls, seed: int = 0, account_id: Optional[str] = None) -> "Opportunity":
        rng = _seeded_rng(seed)
        stage = rng.choice(OPPORTUNITY_STAGES)

        stage_probabilities = {
            "Prospecting": 10,
            "Discovery": 25,
            "Proposal": 50,
            "Negotiation": 75,
            "Closed Won": 100,
            "Closed Lost": 0,
        }

        prefix = rng.choice(_COMPANY_PREFIXES)
        opp_type = rng.choice(OPPORTUNITY_TYPES)
        amount = rng.randint(5, 200) * 1000

        return cls(
            id=_generate_id("opp", seed),
            name=f"{prefix} — {opp_type}",
            account_id=account_id or _generate_id("acct", rng.randint(0, 49)),
            stage=stage,
            amount=float(amount),
            close_date=_random_date(rng, 2025, 2026),
            probability=stage_probabilities[stage],
            owner=f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
            type=opp_type,
            created_date=_random_date(rng, 2024, 2025),
        )


@dataclass
class Contact:
    """Salesforce Contact — represents a person at an Account."""
    id: str
    first_name: str
    last_name: str
    email: str
    account_id: str
    title: str
    role: str
    last_activity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "account_id": self.account_id,
            "title": self.title,
            "role": self.role,
            "last_activity": self.last_activity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        return cls(
            id=data["id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            account_id=data["account_id"],
            title=data["title"],
            role=data["role"],
            last_activity=data["last_activity"],
        )

    @classmethod
    def create_sample(cls, seed: int = 0, account_id: Optional[str] = None) -> "Contact":
        rng = _seeded_rng(seed)
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        domain = rng.choice(_EMAIL_DOMAINS)

        return cls(
            id=_generate_id("con", seed),
            first_name=first,
            last_name=last,
            email=f"{first.lower()}.{last.lower()}@{domain}",
            account_id=account_id or _generate_id("acct", rng.randint(0, 49)),
            title=rng.choice(CONTACT_TITLES),
            role=rng.choice(CONTACT_ROLES),
            last_activity=_random_date(rng, 2024, 2025),
        )


@dataclass
class Lead:
    """Salesforce Lead — represents a potential prospect."""
    id: str
    first_name: str
    last_name: str
    email: str
    company: str
    status: str
    source: str
    score: int
    owner: str
    created_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "company": self.company,
            "status": self.status,
            "source": self.source,
            "score": self.score,
            "owner": self.owner,
            "created_date": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lead":
        return cls(
            id=data["id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            company=data["company"],
            status=data["status"],
            source=data["source"],
            score=data["score"],
            owner=data["owner"],
            created_date=data.get("created_date", ""),
        )

    @classmethod
    def create_sample(cls, seed: int = 0) -> "Lead":
        rng = _seeded_rng(seed)
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        domain = rng.choice(_EMAIL_DOMAINS)
        prefix = rng.choice(_COMPANY_PREFIXES)
        suffix = rng.choice(_COMPANY_SUFFIXES)

        return cls(
            id=_generate_id("lead", seed),
            first_name=first,
            last_name=last,
            email=f"{first.lower()}.{last.lower()}@{domain}",
            company=f"{prefix} {suffix}",
            status=rng.choice(LEAD_STATUSES),
            source=rng.choice(LEAD_SOURCES),
            score=rng.randint(1, 100),
            owner=f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
            created_date=_random_date(rng, 2024, 2025),
        )
