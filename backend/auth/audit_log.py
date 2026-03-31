"""
Audit logger for security-relevant events.

Stores structured JSON-L entries in backend/logs/audit.log.
Events: login, logout, role_change, user_removed, permission_denied.
Retention: 90 days.
"""

import json
import os
import threading
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.utils.logger import LOG_DIR, get_logger

logger = get_logger('mirofish.audit')

AUDIT_LOG_PATH = os.path.join(LOG_DIR, 'audit.log')
RETENTION_DAYS = 90

VALID_ACTIONS = frozenset({
    'login',
    'logout',
    'role_change',
    'user_removed',
    'permission_denied',
})

_write_lock = threading.Lock()


def log_event(
    action: str,
    actor_email: str,
    target: Optional[str] = None,
    details: Optional[dict] = None,
) -> dict:
    """Append a single audit entry to the log file.

    Args:
        action: One of VALID_ACTIONS.
        actor_email: Email of the user performing the action.
        target: Email or identifier of the affected entity.
        details: Arbitrary dict of extra context.

    Returns:
        The entry dict that was written.
    """
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid audit action: {action}. Must be one of {sorted(VALID_ACTIONS)}")

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'actor_email': actor_email,
        'action': action,
        'target': target,
        'details': details or {},
    }

    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

    with _write_lock:
        with open(AUDIT_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    logger.info(f"AUDIT: {action} by={actor_email} target={target}")
    return entry


def read_log(limit: int = 50, action: Optional[str] = None) -> list[dict]:
    """Read the most recent audit entries.

    Args:
        limit: Max entries to return (newest first).
        action: Optional filter by action type.

    Returns:
        List of entry dicts, newest first.
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return []

    entries = []
    with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if action and entry.get('action') != action:
                continue
            entries.append(entry)

    entries.reverse()
    return entries[:limit]


def enforce_retention() -> int:
    """Remove entries older than RETENTION_DAYS.

    Returns:
        Number of entries removed.
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    kept = []
    removed = 0

    with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry['timestamp'])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    kept.append(line)
                else:
                    removed += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                kept.append(line)

    if removed > 0:
        log_dir = os.path.dirname(AUDIT_LOG_PATH)
        fd, tmp_path = tempfile.mkstemp(dir=log_dir, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for line in kept:
                    f.write(line + '\n')
            os.replace(tmp_path, AUDIT_LOG_PATH)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        logger.info(f"AUDIT retention: removed {removed} entries older than {RETENTION_DAYS} days")

    return removed
