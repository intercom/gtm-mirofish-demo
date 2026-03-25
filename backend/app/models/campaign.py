"""
Campaign ROI data models.

Dataclasses for campaign performance tracking, cost breakdown,
and multi-touch attribution analysis.
"""

import uuid
from datetime import date
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class CampaignType(str, Enum):
    PAID = "paid"
    ORGANIC = "organic"
    EVENT = "event"
    EMAIL = "email"
    PARTNER = "partner"


class CampaignStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PLANNED = "planned"


class CostType(str, Enum):
    AD_SPEND = "ad_spend"
    TOOLS = "tools"
    CONTENT = "content"
    EVENTS = "events"
    LABOR = "labor"


class AttributionModel(str, Enum):
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"


@dataclass
class Campaign:
    id: str
    name: str
    type: CampaignType
    channel: str
    start_date: str
    end_date: str
    budget: float
    spend_to_date: float = 0.0
    leads_generated: int = 0
    mqls: int = 0
    sqls: int = 0
    opportunities: int = 0
    closed_won_value: float = 0.0
    cpl: float = 0.0
    cpa: float = 0.0
    roi_percentage: float = 0.0
    status: CampaignStatus = CampaignStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "channel": self.channel,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "budget": self.budget,
            "spend_to_date": self.spend_to_date,
            "leads_generated": self.leads_generated,
            "mqls": self.mqls,
            "sqls": self.sqls,
            "opportunities": self.opportunities,
            "closed_won_value": self.closed_won_value,
            "cpl": self.cpl,
            "cpa": self.cpa,
            "roi_percentage": self.roi_percentage,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        campaign_type = data.get("type", "paid")
        if isinstance(campaign_type, str):
            campaign_type = CampaignType(campaign_type)

        status = data.get("status", "active")
        if isinstance(status, str):
            status = CampaignStatus(status)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            type=campaign_type,
            channel=data.get("channel", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            budget=data.get("budget", 0.0),
            spend_to_date=data.get("spend_to_date", 0.0),
            leads_generated=data.get("leads_generated", 0),
            mqls=data.get("mqls", 0),
            sqls=data.get("sqls", 0),
            opportunities=data.get("opportunities", 0),
            closed_won_value=data.get("closed_won_value", 0.0),
            cpl=data.get("cpl", 0.0),
            cpa=data.get("cpa", 0.0),
            roi_percentage=data.get("roi_percentage", 0.0),
            status=status,
        )


@dataclass
class CampaignCostBreakdown:
    campaign_id: str
    cost_type: CostType
    amount: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "cost_type": self.cost_type.value,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignCostBreakdown":
        cost_type = data.get("cost_type", "ad_spend")
        if isinstance(cost_type, str):
            cost_type = CostType(cost_type)

        return cls(
            campaign_id=data["campaign_id"],
            cost_type=cost_type,
            amount=data.get("amount", 0.0),
        )


@dataclass
class CampaignAttribution:
    campaign_id: str
    opportunity_id: str
    attribution_model: AttributionModel
    credit_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "opportunity_id": self.opportunity_id,
            "attribution_model": self.attribution_model.value,
            "credit_percentage": self.credit_percentage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignAttribution":
        model = data.get("attribution_model", "first_touch")
        if isinstance(model, str):
            model = AttributionModel(model)

        return cls(
            campaign_id=data["campaign_id"],
            opportunity_id=data.get("opportunity_id", ""),
            attribution_model=model,
            credit_percentage=data.get("credit_percentage", 0.0),
        )
