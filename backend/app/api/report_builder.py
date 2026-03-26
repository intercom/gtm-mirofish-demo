"""
Report Builder API
CRUD for report templates and generated reports,
plus AI/template-based report generation.
"""

import uuid
import traceback
import threading
from datetime import datetime

from flask import Blueprint, request, jsonify

from ..config import Config
from ..models.report_builder import (
    ReportBuilderManager,
    ReportTemplate,
    ReportSection,
    GeneratedReport,
    SectionType,
    SectionWidth,
    GenerationMethod,
)
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger

logger = get_logger("mirofish.api.report_builder")

report_builder_bp = Blueprint("report_builder", __name__, url_prefix="/api/report-builder")


# ============== Template endpoints ==============

@report_builder_bp.route("/templates", methods=["GET"])
def list_templates():
    """List all report templates."""
    try:
        limit = request.args.get("limit", 50, type=int)
        templates = ReportBuilderManager.list_templates(limit=limit)
        return jsonify({
            "success": True,
            "data": [t.to_dict() for t in templates],
            "count": len(templates),
        })
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_builder_bp.route("/templates", methods=["POST"])
def create_template():
    """Create a new report template."""
    try:
        data = request.get_json() or {}

        name = data.get("name", "").strip()
        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400

        now = datetime.now().isoformat()
        template_id = f"tmpl_{uuid.uuid4().hex[:12]}"

        sections_raw = data.get("sections", [])
        sections = []
        for i, s in enumerate(sections_raw):
            s.setdefault("id", f"sec_{uuid.uuid4().hex[:8]}")
            s.setdefault("position", i)
            sections.append(ReportSection.from_dict(s))

        template = ReportTemplate(
            id=template_id,
            name=name,
            sections=sections,
            theme=data.get("theme", "intercom"),
            page_orientation=data.get("page_orientation", "portrait"),
            header_config=data.get("header_config", {}),
            footer_config=data.get("footer_config", {}),
            created_at=now,
            updated_at=now,
        )

        ReportBuilderManager.save_template(template)

        return jsonify({
            "success": True,
            "data": template.to_dict(),
        }), 201

    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@report_builder_bp.route("/templates/<template_id>", methods=["GET"])
def get_template(template_id: str):
    """Get a template by ID with its sections."""
    try:
        template = ReportBuilderManager.get_template(template_id)
        if not template:
            return jsonify({"success": False, "error": f"Template not found: {template_id}"}), 404

        return jsonify({"success": True, "data": template.to_dict()})

    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_builder_bp.route("/templates/<template_id>", methods=["PUT"])
def update_template(template_id: str):
    """Update an existing template."""
    try:
        existing = ReportBuilderManager.get_template(template_id)
        if not existing:
            return jsonify({"success": False, "error": f"Template not found: {template_id}"}), 404

        data = request.get_json() or {}

        if "name" in data:
            existing.name = data["name"]
        if "theme" in data:
            existing.theme = data["theme"]
        if "page_orientation" in data:
            existing.page_orientation = data["page_orientation"]
        if "header_config" in data:
            existing.header_config = data["header_config"]
        if "footer_config" in data:
            existing.footer_config = data["footer_config"]

        if "sections" in data:
            sections = []
            for i, s in enumerate(data["sections"]):
                s.setdefault("id", f"sec_{uuid.uuid4().hex[:8]}")
                s.setdefault("position", i)
                sections.append(ReportSection.from_dict(s))
            existing.sections = sections

        ReportBuilderManager.save_template(existing)

        return jsonify({"success": True, "data": existing.to_dict()})

    except Exception as e:
        logger.error(f"Failed to update template: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@report_builder_bp.route("/templates/<template_id>", methods=["DELETE"])
def delete_template(template_id: str):
    """Delete a template."""
    try:
        if not ReportBuilderManager.delete_template(template_id):
            return jsonify({"success": False, "error": f"Template not found: {template_id}"}), 404
        return jsonify({"success": True, "message": f"Template deleted: {template_id}"})
    except Exception as e:
        logger.error(f"Failed to delete template: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== Generated report endpoints ==============

@report_builder_bp.route("/reports", methods=["GET"])
def list_reports():
    """List generated reports."""
    try:
        limit = request.args.get("limit", 50, type=int)
        reports = ReportBuilderManager.list_reports(limit=limit)
        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports),
        })
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_builder_bp.route("/reports/<report_id>", methods=["GET"])
def get_report(report_id: str):
    """Get a generated report by ID."""
    try:
        report = ReportBuilderManager.get_report(report_id)
        if not report:
            return jsonify({"success": False, "error": f"Report not found: {report_id}"}), 404
        return jsonify({"success": True, "data": report.to_dict()})
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_builder_bp.route("/reports/<report_id>", methods=["DELETE"])
def delete_report(report_id: str):
    """Delete a generated report."""
    try:
        if not ReportBuilderManager.delete_report(report_id):
            return jsonify({"success": False, "error": f"Report not found: {report_id}"}), 404
        return jsonify({"success": True, "message": f"Report deleted: {report_id}"})
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== Report generation ==============

