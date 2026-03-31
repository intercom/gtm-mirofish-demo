"""Integration tests for Report API endpoints."""

from unittest.mock import patch, MagicMock


class TestReportGenerate:
    def test_generate_returns_report_id(self, demo_client):
        resp = demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "demo-report-00001"
        assert data["status"] == "generating"
        assert data["already_generated"] is False

    def test_generate_idempotent_after_completion(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        demo_client.post("/api/demo/skip/report")
        resp = demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        data = resp.get_json()["data"]
        assert data["status"] == "completed"
        assert data["already_generated"] is True


class TestReportStatus:
    def test_generate_status_in_progress(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        resp = demo_client.post("/api/report/generate/status", json={"report_id": "demo-report-00001"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert 0 <= data["progress"] <= 100
        assert data["status"] in ("generating", "completed")

    def test_generate_status_not_found(self, demo_client):
        resp = demo_client.post("/api/report/generate/status", json={"report_id": "nonexistent"})
        assert resp.status_code == 404

    def test_generate_status_completed_after_skip(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        demo_client.post("/api/demo/skip/report")
        resp = demo_client.post("/api/report/generate/status", json={"report_id": "demo-report-00001"})
        data = resp.get_json()["data"]
        assert data["progress"] == 100
        assert data["status"] == "completed"


class TestReportProgress:
    def test_progress_fields(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        resp = demo_client.get("/api/report/demo-report-00001/progress")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "progress" in data
        assert "total_sections" in data
        assert data["total_sections"] == 5
        assert "completed_sections" in data
        assert "message" in data

    def test_progress_completes_after_skip(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        demo_client.post("/api/demo/skip/report")
        data = demo_client.get("/api/report/demo-report-00001/progress").get_json()["data"]
        assert data["progress"] == 100
        assert data["completed_sections"] == data["total_sections"]


class TestReportSections:
    def test_sections_progressive(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        demo_client.post("/api/demo/skip/report")
        resp = demo_client.get("/api/report/demo-report-00001/sections")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["is_complete"] is True
        assert len(data["sections"]) == 5

    def test_single_section_by_index(self, demo_client):
        resp = demo_client.get("/api/report/any-report/section/0")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["section_index"] == 0
        assert "Executive Summary" in data["content"]

    def test_single_section_not_found(self, demo_client):
        resp = demo_client.get("/api/report/any-report/section/99")
        assert resp.status_code == 404


class TestReportGet:
    def test_get_full_report(self, demo_client):
        resp = demo_client.get("/api/report/any-report-id")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "any-report-id"
        assert data["status"] == "completed"
        assert len(data["sections"]) == 5

    def test_report_by_simulation(self, demo_client):
        resp = demo_client.get("/api/report/by-simulation/demo-sim-00001")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "demo-report-00001"

    def test_report_list(self, demo_client):
        resp = demo_client.get("/api/report/list")
        assert resp.status_code == 200


class TestReportDownload:
    def test_download_returns_markdown(self, demo_client):
        resp = demo_client.get("/api/report/test-report/download")
        assert resp.status_code == 200
        assert resp.content_type == "text/markdown; charset=utf-8"
        assert "attachment" in resp.headers.get("Content-Disposition", "")
        assert b"Executive Summary" in resp.data

    def test_report_check_no_report(self, demo_client):
        resp = demo_client.get("/api/report/check/demo-sim-99999")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["has_report"] is False

    def test_report_check_with_completed_report(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        demo_client.post("/api/demo/skip/report")
        resp = demo_client.get("/api/report/check/demo-sim-00001")
        data = resp.get_json()["data"]
        assert data["has_report"] is True
        assert data["report_id"] == "demo-report-00001"


class TestReportLogStubs:
    def test_agent_log(self, demo_client):
        resp = demo_client.get("/api/report/r1/agent-log")
        assert resp.status_code == 200

    def test_agent_log_stream(self, demo_client):
        resp = demo_client.get("/api/report/r1/agent-log/stream")
        assert resp.status_code == 200

    def test_console_log(self, demo_client):
        resp = demo_client.get("/api/report/r1/console-log")
        assert resp.status_code == 200

    def test_console_log_stream(self, demo_client):
        resp = demo_client.get("/api/report/r1/console-log/stream")
        assert resp.status_code == 200


# ── GET /api/v1/report/types ──

class TestReportTypes:
    """Tests for the report types metadata endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/api/v1/report/types")
        assert resp.status_code == 200

    def test_response_shape(self, client):
        data = client.get("/api/v1/report/types").get_json()
        assert data["success"] is True
        assert "types" in data["data"]
        assert "default" in data["data"]

    def test_types_is_list(self, client):
        types = client.get("/api/v1/report/types").get_json()["data"]["types"]
        assert isinstance(types, list)
        assert len(types) > 0

    def test_type_item_shape(self, client):
        types = client.get("/api/v1/report/types").get_json()["data"]["types"]
        for t in types:
            assert "id" in t
            assert "description" in t

    def test_known_type_ids(self, client):
        types = client.get("/api/v1/report/types").get_json()["data"]["types"]
        ids = {t["id"] for t in types}
        assert "executive_summary" in ids
        assert "detailed_analysis" in ids

    def test_default_is_executive_summary(self, client):
        data = client.get("/api/v1/report/types").get_json()["data"]
        assert data["default"] == "executive_summary"


# ── GET /api/v1/report/templates ──

class TestReportTemplates:
    """Tests for the report template listing and detail endpoints."""

    def test_list_returns_200(self, client):
        resp = client.get("/api/v1/report/templates")
        assert resp.status_code == 200

    def test_list_response_shape(self, client):
        data = client.get("/api/v1/report/templates").get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_list_not_empty(self, client):
        templates = client.get("/api/v1/report/templates").get_json()["data"]
        assert len(templates) > 0

    def test_template_summary_shape(self, client):
        templates = client.get("/api/v1/report/templates").get_json()["data"]
        item = templates[0]
        for key in ("id", "name", "description", "icon", "category"):
            assert key in item, f"Missing key: {key}"

    def test_get_existing_template(self, client):
        resp = client.get("/api/v1/report/templates/executive_summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == "executive_summary"

    def test_get_template_has_sections(self, client):
        data = client.get("/api/v1/report/templates/executive_summary").get_json()["data"]
        assert "sections" in data
        assert isinstance(data["sections"], list)
        assert len(data["sections"]) > 0

    def test_get_nonexistent_template_returns_404(self, client):
        resp = client.get("/api/v1/report/templates/nonexistent_template")
        assert resp.status_code == 404


# ── GET /api/v1/report/campaign-spend ──

class TestCampaignSpend:
    """Tests for the campaign spend visualization endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/api/v1/report/campaign-spend")
        assert resp.status_code == 200

    def test_response_shape(self, client):
        data = client.get("/api/v1/report/campaign-spend").get_json()
        assert data["success"] is True
        assert "campaigns" in data["data"]
        assert "channels" in data["data"]
        assert "total_budget" in data["data"]
        assert "total_spend" in data["data"]

    def test_campaigns_is_list(self, client):
        campaigns = client.get("/api/v1/report/campaign-spend").get_json()["data"]["campaigns"]
        assert isinstance(campaigns, list)
        assert len(campaigns) > 0

    def test_campaign_item_shape(self, client):
        campaigns = client.get("/api/v1/report/campaign-spend").get_json()["data"]["campaigns"]
        for c in campaigns:
            assert "name" in c
            assert "channel" in c
            assert "spend" in c
            assert "budget" in c

    def test_total_spend_is_sum(self, client):
        data = client.get("/api/v1/report/campaign-spend").get_json()["data"]
        expected = sum(c["spend"] for c in data["campaigns"])
        assert data["total_spend"] == expected


# ── GET /api/v1/report/data-sources ──

class TestDataSources:
    """Tests for the report data source endpoints."""

    def test_list_returns_200(self, client):
        resp = client.get("/api/v1/report/data-sources")
        assert resp.status_code == 200

    def test_list_response_shape(self, client):
        data = client.get("/api/v1/report/data-sources").get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_source_item_shape(self, client):
        sources = client.get("/api/v1/report/data-sources").get_json()["data"]
        for s in sources:
            for key in ("id", "name", "description", "category", "icon", "connected"):
                assert key in s, f"Missing key: {key}"

    def test_simulation_source_is_connected(self, client):
        sources = client.get("/api/v1/report/data-sources").get_json()["data"]
        sim_sources = [s for s in sources if s["id"] == "simulation"]
        assert len(sim_sources) == 1
        assert sim_sources[0]["connected"] is True

    def test_preview_mock_source(self, client):
        resp = client.get("/api/v1/report/data-sources/revenue/preview")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["is_mock"] is True
        assert "metrics" in data
        assert "sample_rows" in data

    def test_preview_nonexistent_source_returns_404(self, client):
        resp = client.get("/api/v1/report/data-sources/nonexistent/preview")
        assert resp.status_code == 404


# ── DELETE /api/v1/report/<report_id> ──

class TestReportDelete:
    """Tests for the report deletion endpoint."""

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/v1/report/nonexistent-report")
        assert resp.status_code == 404

    @patch("app.api.report.ReportManager.delete_report", return_value=True)
    def test_delete_existing_returns_success(self, mock_delete, client):
        resp = client.delete("/api/v1/report/some-report")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        mock_delete.assert_called_once_with("some-report")


# ── POST /api/v1/report/generate (validation) ──

class TestReportGenerateValidation:
    """Tests for report generation request validation."""

    def test_missing_simulation_id_returns_400(self, client):
        resp = client.post("/api/v1/report/generate", json={})
        assert resp.status_code == 400

    def test_invalid_report_type_returns_400(self, client):
        resp = client.post("/api/v1/report/generate", json={
            "simulation_id": "sim_test",
            "report_type": "invalid_type",
        })
        assert resp.status_code == 400

    def test_generate_demo_mode(self, client):
        """When no LLM key is configured, should return a demo report immediately."""
        with patch("app.api.report._is_demo_mode", return_value=True):
            resp = client.post("/api/v1/report/generate", json={
                "simulation_id": "sim_test",
            })
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["data"]["status"] == "completed"


# ── GET /api/v1/report/<report_id>/download (format validation) ──

class TestReportDownloadFormats:
    """Tests for report download format validation on the main app."""

    def test_unsupported_format_returns_400(self, client):
        resp = client.get("/api/v1/report/any-report/download?format=xml")
        assert resp.status_code == 400
        assert "Unsupported format" in resp.get_json()["error"]

    def test_report_not_found_returns_404(self, client):
        resp = client.get("/api/v1/report/nonexistent/download?format=md")
        assert resp.status_code == 404


# ── GET /api/v1/report/<report_id>/export (format validation) ──

class TestReportExportFormats:
    """Tests for report export format validation."""

    def test_unsupported_format_returns_400(self, client):
        resp = client.get("/api/v1/report/any-report/export?format=pdf")
        assert resp.status_code == 400
        assert "Unsupported format" in resp.get_json()["error"]

    def test_nonexistent_report_returns_404(self, client):
        """When no sections found and no report, should 404."""
        resp = client.get("/api/v1/report/nonexistent/export?format=markdown")
        assert resp.status_code == 404


# ── Report Sharing ──

class TestReportSharing:
    """Tests for report sharing endpoints (create, get, revoke, access)."""

    def test_create_share_nonexistent_returns_404(self, client):
        with patch("app.api.report.ReportManager.create_share", return_value=None):
            resp = client.post("/api/v1/report/nonexistent/share")
            assert resp.status_code == 404

    @patch("app.api.report.ReportManager.create_share")
    def test_create_share_success(self, mock_create, client):
        mock_create.return_value = {"token": "abc123", "url": "/shared/abc123"}
        resp = client.post("/api/v1/report/test-report/share")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["token"] == "abc123"

    def test_get_share_no_link(self, client):
        with patch("app.api.report.ReportManager.get_share", return_value=None):
            resp = client.get("/api/v1/report/test-report/share")
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["is_shared"] is False

    def test_revoke_share_no_active_link(self, client):
        with patch("app.api.report.ReportManager.revoke_share", return_value=False):
            resp = client.delete("/api/v1/report/test-report/share")
            assert resp.status_code == 404

    @patch("app.api.report.ReportManager.revoke_share", return_value=True)
    def test_revoke_share_success(self, mock_revoke, client):
        resp = client.delete("/api/v1/report/test-report/share")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_access_shared_invalid_token(self, client):
        with patch("app.api.report.ReportManager.get_report_by_share_token", return_value=None):
            resp = client.get("/api/v1/report/shared/invalid-token")
            assert resp.status_code == 404

    def test_access_shared_incomplete_report(self, client):
        mock_report = MagicMock()
        mock_report.status = MagicMock()
        mock_report.status.__eq__ = lambda self, other: False  # not COMPLETED
        # Simpler: just check the status attribute directly
        from app.services.report_agent import ReportStatus
        mock_report.status = ReportStatus.GENERATING
        with patch("app.api.report.ReportManager.get_report_by_share_token", return_value=mock_report):
            resp = client.get("/api/v1/report/shared/some-token")
            assert resp.status_code == 400


# ── GET /api/v1/report/<report_id>/tool-calls ──

class TestReportToolCalls:
    """Tests for the tool-calls transparency endpoint."""

    def test_nonexistent_report_returns_404(self, client):
        with patch("app.api.report.ReportManager.get_report", return_value=None):
            resp = client.get("/api/v1/report/nonexistent/tool-calls")
            assert resp.status_code == 404

    @patch("app.api.report.ReportManager.get_agent_log")
    @patch("app.api.report.ReportManager.get_report")
    def test_tool_calls_response_shape(self, mock_report, mock_log, client):
        mock_report.return_value = MagicMock()
        mock_log.return_value = {"logs": [
            {"action": "react_thought", "details": {}},
            {"action": "tool_call", "details": {"tool_name": "search"}},
            {"action": "tool_result", "details": {}},
            {"action": "llm_response", "details": {}},
            {"action": "other_action", "details": {}},
        ]}
        resp = client.get("/api/v1/report/test-report/tool-calls")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "test-report"
        assert data["count"] == 4  # excludes "other_action"
        assert "summary" in data
        assert data["summary"]["total_thoughts"] == 1
        assert data["summary"]["total_tool_calls"] == 1


# ── POST /api/v1/report/chat (validation) ──

class TestReportChatValidation:
    """Tests for report chat endpoint input validation."""

    def test_missing_simulation_id_returns_400(self, client):
        resp = client.post("/api/v1/report/chat", json={"message": "hello"})
        assert resp.status_code == 400

    def test_missing_message_returns_400(self, client):
        resp = client.post("/api/v1/report/chat", json={"simulation_id": "sim_test"})
        assert resp.status_code == 400
