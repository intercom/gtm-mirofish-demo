"""
Revenue data models for GTM analytics.
Dataclasses representing SaaS revenue metrics at Intercom scale.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class ChurnReason(str, Enum):
    BUDGET_CUTS = "budget_cuts"
    COMPETITOR = "competitor"
    NOT_USING = "not_using"
    MERGED_ACQUIRED = "merged_acquired"
    OTHER = "other"


class ExpansionType(str, Enum):
    UPSELL = "upsell"
    CROSS_SELL = "cross_sell"
    SEAT_ADD = "seat_add"


class PlanTier(str, Enum):
    ESSENTIAL = "Essential"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


@dataclass
class RevenueMetric:
    month: str
    mrr: float
    arr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churn_mrr: float
    net_new_mrr: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "month": self.month,
            "mrr": self.mrr,
            "arr": self.arr,
            "new_mrr": self.new_mrr,
            "expansion_mrr": self.expansion_mrr,
            "contraction_mrr": self.contraction_mrr,
            "churn_mrr": self.churn_mrr,
            "net_new_mrr": self.net_new_mrr,
        }


@dataclass
class CustomerRevenue:
    account_id: str
    account_name: str
    mrr: float
    plan: str
    seats: int
    usage_units: int
    start_date: str
    last_renewal: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "mrr": self.mrr,
            "plan": self.plan,
            "seats": self.seats,
            "usage_units": self.usage_units,
            "start_date": self.start_date,
            "last_renewal": self.last_renewal,
        }


@dataclass
class ChurnEvent:
    account_id: str
    account_name: str
    mrr_lost: float
    reason: str
    churn_date: str
    was_voluntary: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "mrr_lost": self.mrr_lost,
            "reason": self.reason,
            "churn_date": self.churn_date,
            "was_voluntary": self.was_voluntary,
        }


@dataclass
class ExpansionEvent:
    account_id: str
    account_name: str
    previous_mrr: float
    new_mrr: float
    expansion_type: str
    date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "previous_mrr": self.previous_mrr,
            "new_mrr": self.new_mrr,
            "expansion_type": self.expansion_type,
            "date": self.date,
        }
