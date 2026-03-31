"""
Pipeline data models for GTM funnel analytics.
Defines the Intercom GTM funnel: Raw Lead -> MQL -> SQL -> SAO -> Proposal -> Closed Won / Closed Lost
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional


# Standard Intercom GTM funnel definition
FUNNEL_STAGES = PIPELINE_STAGES = [
    {"name": "Raw Lead", "order": 0, "conversion_rate": 0.25, "avg_days": 7, "color": "#2068FF"},
    {"name": "MQL", "order": 1, "conversion_rate": 0.40, "avg_days": 14, "color": "#1a5ae0"},
    {"name": "SQL", "order": 2, "conversion_rate": 0.60, "avg_days": 21, "color": "#ff5600"},
    {"name": "SAO", "order": 3, "conversion_rate": 0.70, "avg_days": 14, "color": "#e04d00"},
    {"name": "Proposal", "order": 4, "conversion_rate": 0.35, "avg_days": 10, "color": "#050505"},
    {"name": "Closed Won", "order": 5, "conversion_rate": 0.0, "avg_days": 0, "color": "#22c55e"},
    {"name": "Closed Lost", "order": 6, "conversion_rate": 0.0, "avg_days": 0, "color": "#ef4444"},
]


@dataclass
class PipelineStage:
    """A single stage in the GTM pipeline funnel."""
    name: str
    order: int
    count: int = 0
    value: float = 0.0
    conversion_rate_to_next: Optional[float] = None
    avg_days_in_stage: float = 0.0
    color: str = "#2068FF"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineStage":
        return cls(
            name=data["name"],
            order=data["order"],
            count=data.get("count", 0),
            value=data.get("value", 0.0),
            conversion_rate_to_next=data.get("conversion_rate_to_next"),
            avg_days_in_stage=data.get("avg_days_in_stage", 0.0),
            color=data.get("color", "#2068FF"),
        )


@dataclass
class FunnelSnapshot:
    """A point-in-time snapshot of the entire funnel."""
    timestamp: str
    stages: List[PipelineStage] = field(default_factory=list)
    total_leads: int = 0
    total_revenue: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "stages": [s.to_dict() for s in self.stages],
            "total_leads": self.total_leads,
            "total_revenue": self.total_revenue,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunnelSnapshot":
        return cls(
            timestamp=data["timestamp"],
            stages=[PipelineStage.from_dict(s) for s in data.get("stages", [])],
            total_leads=data.get("total_leads", 0),
            total_revenue=data.get("total_revenue", 0.0),
        )


@dataclass
class ConversionEvent:
    """An individual entity moving between pipeline stages."""
    id: str
    entity_id: str
    from_stage: str
    to_stage: str
    timestamp: str
    duration_days: float = 0.0
    owner: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversionEvent":
        return cls(
            id=data["id"],
            entity_id=data["entity_id"],
            from_stage=data["from_stage"],
            to_stage=data["to_stage"],
            timestamp=data["timestamp"],
            duration_days=data.get("duration_days", 0.0),
            owner=data.get("owner", ""),
        )


def default_funnel_stages() -> List[PipelineStage]:
    """Return default pipeline stages as PipelineStage objects."""
    return [PipelineStage.from_dict(s) for s in PIPELINE_STAGES]
