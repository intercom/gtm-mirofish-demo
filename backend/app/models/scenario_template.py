"""
Scenario Template data model.
Defines the structure for GTM simulation scenario templates,
persisted as JSON files in backend/data/templates/.
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScenarioCategory(str, Enum):
    GTM_STRATEGY = "GTM Strategy"
    PIPELINE_MANAGEMENT = "Pipeline Management"
    COMPETITIVE_RESPONSE = "Competitive Response"
    REVENUE_OPERATIONS = "Revenue Operations"
    CUSTOMER_SUCCESS = "Customer Success"
    PRODUCT_LAUNCH = "Product Launch"
    TEAM_DYNAMICS = "Team Dynamics"


class ScenarioDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class ScenarioTemplate:
    id: str
    name: str
    description: str
    category: str
    difficulty: str
    recommended_agents: int
    recommended_rounds: int
    agent_roles: List[str] = field(default_factory=list)
    environment_config: Dict[str, Any] = field(default_factory=dict)
    initial_state: Dict[str, Any] = field(default_factory=dict)
    objectives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = "system"
    created_at: str = ""
    usage_count: int = 0
    avg_rating: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioTemplate":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ScenarioCategory.GTM_STRATEGY.value),
            difficulty=data.get("difficulty", ScenarioDifficulty.MEDIUM.value),
            recommended_agents=data.get("recommended_agents", 4),
            recommended_rounds=data.get("recommended_rounds", 8),
            agent_roles=data.get("agent_roles", []),
            environment_config=data.get("environment_config", {}),
            initial_state=data.get("initial_state", {}),
            objectives=data.get("objectives", []),
            tags=data.get("tags", []),
            author=data.get("author", "system"),
            created_at=data.get("created_at", ""),
            usage_count=data.get("usage_count", 0),
            avg_rating=data.get("avg_rating", 0.0),
        )


class ScenarioTemplateManager:
    """Manages CRUD operations for scenario templates persisted as JSON files."""

    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "../../data/templates")

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)

    @classmethod
    def _template_path(cls, template_id: str) -> str:
        safe_id = os.path.basename(template_id)
        return os.path.join(cls.TEMPLATES_DIR, f"{safe_id}.json")

    @classmethod
    def save(cls, template: ScenarioTemplate) -> None:
        cls._ensure_dir()
        path = cls._template_path(template.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get(cls, template_id: str) -> Optional[ScenarioTemplate]:
        path = cls._template_path(template_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ScenarioTemplate.from_dict(data)

    @classmethod
    def list_all(
        cls,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[ScenarioTemplate]:
        cls._ensure_dir()
        templates = []
        for filename in sorted(os.listdir(cls.TEMPLATES_DIR)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(cls.TEMPLATES_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                templates.append(ScenarioTemplate.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

        if category:
            templates = [t for t in templates if t.category == category]
        if tag:
            templates = [t for t in templates if tag in t.tags]
        if search:
            q = search.lower()
            templates = [
                t
                for t in templates
                if q in t.name.lower() or q in t.description.lower()
            ]
        return templates

    @classmethod
    def create(cls, data: Dict[str, Any]) -> ScenarioTemplate:
        template_id = data.get("id") or f"tpl_{uuid.uuid4().hex[:12]}"
        data["id"] = template_id
        if not data.get("created_at"):
            data["created_at"] = datetime.now().isoformat()
        template = ScenarioTemplate.from_dict(data)
        cls.save(template)
        return template

    @classmethod
    def update(cls, template_id: str, updates: Dict[str, Any]) -> Optional[ScenarioTemplate]:
        template = cls.get(template_id)
        if not template:
            return None
        current = template.to_dict()
        current.update(updates)
        current["id"] = template_id
        updated = ScenarioTemplate.from_dict(current)
        cls.save(updated)
        return updated

    @classmethod
    def delete(cls, template_id: str) -> bool:
        path = cls._template_path(template_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    @classmethod
    def increment_usage(cls, template_id: str) -> Optional[ScenarioTemplate]:
        template = cls.get(template_id)
        if not template:
            return None
        template.usage_count += 1
        cls.save(template)
        return template

    @classmethod
    def add_rating(cls, template_id: str, rating: float) -> Optional[ScenarioTemplate]:
        """Add a rating (1-5) using a running average."""
        template = cls.get(template_id)
        if not template:
            return None
        rating = max(1.0, min(5.0, float(rating)))
        total = template.avg_rating * template.usage_count
        template.usage_count = max(template.usage_count, 1)
        template.avg_rating = round(
            (total + rating) / (template.usage_count + 1), 2
        )
        cls.save(template)
        return template

    @classmethod
    def list_categories(cls) -> List[Dict[str, Any]]:
        templates = cls.list_all()
        counts: Dict[str, int] = {}
        for t in templates:
            counts[t.category] = counts.get(t.category, 0) + 1
        return [
            {"category": cat.value, "count": counts.get(cat.value, 0)}
            for cat in ScenarioCategory
        ]
