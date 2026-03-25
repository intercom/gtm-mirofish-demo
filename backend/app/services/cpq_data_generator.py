"""
CPQ data generator service.
Generates realistic Intercom product catalog, price book, and quote demo data
using deterministic seed-based randomness for consistent results.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from ..models.cpq import (
    Product, PriceBookEntry, Quote, QuoteLine,
    QuoteStatus, BillingFrequency,
)

# Intercom product catalog
PRODUCTS: List[Dict] = [
    {
        "id": "prod-essential",
        "name": "Essential",
        "code": "ICOM-ESS",
        "family": "Platform",
        "unit_price": 39.0,
        "billing_frequency": BillingFrequency.MONTHLY,
        "description": "Core support platform with shared inbox, basic automation, and help center.",
    },
    {
        "id": "prod-advanced",
        "name": "Advanced",
        "code": "ICOM-ADV",
        "family": "Platform",
        "unit_price": 99.0,
        "billing_frequency": BillingFrequency.MONTHLY,
        "description": "Enhanced platform with workflows, reporting, and multi-channel support.",
    },
    {
        "id": "prod-expert",
        "name": "Expert",
        "code": "ICOM-EXP",
        "family": "Platform",
        "unit_price": 139.0,
        "billing_frequency": BillingFrequency.MONTHLY,
        "description": "Full platform with custom roles, SSO, SLA management, and priority support.",
    },
    {
        "id": "prod-fin-ai",
        "name": "Fin AI Agent",
        "code": "ICOM-FIN",
        "family": "AI",
        "unit_price": 0.99,
        "billing_frequency": BillingFrequency.MONTHLY,
        "description": "AI-powered resolution agent billed per successful resolution.",
    },
    {
        "id": "prod-proactive",
        "name": "Proactive Support",
        "code": "ICOM-PRO",
        "family": "Add-on",
        "unit_price": 499.0,
        "billing_frequency": BillingFrequency.MONTHLY,
        "description": "Proactive messaging, banners, and targeted outbound campaigns.",
    },
    {
        "id": "prod-helpcenter",
        "name": "Help Center",
        "code": "ICOM-HC",
        "family": "Included",
        "unit_price": 0.0,
        "billing_frequency": BillingFrequency.MONTHLY,
        "description": "Self-serve knowledge base included with all plans.",
    },
]

# Realistic account names for quote generation
ACCOUNT_NAMES: List[str] = [
    "Meridian Health Systems",
    "TechNova Solutions",
    "Apex Financial Group",
    "CloudBridge Analytics",
    "Vanguard Logistics",
    "Pinnacle Retail Corp",
    "Nexus Payments Inc",
    "Horizon EdTech",
    "Quantum Manufacturing",
    "Atlas Travel Group",
    "Sterling Insurance",
    "Forge Cybersecurity",
    "Cascade Commerce",
    "Lunar SaaS Platform",
    "Ironclad Legal Tech",
    "Summit Healthcare Partners",
    "Velocity Fintech",
    "Ember Digital Agency",
    "Cobalt Enterprise",
    "Prism Data Systems",
]

# Quote status distribution: Draft 30%, Review 20%, Approved 30%, Rejected 20%
STATUS_WEIGHTS: List[Tuple[QuoteStatus, float]] = [
    (QuoteStatus.DRAFT, 0.30),
    (QuoteStatus.REVIEW, 0.20),
    (QuoteStatus.APPROVED, 0.30),
    (QuoteStatus.REJECTED, 0.20),
]


class CpqDataGenerator:
    """Generates deterministic CPQ demo data."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self._products: List[Product] = []
        self._pricebook: List[PriceBookEntry] = []
        self._quotes: List[Quote] = []
        self._generated = False

    def _ensure_generated(self):
        if not self._generated:
            self._generate_all()

    def _generate_all(self):
        self._products = self._build_products()
        self._pricebook = self._build_pricebook()
        self._quotes = self._build_quotes(count=20)
        self._generated = True

    def _build_products(self) -> List[Product]:
        return [Product(**p) for p in PRODUCTS]

    def _build_pricebook(self) -> List[PriceBookEntry]:
        entries = []
        for prod in PRODUCTS:
            entries.append(PriceBookEntry(
                id=f"pbe-{prod['id']}",
                product_id=prod["id"],
                list_price=prod["unit_price"],
            ))
        return entries

    def _pick_status(self) -> QuoteStatus:
        r = self._rng.random()
        cumulative = 0.0
        for status, weight in STATUS_WEIGHTS:
            cumulative += weight
            if r <= cumulative:
                return status
        return QuoteStatus.DRAFT

    def _build_quotes(self, count: int = 20) -> List[Quote]:
        quotes = []
        base_date = datetime(2025, 9, 1)

        for i in range(count):
            quote_id = f"Q-{1001 + i}"
            opp_id = f"OPP-{2001 + i}"
            account = ACCOUNT_NAMES[i % len(ACCOUNT_NAMES)]
            status = self._pick_status()

            created = base_date + timedelta(days=self._rng.randint(0, 180))
            expiry = created + timedelta(days=30)

            lines = self._build_quote_lines(quote_id, i)

            total_price = sum(ln.net_price for ln in lines)
            total_list = sum(ln.list_price * ln.quantity * ln.subscription_term_months for ln in lines)
            discount_pct = round(
                (1 - total_price / total_list) * 100, 1
            ) if total_list > 0 else 0.0

            quotes.append(Quote(
                id=quote_id,
                opportunity_id=opp_id,
                account_name=account,
                status=status,
                total_price=round(total_price, 2),
                discount_pct=discount_pct,
                created_date=created.strftime("%Y-%m-%d"),
                expiry_date=expiry.strftime("%Y-%m-%d"),
                lines=lines,
            ))

        return quotes

    def _build_quote_lines(self, quote_id: str, quote_index: int) -> List[QuoteLine]:
        num_lines = self._rng.randint(2, 5)

        # Always include a platform product; optionally add Fin AI and add-ons
        platform_products = [p for p in PRODUCTS if p["family"] == "Platform"]
        other_products = [p for p in PRODUCTS if p["family"] not in ("Platform", "Included")]

        platform = self._rng.choice(platform_products)
        selected = [platform]

        # Add 1-4 more products from add-ons/AI (no duplicates)
        extras = self._rng.sample(other_products, min(num_lines - 1, len(other_products)))
        selected.extend(extras)

        lines = []
        for idx, prod in enumerate(selected):
            line_id = f"QL-{quote_id}-{idx + 1}"

            if prod["id"] == "prod-fin-ai":
                quantity = self._rng.choice([500, 1000, 2000, 5000, 10000])
            else:
                quantity = self._rng.choice([5, 10, 25, 50, 100, 150, 200, 300, 500])

            discount_pct = round(self._rng.uniform(0, 25), 1)
            term_months = self._rng.choice([12, 24])
            list_price = prod["unit_price"]

            net_price = round(
                list_price * quantity * (1 - discount_pct / 100) * term_months, 2
            )

            lines.append(QuoteLine(
                id=line_id,
                quote_id=quote_id,
                product_id=prod["id"],
                product_name=prod["name"],
                quantity=quantity,
                list_price=list_price,
                discount_pct=discount_pct,
                net_price=net_price,
                subscription_term_months=term_months,
            ))

        return lines

    # --- Public API ---

    def get_products(self) -> List[Product]:
        self._ensure_generated()
        return list(self._products)

    def get_pricebook(self) -> List[PriceBookEntry]:
        self._ensure_generated()
        return list(self._pricebook)

    def get_quotes(self) -> List[Quote]:
        self._ensure_generated()
        return list(self._quotes)

    def get_quote(self, quote_id: str) -> Quote | None:
        self._ensure_generated()
        for q in self._quotes:
            if q.id == quote_id:
                return q
        return None

    def get_stats(self) -> Dict:
        self._ensure_generated()
        total = len(self._quotes)
        approved = sum(1 for q in self._quotes if q.status == QuoteStatus.APPROVED)
        total_value = sum(q.total_price for q in self._quotes)
        avg_discount = (
            sum(q.discount_pct for q in self._quotes) / total if total else 0
        )
        avg_deal_size = total_value / total if total else 0

        revenue_by_product: Dict[str, float] = {}
        for q in self._quotes:
            for ln in q.lines:
                revenue_by_product[ln.product_name] = (
                    revenue_by_product.get(ln.product_name, 0) + ln.net_price
                )

        return {
            "total_quotes": total,
            "approval_rate": round(approved / total * 100, 1) if total else 0,
            "avg_discount": round(avg_discount, 1),
            "avg_deal_size": round(avg_deal_size, 2),
            "total_pipeline_value": round(total_value, 2),
            "revenue_by_product": revenue_by_product,
            "status_breakdown": {
                s.value: sum(1 for q in self._quotes if q.status == s)
                for s in QuoteStatus
            },
        }
