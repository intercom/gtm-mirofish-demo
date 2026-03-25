"""
Integration tests for GTM scenario template endpoints.

Tests the /api/gtm/* routes that serve pre-built scenario templates
and seed data files from the gtm_scenarios/ and gtm_seed_data/ directories.
"""

import json
from unittest.mock import patch, MagicMock

from app.models.task import TaskManager, TaskStatus


# ── GET /api/gtm/scenarios ──

class TestListScenarios:
    """Tests for the scenario listing endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/api/gtm/scenarios")
        assert resp.status_code == 200

    def test_response_has_scenarios_key(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        assert "scenarios" in data

    def test_scenarios_is_list(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        assert isinstance(data["scenarios"], list)

    def test_scenarios_not_empty(self, client):
        """There are 4 pre-built scenario JSON files in gtm_scenarios/."""
        data = client.get("/api/gtm/scenarios").get_json()
        assert len(data["scenarios"]) == 4

    def test_scenario_item_shape(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        item = data["scenarios"][0]
        for key in ("id", "name", "description", "category", "icon"):
            assert key in item, f"Missing key: {key}"

    def test_does_not_include_seed_text(self, client):
        resp = client.get("/api/gtm/scenarios")
        for s in resp.get_json()["scenarios"]:
            assert "seed_text" not in s

    def test_known_scenario_ids(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        ids = {s["id"] for s in data["scenarios"]}
        assert ids == {
            "outbound_campaign",
            "pricing_simulation",
            "personalization",
            "signal_validation",
        }

    def test_empty_when_dir_missing(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "app.api.gtm_scenarios.SCENARIOS_DIR",
            str(tmp_path / "nonexistent"),
        )
        resp = client.get("/api/gtm/scenarios")
        assert resp.get_json()["scenarios"] == []


# ── GET /api/gtm/scenarios/<scenario_id> ──

class TestGetScenario:
    """Tests for fetching a single scenario by ID."""

    def test_existing_scenario_returns_200(self, client):
        resp = client.get("/api/gtm/scenarios/outbound_campaign")
        assert resp.status_code == 200

    def test_existing_scenario_has_required_fields(self, client):
        data = client.get("/api/gtm/scenarios/outbound_campaign").get_json()
        for key in ("id", "name", "description", "seed_text", "agent_config", "simulation_config"):
            assert key in data, f"Missing key: {key}"

    def test_existing_scenario_id_matches(self, client):
        data = client.get("/api/gtm/scenarios/outbound_campaign").get_json()
        assert data["id"] == "outbound_campaign"

    def test_nonexistent_scenario_returns_404(self, client):
        resp = client.get("/api/gtm/scenarios/does_not_exist")
        assert resp.status_code == 404

    def test_nonexistent_scenario_has_error(self, client):
        data = client.get("/api/gtm/scenarios/does_not_exist").get_json()
        assert "error" in data


# ── GET /api/gtm/seed-data/<data_type> ──

class TestGetSeedData:
    """Tests for the seed data endpoint."""

    def test_account_profiles_returns_200(self, client):
        resp = client.get("/api/gtm/seed-data/account_profiles")
        assert resp.status_code == 200

    def test_account_profiles_is_json(self, client):
        data = client.get("/api/gtm/seed-data/account_profiles").get_json()
        assert data is not None

    def test_persona_templates_returns_200(self, client):
        resp = client.get("/api/gtm/seed-data/persona_templates")
        assert resp.status_code == 200

    def test_signal_definitions_returns_200(self, client):
        resp = client.get("/api/gtm/seed-data/signal_definitions")
        assert resp.status_code == 200

    def test_email_templates_returns_200(self, client):
        resp = client.get("/api/gtm/seed-data/email_templates")
        assert resp.status_code == 200

    def test_nonexistent_type_returns_404(self, client):
        resp = client.get("/api/gtm/seed-data/nonexistent_type")
        assert resp.status_code == 404

    def test_nonexistent_type_has_error(self, client):
        data = client.get("/api/gtm/seed-data/nonexistent_type").get_json()
        assert "error" in data


# ── GET /api/gtm/scenarios/<scenario_id>/seed-text ──

class TestGetScenarioSeedText:
    """Tests for the seed text extraction endpoint."""

    def test_existing_scenario_returns_seed_text(self, client):
        resp = client.get("/api/gtm/scenarios/outbound_campaign/seed-text")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "seed_text" in data
        assert len(data["seed_text"]) > 0

    def test_nonexistent_scenario_returns_404(self, client):
        resp = client.get("/api/gtm/scenarios/nonexistent/seed-text")
        assert resp.status_code == 404


# ── POST /api/gtm/simulate ──

class TestSimulate:
    """Tests for the unified simulation endpoint."""

    def test_missing_seed_text_returns_400(self, client):
        resp = client.post(
            "/api/gtm/simulate",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "seed_text" in body["error"]

    def test_empty_seed_text_returns_400(self, client):
        resp = client.post(
            "/api/gtm/simulate",
            json={"seed_text": "   "},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_zep_key(self, client, app):
        app.config["ZEP_API_KEY"] = None
        with patch("app.api.gtm_scenarios.Config") as mock_cfg:
            mock_cfg.ZEP_API_KEY = None
            mock_cfg.DEFAULT_CHUNK_SIZE = 500
            mock_cfg.DEFAULT_CHUNK_OVERLAP = 50
            resp = client.post(
                "/api/gtm/simulate",
                json={"seed_text": "Test scenario text for simulation"},
                content_type="application/json",
            )
        assert resp.status_code == 500
        assert "ZEP_API_KEY" in resp.get_json()["error"]

    @patch("app.api.gtm_scenarios.threading.Thread")
    @patch("app.api.gtm_scenarios.ProjectManager")
    @patch("app.api.gtm_scenarios.TextProcessor")
    def test_successful_simulate(self, mock_tp, mock_pm, mock_thread, client):
        mock_tp.preprocess_text.return_value = "preprocessed text"
        mock_project = MagicMock()
        mock_project.project_id = "proj_abc123"
        mock_pm.create_project.return_value = mock_project

        resp = client.post(
            "/api/gtm/simulate",
            json={
                "seed_text": "Run a GTM simulation for outbound campaign",
                "agent_count": 200,
                "industries": ["SaaS"],
            },
            content_type="application/json",
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "task_id" in body["data"]
        assert body["data"]["project_id"] == "proj_abc123"

        mock_thread.return_value.start.assert_called_once()

    @patch("app.api.gtm_scenarios.threading.Thread")
    @patch("app.api.gtm_scenarios.ProjectManager")
    @patch("app.api.gtm_scenarios.TextProcessor")
    def test_simulate_creates_task(self, mock_tp, mock_pm, mock_thread, client):
        mock_tp.preprocess_text.return_value = "preprocessed"
        mock_project = MagicMock()
        mock_project.project_id = "proj_xyz"
        mock_pm.create_project.return_value = mock_project

        resp = client.post(
            "/api/gtm/simulate",
            json={"seed_text": "Some seed text"},
            content_type="application/json",
        )

        task_id = resp.get_json()["data"]["task_id"]
        tm = TaskManager()
        task = tm.get_task(task_id)
        assert task is not None
        assert task.task_type == "GTM Simulation"
        assert task.metadata["project_id"] == "proj_xyz"

    @patch("app.api.gtm_scenarios.threading.Thread")
    @patch("app.api.gtm_scenarios.ProjectManager")
    @patch("app.api.gtm_scenarios.TextProcessor")
    def test_simulate_stores_metadata(self, mock_tp, mock_pm, mock_thread, client):
        mock_tp.preprocess_text.return_value = "preprocessed"
        mock_project = MagicMock()
        mock_project.project_id = "proj_meta"
        mock_pm.create_project.return_value = mock_project

        resp = client.post(
            "/api/gtm/simulate",
            json={
                "seed_text": "Seed text here",
                "agent_count": 100,
                "persona_types": ["VP of Support"],
                "industries": ["SaaS", "Healthcare"],
                "duration_hours": 48,
            },
            content_type="application/json",
        )

        task_id = resp.get_json()["data"]["task_id"]
        tm = TaskManager()
        task = tm.get_task(task_id)
        assert task.metadata["agent_count"] == 100
        assert task.metadata["persona_types"] == ["VP of Support"]
        assert task.metadata["industries"] == ["SaaS", "Healthcare"]
        assert task.metadata["duration_hours"] == 48
