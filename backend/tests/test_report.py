"""
Integration tests for report endpoints (/api/report/*).

These tests mock the service layer (ReportManager, SimulationManager,
ProjectManager, TaskManager) to isolate HTTP routing / serialization
from external dependencies like Zep and LLM providers.
"""

import json
from dataclasses import dataclass, field
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from app.services.report_agent import Report, ReportStatus, ReportOutline, ReportSection
from app.models.task import Task, TaskStatus


# ── Helpers ──

def _make_report(
    report_id="report_abc123",
    simulation_id="sim_001",
    status=ReportStatus.COMPLETED,
    markdown="# Test Report\n\nContent here.",
):
    return Report(
        report_id=report_id,
        simulation_id=simulation_id,
        graph_id="graph_001",
        simulation_requirement="Test GTM simulation",
        status=status,
        outline=ReportOutline(
            title="Test Report",
            summary="A test summary",
            sections=[ReportSection(title="Executive Summary", content="Details")],
        ),
        markdown_content=markdown,
        created_at="2026-01-01T00:00:00",
        completed_at="2026-01-01T01:00:00",
    )


def _make_simulation_state(simulation_id="sim_001", project_id="proj_001", graph_id="graph_001"):
    state = MagicMock()
    state.simulation_id = simulation_id
    state.project_id = project_id
    state.graph_id = graph_id
    return state


def _make_project(project_id="proj_001", graph_id="graph_001"):
    project = MagicMock()
    project.project_id = project_id
    project.graph_id = graph_id
    project.simulation_requirement = "Test requirement"
    return project


# ── GET /api/report/<report_id> ──

