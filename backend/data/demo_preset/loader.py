"""
Demo preset loader — serves curated demo data for presentations.

When DEMO_PRESET=true, pre-built simulation/report/dashboard data is loaded
from JSON fixtures so the demo tells a compelling, repeatable story about
coalitions debating pipeline strategy and reaching consensus.
"""

import json
import os
from pathlib import Path

_PRESET_DIR = Path(__file__).parent
_cache: dict = {}


def is_demo_preset_enabled() -> bool:
    return os.environ.get("DEMO_PRESET", "").lower() in ("true", "1", "yes")


def _load(filename: str) -> dict:
    if filename not in _cache:
        path = _PRESET_DIR / filename
        with open(path) as f:
            _cache[filename] = json.load(f)
    return _cache[filename]


def get_simulation() -> dict:
    return _load("simulation.json")


def get_report() -> dict:
    return _load("report.json")


def get_dashboard() -> dict:
    return _load("dashboard.json")


def get_preset_sim_id() -> str:
    return get_simulation()["simulation_id"]


def get_preset_report_id() -> str:
    return get_report()["report_id"]
