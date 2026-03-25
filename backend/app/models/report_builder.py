"""
Report Builder data model

Defines the template-driven report building system:
- ReportSection: individual building block (chart, table, text, etc.)
- ReportTemplate: reusable layout composed of ordered sections
- GeneratedReport: concrete report produced from a template + simulation data
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


class PageOrientation(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class ReportSection:
    """A single building block within a report template."""
    id: str
    type: SectionType
    title: str
    position: int
    width: SectionWidth = SectionWidth.FULL
    config: Dict[str, Any] = field(default_factory=dict)
    data_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, SectionType) else self.type,
            "title": self.title,
            "position": self.position,
            "width": self.width.value if isinstance(self.width, SectionWidth) else self.width,
            "config": self.config,
            "data_source": self.data_source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportSection':
        section_type = data.get("type", "text")
        if isinstance(section_type, str):
            section_type = SectionType(section_type)

        width = data.get("width", "full")
        if isinstance(width, str):
            width = SectionWidth(width)

        return cls(
            id=data.get("id", f"sec_{uuid.uuid4().hex[:8]}"),
            type=section_type,
            title=data.get("title", ""),
            position=data.get("position", 0),
            width=width,
            config=data.get("config", {}),
            data_source=data.get("data_source"),
        )


@dataclass
class ReportTemplate:
    """Reusable report layout composed of ordered sections."""
    id: str
    name: str
    sections: List[ReportSection]
    created_at: str
    updated_at: str
    theme: Dict[str, Any] = field(default_factory=lambda: {
        "primary_color": "#2068FF",
        "accent_color": "#ff5600",
        "font_family": "system-ui",
    })
    page_orientation: PageOrientation = PageOrientation.PORTRAIT
    header_config: Dict[str, Any] = field(default_factory=lambda: {
        "show_logo": True,
        "title": "",
        "subtitle": "",
    })
    footer_config: Dict[str, Any] = field(default_factory=lambda: {
        "show_page_numbers": True,
        "text": "",
    })

    def to_dict(self) -> Dict[str, Any]:
        orientation = self.page_orientation
        if isinstance(orientation, PageOrientation):
            orientation = orientation.value

        return {
            "id": self.id,
            "name": self.name,
            "sections": [s.to_dict() for s in self.sections],
            "theme": self.theme,
            "page_orientation": orientation,
            "header_config": self.header_config,
            "footer_config": self.footer_config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportTemplate':
        orientation = data.get("page_orientation", "portrait")
        if isinstance(orientation, str):
            orientation = PageOrientation(orientation)

        sections_raw = data.get("sections", [])
        sections = [ReportSection.from_dict(s) for s in sections_raw]

        return cls(
            id=data["id"],
            name=data.get("name", "Untitled Template"),
            sections=sections,
            theme=data.get("theme", {}),
            page_orientation=orientation,
            header_config=data.get("header_config", {}),
            footer_config=data.get("footer_config", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class GeneratedReport:
    """Concrete report produced from a template + simulation data."""
    id: str
    template_id: str
    simulation_ids: List[str]
    generated_at: str
    generation_method: GenerationMethod
    content_markdown: str = ""
    chart_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        method = self.generation_method
        if isinstance(method, GenerationMethod):
            method = method.value

        return {
            "id": self.id,
            "template_id": self.template_id,
            "simulation_ids": self.simulation_ids,
            "content_markdown": self.content_markdown,
            "chart_data": self.chart_data,
            "generated_at": self.generated_at,
            "generation_method": method,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratedReport':
        method = data.get("generation_method", "template")
        if isinstance(method, str):
            method = GenerationMethod(method)

        return cls(
            id=data["id"],
            template_id=data.get("template_id", ""),
            simulation_ids=data.get("simulation_ids", []),
            content_markdown=data.get("content_markdown", ""),
            chart_data=data.get("chart_data", {}),
            generated_at=data.get("generated_at", ""),
            generation_method=method,
        )


class ReportBuilderManager:
    """
    Filesystem-based persistence for report builder templates and generated reports.

    Storage layout:
        {UPLOAD_FOLDER}/report_builder/
            templates/
                {template_id}.json
            reports/
                {report_id}.json
    """

    BASE_DIR = os.path.join(Config.UPLOAD_FOLDER, 'report_builder')
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

    @classmethod
    def _ensure_dirs(cls):
        os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)

    # ── Template CRUD ──────────────────────────────────────────

    @classmethod
    def save_template(cls, template: ReportTemplate) -> None:
        cls._ensure_dirs()
        template.updated_at = datetime.now().isoformat()
        path = os.path.join(cls.TEMPLATES_DIR, f"{template.id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_template(cls, template_id: str) -> Optional[ReportTemplate]:
        path = os.path.join(cls.TEMPLATES_DIR, f"{template_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return ReportTemplate.from_dict(json.load(f))

    @classmethod
    def list_templates(cls, limit: int = 50) -> List[ReportTemplate]:
        cls._ensure_dirs()
        templates = []
        for fname in os.listdir(cls.TEMPLATES_DIR):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(cls.TEMPLATES_DIR, fname)
            with open(path, 'r', encoding='utf-8') as f:
                templates.append(ReportTemplate.from_dict(json.load(f)))
        templates.sort(key=lambda t: t.updated_at, reverse=True)
        return templates[:limit]

    @classmethod
    def delete_template(cls, template_id: str) -> bool:
        path = os.path.join(cls.TEMPLATES_DIR, f"{template_id}.json")
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    @classmethod
    def create_template(cls, name: str, sections: Optional[List[Dict]] = None) -> ReportTemplate:
        now = datetime.now().isoformat()
        parsed_sections = [ReportSection.from_dict(s) for s in (sections or [])]
        template = ReportTemplate(
            id=f"tpl_{uuid.uuid4().hex[:12]}",
            name=name,
            sections=parsed_sections,
            created_at=now,
            updated_at=now,
        )
        cls.save_template(template)
        return template

    # ── Generated Report CRUD ──────────────────────────────────

    @classmethod
    def save_report(cls, report: GeneratedReport) -> None:
        cls._ensure_dirs()
        path = os.path.join(cls.REPORTS_DIR, f"{report.id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_report(cls, report_id: str) -> Optional[GeneratedReport]:
        path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return GeneratedReport.from_dict(json.load(f))

    @classmethod
    def list_reports(cls, limit: int = 50) -> List[GeneratedReport]:
        cls._ensure_dirs()
        reports = []
        for fname in os.listdir(cls.REPORTS_DIR):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(cls.REPORTS_DIR, fname)
            with open(path, 'r', encoding='utf-8') as f:
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

    @classmethod
    def create_report(
        cls,
        template_id: str,
        simulation_ids: List[str],
        generation_method: str = "template",
        content_markdown: str = "",
        chart_data: Optional[Dict] = None,
    ) -> GeneratedReport:
        report = GeneratedReport(
            id=f"rpt_{uuid.uuid4().hex[:12]}",
            template_id=template_id,
            simulation_ids=simulation_ids,
            content_markdown=content_markdown,
            chart_data=chart_data or {},
            generated_at=datetime.now().isoformat(),
            generation_method=GenerationMethod(generation_method),
        )
        cls.save_report(report)
        return report
