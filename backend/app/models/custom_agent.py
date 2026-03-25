"""
Custom Agent Configuration Model
Persists agent configs as JSON files in backend/data/agents/
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


COMMUNICATION_STYLES = ['formal', 'casual', 'data_driven', 'storytelling', 'diplomatic']

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/agents')


@dataclass
class PersonalityVector:
    analytical: int = 50
    creative: int = 50
    assertive: int = 50
    empathetic: int = 50
    risk_tolerant: int = 50

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
            analytical=data.get('analytical', 50),
            creative=data.get('creative', 50),
            assertive=data.get('assertive', 50),
            empathetic=data.get('empathetic', 50),
            risk_tolerant=data.get('risk_tolerant', 50),
        )

    def validate(self) -> List[str]:
        errors = []
        for name in ('analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant'):
            val = getattr(self, name)
            if not isinstance(val, (int, float)) or val < 0 or val > 100:
                errors.append(f"personality.{name} must be 0-100")
        return errors


@dataclass
class CustomAgentConfig:
    id: str
    name: str
    role: str
    department: str = ""
    personality: PersonalityVector = field(default_factory=PersonalityVector)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = "formal"
    biases: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    backstory: str = ""
    avatar_color: str = "#2068FF"
    created_at: str = ""
    updated_at: str = ""

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
            "updated_at": self.updated_at,
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
            id=data.get('id', ''),
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
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
        )

    def validate(self) -> List[str]:
        errors = []
        if not self.name or not self.name.strip():
            errors.append("name is required")
        if not self.expertise_areas:
            errors.append("at least one expertise_area is required")
        if self.communication_style not in COMMUNICATION_STYLES:
            errors.append(f"communication_style must be one of: {', '.join(COMMUNICATION_STYLES)}")
        errors.extend(self.personality.validate())
        return errors


class CustomAgentManager:
    """Manages persistence of custom agent configs as JSON files."""

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(DATA_DIR, exist_ok=True)

    @classmethod
    def _agent_path(cls, agent_id: str) -> str:
        return os.path.join(DATA_DIR, f"{agent_id}.json")

    @classmethod
    def create(cls, data: Dict[str, Any]) -> CustomAgentConfig:
        cls._ensure_dir()
        now = datetime.now().isoformat()
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        data['id'] = agent_id
        data['created_at'] = now
        data['updated_at'] = now
        agent = CustomAgentConfig.from_dict(data)
        cls._save(agent)
        return agent

    @classmethod
    def _save(cls, agent: CustomAgentConfig):
        cls._ensure_dir()
        path = cls._agent_path(agent.id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(agent.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get(cls, agent_id: str) -> Optional[CustomAgentConfig]:
        path = cls._agent_path(agent_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return CustomAgentConfig.from_dict(json.load(f))

    @classmethod
    def list_agents(cls, limit: int = 100) -> List[CustomAgentConfig]:
        cls._ensure_dir()
        agents = []
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('.json'):
                path = os.path.join(DATA_DIR, fname)
                with open(path, 'r', encoding='utf-8') as f:
                    agents.append(CustomAgentConfig.from_dict(json.load(f)))
        agents.sort(key=lambda a: a.created_at, reverse=True)
        return agents[:limit]

    @classmethod
    def update(cls, agent_id: str, data: Dict[str, Any]) -> Optional[CustomAgentConfig]:
        agent = cls.get(agent_id)
        if not agent:
            return None
        data.pop('id', None)
        data.pop('created_at', None)
        data['updated_at'] = datetime.now().isoformat()
        merged = agent.to_dict()
        merged.update(data)
        updated = CustomAgentConfig.from_dict(merged)
        cls._save(updated)
        return updated

    @classmethod
    def delete(cls, agent_id: str) -> bool:
        path = cls._agent_path(agent_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    @classmethod
    def clone(cls, agent_id: str) -> Optional[CustomAgentConfig]:
        agent = cls.get(agent_id)
        if not agent:
            return None
        clone_data = agent.to_dict()
        clone_data['name'] = f"{agent.name} (Copy)"
        return cls.create(clone_data)
