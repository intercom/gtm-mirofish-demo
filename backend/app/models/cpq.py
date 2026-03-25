"""
CPQ (Configure, Price, Quote) data models
Intercom product catalog, price books, quotes, and quote line items.
"""

import hashlib
import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class BillingFrequency(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class QuoteStatus(str, Enum):
    DRAFT = "Draft"
    REVIEW = "Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"


@dataclass
class Product:
    id: str
    name: str
    code: str
    family: str
    unit_price: float
    billing_frequency: BillingFrequency
    description: str
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "family": self.family,
            "unit_price": self.unit_price,
            "billing_frequency": self.billing_frequency.value,
            "description": self.description,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        return cls(
            id=data["id"],
            name=data["name"],
            code=data["code"],
            family=data["family"],
            unit_price=data["unit_price"],
            billing_frequency=BillingFrequency(data["billing_frequency"]),
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
        )


@dataclass
class PriceBookEntry:
    id: str
    product_id: str
    list_price: float
    currency: str = "USD"
    is_standard: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "list_price": self.list_price,
            "currency": self.currency,
            "is_standard": self.is_standard,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceBookEntry":
        return cls(
            id=data["id"],
            product_id=data["product_id"],
            list_price=data["list_price"],
            currency=data.get("currency", "USD"),
            is_standard=data.get("is_standard", True),
        )


@dataclass
class QuoteLine:
    id: str
    quote_id: str
    product_id: str
    product_name: str
    quantity: int
    list_price: float
    discount_pct: float
    net_price: float
    subscription_term_months: int = 12

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "quote_id": self.quote_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "list_price": self.list_price,
            "discount_pct": self.discount_pct,
            "net_price": self.net_price,
            "subscription_term_months": self.subscription_term_months,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuoteLine":
        return cls(
            id=data["id"],
            quote_id=data["quote_id"],
            product_id=data["product_id"],
            product_name=data["product_name"],
            quantity=data["quantity"],
            list_price=data["list_price"],
            discount_pct=data["discount_pct"],
            net_price=data["net_price"],
            subscription_term_months=data.get("subscription_term_months", 12),
        )


@dataclass
class Quote:
    id: str
    opportunity_id: str
    account_name: str
    status: QuoteStatus
    total_price: float
    discount_pct: float
    created_date: str
    expiry_date: str
    lines: List[QuoteLine] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "account_name": self.account_name,
            "status": self.status.value,
            "total_price": self.total_price,
            "discount_pct": self.discount_pct,
            "created_date": self.created_date,
            "expiry_date": self.expiry_date,
            "lines": [line.to_dict() for line in self.lines],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quote":
        lines = [QuoteLine.from_dict(l) for l in data.get("lines", [])]
        return cls(
            id=data["id"],
            opportunity_id=data["opportunity_id"],
            account_name=data["account_name"],
            status=QuoteStatus(data["status"]),
            total_price=data["total_price"],
            discount_pct=data["discount_pct"],
            created_date=data["created_date"],
            expiry_date=data["expiry_date"],
            lines=lines,
        )


# ---------------------------------------------------------------------------
# Intercom product catalog
# ---------------------------------------------------------------------------

INTERCOM_PRODUCTS: List[Product] = [
    Product(
        id="prod_essential",
        name="Essential",
        code="IC-ESS",
        family="Platform",
        unit_price=39.0,
        billing_frequency=BillingFrequency.MONTHLY,
        description="Essential plan — core messaging and support tools per seat",
    ),
    Product(
        id="prod_advanced",
        name="Advanced",
        code="IC-ADV",
        family="Platform",
        unit_price=99.0,
        billing_frequency=BillingFrequency.MONTHLY,
        description="Advanced plan — automation, reporting, and integrations per seat",
    ),
    Product(
        id="prod_expert",
        name="Expert",
        code="IC-EXP",
        family="Platform",
        unit_price=139.0,
        billing_frequency=BillingFrequency.MONTHLY,
        description="Expert plan — full platform with advanced security and SLAs per seat",
    ),
    Product(
        id="prod_fin_ai",
        name="Fin AI Agent",
        code="IC-FIN",
        family="AI",
        unit_price=0.99,
        billing_frequency=BillingFrequency.MONTHLY,
        description="AI-powered resolution agent — billed per resolution",
    ),
    Product(
        id="prod_proactive",
        name="Proactive Support",
        code="IC-PRS",
        family="Add-on",
        unit_price=499.0,
        billing_frequency=BillingFrequency.MONTHLY,
        description="Proactive Support add-on — targeted messages, tours, and banners",
    ),
    Product(
        id="prod_helpcenter",
        name="Help Center",
        code="IC-HC",
        family="Add-on",
        unit_price=0.0,
        billing_frequency=BillingFrequency.MONTHLY,
        description="Help Center — included with all platform plans",
    ),
]

INTERCOM_PRICEBOOK: List[PriceBookEntry] = [
    PriceBookEntry(id=f"pbe_{p.id}", product_id=p.id, list_price=p.unit_price)
    for p in INTERCOM_PRODUCTS
]

# ---------------------------------------------------------------------------
# Demo-data factory helpers
# ---------------------------------------------------------------------------

_DEMO_ACCOUNTS = [
    "Acme Corp", "TechFlow Inc", "Global Logistics", "Bright Health",
    "Summit Financial", "CloudSync", "NovaPay", "DataHive",
    "PinPoint Analytics", "Horizon Media", "BlueShift Labs", "Evergreen SaaS",
    "Apex Retail", "Quantum Security", "Streamline HR", "Orbit Education",
    "NexGen Robotics", "Coral Insurance", "UrbanGrid", "Pulse Fitness",
]


def _seed_rng(seed_value: str) -> random.Random:
    """Create a deterministic RNG from a string seed."""
    h = int(hashlib.sha256(seed_value.encode()).hexdigest(), 16)
    return random.Random(h)


def generate_demo_quote(
    index: int,
    seed: str = "cpq_demo",
) -> Quote:
    """Generate a single realistic demo quote with 2-5 line items."""
    rng = _seed_rng(f"{seed}_{index}")

    quote_id = f"Q-{10000 + index}"
    opp_id = f"OPP-{6000 + index}"
    account = _DEMO_ACCOUNTS[index % len(_DEMO_ACCOUNTS)]

    statuses = [QuoteStatus.DRAFT] * 6 + [QuoteStatus.REVIEW] * 4 + \
               [QuoteStatus.APPROVED] * 6 + [QuoteStatus.REJECTED] * 4
    status = rng.choice(statuses)

    days_ago = rng.randint(5, 90)
    created = datetime.now() - timedelta(days=days_ago)
    expiry = created + timedelta(days=30)

    term_months = rng.choice([12, 24])

    # pick 2-5 products for line items
    num_lines = rng.randint(2, 5)
    chosen_products = rng.sample(INTERCOM_PRODUCTS, min(num_lines, len(INTERCOM_PRODUCTS)))

    lines: List[QuoteLine] = []
    for li_idx, product in enumerate(chosen_products):
        if product.family == "Platform":
            quantity = rng.choice([5, 10, 15, 25, 50, 75, 100, 150, 200, 300, 500])
        elif product.code == "IC-FIN":
            quantity = rng.choice([500, 1000, 2000, 5000, 10000])
        else:
            quantity = 1

        discount = round(rng.uniform(0, 25), 1) if product.unit_price > 0 else 0.0
        net = round(product.unit_price * quantity * (1 - discount / 100) * term_months, 2)

        lines.append(
            QuoteLine(
                id=f"QL-{quote_id}-{li_idx}",
                quote_id=quote_id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                list_price=product.unit_price,
                discount_pct=discount,
                net_price=net,
                subscription_term_months=term_months,
            )
        )

    total = round(sum(l.net_price for l in lines), 2)
    gross = sum(l.list_price * l.quantity * l.subscription_term_months for l in lines)
    overall_discount = round((1 - total / gross) * 100, 1) if gross > 0 else 0.0

    return Quote(
        id=quote_id,
        opportunity_id=opp_id,
        account_name=account,
        status=status,
        total_price=total,
        discount_pct=overall_discount,
        created_date=created.strftime("%Y-%m-%d"),
        expiry_date=expiry.strftime("%Y-%m-%d"),
        lines=lines,
    )


def generate_demo_quotes(count: int = 20, seed: str = "cpq_demo") -> List[Quote]:
    """Generate a batch of realistic demo quotes."""
    return [generate_demo_quote(i, seed) for i in range(count)]
