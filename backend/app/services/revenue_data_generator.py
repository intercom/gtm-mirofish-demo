"""
Revenue data generator for GTM analytics demo.

Generates 12 months of realistic SaaS revenue history at Intercom scale:
- MRR progression from $1.8M → $2.2M (22% YoY growth)
- 500 customer records with power-law MRR distribution
- 60 churn events and 80 expansion events with realistic distributions
- ±15% monthly variance for realism

All data is deterministic per seed for consistent demo experiences.
"""

import math
import random as _random_mod
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from ..models.revenue import RevenueMetric, CustomerRevenue, ChurnEvent, ExpansionEvent

# Company name components for generating realistic account names
_PREFIXES = [
    "Acme", "Nova", "Zenith", "Apex", "Cobalt", "Vertex", "Nimbus", "Axiom",
    "Prism", "Helix", "Flux", "Orbit", "Qubit", "Forge", "Atlas", "Nexus",
    "Ember", "Ridge", "Spark", "Drift", "Crest", "Pulse", "Vantage", "Onyx",
    "Cedar", "Maple", "Iron", "Slate", "Azure", "Coral", "Sage", "Birch",
    "Pike", "Dune", "Lark", "Fern", "Cove", "Glen", "Vale", "Reef",
]
_SUFFIXES = [
    "Labs", "Systems", "Tech", "AI", "Cloud", "Digital", "Analytics", "Solutions",
    "Group", "Corp", "Inc", "Co", "HQ", "Works", "Dynamics", "Ventures",
    "Software", "Networks", "Data", "Platform", "Health", "Finance", "Media",
    "Robotics", "Security", "Energy", "Logistics", "Bio", "Space", "Auto",
]

PLANS = ["starter", "growth", "professional", "enterprise"]
PLAN_WEIGHTS = [0.30, 0.35, 0.25, 0.10]

CHURN_REASONS = ["budget_cuts", "competitor", "not_using", "merged_acquired", "other"]
CHURN_REASON_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]
CHURN_VOLUNTARY = {
    "budget_cuts": True,
    "competitor": True,
    "not_using": True,
    "merged_acquired": False,
    "other": True,
}

EXPANSION_TYPES = ["seat_add", "upsell", "cross_sell"]
EXPANSION_TYPE_WEIGHTS = [0.50, 0.30, 0.20]


