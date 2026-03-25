"""
Pipeline stage data model for GTM funnel visualization.
Defines the Intercom GTM funnel: Raw Lead -> MQL -> SQL -> SAO -> Proposal -> Closed Won / Closed Lost
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


# Standard Intercom GTM funnel stages with realistic conversion rates
FUNNEL_STAGES = [
    {"name": "Raw Lead", "order": 0, "conversion_rate_to_next": 0.25, "avg_days_in_stage": 5, "color": "#6B9FFF"},
    {"name": "MQL", "order": 1, "conversion_rate_to_next": 0.40, "avg_days_in_stage": 8, "color": "#2068FF"},
    {"name": "SQL", "order": 2, "conversion_rate_to_next": 0.60, "avg_days_in_stage": 12, "color": "#1A4FCC"},
    {"name": "SAO", "order": 3, "conversion_rate_to_next": 0.70, "avg_days_in_stage": 15, "color": "#ff5600"},
    {"name": "Proposal", "order": 4, "conversion_rate_to_next": 0.35, "avg_days_in_stage": 20, "color": "#CC4500"},
    {"name": "Closed Won", "order": 5, "conversion_rate_to_next": None, "avg_days_in_stage": 0, "color": "#2DB553"},
    {"name": "Closed Lost", "order": 6, "conversion_rate_to_next": None, "avg_days_in_stage": 0, "color": "#8C8C8C"},
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
        return {
            "name": self.name,
            "order": self.order,
            "count": self.count,
            "value": self.value,
            "conversion_rate_to_next": self.conversion_rate_to_next,
            "avg_days_in_stage": self.avg_days_in_stage,
            "color": self.color,
        }

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
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "timestamp": self.timestamp,
            "duration_days": self.duration_days,
            "owner": self.owner,
        }

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


def default_funnel_stages(raw_lead_count: int = 1000) -> List[PipelineStage]:
    """Build the standard Intercom GTM funnel with counts derived from conversion rates.

    Starting from ``raw_lead_count`` Raw Leads, each subsequent stage count is
    computed by multiplying the previous count by its conversion rate.  Closed
    Lost receives the leads that drop off at the Proposal stage.
    """
    stages: List[PipelineStage] = []
    current_count = raw_lead_count
    avg_deal_value = 18_000.0

    for cfg in FUNNEL_STAGES:
        if cfg["name"] == "Closed Lost":
            # Closed Lost = leads that didn't convert from Proposal
            proposal = next(s for s in stages if s.name == "Proposal")
            lost_count = proposal.count - int(proposal.count * (proposal.conversion_rate_to_next or 0))
            stages.append(PipelineStage(
                name=cfg["name"],
                order=cfg["order"],
                count=lost_count,
                value=0.0,
                conversion_rate_to_next=None,
                avg_days_in_stage=cfg["avg_days_in_stage"],
                color=cfg["color"],
            ))
            continue

        stage = PipelineStage(
            name=cfg["name"],
            order=cfg["order"],
            count=current_count,
            value=current_count * avg_deal_value if cfg["name"] in ("Proposal", "Closed Won") else 0.0,
            conversion_rate_to_next=cfg["conversion_rate_to_next"],
            avg_days_in_stage=cfg["avg_days_in_stage"],
            color=cfg["color"],
        )
        stages.append(stage)

        if cfg["conversion_rate_to_next"] is not None:
            current_count = int(current_count * cfg["conversion_rate_to_next"])

    return stages
