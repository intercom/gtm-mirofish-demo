"""
Order-to-Cash data models.
Models the Intercom order flow: Quote Approved → Order Created → Validation → Provisioning → Billing → Active.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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
class LineItem:
    product: str
    quantity: int
    unit_price: float
    total: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": self.product,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.total,
        }


@dataclass
class Order:
    id: str
    quote_id: str
    account_id: str
    account_name: str
    status: OrderStatus
    total: float
    line_items: List[LineItem]
    created_date: datetime
    activated_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "quote_id": self.quote_id,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "status": self.status.value,
            "total": self.total,
            "line_items": [li.to_dict() for li in self.line_items],
            "created_date": self.created_date.isoformat(),
            "activated_date": self.activated_date.isoformat() if self.activated_date else None,
        }


@dataclass
class ProvisioningStep:
    order_id: str
    step_name: str
    status: ProvisioningStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "step_name": self.step_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


@dataclass
class BillingRecord:
    id: str
    order_id: str
    account_id: str
    amount: float
    period_start: datetime
    period_end: datetime
    status: BillingStatus
    invoice_number: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "account_id": self.account_id,
            "amount": self.amount,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status.value,
            "invoice_number": self.invoice_number,
        }


@dataclass
class ValidationResult:
    order_id: str
    field: str
    status: ValidationStatus
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "field": self.field,
            "status": self.status.value,
            "message": self.message,
        }
