"""Integration tests for GTM data endpoints.

Tests the read-only data endpoints (scenarios, seed data, seed text)
and the simulate endpoint's input validation, all exercised through
Flask's test client against the real JSON fixture files.
"""

import pytest


# ---------------------------------------------------------------------------
# GET /api/gtm/scenarios
# ---------------------------------------------------------------------------

KNOWN_SCENARIO_IDS = [
    "outbound_campaign",
    "personalization",
    "pricing_simulation",
    "signal_validation",
]

SCENARIO_LIST_FIELDS = {"id", "name", "description", "category", "icon"}


class TestListScenarios:
    def test_returns_200(self, client):
        resp = client.get("/api/gtm/scenarios")
        assert resp.status_code == 200

    def test_response_contains_scenarios_key(self, client):
        data = client.get("/api/gtm/scenarios").get_json()
        assert "scenarios" in data

    def test_returns_all_known_scenarios(self, client):
        scenarios = client.get("/api/gtm/scenarios").get_json()["scenarios"]
        ids = {s["id"] for s in scenarios}
        for sid in KNOWN_SCENARIO_IDS:
            assert sid in ids, f"Missing scenario: {sid}"

    def test_each_scenario_has_required_fields(self, client):
        scenarios = client.get("/api/gtm/scenarios").get_json()["scenarios"]
        for scenario in scenarios:
            missing = SCENARIO_LIST_FIELDS - set(scenario.keys())
            assert not missing, f"Scenario {scenario.get('id')} missing fields: {missing}"


# ---------------------------------------------------------------------------
# GET /api/gtm/scenarios/<scenario_id>
# ---------------------------------------------------------------------------

FULL_SCENARIO_FIELDS = {
    "id", "name", "description", "category", "icon",
    "seed_text", "agent_config", "simulation_config", "expected_outputs",
}


class TestGetScenario:
    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_returns_200_for_known_scenarios(self, client, scenario_id):
        resp = client.get(f"/api/gtm/scenarios/{scenario_id}")
        assert resp.status_code == 200

    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_full_scenario_has_required_fields(self, client, scenario_id):
        data = client.get(f"/api/gtm/scenarios/{scenario_id}").get_json()
        missing = FULL_SCENARIO_FIELDS - set(data.keys())
        assert not missing, f"Scenario {scenario_id} missing fields: {missing}"

    def test_agent_config_structure(self, client):
        data = client.get("/api/gtm/scenarios/outbound_campaign").get_json()
        ac = data["agent_config"]
        assert "count" in ac
        assert "persona_types" in ac
        assert isinstance(ac["persona_types"], list)
        assert "firmographic_mix" in ac
        assert "industries" in ac["firmographic_mix"]

    def test_simulation_config_structure(self, client):
        data = client.get("/api/gtm/scenarios/outbound_campaign").get_json()
        sc = data["simulation_config"]
        assert "total_hours" in sc
        assert "minutes_per_round" in sc
        assert "platform_mode" in sc

    def test_returns_404_for_unknown_scenario(self, client):
        resp = client.get("/api/gtm/scenarios/nonexistent_scenario")
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_id_matches_request(self, client):
        for sid in KNOWN_SCENARIO_IDS:
            data = client.get(f"/api/gtm/scenarios/{sid}").get_json()
            assert data["id"] == sid


# ---------------------------------------------------------------------------
# GET /api/gtm/seed-data/<data_type>
# ---------------------------------------------------------------------------

KNOWN_SEED_TYPES = [
    "account_profiles",
    "email_templates",
    "persona_templates",
    "signal_definitions",
]


class TestGetSeedData:
    @pytest.mark.parametrize("data_type", KNOWN_SEED_TYPES)
    def test_returns_200_for_known_types(self, client, data_type):
        resp = client.get(f"/api/gtm/seed-data/{data_type}")
        assert resp.status_code == 200

    @pytest.mark.parametrize("data_type", KNOWN_SEED_TYPES)
    def test_response_is_valid_json_object(self, client, data_type):
        data = client.get(f"/api/gtm/seed-data/{data_type}").get_json()
        assert isinstance(data, dict)

    def test_account_profiles_has_profiles_list(self, client):
        data = client.get("/api/gtm/seed-data/account_profiles").get_json()
        assert "profiles" in data
        assert isinstance(data["profiles"], list)
        assert len(data["profiles"]) > 0

    def test_account_profile_fields(self, client):
        profile = client.get("/api/gtm/seed-data/account_profiles").get_json()["profiles"][0]
        expected = {"segment", "industry", "company_size", "current_support_tool"}
        assert expected.issubset(set(profile.keys()))

    def test_persona_templates_has_personas_list(self, client):
        data = client.get("/api/gtm/seed-data/persona_templates").get_json()
        assert "personas" in data
        assert isinstance(data["personas"], list)
        assert len(data["personas"]) > 0

    def test_signal_definitions_has_signals_list(self, client):
        data = client.get("/api/gtm/seed-data/signal_definitions").get_json()
        assert "signals" in data
        assert isinstance(data["signals"], list)
        assert len(data["signals"]) > 0

    def test_returns_404_for_unknown_type(self, client):
        resp = client.get("/api/gtm/seed-data/nonexistent_data")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# GET /api/gtm/scenarios/<scenario_id>/seed-text
# ---------------------------------------------------------------------------

class TestGetScenarioSeedText:
    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_returns_200_for_known_scenarios(self, client, scenario_id):
        resp = client.get(f"/api/gtm/scenarios/{scenario_id}/seed-text")
        assert resp.status_code == 200

    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_response_contains_seed_text(self, client, scenario_id):
        data = client.get(f"/api/gtm/scenarios/{scenario_id}/seed-text").get_json()
        assert "seed_text" in data
        assert isinstance(data["seed_text"], str)
        assert len(data["seed_text"]) > 0

    def test_seed_text_matches_full_scenario(self, client):
        """Seed-text endpoint should return the same text as the full scenario."""
        full = client.get("/api/gtm/scenarios/outbound_campaign").get_json()
        seed = client.get("/api/gtm/scenarios/outbound_campaign/seed-text").get_json()
        assert seed["seed_text"] == full["seed_text"]

    def test_returns_404_for_unknown_scenario(self, client):
        resp = client.get("/api/gtm/scenarios/nonexistent_scenario/seed-text")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# POST /api/gtm/simulate — input validation only
# (Full simulation requires external services; we just test guard clauses)
# ---------------------------------------------------------------------------

class TestSimulateValidation:
    def test_rejects_empty_body(self, client):
        resp = client.post("/api/gtm/simulate", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "seed_text" in data["error"]

    def test_rejects_blank_seed_text(self, client):
        resp = client.post("/api/gtm/simulate", json={"seed_text": "   "})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_rejects_missing_content_type(self, client):
        """Non-JSON content-type triggers a 415 caught as 500 by the endpoint."""
        resp = client.post("/api/gtm/simulate", data="not json")
        assert resp.status_code >= 400
        data = resp.get_json()
        assert data["success"] is False
