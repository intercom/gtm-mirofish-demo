"""
User model with file-based JSON persistence.
Follows the same pattern as ProjectManager — stores each user as a JSON file
under uploads/users/{user_id}.json.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from ..config import Config


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    INVITED = "invited"


DEMO_USERS = [
    {
        "name": "Sarah Chen",
        "email": "sarah.chen@intercom.io",
        "role": "admin",
        "status": "active",
        "department": "Product",
    },
    {
        "name": "Marcus Johnson",
        "email": "marcus.johnson@intercom.io",
        "role": "member",
        "status": "active",
        "department": "Sales",
    },
    {
        "name": "Elena Rodriguez",
        "email": "elena.rodriguez@intercom.io",
        "role": "member",
        "status": "active",
        "department": "Marketing",
    },
    {
        "name": "James O'Brien",
        "email": "james.obrien@intercom.io",
        "role": "member",
        "status": "active",
        "department": "Customer Success",
    },
    {
        "name": "Priya Patel",
        "email": "priya.patel@intercom.io",
        "role": "viewer",
        "status": "invited",
        "department": "Engineering",
    },
]


@dataclass
class User:
    user_id: str
    email: str
    name: str
    role: UserRole
    status: UserStatus
    created_at: str
    updated_at: str
    department: Optional[str] = None
    avatar_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "status": self.status.value if isinstance(self.status, UserStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "department": self.department,
            "avatar_url": self.avatar_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        role = data.get("role", "viewer")
        if isinstance(role, str):
            role = UserRole(role)
        status = data.get("status", "active")
        if isinstance(status, str):
            status = UserStatus(status)
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            name=data.get("name", ""),
            role=role,
            status=status,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            department=data.get("department"),
            avatar_url=data.get("avatar_url"),
        )


class UserManager:
    """File-based user persistence — stores JSON files in uploads/users/."""

    USERS_DIR = os.path.join(Config.UPLOAD_FOLDER, "users")

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.USERS_DIR, exist_ok=True)

    @classmethod
    def _user_path(cls, user_id: str) -> str:
        return os.path.join(cls.USERS_DIR, f"{user_id}.json")

    @classmethod
    def create_user(
        cls,
        email: str,
        name: str,
        role: str = "viewer",
        status: str = "active",
        department: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        cls._ensure_dir()
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        user = User(
            user_id=user_id,
            email=email,
            name=name,
            role=UserRole(role),
            status=UserStatus(status),
            created_at=now,
            updated_at=now,
            department=department,
            avatar_url=avatar_url,
        )
        cls._save(user)
        return user

    @classmethod
    def _save(cls, user: User) -> None:
        user.updated_at = datetime.now().isoformat()
        path = cls._user_path(user.user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(user.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_user(cls, user_id: str) -> Optional[User]:
        path = cls._user_path(user_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return User.from_dict(json.load(f))

    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[User]:
        for user in cls.list_users():
            if user.email == email:
                return user
        return None

    @classmethod
    def list_users(cls, limit: int = 100) -> List[User]:
        cls._ensure_dir()
        users = []
        for fname in os.listdir(cls.USERS_DIR):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(cls.USERS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    users.append(User.from_dict(json.load(f)))
            except (json.JSONDecodeError, KeyError):
                continue
        users.sort(key=lambda u: u.created_at, reverse=True)
        return users[:limit]

    @classmethod
    def update_user(cls, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        user = cls.get_user(user_id)
        if not user:
            return None
        allowed = {"name", "email", "role", "status", "department", "avatar_url"}
        for key, value in updates.items():
            if key not in allowed:
                continue
            if key == "role":
                value = UserRole(value)
            elif key == "status":
                value = UserStatus(value)
            setattr(user, key, value)
        cls._save(user)
        return user

    @classmethod
    def delete_user(cls, user_id: str) -> bool:
        path = cls._user_path(user_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    @classmethod
    def seed_demo_users(cls) -> List[User]:
        """Create demo users if none exist yet."""
        if cls.list_users():
            return []
        created = []
        for data in DEMO_USERS:
            user = cls.create_user(**data)
            created.append(user)
        return created
