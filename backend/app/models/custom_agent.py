"""
Custom agent configuration model.
User-defined simulation agents with tunable personality traits,
expertise areas, communication styles, and backstories.
Persisted as JSON files in backend/data/agents/.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


VALID_COMMUNICATION_STYLES = (
    'formal', 'casual', 'data_driven', 'storytelling', 'diplomatic'
)

# Resolve storage path relative to this file: backend/app/models/ -> backend/data/agents/
AGENTS_DATA_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'agents'
)


@dataclass
class PersonalityVector:
    """Five-axis personality profile, each dimension scored 0-100."""
    analytical: int = 50
    creative: int = 50
    assertive: int = 50
    empathetic: int = 50
    risk_tolerant: int = 50

    def validate(self) -> List[str]:
        errors = []
        for attr in ('analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant'):
            val = getattr(self, attr)
            if not isinstance(val, int):
                errors.append(f"personality.{attr} must be an integer")
            elif not 0 <= val <= 100:
                errors.append(f"personality.{attr} must be between 0 and 100")
        return errors

    def to_dict(self) -> Dict[str, int]:
        return {
            "analytical": self.analytical,
            "creative": self.creative,
            "assertive": self.assertive,
            "empathetic": self.empathetic,
            "risk_tolerant": self.risk_tolerant,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityVector':
        return cls(
            analytical=int(data.get('analytical', 50)),
            creative=int(data.get('creative', 50)),
            assertive=int(data.get('assertive', 50)),
            empathetic=int(data.get('empathetic', 50)),
            risk_tolerant=int(data.get('risk_tolerant', 50)),
        )


@dataclass
class CustomAgentConfig:
    """A user-defined agent configuration for GTM simulations."""
    id: str
    name: str
    role: str
    department: str
    personality: PersonalityVector
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = 'formal'
    biases: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    backstory: str = ''
    avatar_color: str = '#2068FF'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def validate(self) -> List[str]:
        """Return a list of validation error strings (empty = valid)."""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("name is required")
        if self.communication_style not in VALID_COMMUNICATION_STYLES:
            errors.append(
                f"communication_style must be one of: {', '.join(VALID_COMMUNICATION_STYLES)}"
            )
        if not self.expertise_areas:
            errors.append("at least one expertise_areas entry is required")
        errors.extend(self.personality.validate())
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "personality": self.personality.to_dict(),
            "expertise_areas": self.expertise_areas,
            "communication_style": self.communication_style,
            "biases": self.biases,
            "goals": self.goals,
            "backstory": self.backstory,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomAgentConfig':
        personality_data = data.get('personality', {})
        personality = (
            PersonalityVector.from_dict(personality_data)
            if isinstance(personality_data, dict)
            else PersonalityVector()
        )
        return cls(
            id=data.get('id', f"agent_{uuid.uuid4().hex[:12]}"),
            name=data.get('name', ''),
            role=data.get('role', ''),
            department=data.get('department', ''),
            personality=personality,
            expertise_areas=data.get('expertise_areas', []),
            communication_style=data.get('communication_style', 'formal'),
            biases=data.get('biases', []),
            goals=data.get('goals', []),
            backstory=data.get('backstory', ''),
            avatar_color=data.get('avatar_color', '#2068FF'),
            created_at=data.get('created_at', datetime.now().isoformat()),
        )


class CustomAgentManager:
    """File-based CRUD manager for custom agent configs.

    Each agent is stored as ``<id>.json`` inside AGENTS_DATA_DIR.
    """

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(AGENTS_DATA_DIR, exist_ok=True)

    @classmethod
    def _agent_path(cls, agent_id: str) -> str:
        return os.path.join(AGENTS_DATA_DIR, f"{agent_id}.json")

    @classmethod
    def create(cls, data: Dict[str, Any]) -> CustomAgentConfig:
        """Create a new agent from a dict (assigns a fresh id)."""
        cls._ensure_dir()
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        data['id'] = agent_id
        data.setdefault('created_at', datetime.now().isoformat())
        agent = CustomAgentConfig.from_dict(data)
        cls._write(agent)
        return agent

    @classmethod
    def get(cls, agent_id: str) -> Optional[CustomAgentConfig]:
        path = cls._agent_path(agent_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return CustomAgentConfig.from_dict(json.load(f))

    @classmethod
    def list_all(cls, limit: int = 100) -> List[CustomAgentConfig]:
        cls._ensure_dir()
        agents = []
        for fname in os.listdir(AGENTS_DATA_DIR):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(AGENTS_DATA_DIR, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    agents.append(CustomAgentConfig.from_dict(json.load(f)))
            except (json.JSONDecodeError, KeyError):
                continue
        agents.sort(key=lambda a: a.created_at, reverse=True)
        return agents[:limit]

    @classmethod
    def update(cls, agent_id: str, data: Dict[str, Any]) -> Optional[CustomAgentConfig]:
        """Merge *data* into an existing agent. Returns None if not found."""
        existing = cls.get(agent_id)
        if existing is None:
            return None
        merged = existing.to_dict()
        merged.update(data)
        merged['id'] = agent_id  # prevent id override
        agent = CustomAgentConfig.from_dict(merged)
        cls._write(agent)
        return agent

    @classmethod
    def delete(cls, agent_id: str) -> bool:
        path = cls._agent_path(agent_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    @classmethod
    def _write(cls, agent: CustomAgentConfig) -> None:
        cls._ensure_dir()
        path = cls._agent_path(agent.id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(agent.to_dict(), f, ensure_ascii=False, indent=2)
