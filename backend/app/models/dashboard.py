"""
Dashboard configuration data model.

Defines the data structures for configurable dashboards:
  - WidgetConfig: individual widget settings (type, data source, display config)
  - LayoutItem: grid position/size for a widget
  - DashboardConfig: a named collection of widgets + layout
  - DashboardManager: file-based persistence (JSON in uploads/dashboards/)
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field

from ..config import Config


class WidgetType(str, Enum):
    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    DONUT_CHART = "donut_chart"
    TABLE = "table"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TEXT = "text"
    ACTIVITY_FEED = "activity_feed"


class DataSource(str, Enum):
    REVENUE = "revenue"
    PIPELINE = "pipeline"
    SALESFORCE = "salesforce"
    CPQ = "cpq"
    ORDERS = "orders"
    SIMULATION = "simulation"
    RECONCILIATION = "reconciliation"


@dataclass
class WidgetConfig:
    id: str
    type: str
    title: str
    data_source: str
    config: Dict[str, Any] = field(default_factory=dict)
    refresh_interval_seconds: int = 300

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "data_source": self.data_source,
            "config": self.config,
            "refresh_interval_seconds": self.refresh_interval_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WidgetConfig":
        return cls(
            id=data["id"],
            type=data["type"],
            title=data.get("title", ""),
            data_source=data.get("data_source", ""),
            config=data.get("config", {}),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 300),
        )


@dataclass
class LayoutItem:
    widget_id: str
    x: int
    y: int
    width: int
    height: int
    min_width: int = 1
    min_height: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "min_width": self.min_width,
            "min_height": self.min_height,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutItem":
        return cls(
            widget_id=data["widget_id"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 4),
            height=data.get("height", 3),
            min_width=data.get("min_width", 1),
            min_height=data.get("min_height", 1),
        )


@dataclass
class DashboardConfig:
    id: str
    name: str
    description: str
    widgets: List[WidgetConfig]
    layout: List[LayoutItem]
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "widgets": [w.to_dict() for w in self.widgets],
            "layout": [l.to_dict() for l in self.layout],
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_default": self.is_default,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardConfig":
        return cls(
            id=data["id"],
            name=data.get("name", "Untitled Dashboard"),
            description=data.get("description", ""),
            widgets=[WidgetConfig.from_dict(w) for w in data.get("widgets", [])],
            layout=[LayoutItem.from_dict(l) for l in data.get("layout", [])],
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            is_default=data.get("is_default", False),
        )


def _widget(id: str, type: str, title: str, data_source: str, **config) -> WidgetConfig:
    """Shorthand for building a WidgetConfig in factory methods."""
    return WidgetConfig(id=id, type=type, title=title, data_source=data_source, config=config)


def _layout(widget_id: str, x: int, y: int, w: int, h: int, min_w: int = 2, min_h: int = 2) -> LayoutItem:
    """Shorthand for building a LayoutItem in factory methods."""
    return LayoutItem(widget_id=widget_id, x=x, y=y, width=w, height=h, min_width=min_w, min_height=min_h)


def create_default_gtm_dashboard() -> DashboardConfig:
    """GTM overview dashboard with revenue, pipeline, and activity widgets."""
    now = datetime.now().isoformat()
    widgets = [
        _widget("w1", WidgetType.KPI_CARD, "Monthly Revenue", DataSource.REVENUE, metric="mrr", prefix="$", show_trend=True),
        _widget("w2", WidgetType.KPI_CARD, "Pipeline Value", DataSource.PIPELINE, metric="total_value", prefix="$", show_trend=True),
        _widget("w3", WidgetType.KPI_CARD, "Open Orders", DataSource.ORDERS, metric="open_count", show_trend=True),
        _widget("w4", WidgetType.KPI_CARD, "Win Rate", DataSource.SALESFORCE, metric="win_rate", suffix="%", show_trend=True),
        _widget("w5", WidgetType.LINE_CHART, "Revenue Trend", DataSource.REVENUE, period="12m", metric="mrr"),
        _widget("w6", WidgetType.BAR_CHART, "Pipeline by Stage", DataSource.PIPELINE, group_by="stage"),
        _widget("w7", WidgetType.DONUT_CHART, "Deals by Source", DataSource.SALESFORCE, group_by="lead_source"),
        _widget("w8", WidgetType.ACTIVITY_FEED, "Recent Activity", DataSource.SALESFORCE, limit=10),
    ]
    layout = [
        _layout("w1", 0, 0, 3, 2),
        _layout("w2", 3, 0, 3, 2),
        _layout("w3", 6, 0, 3, 2),
        _layout("w4", 9, 0, 3, 2),
        _layout("w5", 0, 2, 6, 4),
        _layout("w6", 6, 2, 6, 4),
        _layout("w7", 0, 6, 4, 4),
        _layout("w8", 4, 6, 8, 4),
    ]
    return DashboardConfig(
        id="default_gtm",
        name="GTM Overview",
        description="High-level go-to-market metrics: revenue, pipeline, orders, and win rate.",
        widgets=widgets,
        layout=layout,
        created_by="system",
        created_at=now,
        updated_at=now,
        is_default=True,
    )


def create_simulation_dashboard() -> DashboardConfig:
    """Dashboard focused on simulation results and agent analytics."""
    now = datetime.now().isoformat()
    widgets = [
        _widget("w1", WidgetType.KPI_CARD, "Total Actions", DataSource.SIMULATION, metric="total_actions", show_trend=False),
        _widget("w2", WidgetType.KPI_CARD, "Active Agents", DataSource.SIMULATION, metric="unique_agents", show_trend=False),
        _widget("w3", WidgetType.LINE_CHART, "Activity Over Time", DataSource.SIMULATION, metric="actions_per_round"),
        _widget("w4", WidgetType.BAR_CHART, "Actions by Agent", DataSource.SIMULATION, group_by="agent"),
        _widget("w5", WidgetType.DONUT_CHART, "Sentiment Distribution", DataSource.SIMULATION, group_by="sentiment"),
        _widget("w6", WidgetType.TABLE, "Top Influencers", DataSource.SIMULATION, metric="influence_score", limit=10),
    ]
    layout = [
        _layout("w1", 0, 0, 6, 2),
        _layout("w2", 6, 0, 6, 2),
        _layout("w3", 0, 2, 8, 4),
        _layout("w4", 8, 2, 4, 4),
        _layout("w5", 0, 6, 4, 4),
        _layout("w6", 4, 6, 8, 4),
    ]
    return DashboardConfig(
        id="default_simulation",
        name="Simulation Analytics",
        description="Agent simulation results: actions, sentiment, and influence metrics.",
        widgets=widgets,
        layout=layout,
        created_by="system",
        created_at=now,
        updated_at=now,
        is_default=True,
    )


def create_reconciliation_dashboard() -> DashboardConfig:
    """Dashboard for revenue reconciliation and order tracking."""
    now = datetime.now().isoformat()
    widgets = [
        _widget("w1", WidgetType.KPI_CARD, "Reconciled Revenue", DataSource.RECONCILIATION, metric="reconciled_total", prefix="$"),
        _widget("w2", WidgetType.GAUGE, "Match Rate", DataSource.RECONCILIATION, metric="match_rate", max_value=100, suffix="%"),
        _widget("w3", WidgetType.FUNNEL, "Order Funnel", DataSource.ORDERS, stages=["quoted", "submitted", "approved", "fulfilled"]),
        _widget("w4", WidgetType.TABLE, "Unmatched Items", DataSource.RECONCILIATION, metric="unmatched", limit=20),
        _widget("w5", WidgetType.LINE_CHART, "CPQ Quote Volume", DataSource.CPQ, period="6m", metric="quote_count"),
    ]
    layout = [
        _layout("w1", 0, 0, 4, 2),
        _layout("w2", 4, 0, 4, 2),
        _layout("w3", 8, 0, 4, 4),
        _layout("w4", 0, 2, 8, 4),
        _layout("w5", 0, 6, 12, 4),
    ]
    return DashboardConfig(
        id="default_reconciliation",
        name="Reconciliation & Orders",
        description="Revenue reconciliation status, order funnel, and CPQ quote tracking.",
        widgets=widgets,
        layout=layout,
        created_by="system",
        created_at=now,
        updated_at=now,
        is_default=True,
    )


DEFAULT_DASHBOARDS = {
    "default_gtm": create_default_gtm_dashboard,
    "default_simulation": create_simulation_dashboard,
    "default_reconciliation": create_reconciliation_dashboard,
}


class DashboardManager:
    """File-based persistence for dashboard configurations."""

    STORAGE_DIR = os.path.join(Config.UPLOAD_FOLDER, "dashboards")

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.STORAGE_DIR, exist_ok=True)

    @classmethod
    def _path(cls, dashboard_id: str) -> str:
        return os.path.join(cls.STORAGE_DIR, f"{dashboard_id}.json")

    @classmethod
    def save(cls, dashboard: DashboardConfig) -> None:
        cls._ensure_dir()
        dashboard.updated_at = datetime.now().isoformat()
        with open(cls._path(dashboard.id), "w", encoding="utf-8") as f:
            json.dump(dashboard.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get(cls, dashboard_id: str) -> Optional[DashboardConfig]:
        path = cls._path(dashboard_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return DashboardConfig.from_dict(json.load(f))

    @classmethod
    def list_all(cls, limit: int = 50) -> List[DashboardConfig]:
        cls._ensure_dir()
        dashboards = []
        for fname in os.listdir(cls.STORAGE_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(cls.STORAGE_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    dashboards.append(DashboardConfig.from_dict(json.load(f)))
            except (json.JSONDecodeError, KeyError):
                continue
        dashboards.sort(key=lambda d: d.updated_at, reverse=True)
        return dashboards[:limit]

    @classmethod
    def delete(cls, dashboard_id: str) -> bool:
        path = cls._path(dashboard_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    @classmethod
    def create(cls, name: str, description: str = "", created_by: str = "") -> DashboardConfig:
        now = datetime.now().isoformat()
        dashboard = DashboardConfig(
            id=f"dash_{uuid.uuid4().hex[:12]}",
            name=name,
            description=description,
            widgets=[],
            layout=[],
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        cls.save(dashboard)
        return dashboard

    @classmethod
    def duplicate(cls, dashboard_id: str) -> Optional[DashboardConfig]:
        original = cls.get(dashboard_id)
        if not original:
            return None
        now = datetime.now().isoformat()
        new_id = f"dash_{uuid.uuid4().hex[:12]}"
        widget_id_map = {}
        new_widgets = []
        for w in original.widgets:
            old_id = w.id
            new_wid = f"w_{uuid.uuid4().hex[:8]}"
            widget_id_map[old_id] = new_wid
            new_widgets.append(WidgetConfig(
                id=new_wid,
                type=w.type,
                title=w.title,
                data_source=w.data_source,
                config=dict(w.config),
                refresh_interval_seconds=w.refresh_interval_seconds,
            ))
        new_layout = []
        for l in original.layout:
            new_layout.append(LayoutItem(
                widget_id=widget_id_map.get(l.widget_id, l.widget_id),
                x=l.x, y=l.y,
                width=l.width, height=l.height,
                min_width=l.min_width, min_height=l.min_height,
            ))
        copy = DashboardConfig(
            id=new_id,
            name=f"{original.name} (Copy)",
            description=original.description,
            widgets=new_widgets,
            layout=new_layout,
            created_by=original.created_by,
            created_at=now,
            updated_at=now,
            is_default=False,
        )
        cls.save(copy)
        return copy

    @classmethod
    def ensure_defaults(cls):
        """Seed default dashboards if they don't already exist on disk."""
        cls._ensure_dir()
        for dash_id, factory in DEFAULT_DASHBOARDS.items():
            if not os.path.exists(cls._path(dash_id)):
                cls.save(factory())

    @classmethod
    def get_default(cls) -> Optional[DashboardConfig]:
        """Return the first dashboard marked as default, or the GTM overview."""
        cls.ensure_defaults()
        for dash_id in DEFAULT_DASHBOARDS:
            dashboard = cls.get(dash_id)
            if dashboard and dashboard.is_default:
                return dashboard
        return None
