"""
Pipeline data models for GTM funnel analytics.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class PipelineStage:
    name: str
    order: int
    count: int
    value: float
    conversion_rate_to_next: float
    avg_days_in_stage: float
    color: str

    def to_dict(self):
        return asdict(self)


@dataclass
class FunnelSnapshot:
    timestamp: str
    stages: List[PipelineStage]
    total_leads: int
    total_revenue: float

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "stages": [s.to_dict() for s in self.stages],
            "total_leads": self.total_leads,
            "total_revenue": self.total_revenue,
        }


@dataclass
class ConversionEvent:
    id: str
    entity_id: str
    from_stage: str
    to_stage: str
    timestamp: str
    duration_days: int
    owner: str

    def to_dict(self):
        return asdict(self)


# Standard Intercom GTM funnel definition
PIPELINE_STAGES = [
    {"name": "Raw Lead", "order": 0, "conversion_rate": 0.25, "avg_days": 7, "color": "#2068FF"},
    {"name": "MQL", "order": 1, "conversion_rate": 0.40, "avg_days": 14, "color": "#1a5ae0"},
    {"name": "SQL", "order": 2, "conversion_rate": 0.60, "avg_days": 21, "color": "#ff5600"},
    {"name": "SAO", "order": 3, "conversion_rate": 0.70, "avg_days": 14, "color": "#e04d00"},
    {"name": "Proposal", "order": 4, "conversion_rate": 0.35, "avg_days": 10, "color": "#050505"},
    {"name": "Closed Won", "order": 5, "conversion_rate": 0.0, "avg_days": 0, "color": "#22c55e"},
    {"name": "Closed Lost", "order": 6, "conversion_rate": 0.0, "avg_days": 0, "color": "#ef4444"},
]