class TestGetReport:

    @patch("app.api.report.ReportManager.get_report")
    def test_existing_report_returns_200(self, mock_get, client):
        mock_get.return_value = _make_report()
        resp = client.get("/api/report/report_abc123")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["report_id"] == "report_abc123"

    @patch("app.api.report.ReportManager.get_report")
    def test_existing_report_data_shape(self, mock_get, client):
        mock_get.return_value = _make_report()
        data = client.get("/api/report/report_abc123").get_json()["data"]
        for key in ("report_id", "simulation_id", "graph_id", "status", "outline", "markdown_content"):
            assert key in data, f"Missing key: {key}"

    @patch("app.api.report.ReportManager.get_report")
    def test_nonexistent_report_returns_404(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/report/nonexistent")
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False


# ── GET /api/report/by-simulation/<simulation_id> ──

class TestGetReportBySimulation:

    @patch("app.api.report.ReportManager.get_report_by_simulation")
    def test_found_returns_200(self, mock_get, client):
        mock_get.return_value = _make_report()
        resp = client.get("/api/report/by-simulation/sim_001")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["has_report"] is True

    @patch("app.api.report.ReportManager.get_report_by_simulation")
    def test_not_found_returns_404(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/report/by-simulation/sim_999")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["has_report"] is False


# ── GET /api/report/list ──

class TestListReports:

    @patch("app.api.report.ReportManager.list_reports")
    def test_returns_200(self, mock_list, client):
        mock_list.return_value = [_make_report(), _make_report(report_id="report_def456")]
        resp = client.get("/api/report/list")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["count"] == 2

    @patch("app.api.report.ReportManager.list_reports")
    def test_empty_list(self, mock_list, client):
        mock_list.return_value = []
        resp = client.get("/api/report/list")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 0
        assert data["data"] == []

    @patch("app.api.report.ReportManager.list_reports")
    def test_filters_by_simulation_id(self, mock_list, client):
        mock_list.return_value = [_make_report()]
        client.get("/api/report/list?simulation_id=sim_001")
        mock_list.assert_called_once_with(simulation_id="sim_001", limit=50)

    @patch("app.api.report.ReportManager.list_reports")
    def test_respects_limit_param(self, mock_list, client):
        mock_list.return_value = []
        client.get("/api/report/list?limit=10")
        mock_list.assert_called_once_with(simulation_id=None, limit=10)


# ── DELETE /api/report/<report_id> ──

class TestDeleteReport:

    @patch("app.api.report.ReportManager.delete_report")
    def test_successful_delete(self, mock_del, client):
        mock_del.return_value = True
        resp = client.delete("/api/report/report_abc123")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    @patch("app.api.report.ReportManager.delete_report")
    def test_delete_nonexistent_returns_404(self, mock_del, client):
        mock_del.return_value = False
        resp = client.delete("/api/report/nonexistent")
        assert resp.status_code == 404


# ── GET /api/report/check/<simulation_id> ──

class TestCheckReportStatus:

    @patch("app.api.report.ReportManager.get_report_by_simulation")
    def test_completed_report_unlocks_interview(self, mock_get, client):
        mock_get.return_value = _make_report(status=ReportStatus.COMPLETED)
        resp = client.get("/api/report/check/sim_001")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["has_report"] is True
        assert data["interview_unlocked"] is True
        assert data["report_status"] == "completed"

    @patch("app.api.report.ReportManager.get_report_by_simulation")
    def test_generating_report_does_not_unlock(self, mock_get, client):
        mock_get.return_value = _make_report(status=ReportStatus.GENERATING)
        data = client.get("/api/report/check/sim_001").get_json()["data"]
        assert data["has_report"] is True
        assert data["interview_unlocked"] is False

    @patch("app.api.report.ReportManager.get_report_by_simulation")
    def test_no_report_returns_unlocked_false(self, mock_get, client):
        mock_get.return_value = None
        data = client.get("/api/report/check/sim_001").get_json()["data"]
        assert data["has_report"] is False
        assert data["interview_unlocked"] is False
        assert data["report_id"] is None


# ── GET /api/report/<report_id>/sections ──

class TestGetReportSections:

    @patch("app.api.report.ReportManager.get_report")
    @patch("app.api.report.ReportManager.get_generated_sections")
    def test_returns_sections(self, mock_sections, mock_report, client):
        mock_sections.return_value = [
            {"filename": "section_01.md", "section_index": 1, "content": "## Intro\n\nHello"},
        ]
        mock_report.return_value = _make_report(status=ReportStatus.COMPLETED)
        resp = client.get("/api/report/report_abc123/sections")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total_sections"] == 1
        assert data["is_complete"] is True
        assert data["sections"][0]["section_index"] == 1

    @patch("app.api.report.ReportManager.get_report")
    @patch("app.api.report.ReportManager.get_generated_sections")
    def test_in_progress_is_not_complete(self, mock_sections, mock_report, client):
        mock_sections.return_value = []
        mock_report.return_value = _make_report(status=ReportStatus.GENERATING)
        data = client.get("/api/report/report_abc123/sections").get_json()["data"]
        assert data["is_complete"] is False


# ── GET /api/report/<report_id>/progress ──

class TestGetReportProgress:

    @patch("app.api.report.ReportManager.get_progress")
    def test_returns_progress(self, mock_progress, client):
        mock_progress.return_value = {
            "status": "generating",
            "progress": 45,
            "message": "Writing section",
            "current_section": "Key Findings",
            "completed_sections": ["Executive Summary"],
            "updated_at": "2026-01-01T00:30:00",
        }
        resp = client.get("/api/report/report_abc123/progress")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["progress"] == 45

    @patch("app.api.report.ReportManager.get_progress")
    def test_no_progress_returns_404(self, mock_progress, client):
        mock_progress.return_value = None
        resp = client.get("/api/report/nonexistent/progress")
        assert resp.status_code == 404


# ── GET /api/report/<report_id>/agent-log ──

class TestAgentLog:

    @patch("app.api.report.ReportManager.get_agent_log")
    def test_returns_log_data(self, mock_log, client):
        mock_log.return_value = {
            "logs": [{"action": "tool_call", "timestamp": "2026-01-01T00:10:00"}],
            "total_lines": 1,
            "from_line": 0,
            "has_more": False,
        }
        resp = client.get("/api/report/report_abc123/agent-log")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data["logs"]) == 1

    @patch("app.api.report.ReportManager.get_agent_log")
    def test_from_line_param(self, mock_log, client):
        mock_log.return_value = {"logs": [], "total_lines": 0, "from_line": 5, "has_more": False}
        client.get("/api/report/report_abc123/agent-log?from_line=5")
        mock_log.assert_called_once_with("report_abc123", from_line=5)


# ── GET /api/report/<report_id>/agent-log/stream ──

class TestAgentLogStream:

    @patch("app.api.report.ReportManager.get_agent_log_stream")
    def test_returns_all_logs(self, mock_stream, client):
        mock_stream.return_value = [{"action": "start"}, {"action": "complete"}]
        resp = client.get("/api/report/report_abc123/agent-log/stream")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 2


# ── GET /api/report/<report_id>/console-log ──

class TestConsoleLog:

    @patch("app.api.report.ReportManager.get_console_log")
    def test_returns_log_data(self, mock_log, client):
        mock_log.return_value = {
            "logs": ["[INFO] Started report generation"],
            "total_lines": 1,
            "from_line": 0,
            "has_more": False,
        }
        resp = client.get("/api/report/report_abc123/console-log")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data["logs"]) == 1


