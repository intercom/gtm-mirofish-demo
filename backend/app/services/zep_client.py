"""
Centralized Zep Cloud client factory.

Provides a shared, lazily-initialized Zep client instance so that
services don't each create their own. Supports demo/mock mode when
ZEP_API_KEY is not configured.
"""

from __future__ import annotations

import threading
from typing import Optional

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_client')

_client: Optional[Zep] = None
_lock = threading.Lock()


def get_zep_client() -> Optional[Zep]:
    """Return a shared Zep client, or None if ZEP_API_KEY is not set.

    Thread-safe lazy singleton — the client is created on first call and
    reused for the lifetime of the process.
    """
    global _client

    if _client is not None:
        return _client

    api_key = Config.ZEP_API_KEY
    if not api_key:
        logger.info("ZEP_API_KEY not configured — Zep features disabled (demo mode)")
        return None

    with _lock:
        if _client is not None:
            return _client
        _client = Zep(api_key=api_key)
        logger.info("Zep Cloud client initialized")
        return _client


def is_zep_available() -> bool:
    """Check whether the Zep client can be created (API key is present)."""
    return bool(Config.ZEP_API_KEY)


def require_zep_client() -> Zep:
    """Return the shared Zep client or raise if unavailable.

    Use this in code paths that *must* have Zep (e.g. graph build).
    """
    client = get_zep_client()
    if client is None:
        raise ValueError("ZEP_API_KEY not configured — cannot use Zep features")
    return client


def reset_client() -> None:
    """Reset the cached client (useful for tests or key rotation)."""
    global _client
    with _lock:
        _client = None
