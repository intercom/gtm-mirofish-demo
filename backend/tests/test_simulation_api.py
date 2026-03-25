"""Integration tests for Simulation API endpoints."""


class TestSimulationLifecycle:
    def test_create_simulation(self, client):
        resp = client.post("/api/simulation/create")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"].startswith("demo-sim-")
        assert data["status"] == "created"

    def test_prepare_simulation(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        resp = client.post("/api/simulation/prepare", json={"simulation_id": sim_id})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "prepared"

    def test_prepare_without_body(self, client):
        client.post("/api/simulation/create")
        resp = client.post("/api/simulation/prepare", json={})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "prepared"

    def test_start_simulation(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        resp = client.post("/api/simulation/start", json={"simulation_id": sim_id})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "running"

    def test_start_resets_timer(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        client.post("/api/simulation/start", json={"simulation_id": sim_id})
        status = client.get(f"/api/simulation/{sim_id}/run-status").get_json()["data"]
        assert status["progress_percent"] < 50


class TestSimulationRunStatus:
    def test_run_status_fields(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        client.post("/api/simulation/start", json={"simulation_id": sim_id})
        resp = client.get(f"/api/simulation/{sim_id}/run-status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "runner_status" in data
        assert "progress_percent" in data
        assert "current_round" in data
        assert data["total_rounds"] == 144
        assert "twitter_actions_count" in data
        assert "reddit_actions_count" in data
        assert data["total_simulation_hours"] == 72

    def test_run_status_completes_after_skip(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        client.post("/api/simulation/start", json={"simulation_id": sim_id})
        client.post("/api/demo/skip/simulation")
        status = client.get(f"/api/simulation/{sim_id}/run-status").get_json()["data"]
        assert status["runner_status"] == "completed"
        assert status["progress_percent"] == 100
        assert status["twitter_completed"] is True
        assert status["reddit_completed"] is True

    def test_run_status_unknown_sim_auto_creates(self, client):
        resp = client.get("/api/simulation/unknown-sim/run-status")
        assert resp.status_code == 200


class TestSimulationDetail:
    def test_run_status_detail(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        client.post("/api/simulation/start", json={"simulation_id": sim_id})
        resp = client.get(f"/api/simulation/{sim_id}/run-status/detail")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "recent_actions" in data
        assert "all_actions" in data

    def test_actions_have_required_fields(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        client.post("/api/simulation/start", json={"simulation_id": sim_id})
        client.post("/api/demo/skip/simulation")
        data = client.get(f"/api/simulation/{sim_id}/run-status/detail").get_json()["data"]
        actions = data["recent_actions"]
        assert len(actions) > 0
        action = actions[0]
        assert "agent_name" in action
        assert "action_type" in action
        assert action["platform"] in ("twitter", "reddit")
        assert "round_num" in action
        assert "timestamp" in action


class TestSimulationTimeline:
    def test_timeline_returns_rounds(self, client):
        create = client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        client.post("/api/simulation/start", json={"simulation_id": sim_id})
        client.post("/api/demo/skip/simulation")
        resp = client.get(f"/api/simulation/{sim_id}/timeline")
        assert resp.status_code == 200
        timeline = resp.get_json()["data"]["timeline"]
        assert len(timeline) == 144
        entry = timeline[0]
        assert "round_num" in entry
        assert "twitter_actions" in entry
        assert "reddit_actions" in entry
        assert "total_actions" in entry


class TestSimulationGet:
    def test_sim_get(self, client):
        resp = client.get("/api/simulation/any-sim-id")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"] == "any-sim-id"
        assert "config" in data

    def test_sim_list(self, client):
        resp = client.get("/api/simulation/list")
        assert resp.status_code == 200

    def test_sim_history(self, client):
        resp = client.get("/api/simulation/history")
        assert resp.status_code == 200


class TestSimulationActions:
    def test_sim_actions(self, client):
        resp = client.get("/api/simulation/sim-1/actions")
        assert resp.status_code == 200
        actions = resp.get_json()["data"]["actions"]
        assert len(actions) > 0

    def test_sim_agent_stats(self, client):
        resp = client.get("/api/simulation/sim-1/agent-stats")
        assert resp.status_code == 200

    def test_sim_posts(self, client):
        resp = client.get("/api/simulation/sim-1/posts")
        assert resp.status_code == 200

    def test_sim_comments(self, client):
        resp = client.get("/api/simulation/sim-1/comments")
        assert resp.status_code == 200


class TestSimulationEntities:
    def test_entities_returns_graph_nodes(self, client):
        resp = client.get("/api/simulation/entities/graph-1")
        assert resp.status_code == 200
        entities = resp.get_json()["data"]["entities"]
        assert len(entities) == 55

    def test_entity_by_uuid(self, client):
        resp = client.get("/api/simulation/entities/graph-1/entity-1")
        assert resp.status_code == 200

    def test_entities_by_type(self, client):
        resp = client.get("/api/simulation/entities/graph-1/by-type/persona")
        assert resp.status_code == 200


class TestSimulationStubs:
    def test_prepare_status(self, client):
        resp = client.post("/api/simulation/prepare/status")
        assert resp.status_code == 200

    def test_stop(self, client):
        resp = client.post("/api/simulation/stop")
        assert resp.status_code == 200

    def test_profiles(self, client):
        resp = client.get("/api/simulation/sim-1/profiles")
        assert resp.status_code == 200

    def test_profiles_realtime(self, client):
        resp = client.get("/api/simulation/sim-1/profiles/realtime")
        assert resp.status_code == 200

    def test_config(self, client):
        resp = client.get("/api/simulation/sim-1/config")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["config"]["total_hours"] == 72

    def test_config_realtime(self, client):
        resp = client.get("/api/simulation/sim-1/config/realtime")
        assert resp.status_code == 200

    def test_config_download(self, client):
        resp = client.get("/api/simulation/sim-1/config/download")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("Content-Disposition", "")

    def test_script_download(self, client):
        resp = client.get("/api/simulation/script/test.py/download")
        assert resp.status_code == 200

    def test_generate_profiles(self, client):
        resp = client.post("/api/simulation/generate-profiles")
        assert resp.status_code == 200

    def test_env_status(self, client):
        resp = client.post("/api/simulation/env-status")
        assert resp.status_code == 200

    def test_close_env(self, client):
        resp = client.post("/api/simulation/close-env")
        assert resp.status_code == 200