# ── GET /api/report/<report_id>/console-log/stream ──

class TestConsoleLogStream:

    @patch("app.api.report.ReportManager.get_console_log_stream")
    def test_returns_all_logs(self, mock_stream, client):
        mock_stream.return_value = ["line1", "line2", "line3"]
        resp = client.get("/api/report/report_abc123/console-log/stream")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 3


# ── POST /api/report/generate ──

class TestGenerateReport:

    def test_missing_simulation_id_returns_400(self, client):
        resp = client.post("/api/report/generate", json={})
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    @patch("app.api.report.SimulationManager")
    def test_nonexistent_simulation_returns_404(self, MockSimMgr, client):
        MockSimMgr.return_value.get_simulation.return_value = None
        resp = client.post("/api/report/generate", json={"simulation_id": "sim_999"})
        assert resp.status_code == 404

    @patch("app.api.report.ProjectManager.get_project")
    @patch("app.api.report.ReportManager.get_report_by_simulation")
    @patch("app.api.report.SimulationManager")
    def test_already_completed_report_returns_existing(self, MockSimMgr, mock_by_sim, mock_project, client):
        MockSimMgr.return_value.get_simulation.return_value = _make_simulation_state()
        mock_by_sim.return_value = _make_report(status=ReportStatus.COMPLETED)
        resp = client.post("/api/report/generate", json={"simulation_id": "sim_001"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["already_generated"] is True
        assert data["status"] == "completed"


# ── POST /api/report/generate/status ──

class TestGenerateStatus:

    def test_missing_both_ids_returns_400(self, client):
        resp = client.post("/api/report/generate/status", json={})
        assert resp.status_code == 400

    @patch("app.api.report.ReportManager.get_report_by_simulation")
    def test_completed_report_by_simulation_id(self, mock_by_sim, client):
        mock_by_sim.return_value = _make_report(status=ReportStatus.COMPLETED)
        resp = client.post("/api/report/generate/status", json={"simulation_id": "sim_001"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["already_completed"] is True

    @patch("app.api.report.TaskManager")
    def test_task_not_found_returns_404(self, MockTaskMgr, client):
        MockTaskMgr.return_value.get_task.return_value = None
        resp = client.post("/api/report/generate/status", json={"task_id": "task_999"})
        assert resp.status_code == 404

    @patch("app.api.report.TaskManager")
    def test_returns_task_status(self, MockTaskMgr, client):
        mock_task = Task(
            task_id="task_123",
            task_type="report_generate",
            status=TaskStatus.PROCESSING,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            progress=50,
            message="Generating section 2",
        )
        MockTaskMgr.return_value.get_task.return_value = mock_task
        resp = client.post("/api/report/generate/status", json={"task_id": "task_123"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["progress"] == 50
        assert data["status"] == "processing"


# ── POST /api/report/chat ──

class TestReportChat:

    def test_missing_simulation_id_returns_400(self, client):
        resp = client.post("/api/report/chat", json={"message": "hello"})
        assert resp.status_code == 400

    def test_missing_message_returns_400(self, client):
        resp = client.post("/api/report/chat", json={"simulation_id": "sim_001"})
        assert resp.status_code == 400

    @patch("app.api.report.SimulationManager")
    def test_nonexistent_simulation_returns_404(self, MockSimMgr, client):
        MockSimMgr.return_value.get_simulation.return_value = None
        resp = client.post("/api/report/chat", json={"simulation_id": "sim_999", "message": "hi"})
        assert resp.status_code == 404


# ── POST /api/report/tools/search ──

class TestToolsSearch:

    def test_missing_params_returns_400(self, client):
        resp = client.post("/api/report/tools/search", json={})
        assert resp.status_code == 400

    def test_missing_query_returns_400(self, client):
        resp = client.post("/api/report/tools/search", json={"graph_id": "g1"})
        assert resp.status_code == 400


# ── POST /api/report/tools/statistics ──

class TestToolsStatistics:

    def test_missing_graph_id_returns_400(self, client):
        resp = client.post("/api/report/tools/statistics", json={})
        assert resp.status_code == 400
