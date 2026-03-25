"""
Data pipeline models.
Represents sync jobs, dbt models, tests, and data freshness
for the pipeline monitoring dashboard.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class SyncJob:
    id: str
    connector_name: str
    source: str
    destination: str
    status: str  # running|success|failed|scheduled
    rows_synced: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connector_name": self.connector_name,
            "source": self.source,
            "destination": self.destination,
            "status": self.status,
            "rows_synced": self.rows_synced,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
        }


@dataclass
class DbtModel:
    name: str
    schema: str
    materialization: str  # table|view|incremental
    depends_on: List[str] = field(default_factory=list)
    status: str = "success"  # success|error|skipped
    rows_affected: int = 0
    execution_time_seconds: float = 0.0
    last_run: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "materialization": self.materialization,
            "depends_on": self.depends_on,
            "status": self.status,
            "rows_affected": self.rows_affected,
            "execution_time_seconds": self.execution_time_seconds,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }


@dataclass
class DbtTest:
    name: str
    model: str
    status: str  # pass|fail|warn
    severity: str  # error|warn
    message: str = ""
    last_run: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }


@dataclass
class DataFreshness:
    table_name: str
    last_updated: datetime
    expected_interval_hours: float
    is_stale: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "last_updated": self.last_updated.isoformat(),
            "expected_interval_hours": self.expected_interval_hours,
            "is_stale": self.is_stale,
        }
