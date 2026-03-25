"""Integration tests for Report API endpoints."""


class TestReportGenerate:
    def test_generate_returns_report_id(self, client):
        resp = client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "demo-report-00001"
        assert data["status"] == "generating"
        assert data["already_generated"] is False

    def test_generate_idempotent_after_completion(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        client.post("/api/demo/skip/report")
        resp = client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        data = resp.get_json()["data"]
        assert data["status"] == "completed"
        assert data["already_generated"] is True


class TestReportStatus:
    def test_generate_status_in_progress(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        resp = client.post("/api/report/generate/status", json={"report_id": "demo-report-00001"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert 0 <= data["progress"] <= 100
        assert data["status"] in ("generating", "completed")

    def test_generate_status_not_found(self, client):
        resp = client.post("/api/report/generate/status", json={"report_id": "nonexistent"})
        assert resp.status_code == 404

    def test_generate_status_completed_after_skip(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        client.post("/api/demo/skip/report")
        resp = client.post("/api/report/generate/status", json={"report_id": "demo-report-00001"})
        data = resp.get_json()["data"]
        assert data["progress"] == 100
        assert data["status"] == "completed"


class TestReportProgress:
    def test_progress_fields(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        resp = client.get("/api/report/demo-report-00001/progress")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "progress" in data
        assert "total_sections" in data
        assert data["total_sections"] == 5
        assert "completed_sections" in data
        assert "message" in data

    def test_progress_completes_after_skip(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        client.post("/api/demo/skip/report")
        data = client.get("/api/report/demo-report-00001/progress").get_json()["data"]
        assert data["progress"] == 100
        assert data["completed_sections"] == data["total_sections"]


class TestReportSections:
    def test_sections_progressive(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        client.post("/api/demo/skip/report")
        resp = client.get("/api/report/demo-report-00001/sections")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["is_complete"] is True
        assert len(data["sections"]) == 5

    def test_single_section_by_index(self, client):
        resp = client.get("/api/report/any-report/section/0")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["section_index"] == 0
        assert "Executive Summary" in data["content"]

    def test_single_section_not_found(self, client):
        resp = client.get("/api/report/any-report/section/99")
        assert resp.status_code == 404


class TestReportGet:
    def test_get_full_report(self, client):
        resp = client.get("/api/report/any-report-id")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "any-report-id"
        assert data["status"] == "completed"
        assert len(data["sections"]) == 5

    def test_report_by_simulation(self, client):
        resp = client.get("/api/report/by-simulation/demo-sim-00001")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["report_id"] == "demo-report-00001"

    def test_report_list(self, client):
        resp = client.get("/api/report/list")
        assert resp.status_code == 200


class TestReportDownload:
    def test_download_returns_markdown(self, client):
        resp = client.get("/api/report/test-report/download")
        assert resp.status_code == 200
        assert resp.content_type == "text/markdown; charset=utf-8"
        assert "attachment" in resp.headers.get("Content-Disposition", "")
        assert b"Executive Summary" in resp.data

    def test_report_check_no_report(self, client):
        resp = client.get("/api/report/check/demo-sim-99999")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["has_report"] is False

    def test_report_check_with_completed_report(self, client):
        client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        client.post("/api/demo/skip/report")
        resp = client.get("/api/report/check/demo-sim-00001")
        data = resp.get_json()["data"]
        assert data["has_report"] is True
        assert data["report_id"] == "demo-report-00001"


class TestReportLogStubs:
    def test_agent_log(self, client):
        resp = client.get("/api/report/r1/agent-log")
        assert resp.status_code == 200

    def test_agent_log_stream(self, client):
        resp = client.get("/api/report/r1/agent-log/stream")
        assert resp.status_code == 200

    def test_console_log(self, client):
        resp = client.get("/api/report/r1/console-log")
        assert resp.status_code == 200

    def test_console_log_stream(self, client):
        resp = client.get("/api/report/r1/console-log/stream")
        assert resp.status_code == 200
