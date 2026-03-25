"""
Report Builder data models and persistence.

Manages report templates (user-designed layouts) and generated reports
(populated templates with simulation data).
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict

from ..config import Config


class SectionType(str, Enum):
    TEXT = "text"
    CHART = "chart"
    TABLE = "table"
    KPI_ROW = "kpi_row"
    DIVIDER = "divider"
    IMAGE = "image"


class SectionWidth(str, Enum):
    FULL = "full"
    HALF = "half"
    THIRD = "third"


class GenerationMethod(str, Enum):
    AI = "ai"
    TEMPLATE = "template"


@dataclass
class ReportSection:
    """A single section within a report template."""
    id: str
    type: SectionType
    title: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    data_source: Optional[str] = None
    position: int = 0
    width: SectionWidth = SectionWidth.FULL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, SectionType) else self.type,
            "title": self.title,
            "config": self.config,
            "data_source": self.data_source,
            "position": self.position,
            "width": self.width.value if isinstance(self.width, SectionWidth) else self.width,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportSection":
        section_type = data.get("type", "text")
        if isinstance(section_type, str):
            section_type = SectionType(section_type)

        width = data.get("width", "full")
        if isinstance(width, str):
            width = SectionWidth(width)

        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            type=section_type,
            title=data.get("title", ""),
            config=data.get("config", {}),
            data_source=data.get("data_source"),
            position=data.get("position", 0),
            width=width,
        )


@dataclass
class ReportTemplate:
    """A reusable report layout template."""
    id: str
    name: str
    sections: List[ReportSection] = field(default_factory=list)
    theme: str = "intercom"
    page_orientation: str = "portrait"
    header_config: Dict[str, Any] = field(default_factory=dict)
    footer_config: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "sections": [s.to_dict() for s in self.sections],
            "theme": self.theme,
            "page_orientation": self.page_orientation,
            "header_config": self.header_config,
            "footer_config": self.footer_config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportTemplate":
        sections_raw = data.get("sections", [])
        sections = [ReportSection.from_dict(s) for s in sections_raw]

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled Template"),
            sections=sections,
            theme=data.get("theme", "intercom"),
            page_orientation=data.get("page_orientation", "portrait"),
            header_config=data.get("header_config", {}),
            footer_config=data.get("footer_config", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class GeneratedReport:
    """A report generated from a template + simulation data."""
    id: str
    template_id: Optional[str] = None
    simulation_ids: List[str] = field(default_factory=list)
    content_markdown: str = ""
    chart_data: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""
    generation_method: GenerationMethod = GenerationMethod.TEMPLATE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "simulation_ids": self.simulation_ids,
            "content_markdown": self.content_markdown,
            "chart_data": self.chart_data,
            "generated_at": self.generated_at,
            "generation_method": (
                self.generation_method.value
                if isinstance(self.generation_method, GenerationMethod)
                else self.generation_method
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneratedReport":
        method = data.get("generation_method", "template")
        if isinstance(method, str):
            method = GenerationMethod(method)

        return cls(
            id=data.get("id", ""),
            template_id=data.get("template_id"),
            simulation_ids=data.get("simulation_ids", []),
            content_markdown=data.get("content_markdown", ""),
            chart_data=data.get("chart_data", {}),
            generated_at=data.get("generated_at", ""),
            generation_method=method,
        )


class ReportBuilderManager:
    """Persistence layer for report templates and generated reports."""

    TEMPLATES_DIR = os.path.join(Config.UPLOAD_FOLDER, "report_builder", "templates")
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, "report_builder", "reports")

    @classmethod
    def _ensure_dirs(cls):
        os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)

    # ── Template CRUD ──────────────────────────────────────

    @classmethod
    def save_template(cls, template: ReportTemplate) -> None:
        cls._ensure_dirs()
        template.updated_at = datetime.now().isoformat()
        path = os.path.join(cls.TEMPLATES_DIR, f"{template.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_template(cls, template_id: str) -> Optional[ReportTemplate]:
        path = os.path.join(cls.TEMPLATES_DIR, f"{template_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return ReportTemplate.from_dict(json.load(f))

    @classmethod
    def list_templates(cls, limit: int = 50) -> List[ReportTemplate]:
        cls._ensure_dirs()
        templates = []
        for fname in os.listdir(cls.TEMPLATES_DIR):
            if fname.endswith(".json"):
                path = os.path.join(cls.TEMPLATES_DIR, fname)
                with open(path, "r", encoding="utf-8") as f:
                    templates.append(ReportTemplate.from_dict(json.load(f)))
        templates.sort(key=lambda t: t.updated_at or t.created_at, reverse=True)
        return templates[:limit]

    @classmethod
    def delete_template(cls, template_id: str) -> bool:
        path = os.path.join(cls.TEMPLATES_DIR, f"{template_id}.json")
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    # ── Generated Report CRUD ──────────────────────────────

    @classmethod
    def save_report(cls, report: GeneratedReport) -> None:
        cls._ensure_dirs()
        path = os.path.join(cls.REPORTS_DIR, f"{report.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_report(cls, report_id: str) -> Optional[GeneratedReport]:
        path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return GeneratedReport.from_dict(json.load(f))

    @classmethod
    def list_reports(cls, limit: int = 50) -> List[GeneratedReport]:
        cls._ensure_dirs()
        reports = []
        for fname in os.listdir(cls.REPORTS_DIR):
            if fname.endswith(".json"):
                path = os.path.join(cls.REPORTS_DIR, fname)
                with open(path, "r", encoding="utf-8") as f:
                    reports.append(GeneratedReport.from_dict(json.load(f)))
        reports.sort(key=lambda r: r.generated_at, reverse=True)
        return reports[:limit]

    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True
