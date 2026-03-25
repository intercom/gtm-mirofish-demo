"""
Reconciliation data models for three-way MRR reconciliation:
Salesforce vs Billing (Stripe) vs Snowflake data warehouse.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    DISCREPANCY = "discrepancy"
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"


class DiscrepancyType(str, Enum):
    AMOUNT_MISMATCH = "amount_mismatch"
    MISSING_IN_SOURCE = "missing_in_source"
    TIMING_LAG = "timing_lag"
    CURRENCY_ROUNDING = "currency_rounding"


class RuleAction(str, Enum):
    FLAG = "flag"
    AUTO_RESOLVE = "auto_resolve"
    ESCALATE = "escalate"


@dataclass
class ReconciliationRecord:
    record_id: str
    account_id: str
    account_name: str
    sf_mrr: float
    billing_mrr: float
    snowflake_mrr: float
    sf_vs_billing_diff: float
    sf_vs_snowflake_diff: float
    billing_vs_snowflake_diff: float
    status: ReconciliationStatus
    discrepancy_type: Optional[DiscrepancyType] = None
    resolution_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "sf_mrr": self.sf_mrr,
            "billing_mrr": self.billing_mrr,
            "snowflake_mrr": self.snowflake_mrr,
            "sf_vs_billing_diff": self.sf_vs_billing_diff,
            "sf_vs_snowflake_diff": self.sf_vs_snowflake_diff,
            "billing_vs_snowflake_diff": self.billing_vs_snowflake_diff,
            "status": self.status.value,
            "discrepancy_type": self.discrepancy_type.value if self.discrepancy_type else None,
            "resolution_notes": self.resolution_notes,
        }


@dataclass
class ReconciliationRun:
    run_id: str
    run_date: str
    total_accounts: int
    matched_count: int
    discrepancy_count: int
    total_discrepancy_value: float
    largest_discrepancy: float
    avg_discrepancy: float
    run_duration_seconds: float
    records: List[ReconciliationRecord] = field(default_factory=list)

    def to_dict(self, include_records: bool = False) -> Dict[str, Any]:
        d = {
            "run_id": self.run_id,
            "run_date": self.run_date,
            "total_accounts": self.total_accounts,
            "matched_count": self.matched_count,
            "discrepancy_count": self.discrepancy_count,
            "match_rate": round(self.matched_count / self.total_accounts * 100, 2) if self.total_accounts else 0,
            "total_discrepancy_value": round(self.total_discrepancy_value, 2),
            "largest_discrepancy": round(self.largest_discrepancy, 2),
            "avg_discrepancy": round(self.avg_discrepancy, 2),
            "run_duration_seconds": self.run_duration_seconds,
        }
        if include_records:
            d["records"] = [r.to_dict() for r in self.records]
        return d


@dataclass
class ReconciliationRule:
    rule_id: str
    name: str
    description: str
    check_type: str
    threshold: float
    action: RuleAction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "check_type": self.check_type,
            "threshold": self.threshold,
            "action": self.action.value,
        }
