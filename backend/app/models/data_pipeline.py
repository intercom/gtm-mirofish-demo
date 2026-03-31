"""
Data pipeline models for sync job tracking, dbt model/test status, and data freshness.
Covers both Fivetran (source → Snowflake) and Census (Snowflake → CRM) sync patterns.
Used by the pipeline sync generator to produce realistic demo data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SyncStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class SyncDirection(str, Enum):
    INGEST = "ingest"          # Fivetran: source → warehouse
    REVERSE = "reverse"        # Census: warehouse → destination


class DbtMaterialization(str, Enum):
    TABLE = "table"
    VIEW = "view"
    INCREMENTAL = "incremental"


class DbtModelStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class DbtTestStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class DbtTestSeverity(str, Enum):
    ERROR = "error"
    WARN = "warn"


@dataclass
class SyncJob:
    id: str
    connector_name: str
    source: str
    destination: str
    status: SyncStatus
    started_at: str
    direction: SyncDirection = SyncDirection.INGEST
    completed_at: Optional[str] = None
    rows_synced: int = 0
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connector_name": self.connector_name,
            "source": self.source,
            "destination": self.destination,
            "status": self.status.value if isinstance(self.status, SyncStatus) else self.status,
            "direction": self.direction.value if isinstance(self.direction, SyncDirection) else self.direction,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "rows_synced": self.rows_synced,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncJob":
        status = data.get("status", "scheduled")
        if isinstance(status, str):
            status = SyncStatus(status)
        direction = data.get("direction", "ingest")
        if isinstance(direction, str):
            direction = SyncDirection(direction)
        return cls(
            id=data["id"],
            connector_name=data["connector_name"],
            source=data["source"],
            destination=data["destination"],
            status=status,
            direction=direction,
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at"),
            rows_synced=data.get("rows_synced", 0),
            duration_seconds=data.get("duration_seconds"),
            error_message=data.get("error_message"),
        )


@dataclass
class DbtModel:
    name: str
    schema: str
    materialization: DbtMaterialization
    status: DbtModelStatus
    depends_on: List[str] = field(default_factory=list)
    rows_affected: int = 0
    execution_time_seconds: Optional[float] = None
    last_run: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "materialization": self.materialization.value if isinstance(self.materialization, DbtMaterialization) else self.materialization,
            "status": self.status.value if isinstance(self.status, DbtModelStatus) else self.status,
            "depends_on": self.depends_on,
            "rows_affected": self.rows_affected,
            "execution_time_seconds": self.execution_time_seconds,
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DbtModel":
        materialization = data.get("materialization", "table")
        if isinstance(materialization, str):
            materialization = DbtMaterialization(materialization)
        status = data.get("status", "success")
        if isinstance(status, str):
            status = DbtModelStatus(status)
        return cls(
            name=data["name"],
            schema=data["schema"],
            materialization=materialization,
            status=status,
            depends_on=data.get("depends_on", []),
            rows_affected=data.get("rows_affected", 0),
            execution_time_seconds=data.get("execution_time_seconds"),
            last_run=data.get("last_run"),
        )


@dataclass
class DbtTest:
    name: str
    model: str
    status: DbtTestStatus
    severity: DbtTestSeverity = DbtTestSeverity.ERROR
    message: Optional[str] = None
    last_run: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status.value if isinstance(self.status, DbtTestStatus) else self.status,
            "severity": self.severity.value if isinstance(self.severity, DbtTestSeverity) else self.severity,
            "message": self.message,
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DbtTest":
        status = data.get("status", "pass")
        if isinstance(status, str):
            status = DbtTestStatus(status)
        severity = data.get("severity", "error")
        if isinstance(severity, str):
            severity = DbtTestSeverity(severity)
        return cls(
            name=data["name"],
            model=data["model"],
            status=status,
            severity=severity,
            message=data.get("message"),
            last_run=data.get("last_run"),
        )


@dataclass
class DataFreshness:
    table_name: str
    last_updated: Optional[str] = None
    expected_interval_hours: float = 24.0
    is_stale: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "last_updated": self.last_updated,
            "expected_interval_hours": self.expected_interval_hours,
            "is_stale": self.is_stale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataFreshness":
        return cls(
            table_name=data["table_name"],
            last_updated=data.get("last_updated"),
            expected_interval_hours=data.get("expected_interval_hours", 24.0),
            is_stale=data.get("is_stale", False),
        )
