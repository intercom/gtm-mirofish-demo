"""
CPQ (Configure, Price, Quote) data models.
Intercom product catalog, price book entries, quotes, and quote line items.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


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

    def to_dict(self):
        d = asdict(self)
        d["billing_frequency"] = self.billing_frequency.value
        return d


@dataclass
class PriceBookEntry:
    id: str
    product_id: str
    list_price: float
    currency: str = "USD"
    is_standard: bool = True

    def to_dict(self):
        return asdict(self)


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
    subscription_term_months: int

    def to_dict(self):
        return asdict(self)


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

    def to_dict(self):
        d = asdict(self)
        d["status"] = self.status.value
        d["lines"] = [line.to_dict() if isinstance(line, QuoteLine) else line for line in self.lines]
        return d
