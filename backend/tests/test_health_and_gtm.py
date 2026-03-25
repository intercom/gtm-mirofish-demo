"""Integration tests for Health, GTM Scenarios, and Seed Data endpoints."""


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["mode"] == "demo"


class TestGTMScenarios:
    def test_list_scenarios(self, client):
        resp = client.get("/api/gtm/scenarios")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "scenarios" in data
        scenarios = data["scenarios"]
        assert len(scenarios) == 4
        ids = {s["id"] for s in scenarios}
        assert "outbound_campaign" in ids

    def test_get_scenario_by_id(self, client):
        resp = client.get("/api/gtm/scenarios/outbound_campaign")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == "outbound_campaign"
        assert "seed_text" in data
        assert "agent_config" in data

    def test_get_scenario_not_found(self, client):
        resp = client.get("/api/gtm/scenarios/nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_get_seed_text(self, client):
        resp = client.get("/api/gtm/scenarios/outbound_campaign/seed-text")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]["seed_text"]) > 0

    def test_get_seed_text_not_found(self, client):
        resp = client.get("/api/gtm/scenarios/nonexistent/seed-text")
        assert resp.status_code == 404


class TestSeedData:
    def test_get_companies(self, client):
        resp = client.get("/api/gtm/seed-data/companies")
        assert resp.status_code == 200
        data = resp.get_json()
        companies = data["data"]
        assert len(companies) == 5
        assert all("name" in c and "industry" in c for c in companies)

    def test_get_personas(self, client):
        resp = client.get("/api/gtm/seed-data/personas")
        assert resp.status_code == 200
        data = resp.get_json()
        personas = data["data"]
        assert len(personas) == 5
        assert all("name" in p and "title" in p for p in personas)

    def test_get_unknown_type_returns_empty(self, client):
        resp = client.get("/api/gtm/seed-data/unknown_type")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []
