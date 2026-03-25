"""
Revenue data models for GTM simulation.
Dataclasses representing MRR/ARR metrics, customer revenue,
churn events, and expansion events at Intercom scale.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class ExpansionType(str, Enum):
    UPSELL = "upsell"
    CROSS_SELL = "cross_sell"
    SEAT_ADD = "seat_add"


class ChurnReason(str, Enum):
    BUDGET_CUTS = "budget_cuts"
    COMPETITOR = "competitor"
    NOT_USING = "not_using"
    MERGED_ACQUIRED = "merged_acquired"
    OTHER = "other"


class PlanTier(str, Enum):
    ESSENTIAL = "Essential"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


@dataclass
class RevenueMetric:
    """Monthly revenue breakdown."""
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RevenueMetric':
        return cls(
            month=data["month"],
            mrr=data["mrr"],
            arr=data["arr"],
            new_mrr=data["new_mrr"],
            expansion_mrr=data["expansion_mrr"],
            contraction_mrr=data["contraction_mrr"],
            churn_mrr=data["churn_mrr"],
            net_new_mrr=data["net_new_mrr"],
        )


@dataclass
class CustomerRevenue:
    """Individual customer revenue record."""
    account_id: str
    account_name: str
    mrr: float
    plan: PlanTier
    seats: int
    usage_units: int
    start_date: str
    last_renewal: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "mrr": self.mrr,
            "plan": self.plan.value if isinstance(self.plan, PlanTier) else self.plan,
            "seats": self.seats,
            "usage_units": self.usage_units,
            "start_date": self.start_date,
            "last_renewal": self.last_renewal,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerRevenue':
        plan = data.get("plan", "Essential")
        if isinstance(plan, str):
            plan = PlanTier(plan)
        return cls(
            account_id=data["account_id"],
            account_name=data["account_name"],
            mrr=data["mrr"],
            plan=plan,
            seats=data["seats"],
            usage_units=data["usage_units"],
            start_date=data["start_date"],
            last_renewal=data["last_renewal"],
        )


@dataclass
class ChurnEvent:
    """A customer churn event with revenue impact."""
    account_id: str
    account_name: str
    mrr_lost: float
    reason: ChurnReason
    churn_date: str
    was_voluntary: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "mrr_lost": self.mrr_lost,
            "reason": self.reason.value if isinstance(self.reason, ChurnReason) else self.reason,
            "churn_date": self.churn_date,
            "was_voluntary": self.was_voluntary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChurnEvent':
        reason = data.get("reason", "other")
        if isinstance(reason, str):
            reason = ChurnReason(reason)
        return cls(
            account_id=data["account_id"],
            account_name=data["account_name"],
            mrr_lost=data["mrr_lost"],
            reason=reason,
            churn_date=data["churn_date"],
            was_voluntary=data["was_voluntary"],
        )


@dataclass
class ExpansionEvent:
    """A customer expansion event (upsell, cross-sell, or seat addition)."""
    account_id: str
    account_name: str
    previous_mrr: float
    new_mrr: float
    expansion_type: ExpansionType
    date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "previous_mrr": self.previous_mrr,
            "new_mrr": self.new_mrr,
            "expansion_type": self.expansion_type.value if isinstance(self.expansion_type, ExpansionType) else self.expansion_type,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpansionEvent':
        exp_type = data.get("expansion_type", "upsell")
        if isinstance(exp_type, str):
            exp_type = ExpansionType(exp_type)
        return cls(
            account_id=data["account_id"],
            account_name=data["account_name"],
            previous_mrr=data["previous_mrr"],
            new_mrr=data["new_mrr"],
            expansion_type=exp_type,
            date=data["date"],
        )
