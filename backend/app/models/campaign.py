"""
Campaign ROI data models.
Dataclasses representing campaigns, cost breakdowns, and multi-touch attribution.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class CampaignCostBreakdown:
    campaign_id: str
    cost_type: str  # ad_spend | tools | content | events | labor
    amount: float

    def to_dict(self):
        return asdict(self)


@dataclass
class CampaignAttribution:
    campaign_id: str
    opportunity_id: str
    attribution_model: str  # first_touch | last_touch | linear | time_decay
    credit_percentage: float

    def to_dict(self):
        return asdict(self)


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
    cost_breakdown: List[CampaignCostBreakdown] = field(default_factory=list)
    attributions: List[CampaignAttribution] = field(default_factory=list)

    def to_dict(self, include_details=False):
        d = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'channel': self.channel,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'budget': self.budget,
            'spend_to_date': self.spend_to_date,
            'leads_generated': self.leads_generated,
            'mqls': self.mqls,
            'sqls': self.sqls,
            'opportunities': self.opportunities,
            'closed_won_value': self.closed_won_value,
            'cpl': self.cpl,
            'cpa': self.cpa,
            'roi_percentage': self.roi_percentage,
            'status': self.status,
        }
        if include_details:
            d['cost_breakdown'] = [c.to_dict() for c in self.cost_breakdown]
            d['attributions'] = [a.to_dict() for a in self.attributions]
        return d
