"""
Integration tests for GTM scenario template endpoints.

Tests the /api/gtm/* routes that serve pre-built scenario templates
and seed data files from the gtm_scenarios/ and gtm_seed_data/ directories.
"""

import json
from unittest.mock import patch, MagicMock

from app.models.task import TaskManager, TaskStatus

PREFIX = "/api/v1/gtm"


# ── GET /api/v1/gtm/scenarios ──

class TestListScenarios:
    """Tests for the scenario listing endpoint."""

    def test_returns_200(self, client):
        resp = client.get(f"{PREFIX}/scenarios")
        assert resp.status_code == 200

    def test_response_has_scenarios_key(self, client):
        data = client.get(f"{PREFIX}/scenarios").get_json()
        assert "scenarios" in data

    def test_scenarios_is_list(self, client):
        data = client.get(f"{PREFIX}/scenarios").get_json()
        assert isinstance(data["scenarios"], list)

    def test_scenarios_not_empty(self, client):
        """At least the 4 original pre-built scenario JSON files exist."""
        data = client.get(f"{PREFIX}/scenarios").get_json()
        assert len(data["scenarios"]) >= 4

    def test_scenario_item_shape(self, client):
        data = client.get(f"{PREFIX}/scenarios").get_json()
        item = data["scenarios"][0]
        for key in ("id", "name", "description", "category", "icon"):
            assert key in item, f"Missing key: {key}"

    def test_does_not_include_seed_text(self, client):
        resp = client.get(f"{PREFIX}/scenarios")
        for s in resp.get_json()["scenarios"]:
            assert "seed_text" not in s

    def test_known_scenario_ids(self, client):
        """The 4 original scenarios must always be present (others may exist too)."""
        data = client.get(f"{PREFIX}/scenarios").get_json()
        ids = {s["id"] for s in data["scenarios"]}
        expected = {"outbound_campaign", "pricing_simulation", "personalization", "signal_validation"}
        assert expected.issubset(ids), f"Missing: {expected - ids}"

    def test_empty_when_dir_missing(self, app, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "app.api.gtm_scenarios.SCENARIOS_DIR",
            str(tmp_path / "nonexistent"),
        )
        # Clear the response cache to avoid stale cached results
        from app.services.cache import cache_manager
        cache_manager.clear()
        with app.test_client() as c:
            resp = c.get(f"{PREFIX}/scenarios")
            assert resp.get_json()["scenarios"] == []


# ── GET /api/gtm/scenarios/<scenario_id> ──

