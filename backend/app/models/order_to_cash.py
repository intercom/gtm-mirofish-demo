"""
Order-to-Cash data models.

Models the Intercom order lifecycle:
Quote Approved -> Order Created -> Validation -> Provisioning -> Billing -> Active
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class OrderStatus(str, Enum):
    PENDING = "Pending"
    VALIDATED = "Validated"
    PROVISIONED = "Provisioned"
    ACTIVE = "Active"
    FAILED = "Failed"


class ProvisioningStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class BillingStatus(str, Enum):
    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"
    OVERDUE = "overdue"


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Result of a single validation check on an order."""
    order_id: str
    field: str
    status: ValidationStatus
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "field": self.field,
            "status": self.status.value if isinstance(self.status, ValidationStatus) else self.status,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        status = data.get("status", "pass")
        if isinstance(status, str):
            status = ValidationStatus(status)
        return cls(
            order_id=data["order_id"],
            field=data.get("field", ""),
            status=status,
            message=data.get("message", ""),
        )


@dataclass
class ProvisioningStep:
    """A single provisioning step within an order's activation workflow."""
    order_id: str
    step_name: str
    status: ProvisioningStatus = ProvisioningStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "step_name": self.step_name,
            "status": self.status.value if isinstance(self.status, ProvisioningStatus) else self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvisioningStep":
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = ProvisioningStatus(status)
        return cls(
            order_id=data["order_id"],
            step_name=data.get("step_name", ""),
            status=status,
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
        )


@dataclass
class BillingRecord:
    """A billing/invoice record tied to an active order."""
    id: str
    order_id: str
    account_id: str
    amount: float
    period_start: str
    period_end: str
    status: BillingStatus = BillingStatus.PENDING
    invoice_number: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "account_id": self.account_id,
            "amount": self.amount,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "status": self.status.value if isinstance(self.status, BillingStatus) else self.status,
            "invoice_number": self.invoice_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BillingRecord":
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = BillingStatus(status)
        return cls(
            id=data["id"],
            order_id=data["order_id"],
            account_id=data.get("account_id", ""),
            amount=data.get("amount", 0.0),
            period_start=data.get("period_start", ""),
            period_end=data.get("period_end", ""),
            status=status,
            invoice_number=data.get("invoice_number"),
        )


@dataclass
class Order:
    """An order created from an approved quote, tracking its lifecycle through provisioning to billing."""
    id: str
    quote_id: str
    account_id: str
    status: OrderStatus = OrderStatus.PENDING
    total: float = 0.0
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    created_date: str = ""
    activated_date: Optional[str] = None
    provisioning_steps: List[ProvisioningStep] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    billing_records: List[BillingRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "quote_id": self.quote_id,
            "account_id": self.account_id,
            "status": self.status.value if isinstance(self.status, OrderStatus) else self.status,
            "total": self.total,
            "line_items": self.line_items,
            "created_date": self.created_date,
            "activated_date": self.activated_date,
            "provisioning_steps": [s.to_dict() for s in self.provisioning_steps],
            "validation_results": [v.to_dict() for v in self.validation_results],
            "billing_records": [b.to_dict() for b in self.billing_records],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        status = data.get("status", "Pending")
        if isinstance(status, str):
            status = OrderStatus(status)
        order = cls(
            id=data["id"],
            quote_id=data.get("quote_id", ""),
            account_id=data.get("account_id", ""),
            status=status,
            total=data.get("total", 0.0),
            line_items=data.get("line_items", []),
            created_date=data.get("created_date", ""),
            activated_date=data.get("activated_date"),
        )
        order.provisioning_steps = [
            ProvisioningStep.from_dict(s) for s in data.get("provisioning_steps", [])
        ]
        order.validation_results = [
            ValidationResult.from_dict(v) for v in data.get("validation_results", [])
        ]
        order.billing_records = [
            BillingRecord.from_dict(b) for b in data.get("billing_records", [])
        ]
        return order