class RevenueDataGenerator:
    """Generates realistic SaaS revenue demo data."""

    def __init__(self, seed: int = 42):
        self._rng = _random_mod.Random(seed)
        self._base_date = date(2025, 4, 1)  # 12-month window ending March 2026
        self._customers: Optional[List[CustomerRevenue]] = None
        self._metrics: Optional[List[RevenueMetric]] = None
        self._churn_events: Optional[List[ChurnEvent]] = None
        self._expansion_events: Optional[List[ExpansionEvent]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_monthly_metrics(self, months: int = 12) -> List[RevenueMetric]:
        if self._metrics is not None and len(self._metrics) == months:
            return self._metrics

        start_mrr = 1_800_000.0
        target_end_mrr = 2_200_000.0
        monthly_net_target = (target_end_mrr - start_mrr) / months

        avg_new = 80_000.0
        avg_expansion = 40_000.0
        avg_contraction = 15_000.0
        avg_churn = 30_000.0

        metrics: List[RevenueMetric] = []
        current_mrr = start_mrr

        for i in range(months):
            month_date = date(self._base_date.year, self._base_date.month + i, 1) if (
                self._base_date.month + i <= 12
            ) else date(
                self._base_date.year + (self._base_date.month + i - 1) // 12,
                (self._base_date.month + i - 1) % 12 + 1,
                1,
            )
            month_str = month_date.strftime("%Y-%m")

            variance = self._rng.uniform(0.85, 1.15)
            new_mrr = avg_new * variance
            expansion_mrr = avg_expansion * self._rng.uniform(0.85, 1.15)
            contraction_mrr = avg_contraction * self._rng.uniform(0.85, 1.15)
            churn_mrr = avg_churn * self._rng.uniform(0.85, 1.15)

            net_new = new_mrr + expansion_mrr - contraction_mrr - churn_mrr
            # Steer toward target trajectory to keep the 12-month arc realistic
            target_mrr = start_mrr + monthly_net_target * (i + 1)
            overshoot = (current_mrr + net_new) - target_mrr
            # Scale new_mrr down/up to compensate for drift
            adjustment = -overshoot * 0.7
            new_mrr = max(new_mrr + adjustment, avg_new * 0.4)
            net_new = new_mrr + expansion_mrr - contraction_mrr - churn_mrr

            current_mrr += net_new
            arr = current_mrr * 12

            metrics.append(RevenueMetric(
                month=month_str,
                mrr=current_mrr,
                arr=arr,
                new_mrr=new_mrr,
                expansion_mrr=expansion_mrr,
                contraction_mrr=contraction_mrr,
                churn_mrr=churn_mrr,
                net_new_mrr=net_new,
            ))

        self._metrics = metrics
        return metrics

    def generate_customers(self, count: int = 500) -> List[CustomerRevenue]:
        if self._customers is not None and len(self._customers) == count:
            return self._customers

        target_total_mrr = 2_000_000.0  # ~$2M total across all customers
        names = self._generate_company_names(count)

        # Power-law (Pareto) distribution: alpha=1.5 gives heavy right tail
        # Cap individual values to prevent a single account dominating total MRR
        max_single = target_total_mrr * 0.04  # no account > 4% of total (~$80K)
        raw = [min(self._pareto(1.5), 20.0) for _ in range(count)]
        total_raw = sum(raw)
        mrr_values = [min(r / total_raw * target_total_mrr, max_single) for r in raw]
        mrr_values.sort(reverse=True)

        customers: List[CustomerRevenue] = []
        for i in range(count):
            mrr = mrr_values[i]
            plan = self._plan_from_mrr(mrr)
            seats = self._seats_from_plan(plan, mrr)
            usage = int(seats * self._rng.uniform(50, 500))
            start = self._random_start_date()
            renewal = self._next_renewal(start)

            customers.append(CustomerRevenue(
                account_id=f"ACC-{i+1:04d}",
                account_name=names[i],
                mrr=mrr,
                plan=plan,
                seats=seats,
                usage_units=usage,
                start_date=start.isoformat(),
                last_renewal=renewal.isoformat(),
            ))

        self._customers = customers
        return customers

    def generate_churn_events(self, count: int = 60) -> List[ChurnEvent]:
        if self._churn_events is not None and len(self._churn_events) == count:
            return self._churn_events

        customers = self.generate_customers()
        # Pick churn candidates from the lower half of MRR (smaller accounts churn more)
        sorted_by_mrr = sorted(customers, key=lambda c: c.mrr)
        candidate_pool = sorted_by_mrr[:len(sorted_by_mrr) * 3 // 4]

        churned = self._rng.sample(candidate_pool, min(count, len(candidate_pool)))
        events: List[ChurnEvent] = []

        for c in churned:
            reason = self._weighted_choice(CHURN_REASONS, CHURN_REASON_WEIGHTS)
            churn_date = self._random_date_in_window()

            events.append(ChurnEvent(
                account_id=c.account_id,
                account_name=c.account_name,
                mrr_lost=c.mrr * self._rng.uniform(0.5, 1.0),
                reason=reason,
                churn_date=churn_date.isoformat(),
                was_voluntary=CHURN_VOLUNTARY[reason],
            ))

        events.sort(key=lambda e: e.churn_date)
        self._churn_events = events
        return events

    def generate_expansion_events(self, count: int = 80) -> List[ExpansionEvent]:
        if self._expansion_events is not None and len(self._expansion_events) == count:
            return self._expansion_events

        customers = self.generate_customers()
        # Expansion candidates: accounts with moderate-to-high MRR (active, growing)
        sorted_by_mrr = sorted(customers, key=lambda c: c.mrr, reverse=True)
        candidate_pool = sorted_by_mrr[:len(sorted_by_mrr) * 2 // 3]

        expanded = self._rng.sample(candidate_pool, min(count, len(candidate_pool)))
        events: List[ExpansionEvent] = []

        for c in expanded:
            exp_type = self._weighted_choice(EXPANSION_TYPES, EXPANSION_TYPE_WEIGHTS)
            multiplier = {
                "seat_add": self._rng.uniform(1.05, 1.25),
                "upsell": self._rng.uniform(1.20, 1.60),
                "cross_sell": self._rng.uniform(1.10, 1.35),
            }[exp_type]

            events.append(ExpansionEvent(
                account_id=c.account_id,
                account_name=c.account_name,
                previous_mrr=c.mrr,
                new_mrr=c.mrr * multiplier,
                expansion_type=exp_type,
                date=self._random_date_in_window().isoformat(),
            ))

        events.sort(key=lambda e: e.date)
        self._expansion_events = events
        return events

    def generate_summary(self) -> Dict[str, Any]:
        metrics = self.generate_monthly_metrics()
        customers = self.generate_customers()

        current = metrics[-1]
        previous = metrics[-2] if len(metrics) >= 2 else metrics[0]
        first = metrics[0]

        total_churn_mrr = sum(m.churn_mrr for m in metrics)
        total_contraction_mrr = sum(m.contraction_mrr for m in metrics)
        total_expansion_mrr = sum(m.expansion_mrr for m in metrics)
        beginning_mrr = first.mrr - first.net_new_mrr

        # Net revenue retention: (beginning + expansion - contraction - churn) / beginning
        gross_retention = max(0, 1 - (total_churn_mrr + total_contraction_mrr) / (beginning_mrr * len(metrics))) * 100
        net_retention = max(0, 1 - (total_churn_mrr + total_contraction_mrr - total_expansion_mrr) / (beginning_mrr * len(metrics))) * 100

        avg_mrr = sum(c.mrr for c in customers) / len(customers) if customers else 0
        growth_rate = ((current.mrr / (first.mrr - first.net_new_mrr)) - 1) * 100 if first.mrr else 0

        # Simplified LTV and CAC for demo
        monthly_churn_rate = (total_churn_mrr / len(metrics)) / current.mrr if current.mrr else 0
        ltv = avg_mrr / monthly_churn_rate if monthly_churn_rate > 0 else avg_mrr * 36
        cac = avg_mrr * self._rng.uniform(10, 14)  # typical SaaS CAC ~12x MRR

        return {
            "current_mrr": round(current.mrr, 2),
            "current_arr": round(current.arr, 2),
            "growth_rate": round(growth_rate, 1),
            "net_retention": round(net_retention, 1),
            "gross_retention": round(gross_retention, 1),
            "ltv": round(ltv, 2),
            "cac": round(cac, 2),
            "ltv_cac_ratio": round(ltv / cac, 1) if cac > 0 else 0,
            "total_customers": len(customers),
            "avg_mrr": round(avg_mrr, 2),
            "mrr_growth_mom": round(
                ((current.mrr / previous.mrr) - 1) * 100, 1
            ) if previous.mrr else 0,
        }

    def generate_cohort_data(self) -> Dict[str, Any]:
        customers = self.generate_customers()
        metrics = self.generate_monthly_metrics()
        months = [m.month for m in metrics]

        cohorts: Dict[str, Dict[str, Any]] = {}
        for month_str in months:
            # Assign a cohort of customers who "started" in this month
            cohort_customers = [
                c for c in customers
                if c.start_date[:7] == month_str
            ]
            if not cohort_customers:
                # Assign some customers to fill empty cohorts
                cohort_size = max(5, len(customers) // len(months))
                cohort_customers = self._rng.sample(customers, min(cohort_size, len(customers)))

            initial_mrr = sum(c.mrr for c in cohort_customers)
            month_idx = months.index(month_str)
            remaining_months = len(months) - month_idx

            retention = []
            current_retained = 100.0
            for j in range(remaining_months):
                if j == 0:
                    retention.append(100.0)
                else:
                    # Natural decay with some expansion offsetting churn
                    monthly_decay = self._rng.uniform(1.5, 4.0)
                    monthly_expansion = self._rng.uniform(0.5, 2.0)
                    current_retained = current_retained - monthly_decay + monthly_expansion
                    current_retained = max(current_retained, 60.0)
                    retention.append(round(current_retained, 1))

            cohorts[month_str] = {
                "month": month_str,
                "customers": len(cohort_customers),
                "initial_mrr": round(initial_mrr, 2),
                "retention": retention,
            }

        return {
            "months": months,
            "cohorts": cohorts,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pareto(self, alpha: float) -> float:
        """Generate a Pareto-distributed value using inverse transform."""
        u = self._rng.random()
        return (1.0 - u) ** (-1.0 / alpha)

    def _weighted_choice(self, items: list, weights: list):
        return self._rng.choices(items, weights=weights, k=1)[0]

    def _generate_company_names(self, count: int) -> List[str]:
        names = set()
        while len(names) < count:
            prefix = self._rng.choice(_PREFIXES)
            suffix = self._rng.choice(_SUFFIXES)
            names.add(f"{prefix} {suffix}")
        return list(names)

    def _plan_from_mrr(self, mrr: float) -> str:
        if mrr >= 15_000:
            return "enterprise"
        elif mrr >= 5_000:
            return "professional"
        elif mrr >= 1_500:
            return "growth"
        return "starter"

    def _seats_from_plan(self, plan: str, mrr: float) -> int:
        base = {"starter": 5, "growth": 15, "professional": 40, "enterprise": 100}
        per_seat = {"starter": 30, "growth": 50, "professional": 80, "enterprise": 120}
        return max(base[plan], int(mrr / per_seat[plan]))

    def _random_start_date(self) -> date:
        days_back = self._rng.randint(90, 1095)  # 3 months to 3 years ago
        return self._base_date - timedelta(days=days_back)

    def _next_renewal(self, start: date) -> date:
        # Annual renewal cycle
        years_since = max(1, (self._base_date - start).days // 365)
        return date(start.year + years_since, start.month, min(start.day, 28))

    def _random_date_in_window(self) -> date:
        offset = self._rng.randint(0, 364)
        return self._base_date + timedelta(days=offset)
