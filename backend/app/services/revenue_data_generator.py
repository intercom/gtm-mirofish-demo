"""
Revenue data generator for demo/mock mode.
Generates 12 months of realistic SaaS revenue history at Intercom scale.

All data is deterministic (seeded random) so repeated calls return consistent results.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models.revenue import (
    ChurnEvent,
    ChurnReason,
    CustomerRevenue,
    ExpansionEvent,
    ExpansionType,
    PlanTier,
    RevenueMetric,
)

# Seed for reproducibility
_SEED = 42

# Intercom-scale base numbers
_BASE_MRR = 1_800_000  # $1.8M starting MRR
_TARGET_MRR = 2_200_000  # $2.2M after 12 months
_CUSTOMER_COUNT = 500
_CHURN_EVENT_COUNT = 60
_EXPANSION_EVENT_COUNT = 80
_MONTHS = 12

# Monthly movement baselines
_NEW_MRR_BASE = 80_000
_EXPANSION_MRR_BASE = 40_000
_CONTRACTION_MRR_BASE = 15_000
_CHURN_MRR_BASE = 30_000

# Variance factor (±15%)
_VARIANCE = 0.15

# Churn reason distribution
_CHURN_REASONS = [
    (ChurnReason.BUDGET_CUTS, 0.30),
    (ChurnReason.COMPETITOR, 0.25),
    (ChurnReason.NOT_USING, 0.20),
    (ChurnReason.MERGED_ACQUIRED, 0.15),
    (ChurnReason.OTHER, 0.10),
]

# Expansion type distribution
_EXPANSION_TYPES = [
    (ExpansionType.SEAT_ADD, 0.50),
    (ExpansionType.UPSELL, 0.30),
    (ExpansionType.CROSS_SELL, 0.20),
]

# Plan distribution (weighted)
_PLAN_DISTRIBUTION = [
    (PlanTier.ESSENTIAL, 0.50),
    (PlanTier.ADVANCED, 0.35),
    (PlanTier.EXPERT, 0.15),
]

# Company name components for realistic generation
_PREFIXES = [
    "Acme", "Nova", "Apex", "Velo", "Flux", "Zeta", "Neon", "Orbit",
    "Pulse", "Helix", "Prism", "Forge", "Atlas", "Bloom", "Cedar",
    "Drift", "Echo", "Fable", "Grain", "Haven", "Ionic", "Jade",
    "Kite", "Lumen", "Maple", "Nexus", "Opal", "Petal", "Quill",
    "Ridge", "Slate", "Terra", "Unity", "Vivid", "Wave", "Xenon",
]
_SUFFIXES = [
    "Labs", "Tech", "AI", "Systems", "Cloud", "Data", "Digital",
    "Solutions", "Software", "Analytics", "Networks", "Dynamics",
    "Ventures", "Group", "Co", "Inc", "Corp", "HQ", "IO", "Platform",
]


def _vary(base: float, rng: random.Random) -> float:
    """Apply ±15% random variance to a base value."""
    return base * (1 + rng.uniform(-_VARIANCE, _VARIANCE))


def _weighted_choice(choices: list, rng: random.Random):
    """Pick from weighted choices list of (value, weight) tuples."""
    roll = rng.random()
    cumulative = 0.0
    for value, weight in choices:
        cumulative += weight
        if roll <= cumulative:
            return value
    return choices[-1][0]


def _generate_company_name(idx: int, rng: random.Random) -> str:
    """Generate a unique company name."""
    prefix = rng.choice(_PREFIXES)
    suffix = rng.choice(_SUFFIXES)
    return f"{prefix} {suffix}"


class RevenueDataGenerator:
    """Generates deterministic mock revenue data for the GTM demo."""

    def __init__(self, seed: int = _SEED):
        self._seed = seed
        self._rng = random.Random(seed)
        self._generated = False
        self._metrics: List[RevenueMetric] = []
        self._customers: List[CustomerRevenue] = []
        self._churn_events: List[ChurnEvent] = []
        self._expansion_events: List[ExpansionEvent] = []

    def _ensure_generated(self):
        if not self._generated:
            self._rng = random.Random(self._seed)
            self._generate_all()
            self._generated = True

    def _generate_all(self):
        self._generate_metrics()
        self._generate_customers()
        self._generate_churn_events()
        self._generate_expansion_events()

    def _month_str(self, months_ago: int) -> str:
        """Return YYYY-MM string for N months ago from a fixed reference."""
        ref = datetime(2026, 3, 1)
        dt = ref - timedelta(days=30 * months_ago)
        return dt.strftime("%Y-%m")

    def _random_date_in_month(self, month_str: str) -> str:
        """Return a random date within a given YYYY-MM month."""
        year, month = map(int, month_str.split("-"))
        day = self._rng.randint(1, 28)
        return f"{year}-{month:02d}-{day:02d}"

    def _generate_metrics(self):
        """Generate 12 months of revenue metrics with realistic growth."""
        self._metrics = []
        current_mrr = _BASE_MRR

        for i in range(_MONTHS):
            month = self._month_str(_MONTHS - 1 - i)

            new_mrr = round(_vary(_NEW_MRR_BASE, self._rng), 2)
            expansion_mrr = round(_vary(_EXPANSION_MRR_BASE, self._rng), 2)
            contraction_mrr = round(_vary(_CONTRACTION_MRR_BASE, self._rng), 2)
            churn_mrr = round(_vary(_CHURN_MRR_BASE, self._rng), 2)
            net_new = round(new_mrr + expansion_mrr - contraction_mrr - churn_mrr, 2)

            current_mrr = round(current_mrr + net_new, 2)

            self._metrics.append(RevenueMetric(
                month=month,
                mrr=current_mrr,
                arr=round(current_mrr * 12, 2),
                new_mrr=new_mrr,
                expansion_mrr=expansion_mrr,
                contraction_mrr=contraction_mrr,
                churn_mrr=churn_mrr,
                net_new_mrr=net_new,
            ))

    def _generate_customers(self):
        """Generate 500 customer records with power-law MRR distribution."""
        self._customers = []
        used_names = set()

        latest_mrr = self._metrics[-1].mrr if self._metrics else _TARGET_MRR

        for i in range(_CUSTOMER_COUNT):
            name = _generate_company_name(i, self._rng)
            while name in used_names:
                name = _generate_company_name(i, self._rng)
            used_names.add(name)

            # Power-law: rank^(-0.8) gives few large, many small
            rank = i + 1
            raw_weight = rank ** (-0.8)
            plan = _weighted_choice(_PLAN_DISTRIBUTION, self._rng)

            # Scale MRR based on plan tier
            plan_multiplier = {"Essential": 0.6, "Advanced": 1.0, "Expert": 2.5}
            base_mrr = (latest_mrr / _CUSTOMER_COUNT) * raw_weight * 20
            mrr = round(base_mrr * plan_multiplier.get(plan, 1.0) * (1 + self._rng.uniform(-0.2, 0.2)), 2)
            mrr = max(500, mrr)  # minimum $500 MRR

            seats = max(5, int(mrr / self._rng.uniform(100, 500)))
            usage_units = int(seats * self._rng.uniform(50, 300))

            months_as_customer = self._rng.randint(1, 36)
            start = datetime(2026, 3, 1) - timedelta(days=30 * months_as_customer)
            last_renewal = start + timedelta(days=365 * (months_as_customer // 12)) if months_as_customer >= 12 else start

            self._customers.append(CustomerRevenue(
                account_id=f"acc_{i + 1:04d}",
                account_name=name,
                mrr=mrr,
                plan=plan,
                seats=seats,
                usage_units=usage_units,
                start_date=start.strftime("%Y-%m-%d"),
                last_renewal=last_renewal.strftime("%Y-%m-%d"),
            ))

    def _generate_churn_events(self):
        """Generate 60 churn events spread across the 12-month period."""
        self._churn_events = []

        for i in range(_CHURN_EVENT_COUNT):
            month_idx = self._rng.randint(0, _MONTHS - 1)
            month = self._month_str(_MONTHS - 1 - month_idx)
            reason = _weighted_choice(_CHURN_REASONS, self._rng)
            mrr_lost = round(self._rng.uniform(1000, 15000), 2)
            was_voluntary = reason in (ChurnReason.BUDGET_CUTS, ChurnReason.COMPETITOR, ChurnReason.NOT_USING)

            self._churn_events.append(ChurnEvent(
                account_id=f"churn_{i + 1:04d}",
                account_name=_generate_company_name(1000 + i, self._rng),
                mrr_lost=mrr_lost,
                reason=reason.value,
                churn_date=self._random_date_in_month(month),
                was_voluntary=was_voluntary,
            ))

    def _generate_expansion_events(self):
        """Generate 80 expansion events spread across the 12-month period."""
        self._expansion_events = []

        for i in range(_EXPANSION_EVENT_COUNT):
            month_idx = self._rng.randint(0, _MONTHS - 1)
            month = self._month_str(_MONTHS - 1 - month_idx)
            exp_type = _weighted_choice(_EXPANSION_TYPES, self._rng)
            previous_mrr = round(self._rng.uniform(2000, 20000), 2)

            # Expansion amount varies by type
            multiplier = {
                ExpansionType.SEAT_ADD: self._rng.uniform(1.05, 1.25),
                ExpansionType.UPSELL: self._rng.uniform(1.3, 2.0),
                ExpansionType.CROSS_SELL: self._rng.uniform(1.1, 1.5),
            }
            new_mrr = round(previous_mrr * multiplier.get(exp_type, 1.2), 2)

            self._expansion_events.append(ExpansionEvent(
                account_id=f"exp_{i + 1:04d}",
                account_name=_generate_company_name(2000 + i, self._rng),
                previous_mrr=previous_mrr,
                new_mrr=new_mrr,
                expansion_type=exp_type.value,
                date=self._random_date_in_month(month),
            ))

    # ---- Public API ----

    def get_metrics(self, months: int = 12) -> List[Dict]:
        self._ensure_generated()
        data = self._metrics[-months:]
        return [m.to_dict() for m in data]

    def get_customers(
        self,
        plan: Optional[str] = None,
        mrr_min: Optional[float] = None,
        mrr_max: Optional[float] = None,
        sort_by: str = "mrr",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict:
        self._ensure_generated()
        filtered = self._customers

        if plan:
            filtered = [c for c in filtered if c.plan == plan]
        if mrr_min is not None:
            filtered = [c for c in filtered if c.mrr >= mrr_min]
        if mrr_max is not None:
            filtered = [c for c in filtered if c.mrr <= mrr_max]

        reverse = sort_order == "desc"
        if sort_by in ("mrr", "seats", "usage_units"):
            filtered.sort(key=lambda c: getattr(c, sort_by), reverse=reverse)
        elif sort_by == "account_name":
            filtered.sort(key=lambda c: c.account_name, reverse=reverse)
        else:
            filtered.sort(key=lambda c: c.mrr, reverse=reverse)

        total = len(filtered)
        page = filtered[offset: offset + limit]
        return {
            "customers": [c.to_dict() for c in page],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_churn_events(
        self,
        reason: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict]:
        self._ensure_generated()
        filtered = self._churn_events

        if reason:
            filtered = [e for e in filtered if e.reason == reason]
        if date_from:
            filtered = [e for e in filtered if e.churn_date >= date_from]
        if date_to:
            filtered = [e for e in filtered if e.churn_date <= date_to]

        return [e.to_dict() for e in sorted(filtered, key=lambda e: e.churn_date)]

    def get_expansion_events(
        self,
        expansion_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict]:
        self._ensure_generated()
        filtered = self._expansion_events

        if expansion_type:
            filtered = [e for e in filtered if e.expansion_type == expansion_type]
        if date_from:
            filtered = [e for e in filtered if e.date >= date_from]
        if date_to:
            filtered = [e for e in filtered if e.date <= date_to]

        return [e.to_dict() for e in sorted(filtered, key=lambda e: e.date)]

    def get_summary(self) -> Dict:
        self._ensure_generated()
        if not self._metrics:
            return {}

        latest = self._metrics[-1]
        first = self._metrics[0]
        growth_rate = round((latest.mrr - first.mrr) / first.mrr * 100, 2) if first.mrr else 0

        total_churn_mrr = sum(m.churn_mrr for m in self._metrics)
        total_contraction_mrr = sum(m.contraction_mrr for m in self._metrics)
        total_expansion_mrr = sum(m.expansion_mrr for m in self._metrics)
        avg_beginning_mrr = sum(m.mrr - m.net_new_mrr for m in self._metrics) / len(self._metrics)

        # Net retention = (beginning MRR + expansion - contraction - churn) / beginning MRR
        net_retention = round(
            (avg_beginning_mrr + total_expansion_mrr / _MONTHS - total_contraction_mrr / _MONTHS - total_churn_mrr / _MONTHS)
            / avg_beginning_mrr * 100, 1
        ) if avg_beginning_mrr else 0

        # Gross retention = (beginning MRR - contraction - churn) / beginning MRR
        gross_retention = round(
            (avg_beginning_mrr - total_contraction_mrr / _MONTHS - total_churn_mrr / _MONTHS)
            / avg_beginning_mrr * 100, 1
        ) if avg_beginning_mrr else 0

        avg_customer_mrr = round(latest.mrr / _CUSTOMER_COUNT, 2)
        ltv = round(avg_customer_mrr / (1 - gross_retention / 100) if gross_retention < 100 else avg_customer_mrr * 36, 2)
        cac = round(ltv / self._rng.uniform(3, 5), 2)  # LTV:CAC ratio of 3-5x

        return {
            "current_mrr": latest.mrr,
            "current_arr": latest.arr,
            "growth_rate": growth_rate,
            "net_retention": net_retention,
            "gross_retention": gross_retention,
            "ltv": ltv,
            "cac": cac,
            "avg_customer_mrr": avg_customer_mrr,
            "total_customers": _CUSTOMER_COUNT,
        }

    def get_cohort_data(self) -> Dict:
        """Generate cohort retention analysis by signup month."""
        self._ensure_generated()

        cohorts = []
        for i in range(_MONTHS):
            month = self._month_str(_MONTHS - 1 - i)
            months_active = i + 1
            retention = []

            for j in range(months_active):
                if j == 0:
                    retention.append(100.0)
                else:
                    # Natural decay with some expansion offsetting churn
                    base_decay = self._rng.uniform(0.97, 0.995)
                    expansion_boost = self._rng.uniform(0, 0.015)
                    prev = retention[-1]
                    val = round(prev * base_decay + prev * expansion_boost, 1)
                    retention.append(val)

            cohorts.append({
                "signup_month": month,
                "retention": retention,
                "starting_customers": self._rng.randint(30, 60),
                "starting_mrr": round(self._rng.uniform(60000, 120000), 2),
            })

        return {"cohorts": cohorts}


# Module-level singleton for consistent data across requests
_generator_instance: Optional[RevenueDataGenerator] = None


def get_revenue_generator() -> RevenueDataGenerator:
    """Get or create the singleton revenue data generator."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = RevenueDataGenerator()
    return _generator_instance
