"""
API Key Management Service
Thread-safe in-memory storage for API keys with hash-based security.
"""

import hashlib
import secrets
import threading
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional


AVAILABLE_SCOPES = [
    {"id": "simulation:read", "label": "Read simulations"},
    {"id": "simulation:write", "label": "Run simulations"},
    {"id": "graph:read", "label": "Read knowledge graphs"},
    {"id": "graph:write", "label": "Build knowledge graphs"},
    {"id": "report:read", "label": "Read reports"},
    {"id": "report:write", "label": "Generate reports"},
    {"id": "chat", "label": "Chat with simulated world"},
]


@dataclass
class ApiKey:
    id: str
    name: str
    prefix: str
    key_hash: str
    scopes: List[str]
    created_at: str
    last_used_at: Optional[str] = None
    revoked: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "scopes": self.scopes,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "revoked": self.revoked,
        }


class ApiKeyService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._keys: Dict[str, ApiKey] = {}
                    cls._instance._hash_index: Dict[str, str] = {}
                    cls._instance._data_lock = threading.Lock()
        return cls._instance

    @staticmethod
    def _generate_raw_key() -> str:
        return "mf_" + secrets.token_urlsafe(32)

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def create_key(self, name: str, scopes: List[str]) -> dict:
        raw_key = self._generate_raw_key()
        key_hash = self._hash_key(raw_key)
        key_id = secrets.token_hex(8)
        prefix = raw_key[:11]
        now = datetime.now(timezone.utc).isoformat()

        valid_scope_ids = {s["id"] for s in AVAILABLE_SCOPES}
        scopes = [s for s in scopes if s in valid_scope_ids] or [valid_scope_ids.pop()]

        entry = ApiKey(
            id=key_id,
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            scopes=scopes,
            created_at=now,
        )

        with self._data_lock:
            self._keys[key_id] = entry
            self._hash_index[key_hash] = key_id

        result = entry.to_dict()
        result["key"] = raw_key
        return result

    def list_keys(self) -> List[dict]:
        with self._data_lock:
            return [
                k.to_dict()
                for k in sorted(
                    self._keys.values(),
                    key=lambda x: x.created_at,
                    reverse=True,
                )
                if not k.revoked
            ]

    def revoke_key(self, key_id: str) -> bool:
        with self._data_lock:
            entry = self._keys.get(key_id)
            if not entry or entry.revoked:
                return False
            entry.revoked = True
            self._hash_index.pop(entry.key_hash, None)
            return True

    def validate_key(self, raw_key: str) -> Optional[ApiKey]:
        key_hash = self._hash_key(raw_key)
        with self._data_lock:
            key_id = self._hash_index.get(key_hash)
            if not key_id:
                return None
            entry = self._keys.get(key_id)
            if not entry or entry.revoked:
                return None
            entry.last_used_at = datetime.now(timezone.utc).isoformat()
            return entry
