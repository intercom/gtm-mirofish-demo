"""
Integration tests for GTM scenario template endpoints.

Tests the /api/gtm/* routes that serve pre-built scenario templates
and seed data files from the gtm_scenarios/ and gtm_seed_data/ directories.
"""

import json
import os


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
        assert len(data["scenarios"]) >= 4

    def test_scenario_item_shape(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        item = data["scenarios"][0]
        for key in ("id", "name", "description", "category", "icon"):
            assert key in item, f"Missing key: {key}"

    def test_known_scenario_ids(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        ids = {s["id"] for s in data["scenarios"]}
        expected = {"outbound_campaign", "personalization", "pricing_simulation", "signal_validation"}
        assert expected.issubset(ids)


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

class TestSimulateEndpoint:
    """Tests for the unified simulation endpoint (validation only — no real services)."""

    def test_missing_seed_text_returns_400(self, client):
        resp = client.post(
            "/api/gtm/simulate",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "seed_text" in data["error"]

    def test_empty_seed_text_returns_400(self, client):
        resp = client.post(
            "/api/gtm/simulate",
            json={"seed_text": "   "},
            content_type="application/json",
        )
        assert resp.status_code == 400
