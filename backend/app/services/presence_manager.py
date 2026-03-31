"""
Presence Manager — simulates realistic multi-user presence for the GTM demo.

Generates and tracks simulated users who appear to be concurrently viewing
and interacting with the simulation workspace. Each user has a persona with
realistic navigation patterns and activity behaviors.
"""

import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class UserStatus(str, Enum):
    ACTIVE = 'active'
    IDLE = 'idle'
    VIEWING = 'viewing'
    EDITING = 'editing'


PAGES = [
    'Dashboard', 'Scenarios', 'Workspace', 'Graph', 'Simulation',
    'Report', 'Chat', 'Settings', 'Team', 'Analytics',
]

SIMULATED_USERS = [
    {'name': 'Alice Chen', 'initials': 'AC', 'role': 'VP of Sales', 'color': '#2068FF'},
    {'name': 'Marcus Rodriguez', 'initials': 'MR', 'role': 'CX Director', 'color': '#ff5600'},
    {'name': 'Sarah Kim', 'initials': 'SK', 'role': 'Product Manager', 'color': '#AA00FF'},
    {'name': 'James Wright', 'initials': 'JW', 'role': 'Head of Ops', 'color': '#009900'},
    {'name': 'Priya Patel', 'initials': 'PP', 'role': 'Data Analyst', 'color': '#f59e0b'},
    {'name': 'David Park', 'initials': 'DP', 'role': 'Support Lead', 'color': '#06b6d4'},
    {'name': 'Emily Watson', 'initials': 'EW', 'role': 'Marketing Dir', 'color': '#ec4899'},
    {'name': 'Carlos Rivera', 'initials': 'CR', 'role': 'Finance Lead', 'color': '#8b5cf6'},
]

ACTIVITY_VERBS = [
    'viewing', 'reviewing scenario', 'editing parameters', 'analyzing graph',
    'running simulation', 'checking results', 'comparing branches',
    'configuring team', 'generating report', 'chatting with AI',
]

# Cursor position zones (named areas users might focus on)
FOCUS_ZONES = [
    'graph-panel', 'simulation-controls', 'timeline-chart', 'action-feed',
    'metrics-panel', 'scenario-config', 'report-section', 'chat-input',
    'nav-bar', 'team-composer', 'branch-tree', 'settings-form',
]


@dataclass
class PresenceUser:
    id: str
    name: str
    initials: str
    role: str
    color: str
    status: UserStatus = UserStatus.ACTIVE
    current_page: str = 'Dashboard'
    focus_zone: Optional[str] = None
    activity: str = 'viewing'
    cursor_x: float = 0.5
    cursor_y: float = 0.5
    joined_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    is_typing: bool = False

    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value,
        }


class PresenceManager:
    """Manages simulated user presence state with realistic behavior."""

    def __init__(self, min_users=2, max_users=5):
        self._min_users = min_users
        self._max_users = max_users
        self._users: dict[str, PresenceUser] = {}
        self._events: list[dict] = []
        self._max_events = 100
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True
        count = random.randint(self._min_users, self._max_users)
        templates = random.sample(SIMULATED_USERS, min(count, len(SIMULATED_USERS)))
        for t in templates:
            user = PresenceUser(
                id=str(uuid.uuid4())[:8],
                name=t['name'],
                initials=t['initials'],
                role=t['role'],
                color=t['color'],
                current_page=random.choice(PAGES),
                cursor_x=random.random(),
                cursor_y=random.random(),
                activity=random.choice(ACTIVITY_VERBS),
                focus_zone=random.choice(FOCUS_ZONES),
            )
            self._users[user.id] = user
            self._add_event('join', user)

    def _add_event(self, event_type: str, user: PresenceUser, details: str = ''):
        self._events.append({
            'type': event_type,
            'user_id': user.id,
            'user_name': user.name,
            'details': details or f'{user.name} {event_type}',
            'timestamp': time.time(),
        })
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def tick(self):
        """Advance simulation by one tick — updates user behaviors."""
        self._ensure_initialized()
        now = time.time()

        for user in list(self._users.values()):
            elapsed = now - user.last_active

            # Random page navigation (every ~15-30s)
            if random.random() < 0.08:
                old_page = user.current_page
                user.current_page = random.choice(PAGES)
                if user.current_page != old_page:
                    user.focus_zone = random.choice(FOCUS_ZONES)
                    user.activity = random.choice(ACTIVITY_VERBS)
                    self._add_event(
                        'navigate', user,
                        f'{user.name} moved to {user.current_page}',
                    )

            # Status transitions
            if random.random() < 0.05:
                old_status = user.status
                weights = {
                    UserStatus.ACTIVE: 0.5,
                    UserStatus.VIEWING: 0.3,
                    UserStatus.EDITING: 0.15,
                    UserStatus.IDLE: 0.05,
                }
                user.status = random.choices(
                    list(weights.keys()), list(weights.values())
                )[0]
                if user.status != old_status:
                    self._add_event('status_change', user, f'{user.name} is now {user.status.value}')

            # Cursor drift
            user.cursor_x = max(0, min(1, user.cursor_x + (random.random() - 0.5) * 0.1))
            user.cursor_y = max(0, min(1, user.cursor_y + (random.random() - 0.5) * 0.1))

            # Typing simulation
            user.is_typing = user.status == UserStatus.EDITING and random.random() < 0.3

            user.last_active = now

        # Occasionally add/remove a user
        if len(self._users) < self._max_users and random.random() < 0.02:
            self._add_random_user()
        elif len(self._users) > self._min_users and random.random() < 0.01:
            self._remove_random_user()

    def _add_random_user(self):
        existing_names = {u.name for u in self._users.values()}
        available = [t for t in SIMULATED_USERS if t['name'] not in existing_names]
        if not available:
            return
        t = random.choice(available)
        user = PresenceUser(
            id=str(uuid.uuid4())[:8],
            name=t['name'],
            initials=t['initials'],
            role=t['role'],
            color=t['color'],
            current_page=random.choice(PAGES),
            cursor_x=random.random(),
            cursor_y=random.random(),
            activity=random.choice(ACTIVITY_VERBS),
            focus_zone=random.choice(FOCUS_ZONES),
        )
        self._users[user.id] = user
        self._add_event('join', user, f'{user.name} joined')

    def _remove_random_user(self):
        if not self._users:
            return
        uid = random.choice(list(self._users.keys()))
        user = self._users.pop(uid)
        self._add_event('leave', user, f'{user.name} left')

    def get_presence(self) -> dict:
        """Return current presence state for all users."""
        self._ensure_initialized()
        self.tick()
        return {
            'users': [u.to_dict() for u in self._users.values()],
            'total_online': len(self._users),
            'timestamp': time.time(),
        }

    def get_events(self, since: float = 0) -> list[dict]:
        """Return presence events since a timestamp."""
        self._ensure_initialized()
        if since:
            return [e for e in self._events if e['timestamp'] > since]
        return list(self._events[-20:])

    def get_cursors(self) -> list[dict]:
        """Return cursor positions for all active users."""
        self._ensure_initialized()
        return [
            {
                'user_id': u.id,
                'name': u.name,
                'initials': u.initials,
                'color': u.color,
                'x': u.cursor_x,
                'y': u.cursor_y,
                'focus_zone': u.focus_zone,
                'is_typing': u.is_typing,
            }
            for u in self._users.values()
            if u.status != UserStatus.IDLE
        ]

    def reset(self):
        """Clear all presence state."""
        self._users.clear()
        self._events.clear()
        self._initialized = False


# Module-level singleton — presence is shared across requests
presence_manager = PresenceManager()
