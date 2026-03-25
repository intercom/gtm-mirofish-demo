"""
Revenue data models for GTM analytics.
Dataclasses representing SaaS revenue metrics at Intercom scale (~$2M MRR, 500 customers).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


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
            "mrr": round(self.mrr, 2),
            "arr": round(self.arr, 2),
            "new_mrr": round(self.new_mrr, 2),
            "expansion_mrr": round(self.expansion_mrr, 2),
            "contraction_mrr": round(self.contraction_mrr, 2),
            "churn_mrr": round(self.churn_mrr, 2),
            "net_new_mrr": round(self.net_new_mrr, 2),
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
            "mrr": round(self.mrr, 2),
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
            "mrr_lost": round(self.mrr_lost, 2),
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
    expansion_type: str  # upsell | cross_sell | seat_add
    date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "previous_mrr": round(self.previous_mrr, 2),
            "new_mrr": round(self.new_mrr, 2),
            "expansion_type": self.expansion_type,
            "expansion_mrr": round(self.new_mrr - self.previous_mrr, 2),
            "date": self.date,
        }