class TestGetScenario:
    """Tests for fetching a single scenario by ID."""

    def test_existing_scenario_returns_200(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign")
        assert resp.status_code == 200

    def test_existing_scenario_has_required_fields(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign").get_json()
        for key in ("id", "name", "description", "seed_text", "agent_config", "simulation_config"):
            assert key in data, f"Missing key: {key}"

    def test_existing_scenario_id_matches(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign").get_json()
        assert data["id"] == "outbound_campaign"

    def test_nonexistent_scenario_returns_404(self, client):
        resp = client.get(f"{PREFIX}/scenarios/does_not_exist")
        assert resp.status_code == 404

    def test_nonexistent_scenario_has_error(self, client):
        data = client.get(f"{PREFIX}/scenarios/does_not_exist").get_json()
        assert "error" in data


# ── GET /api/gtm/seed-data/<data_type> ──

class TestGetSeedData:
    """Tests for the seed data endpoint."""

    def test_account_profiles_returns_200(self, client):
        resp = client.get(f"{PREFIX}/seed-data/account_profiles")
        assert resp.status_code == 200

    def test_account_profiles_is_json(self, client):
        data = client.get(f"{PREFIX}/seed-data/account_profiles").get_json()
        assert data is not None

    def test_persona_templates_returns_200(self, client):
        resp = client.get(f"{PREFIX}/seed-data/persona_templates")
        assert resp.status_code == 200

    def test_signal_definitions_returns_200(self, client):
        resp = client.get(f"{PREFIX}/seed-data/signal_definitions")
        assert resp.status_code == 200

    def test_email_templates_returns_200(self, client):
        resp = client.get(f"{PREFIX}/seed-data/email_templates")
        assert resp.status_code == 200

    def test_nonexistent_type_returns_404(self, client):
        resp = client.get(f"{PREFIX}/seed-data/nonexistent_type")
        assert resp.status_code == 404

    def test_nonexistent_type_has_error(self, client):
        data = client.get(f"{PREFIX}/seed-data/nonexistent_type").get_json()
        assert "error" in data


# ── GET /api/gtm/scenarios/<scenario_id>/seed-text ──

class TestGetScenarioSeedText:
    """Tests for the seed text extraction endpoint."""

    def test_existing_scenario_returns_seed_text(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign/seed-text")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "seed_text" in data
        assert len(data["seed_text"]) > 0

    def test_nonexistent_scenario_returns_404(self, client):
        resp = client.get(f"{PREFIX}/scenarios/nonexistent/seed-text")
        assert resp.status_code == 404


# ── POST /api/gtm/simulate ──

class TestSimulate:
    """Tests for the unified simulation endpoint."""

    def test_missing_seed_text_returns_400(self, client):
        resp = client.post(
            f"{PREFIX}/simulate",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "seed_text" in body["error"]

    def test_empty_seed_text_returns_400(self, client):
        resp = client.post(
            f"{PREFIX}/simulate",
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
                f"{PREFIX}/simulate",
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
            f"{PREFIX}/simulate",
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
            f"{PREFIX}/simulate",
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
            f"{PREFIX}/simulate",
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


# ── GET /api/v1/gtm/scenarios/<scenario_id>/export ──

class TestExportScenario:
    """Tests for the scenario export endpoint."""

    def test_export_existing_scenario(self, client):
        resp = client.get("/api/v1/gtm/scenarios/outbound_campaign/export")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        assert "attachment" in resp.headers.get("Content-Disposition", "")
        assert "outbound_campaign.json" in resp.headers["Content-Disposition"]

    def test_export_contains_valid_json(self, client):
        resp = client.get("/api/v1/gtm/scenarios/outbound_campaign/export")
        data = json.loads(resp.data)
        assert "id" in data
        assert data["id"] == "outbound_campaign"

    def test_export_nonexistent_returns_404(self, client):
        resp = client.get("/api/v1/gtm/scenarios/nonexistent/export")
        assert resp.status_code == 404


# ── GET /api/v1/gtm/scenarios/<scenario_id>/walkthrough ──

class TestScenarioWalkthrough:
    """Tests for the scenario walkthrough endpoint."""

    def test_walkthrough_returns_200(self, client):
        resp = client.get("/api/v1/gtm/scenarios/outbound_campaign/walkthrough")
        assert resp.status_code == 200

    def test_walkthrough_has_5_steps(self, client):
        data = client.get("/api/v1/gtm/scenarios/outbound_campaign/walkthrough").get_json()
        assert data["total_steps"] == 5
        assert len(data["steps"]) == 5

    def test_walkthrough_step_keys(self, client):
        data = client.get("/api/v1/gtm/scenarios/outbound_campaign/walkthrough").get_json()
        expected_keys = ["overview", "seed_document", "agent_population", "simulation_config", "expected_outcomes"]
        actual_keys = [step["key"] for step in data["steps"]]
        assert actual_keys == expected_keys

    def test_walkthrough_includes_scenario_metadata(self, client):
        data = client.get("/api/v1/gtm/scenarios/outbound_campaign/walkthrough").get_json()
        assert data["scenario_id"] == "outbound_campaign"
        assert "scenario_name" in data

    def test_walkthrough_nonexistent_returns_404(self, client):
        resp = client.get("/api/v1/gtm/scenarios/nonexistent/walkthrough")
        assert resp.status_code == 404


# ── POST /api/v1/gtm/scenarios/import ──

class TestImportScenario:
    """Tests for the scenario import endpoint."""

    def test_import_missing_body_returns_400(self, client):
        resp = client.post(
            "/api/v1/gtm/scenarios/import",
            data="not json",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_import_missing_required_fields_returns_400(self, client):
        resp = client.post(
            "/api/v1/gtm/scenarios/import",
            json={"id": "test_import", "name": "Test"},
        )
        assert resp.status_code == 400
        assert "Missing required fields" in resp.get_json()["error"]

    def test_import_invalid_id_returns_400(self, client):
        resp = client.post(
            "/api/v1/gtm/scenarios/import",
            json={
                "id": "INVALID ID!",
                "name": "Test",
                "seed_text": "text",
                "agent_config": {},
                "simulation_config": {},
            },
        )
        assert resp.status_code == 400
        assert "Invalid scenario id" in resp.get_json()["error"]

    def test_import_valid_scenario(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path))
        resp = client.post(
            "/api/v1/gtm/scenarios/import",
            json={
                "id": "test_import",
                "name": "Test Import",
                "description": "A test scenario",
                "seed_text": "Some seed text",
                "agent_config": {"count": 50},
                "simulation_config": {"total_hours": 24},
            },
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["scenario"]["id"] == "test_import"
        assert body["overwritten"] is False

    def test_import_overwrites_existing(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path))
        payload = {
            "id": "test_overwrite",
            "name": "Original",
            "seed_text": "text",
            "agent_config": {},
            "simulation_config": {},
        }
        client.post("/api/v1/gtm/scenarios/import", json=payload)
        payload["name"] = "Updated"
        resp = client.post("/api/v1/gtm/scenarios/import", json=payload)
        assert resp.status_code == 200
        assert resp.get_json()["overwritten"] is True


# ── POST /api/v1/gtm/scenarios/leaderboard ──

class TestLeaderboard:
    """Tests for the scenario leaderboard endpoint."""

    def test_empty_body_returns_mock_data(self, client):
        resp = client.post("/api/v1/gtm/scenarios/leaderboard", json={})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        entries = data["data"]
        assert len(entries) > 0
        assert entries[0]["rank"] == 1

    def test_mock_entries_are_ranked(self, client):
        entries = client.post("/api/v1/gtm/scenarios/leaderboard", json={}).get_json()["data"]
        composites = [e["scores"]["composite"] for e in entries]
        assert composites == sorted(composites, reverse=True)

    def test_custom_runs_scored(self, client):
        runs = [
            {"id": "run-1", "totalActions": 500, "totalRounds": 100, "agentCount": 12},
            {"id": "run-2", "totalActions": 200, "totalRounds": 50, "agentCount": 8},
        ]
        resp = client.post("/api/v1/gtm/scenarios/leaderboard", json={"runs": runs})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) == 2
        for entry in data:
            assert "scores" in entry
            assert "rank" in entry
            for key in ("sentiment", "consensus", "decisionQuality", "composite"):
                assert key in entry["scores"]

    def test_scores_are_deterministic(self, client):
        runs = [{"id": "stable-run", "totalActions": 300, "totalRounds": 80, "agentCount": 10}]
        r1 = client.post("/api/v1/gtm/scenarios/leaderboard", json={"runs": runs}).get_json()["data"]
        r2 = client.post("/api/v1/gtm/scenarios/leaderboard", json={"runs": runs}).get_json()["data"]
        assert r1[0]["scores"] == r2[0]["scores"]


# ── GET /api/v1/gtm/outcomes/<scenario_id> ──

class TestOutcomes:
    """Tests for the decision→impact outcome mapping endpoint."""

    def test_known_scenario_returns_200(self, client):
        resp = client.get("/api/v1/gtm/outcomes/outbound_campaign")
        assert resp.status_code == 200

    def test_response_shape(self, client):
        data = client.get("/api/v1/gtm/outcomes/outbound_campaign").get_json()
        assert "scenario_id" in data
        assert "scenario_name" in data
        assert "decisions" in data
        assert "totals" in data

    def test_decisions_have_required_fields(self, client):
        decisions = client.get("/api/v1/gtm/outcomes/outbound_campaign").get_json()["decisions"]
        assert len(decisions) > 0
        for d in decisions:
            for key in ("id", "title", "category", "impact", "timeline", "roi", "confidence"):
                assert key in d, f"Missing key: {key}"

    def test_totals_are_aggregated(self, client):
        data = client.get("/api/v1/gtm/outcomes/outbound_campaign").get_json()
        totals = data["totals"]
        decisions = data["decisions"]
        expected_pipeline = sum(d["impact"]["pipeline_per_month"] for d in decisions)
        assert totals["pipeline_per_month"] == expected_pipeline
        assert "net_impact" in totals
        assert "avg_roi" in totals

    def test_unknown_scenario_returns_fallback(self, client):
        resp = client.get("/api/v1/gtm/outcomes/unknown_scenario")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["scenario_id"] == "unknown_scenario"
        assert len(data["decisions"]) > 0


# ── GET /api/v1/gtm/templates ──

class TestSimulationTemplates:
    """Tests for the simulation scenario template endpoints."""

    def test_list_returns_200(self, client):
        resp = client.get("/api/v1/gtm/templates")
        assert resp.status_code == 200

    def test_list_has_templates_key(self, client):
        data = client.get("/api/v1/gtm/templates").get_json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

    def test_list_not_empty(self, client):
        templates = client.get("/api/v1/gtm/templates").get_json()["templates"]
        assert len(templates) >= 6  # 6 pre-built templates

    def test_template_summary_shape(self, client):
        templates = client.get("/api/v1/gtm/templates").get_json()["templates"]
        item = templates[0]
        for key in ("id", "name", "description", "environment_type", "num_rounds", "agent_count"):
            assert key in item, f"Missing key: {key}"

    def test_get_existing_template(self, client):
        resp = client.get("/api/v1/gtm/templates/pipeline_review")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == "pipeline_review"
        assert "agent_configs" in data
        assert "constraints" in data

    def test_get_nonexistent_template_returns_404(self, client):
        resp = client.get("/api/v1/gtm/templates/nonexistent")
        assert resp.status_code == 404


# ── GET /api/v1/gtm/scenarios/<scenario_id>/context ──

class TestScenarioContext:
    """Tests for the GTM business context metrics endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/api/v1/gtm/scenarios/outbound_campaign/context")
        assert resp.status_code == 200

    def test_response_shape(self, client):
        data = client.get("/api/v1/gtm/scenarios/outbound_campaign/context").get_json()
        assert data["scenario_id"] == "outbound_campaign"
        assert "scenario_name" in data
        assert "sections" in data

    def test_context_has_standard_sections(self, client):
        sections = client.get("/api/v1/gtm/scenarios/outbound_campaign/context").get_json()["sections"]
        for key in ("revenue", "pipeline", "accounts", "campaigns"):
            assert key in sections, f"Missing section: {key}"

    def test_section_has_metrics(self, client):
        sections = client.get("/api/v1/gtm/scenarios/outbound_campaign/context").get_json()["sections"]
        revenue = sections["revenue"]
        assert "label" in revenue
        assert "metrics" in revenue
        assert len(revenue["metrics"]) > 0

    def test_all_known_scenarios_have_context(self, client):
        for sid in ("outbound_campaign", "pricing_simulation", "personalization", "signal_validation"):
            resp = client.get(f"/api/v1/gtm/scenarios/{sid}/context")
            assert resp.status_code == 200

    def test_nonexistent_scenario_returns_404(self, client):
        resp = client.get("/api/v1/gtm/scenarios/nonexistent/context")
        assert resp.status_code == 404


# ── GET /api/v1/gtm/scenarios/compare ──

class TestScenarioComparison:
    """Tests for the scenario comparison matrix endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/api/v1/gtm/scenarios/compare")
        assert resp.status_code == 200

    def test_response_shape(self, client):
        data = client.get("/api/v1/gtm/scenarios/compare").get_json()
        assert "scenarios" in data
        assert "dimensions" in data
        assert "matrix" in data

    def test_has_all_scenarios(self, client):
        data = client.get("/api/v1/gtm/scenarios/compare").get_json()
        assert len(data["scenarios"]) >= 4

    def test_dimensions_list(self, client):
        dimensions = client.get("/api/v1/gtm/scenarios/compare").get_json()["dimensions"]
        expected = ["agent_count", "persona_count", "industry_count", "duration_hours", "expected_outputs"]
        assert dimensions == expected

    def test_matrix_values_normalized(self, client):
        matrix = client.get("/api/v1/gtm/scenarios/compare").get_json()["matrix"]
        for scenario_id, vals in matrix.items():
            for dim, val in vals.items():
                assert 0 <= val <= 1, f"{scenario_id}.{dim} = {val} not in [0, 1]"

    def test_empty_dir_returns_empty(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path / "empty"))
        data = client.get("/api/v1/gtm/scenarios/compare").get_json()
        assert data["scenarios"] == []
        assert data["matrix"] == {}


# ── ETag Caching ──

class TestETagCaching:
    """Tests for ETag-based caching on GTM scenario endpoints.

    The cached_response decorator intercepts responses. We must clear
    the in-memory cache first to force a cache MISS so the underlying
    route handler runs and sets ETag headers.
    """

    @staticmethod
    def _clear_cache():
        from app.services.cache import cache_manager
        cache_manager.clear()

    def test_scenarios_list_has_etag(self, client):
        self._clear_cache()
        resp = client.get("/api/v1/gtm/scenarios")
        assert "ETag" in resp.headers

    def test_scenario_detail_has_etag(self, client):
        self._clear_cache()
        resp = client.get("/api/v1/gtm/scenarios/outbound_campaign")
        assert "ETag" in resp.headers

    def test_seed_data_has_etag(self, client):
        self._clear_cache()
        resp = client.get("/api/v1/gtm/seed-data/account_profiles")
        assert "ETag" in resp.headers
