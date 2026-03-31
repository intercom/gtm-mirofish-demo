"""Tests for Flask API routes — health, GTM scenarios, and settings."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "MiroFish Backend"


class TestGTMScenariosAPI:
    """Test GTM scenario template endpoints."""

    def test_list_scenarios(self, client):
        resp = client.get("/api/v1/gtm/scenarios")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)

    def test_list_scenarios_contains_expected_fields(self, client):
        resp = client.get("/api/v1/gtm/scenarios")
        data = resp.get_json()
        if data["scenarios"]:
            scenario = data["scenarios"][0]
            assert "id" in scenario
            assert "name" in scenario
            assert "description" in scenario

    def test_get_scenario_not_found(self, client):
        resp = client.get("/api/v1/gtm/scenarios/nonexistent_scenario")
        assert resp.status_code == 404

    def test_get_known_scenario(self, client):
        # First list to get a valid ID
        list_resp = client.get("/api/v1/gtm/scenarios")
        scenarios = list_resp.get_json()["scenarios"]
        if not scenarios:
            pytest.skip("No scenarios available")
        scenario_id = scenarios[0]["id"]

        resp = client.get(f"/api/v1/gtm/scenarios/{scenario_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "id" in data or "name" in data

    def test_get_seed_data_not_found(self, client):
        resp = client.get("/api/v1/gtm/seed-data/nonexistent_type")
        assert resp.status_code == 404

    def test_get_seed_text_not_found(self, client):
        resp = client.get("/api/v1/gtm/scenarios/nonexistent/seed-text")
        assert resp.status_code == 404


class TestGTMSimulateEndpoint:
    def test_simulate_requires_seed_text(self, client):
        resp = client.post(
            "/api/v1/gtm/simulate",
            data=json.dumps({"seed_text": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "seed_text" in data["error"]

    def test_simulate_requires_zep_key(self, client, app):
        with patch("app.api.gtm_scenarios.Config") as mock_config:
            mock_config.ZEP_API_KEY = None
            mock_config.DEFAULT_CHUNK_SIZE = 500
            mock_config.DEFAULT_CHUNK_OVERLAP = 50
            resp = client.post(
                "/api/v1/gtm/simulate",
                data=json.dumps({"seed_text": "Test scenario text"}),
                content_type="application/json",
            )
            assert resp.status_code == 500
            data = resp.get_json()
            assert "ZEP_API_KEY" in data["error"]

    @patch("app.api.gtm_scenarios.GraphBuilderService")
    @patch("app.api.gtm_scenarios.OntologyGenerator")
    def test_simulate_returns_task_id(self, mock_onto_cls, mock_builder_cls, client, app):
        with patch("app.api.gtm_scenarios.Config") as mock_config:
            mock_config.ZEP_API_KEY = "test-key"
            mock_config.DEFAULT_CHUNK_SIZE = 500
            mock_config.DEFAULT_CHUNK_OVERLAP = 50
            mock_config.UPLOAD_FOLDER = "/tmp/test_uploads"
            resp = client.post(
                "/api/v1/gtm/simulate",
                data=json.dumps({"seed_text": "Run a GTM market simulation"}),
                content_type="application/json",
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert "task_id" in data["data"]
            assert "project_id" in data["data"]


class TestSettingsAPI:
    def test_test_llm_missing_key(self, client):
        resp = client.post(
            "/api/settings/test-llm",
            data=json.dumps({"provider": "openai", "apiKey": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False

    def test_test_llm_unknown_provider(self, client):
        resp = client.post(
            "/api/settings/test-llm",
            data=json.dumps({"provider": "unknown_provider", "apiKey": "k"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "Unknown provider" in data["error"]

    @patch("app.api.settings.OpenAI")
    def test_test_llm_success(self, mock_openai_cls, client):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        resp = client.post(
            "/api/settings/test-llm",
            data=json.dumps({"provider": "openai", "apiKey": "sk-test"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True

    @patch("app.api.settings.OpenAI")
    def test_test_llm_connection_failure(self, mock_openai_cls, client):
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Connection refused")
        mock_openai_cls.return_value = mock_client
        resp = client.post(
            "/api/settings/test-llm",
            data=json.dumps({"provider": "openai", "apiKey": "sk-bad"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert "Connection refused" in data["error"]

    def test_test_zep_missing_key(self, client):
        resp = client.post(
            "/api/settings/test-zep",
            data=json.dumps({"apiKey": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_auth_status_disabled(self, client):
        resp = client.get("/api/settings/auth-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["authEnabled"] is False
        assert data["provider"] is None
        assert data["user"] is None
