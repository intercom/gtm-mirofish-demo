"""
Integration tests for GTM data endpoints that were previously uncovered.

Tests walkthrough, export, import, leaderboard, outcomes, context,
compare, and template endpoints — all exercised through Flask's test
client against real JSON fixture files and deterministic demo data.
"""

import json

import pytest

# ── Constants ──

PREFIX = "/api/v1/gtm"

KNOWN_SCENARIO_IDS = [
    "outbound_campaign",
    "personalization",
    "pricing_simulation",
    "signal_validation",
]

KNOWN_TEMPLATE_IDS = [
    "pipeline_review",
    "competitive_response",
    "product_launch_gtm",
    "churn_prevention",
    "budget_allocation",
    "mrr_reconciliation",
]


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/scenarios/<id>/walkthrough
# ---------------------------------------------------------------------------

class TestGetScenarioWalkthrough:
    def test_returns_200_for_known_scenario(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign/walkthrough")
        assert resp.status_code == 200

    def test_response_has_walkthrough_structure(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/walkthrough").get_json()
        assert data["scenario_id"] == "outbound_campaign"
        assert "scenario_name" in data
        assert data["total_steps"] == 5
        assert len(data["steps"]) == 5

    def test_steps_have_required_keys(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/walkthrough").get_json()
        for step in data["steps"]:
            assert "step" in step
            assert "key" in step
            assert "title" in step
            assert "description" in step
            assert "tip" in step

    def test_step_keys_ordered(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/walkthrough").get_json()
        keys = [s["key"] for s in data["steps"]]
        assert keys == [
            "overview",
            "seed_document",
            "agent_population",
            "simulation_config",
            "expected_outcomes",
        ]

    def test_seed_document_step_has_preview(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/walkthrough").get_json()
        seed_step = data["steps"][1]
        assert seed_step["key"] == "seed_document"
        assert "seed_text" in seed_step
        assert "seed_preview" in seed_step
        assert "word_count" in seed_step
        assert seed_step["word_count"] > 0

    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_returns_200_for_all_known_scenarios(self, client, scenario_id):
        resp = client.get(f"{PREFIX}/scenarios/{scenario_id}/walkthrough")
        assert resp.status_code == 200

    def test_returns_404_for_unknown_scenario(self, client):
        resp = client.get(f"{PREFIX}/scenarios/nonexistent/walkthrough")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/scenarios/<id>/export
# ---------------------------------------------------------------------------

class TestExportScenario:
    def test_returns_200_for_known_scenario(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign/export")
        assert resp.status_code == 200

    def test_content_disposition_header(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign/export")
        cd = resp.headers.get("Content-Disposition", "")
        assert "attachment" in cd
        assert "outbound_campaign.json" in cd

    def test_response_is_valid_json(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign/export")
        data = json.loads(resp.data)
        assert data["id"] == "outbound_campaign"
        assert "seed_text" in data
        assert "agent_config" in data

    def test_content_type_is_json(self, client):
        resp = client.get(f"{PREFIX}/scenarios/outbound_campaign/export")
        assert "application/json" in resp.content_type

    def test_returns_404_for_unknown_scenario(self, client):
        resp = client.get(f"{PREFIX}/scenarios/nonexistent/export")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# POST /api/v1/gtm/scenarios/import
# ---------------------------------------------------------------------------

class TestImportScenario:
    VALID_PAYLOAD = {
        "id": "test_import",
        "name": "Test Import Scenario",
        "seed_text": "Some seed text for testing import.",
        "agent_config": {"count": 10, "persona_types": ["Tester"]},
        "simulation_config": {"total_hours": 24, "minutes_per_round": 30},
    }

    def test_successful_import_returns_201(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path))
        resp = client.post(f"{PREFIX}/scenarios/import", json=self.VALID_PAYLOAD)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["scenario"]["id"] == "test_import"
        assert body["overwritten"] is False

    def test_overwrite_returns_200(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path))
        # First import
        client.post(f"{PREFIX}/scenarios/import", json=self.VALID_PAYLOAD)
        # Second import (overwrite)
        resp = client.post(f"{PREFIX}/scenarios/import", json=self.VALID_PAYLOAD)
        assert resp.status_code == 200
        assert resp.get_json()["overwritten"] is True

    def test_writes_file_to_disk(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path))
        client.post(f"{PREFIX}/scenarios/import", json=self.VALID_PAYLOAD)
        written = json.loads((tmp_path / "test_import.json").read_text())
        assert written["name"] == "Test Import Scenario"

    def test_rejects_empty_body(self, client):
        resp = client.post(f"{PREFIX}/scenarios/import", data="", content_type="application/json")
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_rejects_missing_required_fields(self, client):
        resp = client.post(f"{PREFIX}/scenarios/import", json={"id": "x", "name": "x"})
        assert resp.status_code == 400
        body = resp.get_json()
        assert "Missing required fields" in body["error"]

    def test_rejects_invalid_scenario_id(self, client):
        payload = {**self.VALID_PAYLOAD, "id": "INVALID ID!!"}
        resp = client.post(f"{PREFIX}/scenarios/import", json=payload)
        assert resp.status_code == 400
        assert "Invalid scenario id" in resp.get_json()["error"]

    @pytest.mark.parametrize("bad_id", ["", " ", "A", "has spaces", "has.dot", "../traversal"])
    def test_rejects_various_bad_ids(self, client, bad_id):
        payload = {**self.VALID_PAYLOAD, "id": bad_id}
        resp = client.post(f"{PREFIX}/scenarios/import", json=payload)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/v1/gtm/scenarios/leaderboard
# ---------------------------------------------------------------------------

class TestLeaderboard:
    def test_empty_body_returns_mock_data(self, client):
        resp = client.post(f"{PREFIX}/scenarios/leaderboard", json={})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]) == 8  # 8 mock scenario names

    def test_no_body_returns_mock_data(self, client):
        resp = client.post(
            f"{PREFIX}/scenarios/leaderboard",
            data="",
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]) > 0

    def test_mock_entries_are_ranked(self, client):
        body = client.post(f"{PREFIX}/scenarios/leaderboard", json={}).get_json()
        ranks = [e["rank"] for e in body["data"]]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_mock_entries_sorted_by_composite_desc(self, client):
        body = client.post(f"{PREFIX}/scenarios/leaderboard", json={}).get_json()
        composites = [e["scores"]["composite"] for e in body["data"]]
        assert composites == sorted(composites, reverse=True)

    def test_custom_runs_scored_and_ranked(self, client):
        runs = [
            {"id": "run-a", "totalActions": 500, "totalRounds": 100, "agentCount": 10},
            {"id": "run-b", "totalActions": 100, "totalRounds": 20, "agentCount": 5},
        ]
        body = client.post(f"{PREFIX}/scenarios/leaderboard", json={"runs": runs}).get_json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        for entry in body["data"]:
            assert "scores" in entry
            assert "rank" in entry
            scores = entry["scores"]
            for key in ("sentiment", "consensus", "decisionQuality", "composite"):
                assert key in scores
                assert 0 <= scores[key] <= 100

    def test_scoring_is_deterministic(self, client):
        runs = [{"id": "stable-run", "totalActions": 300, "totalRounds": 50, "agentCount": 8}]
        body1 = client.post(f"{PREFIX}/scenarios/leaderboard", json={"runs": runs}).get_json()
        body2 = client.post(f"{PREFIX}/scenarios/leaderboard", json={"runs": runs}).get_json()
        assert body1["data"][0]["scores"] == body2["data"][0]["scores"]


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/outcomes/<scenario_id>
# ---------------------------------------------------------------------------

class TestGetOutcomes:
    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_returns_200_for_known_scenarios(self, client, scenario_id):
        resp = client.get(f"{PREFIX}/outcomes/{scenario_id}")
        assert resp.status_code == 200

    def test_response_structure(self, client):
        data = client.get(f"{PREFIX}/outcomes/outbound_campaign").get_json()
        assert data["scenario_id"] == "outbound_campaign"
        assert "scenario_name" in data
        assert "decisions" in data
        assert isinstance(data["decisions"], list)
        assert len(data["decisions"]) > 0
        assert "totals" in data

    def test_decision_structure(self, client):
        data = client.get(f"{PREFIX}/outcomes/outbound_campaign").get_json()
        decision = data["decisions"][0]
        for key in ("id", "title", "category", "impact", "timeline", "roi", "confidence"):
            assert key in decision, f"Missing key: {key}"
        assert "pipeline_per_month" in decision["impact"]
        assert "cost_per_month" in decision["impact"]

    def test_totals_structure(self, client):
        data = client.get(f"{PREFIX}/outcomes/outbound_campaign").get_json()
        totals = data["totals"]
        for key in ("pipeline_per_month", "cost_per_month", "net_impact", "avg_roi"):
            assert key in totals, f"Missing totals key: {key}"
        assert totals["net_impact"] == totals["pipeline_per_month"] - totals["cost_per_month"]

    def test_unknown_scenario_returns_generic_outcomes(self, client):
        """Unknown scenario IDs fall back to 'general' category outcomes."""
        resp = client.get(f"{PREFIX}/outcomes/nonexistent")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["scenario_id"] == "nonexistent"
        assert len(data["decisions"]) > 0

    def test_different_categories_return_different_outcomes(self, client):
        outbound = client.get(f"{PREFIX}/outcomes/outbound_campaign").get_json()
        pricing = client.get(f"{PREFIX}/outcomes/pricing_simulation").get_json()
        assert outbound["scenario_name"] != pricing["scenario_name"]


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/scenarios/<id>/context
# ---------------------------------------------------------------------------

class TestGetScenarioContext:
    @pytest.mark.parametrize("scenario_id", KNOWN_SCENARIO_IDS)
    def test_returns_200_for_known_scenarios(self, client, scenario_id):
        resp = client.get(f"{PREFIX}/scenarios/{scenario_id}/context")
        assert resp.status_code == 200

    def test_response_structure(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/context").get_json()
        assert data["scenario_id"] == "outbound_campaign"
        assert "scenario_name" in data
        assert "sections" in data

    def test_sections_contain_expected_categories(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/context").get_json()
        sections = data["sections"]
        for section_key in ("revenue", "pipeline", "accounts", "campaigns"):
            assert section_key in sections, f"Missing section: {section_key}"
            section = sections[section_key]
            assert "label" in section
            assert "metrics" in section
            assert isinstance(section["metrics"], list)
            assert len(section["metrics"]) > 0

    def test_metric_item_structure(self, client):
        data = client.get(f"{PREFIX}/scenarios/outbound_campaign/context").get_json()
        metric = data["sections"]["revenue"]["metrics"][0]
        for key in ("key", "label", "value", "trend"):
            assert key in metric, f"Missing metric key: {key}"

    def test_returns_404_for_unknown_scenario(self, client):
        resp = client.get(f"{PREFIX}/scenarios/nonexistent/context")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/scenarios/compare
# ---------------------------------------------------------------------------

class TestCompareScenarios:
    def test_returns_200(self, client):
        resp = client.get(f"{PREFIX}/scenarios/compare")
        assert resp.status_code == 200

    def test_response_structure(self, client):
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        assert "scenarios" in data
        assert "dimensions" in data
        assert "matrix" in data

    def test_all_scenarios_included(self, client):
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        ids = {s["id"] for s in data["scenarios"]}
        for sid in KNOWN_SCENARIO_IDS:
            assert sid in ids

    def test_expected_dimensions(self, client):
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        expected = {"agent_count", "persona_count", "industry_count", "duration_hours", "expected_outputs"}
        assert set(data["dimensions"]) == expected

    def test_matrix_has_entry_per_scenario(self, client):
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        for sid in KNOWN_SCENARIO_IDS:
            assert sid in data["matrix"]

    def test_matrix_values_normalized_0_to_1(self, client):
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        for sid, dims in data["matrix"].items():
            for dim, val in dims.items():
                assert 0 <= val <= 1, f"{sid}.{dim} = {val} is out of [0,1]"

    def test_at_least_one_dimension_has_max_1(self, client):
        """Normalization divides by max, so the highest value in each dimension should be 1.0."""
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        for dim in data["dimensions"]:
            max_val = max(data["matrix"][sid][dim] for sid in data["matrix"])
            assert max_val == 1.0, f"Dimension {dim} max is {max_val}, expected 1.0"

    def test_empty_when_dir_missing(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.api.gtm_scenarios.SCENARIOS_DIR", str(tmp_path / "empty"))
        data = client.get(f"{PREFIX}/scenarios/compare").get_json()
        assert data["scenarios"] == []
        assert data["matrix"] == {}


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/templates
# ---------------------------------------------------------------------------

class TestListTemplates:
    def test_returns_200(self, client):
        resp = client.get(f"{PREFIX}/templates")
        assert resp.status_code == 200

    def test_response_has_templates_key(self, client):
        data = client.get(f"{PREFIX}/templates").get_json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

    def test_returns_known_templates(self, client):
        data = client.get(f"{PREFIX}/templates").get_json()
        ids = {t["id"] for t in data["templates"]}
        for tid in KNOWN_TEMPLATE_IDS:
            assert tid in ids, f"Missing template: {tid}"

    def test_template_summary_fields(self, client):
        data = client.get(f"{PREFIX}/templates").get_json()
        for t in data["templates"]:
            assert "id" in t
            assert "name" in t
            assert "description" in t


# ---------------------------------------------------------------------------
# GET /api/v1/gtm/templates/<template_id>
# ---------------------------------------------------------------------------

class TestGetTemplate:
    @pytest.mark.parametrize("template_id", KNOWN_TEMPLATE_IDS)
    def test_returns_200_for_known_templates(self, client, template_id):
        resp = client.get(f"{PREFIX}/templates/{template_id}")
        assert resp.status_code == 200

    def test_full_template_has_required_fields(self, client):
        data = client.get(f"{PREFIX}/templates/pipeline_review").get_json()
        for key in ("id", "name", "description", "environment_type", "num_rounds", "agent_configs"):
            assert key in data, f"Missing key: {key}"

    def test_agent_configs_structure(self, client):
        data = client.get(f"{PREFIX}/templates/pipeline_review").get_json()
        assert isinstance(data["agent_configs"], list)
        assert len(data["agent_configs"]) > 0
        agent = data["agent_configs"][0]
        assert "role" in agent
        assert "persona" in agent

    def test_returns_404_for_unknown_template(self, client):
        resp = client.get(f"{PREFIX}/templates/nonexistent_template")
        assert resp.status_code == 404
        assert "error" in resp.get_json()
