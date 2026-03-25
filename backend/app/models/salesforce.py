"""
Salesforce CRM data models.
Dataclasses representing core Salesforce objects for GTM demo data.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Account:
    id: str
    name: str
    industry: str
    arr: float
    plan_tier: str
    health_score: int
    owner: str
    created_date: str
    renewal_date: str
    employee_count: int = 0
    website: str = ""
    region: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "industry": self.industry,
            "arr": self.arr,
            "plan_tier": self.plan_tier,
            "health_score": self.health_score,
            "owner": self.owner,
            "created_date": self.created_date,
            "renewal_date": self.renewal_date,
            "employee_count": self.employee_count,
            "website": self.website,
            "region": self.region,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            id=data["id"],
            name=data["name"],
            industry=data["industry"],
            arr=data["arr"],
            plan_tier=data["plan_tier"],
            health_score=data["health_score"],
            owner=data["owner"],
            created_date=data["created_date"],
            renewal_date=data["renewal_date"],
            employee_count=data.get("employee_count", 0),
            website=data.get("website", ""),
            region=data.get("region", ""),
        )


@dataclass
class Opportunity:
    id: str
    name: str
    account_id: str
    stage: str
    amount: float
    close_date: str
    probability: int
    owner: str
    type: str
    created_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "account_id": self.account_id,
            "stage": self.stage,
            "amount": self.amount,
            "close_date": self.close_date,
            "probability": self.probability,
            "owner": self.owner,
            "type": self.type,
            "created_date": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Opportunity":
        return cls(
            id=data["id"],
            name=data["name"],
            account_id=data["account_id"],
            stage=data["stage"],
            amount=data["amount"],
            close_date=data["close_date"],
            probability=data["probability"],
            owner=data["owner"],
            type=data["type"],
            created_date=data.get("created_date", ""),
        )


@dataclass
class Contact:
    id: str
    first_name: str
    last_name: str
    email: str
    account_id: str
    title: str
    role: str
    last_activity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "account_id": self.account_id,
            "title": self.title,
            "role": self.role,
            "last_activity": self.last_activity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        return cls(
            id=data["id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            account_id=data["account_id"],
            title=data["title"],
            role=data["role"],
            last_activity=data["last_activity"],
        )


@dataclass
class Lead:
    id: str
    first_name: str
    last_name: str
    email: str
    company: str
    status: str
    source: str
    score: int
    owner: str
    created_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "company": self.company,
            "status": self.status,
            "source": self.source,
            "score": self.score,
            "owner": self.owner,
            "created_date": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lead":
        return cls(
            id=data["id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            company=data["company"],
            status=data["status"],
            source=data["source"],
            score=data["score"],
            owner=data["owner"],
            created_date=data.get("created_date", ""),
        )
