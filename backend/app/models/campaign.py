"""
Campaign ROI data models.

Dataclasses for campaign performance tracking, cost breakdowns,
and multi-touch attribution analysis.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class Campaign:
    id: str
    name: str
    type: str  # paid | organic | event | email | partner
    channel: str
    start_date: str
    end_date: str
    budget: float
    spend_to_date: float
    leads_generated: int
    mqls: int
    sqls: int
    opportunities: int
    closed_won_value: float
    cpl: float  # cost per lead
    cpa: float  # cost per acquisition
    roi_percentage: float
    status: str  # active | completed | planned

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignCostBreakdown:
    campaign_id: str
    cost_type: str  # ad_spend | tools | content | events | labor
    amount: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignAttribution:
    campaign_id: str
    opportunity_id: str
    attribution_model: str  # first_touch | last_touch | linear | time_decay
    credit_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
