"""
Session management
Persistent session state for grouping simulation runs and scenario work.
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from ..config import Config


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Session:
    session_id: str
    name: str
    status: SessionStatus
    created_at: str
    updated_at: str
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None
    project_id: Optional[str] = None
    simulation_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "status": self.status.value if isinstance(self.status, SessionStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "project_id": self.project_id,
            "simulation_ids": self.simulation_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        status = data.get('status', 'active')
        if isinstance(status, str):
            status = SessionStatus(status)

        return cls(
            session_id=data['session_id'],
            name=data.get('name', 'Untitled Session'),
            status=status,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            scenario_id=data.get('scenario_id'),
            scenario_name=data.get('scenario_name'),
            project_id=data.get('project_id'),
            simulation_ids=data.get('simulation_ids', []),
            metadata=data.get('metadata', {}),
        )


class SessionManager:
    """File-based session persistence under uploads/sessions/."""

    SESSIONS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'sessions')

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.SESSIONS_DIR, exist_ok=True)

    @classmethod
    def _session_path(cls, session_id: str) -> str:
        return os.path.join(cls.SESSIONS_DIR, session_id, 'session.json')

    @classmethod
    def _session_dir(cls, session_id: str) -> str:
        return os.path.join(cls.SESSIONS_DIR, session_id)

    @classmethod
    def create(cls, name: str = "Untitled Session", **kwargs) -> Session:
        cls._ensure_dir()

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        session = Session(
            session_id=session_id,
            name=name,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            scenario_id=kwargs.get('scenario_id'),
            scenario_name=kwargs.get('scenario_name'),
            project_id=kwargs.get('project_id'),
            metadata=kwargs.get('metadata', {}),
        )

        os.makedirs(cls._session_dir(session_id), exist_ok=True)
        cls.save(session)
        return session

    @classmethod
    def save(cls, session: Session) -> None:
        session.updated_at = datetime.now().isoformat()
        path = cls._session_path(session.session_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get(cls, session_id: str) -> Optional[Session]:
        path = cls._session_path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Session.from_dict(data)

    @classmethod
    def list_sessions(cls, status: Optional[str] = None, limit: int = 50) -> List[Session]:
        cls._ensure_dir()
        sessions = []
        for entry in os.listdir(cls.SESSIONS_DIR):
            session = cls.get(entry)
            if session:
                if status and session.status.value != status:
                    continue
                sessions.append(session)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]

    @classmethod
    def delete(cls, session_id: str) -> bool:
        session_dir = cls._session_dir(session_id)
        if not os.path.exists(session_dir):
            return False
        shutil.rmtree(session_dir)
        return True

    @classmethod
    def add_simulation(cls, session_id: str, simulation_id: str) -> Optional[Session]:
        session = cls.get(session_id)
        if not session:
            return None
        if simulation_id not in session.simulation_ids:
            session.simulation_ids.append(simulation_id)
            cls.save(session)
        return session