@report_builder_bp.route("/generate", methods=["POST"])
def generate_report():
    """
    Generate a report from a template and simulation data.

    Request JSON:
        {
            "template_id": "tmpl_xxx",          // required
            "simulation_ids": ["sim_xxx"],       // optional list of simulation IDs
            "generation_method": "ai|template"   // optional, defaults to "template"
        }

    Returns immediately with a task_id for polling via GET /api/graph/task/<task_id>.
    When the LLM key is not configured the report is generated from
    mock/demo data so the endpoint always works.
    """
    try:
        data = request.get_json() or {}

        template_id = data.get("template_id")
        if not template_id:
            return jsonify({"success": False, "error": "template_id is required"}), 400

        template = ReportBuilderManager.get_template(template_id)
        if not template:
            return jsonify({"success": False, "error": f"Template not found: {template_id}"}), 404

        simulation_ids = data.get("simulation_ids", [])
        method_str = data.get("generation_method", "template")
        try:
            method = GenerationMethod(method_str)
        except ValueError:
            method = GenerationMethod.TEMPLATE

        report_id = f"rpt_{uuid.uuid4().hex[:12]}"

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="report_builder_generate",
            metadata={
                "report_id": report_id,
                "template_id": template_id,
                "simulation_ids": simulation_ids,
            },
        )

        def _background():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="Loading template sections...",
                )

                use_ai = method == GenerationMethod.AI and Config.LLM_API_KEY
                if use_ai:
                    content_md, chart_data = _generate_with_llm(template, simulation_ids, task_manager, task_id)
                    gen_method = GenerationMethod.AI
                else:
                    content_md, chart_data = _generate_from_template(template, simulation_ids, task_manager, task_id)
                    gen_method = GenerationMethod.TEMPLATE

                report = GeneratedReport(
                    id=report_id,
                    template_id=template_id,
                    simulation_ids=simulation_ids,
                    content_markdown=content_md,
                    chart_data=chart_data,
                    generated_at=datetime.now().isoformat(),
                    generation_method=gen_method,
                )
                ReportBuilderManager.save_report(report)

                task_manager.complete_task(task_id, result={
                    "report_id": report_id,
                    "template_id": template_id,
                    "generation_method": gen_method.value,
                })

            except Exception as exc:
                logger.error(f"Report generation failed: {exc}")
                task_manager.fail_task(task_id, str(exc))

        thread = threading.Thread(target=_background, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "task_id": task_id,
                "report_id": report_id,
                "template_id": template_id,
                "status": "generating",
            },
        })

    except Exception as e:
        logger.error(f"Failed to start report generation: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ============== Generation helpers ==============

def _generate_from_template(
    template: ReportTemplate,
    simulation_ids: list,
    task_manager: TaskManager,
    task_id: str,
) -> tuple:
    """Generate report content from the template using demo/mock data."""
    lines = [f"# {template.name}\n"]
    chart_data: dict = {}
    total = max(len(template.sections), 1)

    for idx, section in enumerate(template.sections):
        progress = 10 + int((idx / total) * 80)
        task_manager.update_task(
            task_id, progress=progress,
            message=f"Generating section {idx + 1}/{total}: {section.title or section.type.value}",
        )

        if section.type == SectionType.TEXT:
            lines.append(f"## {section.title or 'Text Section'}\n")
            lines.append(
                section.config.get("content", "")
                or _demo_text_for_section(section)
            )
            lines.append("")

        elif section.type == SectionType.CHART:
            chart_type = section.config.get("chart_type", "bar")
            lines.append(f"## {section.title or 'Chart'}\n")
            lines.append(f"*[{chart_type} chart — rendered on frontend]*\n")
            chart_data[section.id] = _demo_chart_data(chart_type)

        elif section.type == SectionType.TABLE:
            lines.append(f"## {section.title or 'Data Table'}\n")
            lines.append(_demo_table_markdown())
            lines.append("")

        elif section.type == SectionType.KPI_ROW:
            lines.append(f"## {section.title or 'Key Metrics'}\n")
            kpis = _demo_kpi_data()
            chart_data[section.id] = kpis
            for kpi in kpis:
                lines.append(f"- **{kpi['label']}**: {kpi['value']}")
            lines.append("")

        elif section.type == SectionType.DIVIDER:
            lines.append("---\n")

        elif section.type == SectionType.IMAGE:
            lines.append(f"## {section.title or 'Image'}\n")
            lines.append(f"*[Image placeholder: {section.config.get('alt', 'report image')}]*\n")

    task_manager.update_task(task_id, progress=95, message="Finalising report...")
    return "\n".join(lines), chart_data


def _generate_with_llm(
    template: ReportTemplate,
    simulation_ids: list,
    task_manager: TaskManager,
    task_id: str,
) -> tuple:
    """Generate report content using the configured LLM provider."""
    from ..utils.llm_client import LLMClient

    task_manager.update_task(task_id, progress=15, message="Connecting to LLM...")

    client = LLMClient()

    section_descriptions = []
    for s in template.sections:
        section_descriptions.append(
            f"- Section '{s.title or s.type.value}' (type={s.type.value}, width={s.width.value})"
        )

    prompt = (
        "You are a GTM (Go-To-Market) analyst writing a professional report.\n"
        f"Report title: {template.name}\n"
        f"Theme: {template.theme}\n\n"
        "The report has these sections:\n"
        + "\n".join(section_descriptions)
        + "\n\nFor each section, write clear, data-driven content in Markdown. "
        "Use realistic GTM metrics (pipeline, conversion, engagement, revenue). "
        "For chart sections, describe what the chart shows. "
        "For KPI sections, provide 3-4 key metrics with values. "
        "For table sections, create a Markdown table with sample data.\n"
        "Return the full report as a single Markdown document."
    )

    task_manager.update_task(task_id, progress=30, message="Generating report with AI...")

    content = client.chat(
        messages=[
            {"role": "system", "content": "You are a professional GTM analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=4096,
    )

    task_manager.update_task(task_id, progress=80, message="Processing chart data...")

    chart_data: dict = {}
    for section in template.sections:
        if section.type == SectionType.CHART:
            chart_type = section.config.get("chart_type", "bar")
            chart_data[section.id] = _demo_chart_data(chart_type)
        elif section.type == SectionType.KPI_ROW:
            chart_data[section.id] = _demo_kpi_data()

    task_manager.update_task(task_id, progress=95, message="Finalising report...")
    return content, chart_data


# ── Demo data helpers ──────────────────────────────────────

def _demo_text_for_section(section: ReportSection) -> str:
    title = section.title or "Analysis"
    return (
        f"This section provides a detailed analysis of {title.lower()} across the "
        "simulation. Key findings indicate strong engagement from VP-level personas "
        "and notable competitive mentions of Zendesk and Freshdesk. Pipeline velocity "
        "increased 23% during the observation window, with conversion rates improving "
        "across mid-market segments."
    )


def _demo_chart_data(chart_type: str) -> dict:
    base = {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "chart_type": chart_type,
    }
    if chart_type == "donut":
        base["labels"] = ["VP Support", "CX Director", "IT Leader", "Operations", "Finance"]
        base["datasets"] = [{"data": [32, 25, 20, 15, 8]}]
    elif chart_type == "radar":
        base["labels"] = ["Engagement", "Sentiment", "Reach", "Influence", "Conversion"]
        base["datasets"] = [
            {"label": "Current", "data": [85, 72, 68, 91, 56]},
            {"label": "Target", "data": [90, 80, 75, 85, 70]},
        ]
    elif chart_type == "line":
        base["datasets"] = [
            {"label": "Pipeline Value ($K)", "data": [120, 185, 240, 310]},
            {"label": "Qualified Leads", "data": [45, 62, 78, 95]},
        ]
    else:
        base["datasets"] = [
            {"label": "Engagement Score", "data": [72, 81, 68, 90]},
        ]
    return base


def _demo_table_markdown() -> str:
    return (
        "| Agent | Posts | Avg Sentiment | Engagement | Stage |\n"
        "|-------|-------|---------------|------------|-------|\n"
        "| Sarah Chen (VP Support) | 24 | 0.72 | High | Evaluation |\n"
        "| Mike Torres (CX Director) | 18 | 0.65 | Medium | Consideration |\n"
        "| Priya Patel (IT Leader) | 15 | 0.58 | Medium | Interest |\n"
        "| James Wilson (Operations) | 12 | 0.81 | High | Decision |\n"
        "| Lisa Park (Finance) | 9 | 0.45 | Low | Awareness |"
    )


def _demo_kpi_data() -> list:
    return [
        {"label": "Total Engagement", "value": "2,847", "change": "+23%", "trend": "up"},
        {"label": "Pipeline Value", "value": "$1.2M", "change": "+18%", "trend": "up"},
        {"label": "Avg Sentiment", "value": "0.72", "change": "+0.05", "trend": "up"},
        {"label": "Active Agents", "value": "15", "change": "0", "trend": "stable"},
    ]
