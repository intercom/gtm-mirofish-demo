"""
Reconciliation data models for three-way MRR reconciliation:
Salesforce MRR vs Stripe/Billing MRR vs Snowflake mart MRR.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    DISCREPANCY = "discrepancy"
    UNRESOLVED = "unresolved"


class DiscrepancyType(str, Enum):
    AMOUNT_MISMATCH = "amount_mismatch"
    MISSING_IN_SOURCE = "missing_in_source"
    TIMING_LAG = "timing_lag"
    CURRENCY_ROUNDING = "currency_rounding"


class RuleAction(str, Enum):
    FLAG = "flag"
    AUTO_RESOLVE = "auto_resolve"
    ESCALATE = "escalate"


class RuleCheckType(str, Enum):
    ABSOLUTE_THRESHOLD = "absolute_threshold"
    PERCENTAGE_THRESHOLD = "percentage_threshold"
    MISSING_RECORD = "missing_record"
    CURRENCY_NORMALIZATION = "currency_normalization"
    TIMING_WINDOW = "timing_window"


@dataclass
class ReconciliationRecord:
    """Individual account reconciliation comparing three MRR sources."""

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReconciliationRecord":
        status = data.get("status", "matched")
        if isinstance(status, str):
            status = ReconciliationStatus(status)

        disc_type = data.get("discrepancy_type")
        if isinstance(disc_type, str):
            disc_type = DiscrepancyType(disc_type)

        return cls(
            account_id=data["account_id"],
            account_name=data["account_name"],
            sf_mrr=float(data.get("sf_mrr", 0)),
            billing_mrr=float(data.get("billing_mrr", 0)),
            snowflake_mrr=float(data.get("snowflake_mrr", 0)),
            sf_vs_billing_diff=float(data.get("sf_vs_billing_diff", 0)),
            sf_vs_snowflake_diff=float(data.get("sf_vs_snowflake_diff", 0)),
            billing_vs_snowflake_diff=float(data.get("billing_vs_snowflake_diff", 0)),
            status=status,
            discrepancy_type=disc_type,
            resolution_notes=data.get("resolution_notes"),
        )


@dataclass
class ReconciliationRun:
    """Aggregate statistics for a single reconciliation run."""

    id: str
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
        result = {
            "id": self.id,
            "run_date": self.run_date,
            "total_accounts": self.total_accounts,
            "matched_count": self.matched_count,
            "discrepancy_count": self.discrepancy_count,
            "match_rate": round(self.matched_count / self.total_accounts * 100, 2) if self.total_accounts else 0,
            "total_discrepancy_value": round(self.total_discrepancy_value, 2),
            "largest_discrepancy": round(self.largest_discrepancy, 2),
            "avg_discrepancy": round(self.avg_discrepancy, 2),
            "run_duration_seconds": round(self.run_duration_seconds, 2),
        }
        if include_records:
            result["records"] = [r.to_dict() for r in self.records]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReconciliationRun":
        records = [ReconciliationRecord.from_dict(r) for r in data.get("records", [])]
        return cls(
            id=data["id"],
            run_date=data["run_date"],
            total_accounts=int(data.get("total_accounts", 0)),
            matched_count=int(data.get("matched_count", 0)),
            discrepancy_count=int(data.get("discrepancy_count", 0)),
            total_discrepancy_value=float(data.get("total_discrepancy_value", 0)),
            largest_discrepancy=float(data.get("largest_discrepancy", 0)),
            avg_discrepancy=float(data.get("avg_discrepancy", 0)),
            run_duration_seconds=float(data.get("run_duration_seconds", 0)),
            records=records,
        )


@dataclass
class ReconciliationRule:
    """Rule defining how a reconciliation check is performed."""

    name: str
    description: str
    check_type: RuleCheckType
    threshold: float
    action: RuleAction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "check_type": self.check_type.value,
            "threshold": self.threshold,
            "action": self.action.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReconciliationRule":
        check_type = data.get("check_type", "absolute_threshold")
        if isinstance(check_type, str):
            check_type = RuleCheckType(check_type)

        action = data.get("action", "flag")
        if isinstance(action, str):
            action = RuleAction(action)

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            check_type=check_type,
            threshold=float(data.get("threshold", 0)),
            action=action,
        )
