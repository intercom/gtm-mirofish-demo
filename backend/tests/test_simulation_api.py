"""
API integration tests for simulation endpoints.

Uses Flask test client with mocked external services (Zep, LLM, OASIS)
to verify request validation, response structure, and endpoint behaviour.
"""

import json
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest


# ============================================================
# 1. Simulation Lifecycle: create / get / list / history
# ============================================================

class TestCreateSimulation:
    """POST /api/simulation/create"""

    def test_create_success(self, client, make_project):
        make_project()
        resp = client.post("/api/v1/simulation/create", json={
            "project_id": "proj_test123",
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        data = body["data"]
        assert data["project_id"] == "proj_test123"
        assert data["graph_id"] == "mirofish_test"
        assert data["status"] == "created"
        assert "simulation_id" in data

    def test_create_missing_project_id(self, client):
        resp = client.post("/api/v1/simulation/create", json={})
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_create_project_not_found(self, client):
        resp = client.post("/api/v1/simulation/create", json={
            "project_id": "proj_nonexistent",
        })
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_create_no_graph_id(self, client, make_project):
        make_project(graph_id=None)
        resp = client.post("/api/v1/simulation/create", json={
            "project_id": "proj_test123",
        })
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_create_with_platform_flags(self, client, make_project):
        make_project()
        resp = client.post("/api/v1/simulation/create", json={
            "project_id": "proj_test123",
            "enable_twitter": False,
            "enable_reddit": True,
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["enable_twitter"] is False
        assert data["enable_reddit"] is True


class TestGetSimulation:
    """GET /api/simulation/<simulation_id>"""

    def test_get_existing(self, client, make_simulation):
        make_simulation()
        resp = client.get("/api/v1/simulation/sim_test123")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"] == "sim_test123"
        assert data["status"] == "created"

    def test_get_nonexistent(self, client):
        resp = client.get("/api/v1/simulation/sim_nope")
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_get_ready_includes_run_instructions(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation()
        resp = client.get("/api/v1/simulation/sim_ready")
        assert resp.status_code == 200


class TestListSimulations:
    """GET /api/simulation/list"""

    def test_list_empty(self, client):
        resp = client.get("/api/v1/simulation/list")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["pagination"]["total"] == 0

    def test_list_returns_created(self, client, make_simulation):
        make_simulation(simulation_id="sim_a")
        make_simulation(simulation_id="sim_b")
        resp = client.get("/api/v1/simulation/list")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["pagination"]["total"] == 2

    def test_list_filter_by_project(self, client, make_simulation):
        make_simulation(simulation_id="sim_a", project_id="proj_1")
        make_simulation(simulation_id="sim_b", project_id="proj_2")
        resp = client.get("/api/v1/simulation/list?project_id=proj_1")
        body = resp.get_json()
        assert body["pagination"]["total"] == 1
        assert body["data"][0]["project_id"] == "proj_1"


class TestSimulationHistory:
    """GET /api/simulation/history"""

    def test_history_empty(self, client):
        resp = client.get("/api/v1/simulation/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 0

    def test_history_enriched_fields(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation()
        resp = client.get("/api/v1/simulation/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["count"] >= 1
        item = body["data"][0]
        assert "version" in item
        assert "created_date" in item

    def test_history_limit(self, client, make_simulation):
        for i in range(5):
            make_simulation(simulation_id=f"sim_{i}")
        resp = client.get("/api/v1/simulation/history?limit=2")
        body = resp.get_json()
        assert len(body["data"]) <= 2


# ============================================================
# 2. Simulation Preparation: prepare / prepare/status
# ============================================================

class TestPrepareSimulation:
    """POST /api/simulation/prepare"""

    def test_prepare_missing_simulation_id(self, client):
        resp = client.post("/api/v1/simulation/prepare", json={})
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_prepare_nonexistent_simulation(self, client):
        resp = client.post("/api/v1/simulation/prepare", json={
            "simulation_id": "sim_nope",
        })
        assert resp.status_code == 404

    def test_prepare_already_ready(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_prep")
        resp = client.post("/api/v1/simulation/prepare", json={
            "simulation_id": "sim_prep",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["already_prepared"] is True
        assert data["status"] == "ready"

    @patch("app.api.simulation.ZepEntityReader")
    def test_prepare_missing_requirement(self, mock_reader, client,
                                         make_simulation, make_project):
        make_project(simulation_requirement=None)
        make_simulation()
        resp = client.post("/api/v1/simulation/prepare", json={
            "simulation_id": "sim_test123",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.ZepEntityReader")
    def test_prepare_starts_task(self, mock_reader, client,
                                 make_simulation, make_project):
        make_project()
        make_simulation()

        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.filtered_count = 5
        mock_result.entity_types = {"Student"}
        mock_instance.filter_defined_entities.return_value = mock_result
        mock_reader.return_value = mock_instance

        resp = client.post("/api/v1/simulation/prepare", json={
            "simulation_id": "sim_test123",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["already_prepared"] is False
        assert "task_id" in data
        assert data["status"] == "preparing"


class TestPrepareStatus:
    """POST /api/simulation/prepare/status"""

    def test_status_missing_ids(self, client):
        resp = client.post("/api/v1/simulation/prepare/status", json={})
        assert resp.status_code == 400

    def test_status_by_simulation_id_ready(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_s")
        resp = client.post("/api/v1/simulation/prepare/status", json={
            "simulation_id": "sim_s",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["already_prepared"] is True
        assert data["progress"] == 100

    def test_status_simulation_not_started(self, client, make_simulation):
        make_simulation(simulation_id="sim_ns")
        resp = client.post("/api/v1/simulation/prepare/status", json={
            "simulation_id": "sim_ns",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "not_started"

    def test_status_task_not_found(self, client):
        resp = client.post("/api/v1/simulation/prepare/status", json={
            "task_id": "nonexistent_task",
        })
        assert resp.status_code == 404


# ============================================================
# 3. Simulation Execution: start / stop / run-status
# ============================================================

class TestStartSimulation:
    """POST /api/simulation/start"""

    def test_start_missing_simulation_id(self, client):
        resp = client.post("/api/v1/simulation/start", json={})
        assert resp.status_code == 400

    def test_start_nonexistent(self, client):
        resp = client.post("/api/v1/simulation/start", json={
            "simulation_id": "sim_nope",
        })
        assert resp.status_code == 404

    def test_start_not_ready(self, client, make_simulation):
        make_simulation(simulation_id="sim_nr", status="created")
        resp = client.post("/api/v1/simulation/start", json={
            "simulation_id": "sim_nr",
        })
        assert resp.status_code == 400
        assert "未准备好" in resp.get_json()["error"]

    def test_start_invalid_platform(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_ip")
        resp = client.post("/api/v1/simulation/start", json={
            "simulation_id": "sim_ip",
            "platform": "facebook",
        })
        assert resp.status_code == 400

    def test_start_invalid_max_rounds(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_mr")
        resp = client.post("/api/v1/simulation/start", json={
            "simulation_id": "sim_mr",
            "max_rounds": -5,
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_start_success(self, mock_runner_cls, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_go")

        mock_run_state = MagicMock()
        mock_run_state.to_dict.return_value = {
            "simulation_id": "sim_go",
            "runner_status": "running",
            "process_pid": 1234,
        }
        mock_runner_cls.start_simulation.return_value = mock_run_state
        mock_runner_cls.get_run_state.return_value = None

        resp = client.post("/api/v1/simulation/start", json={
            "simulation_id": "sim_go",
            "platform": "parallel",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["runner_status"] == "running"


class TestStopSimulation:
    """POST /api/simulation/stop"""

    def test_stop_missing_id(self, client):
        resp = client.post("/api/v1/simulation/stop", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_stop_success(self, mock_runner_cls, client, make_simulation):
        make_simulation(simulation_id="sim_stop", status="running")
        mock_run_state = MagicMock()
        mock_run_state.to_dict.return_value = {
            "simulation_id": "sim_stop",
            "runner_status": "stopped",
        }
        mock_runner_cls.stop_simulation.return_value = mock_run_state

        resp = client.post("/api/v1/simulation/stop", json={
            "simulation_id": "sim_stop",
        })
        assert resp.status_code == 200
        assert resp.get_json()["data"]["runner_status"] == "stopped"

    @patch("app.api.simulation.SimulationRunner")
    def test_stop_not_running(self, mock_runner_cls, client):
        mock_runner_cls.stop_simulation.side_effect = ValueError("Not running")
        resp = client.post("/api/v1/simulation/stop", json={
            "simulation_id": "sim_idle",
        })
        assert resp.status_code == 400


class TestRunStatus:
    """GET /api/simulation/<id>/run-status"""

    @patch("app.api.simulation.SimulationRunner")
    def test_run_status_idle(self, mock_runner_cls, client):
        mock_runner_cls.get_run_state.return_value = None
        resp = client.get("/api/v1/simulation/sim_x/run-status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["runner_status"] == "idle"
        assert data["current_round"] == 0

    @patch("app.api.simulation.SimulationRunner")
    def test_run_status_running(self, mock_runner_cls, client):
        mock_state = MagicMock()
        mock_state.to_dict.return_value = {
            "simulation_id": "sim_x",
            "runner_status": "running",
            "current_round": 5,
            "total_rounds": 100,
        }
        mock_runner_cls.get_run_state.return_value = mock_state
        resp = client.get("/api/v1/simulation/sim_x/run-status")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_round"] == 5


class TestRunStatusDetail:
    """GET /api/simulation/<id>/run-status/detail"""

    @patch("app.api.simulation.SimulationRunner")
    def test_detail_idle(self, mock_runner_cls, client):
        mock_runner_cls.get_run_state.return_value = None
        resp = client.get("/api/v1/simulation/sim_x/run-status/detail")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["runner_status"] == "idle"
        assert data["all_actions"] == []


# ============================================================
# 4. Profiles, Config, Actions, Timeline, Posts, Comments
# ============================================================

class TestProfiles:
    """GET /api/simulation/<id>/profiles"""

    def test_profiles_nonexistent(self, client):
        resp = client.get("/api/v1/simulation/sim_nope/profiles")
        assert resp.status_code == 404

    def test_profiles_reddit(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_p")
        resp = client.get("/api/v1/simulation/sim_p/profiles?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["platform"] == "reddit"
        assert data["count"] >= 1


class TestProfilesRealtime:
    """GET /api/simulation/<id>/profiles/realtime"""

    def test_realtime_nonexistent(self, client):
        resp = client.get("/api/v1/simulation/sim_nope/profiles/realtime")
        assert resp.status_code == 404

    def test_realtime_exists(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_rt")
        resp = client.get("/api/v1/simulation/sim_rt/profiles/realtime?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["file_exists"] is True
        assert data["count"] >= 1
        assert data["is_generating"] is False


class TestConfig:
    """GET /api/simulation/<id>/config"""

    def test_config_not_found(self, client, make_simulation):
        make_simulation(simulation_id="sim_nc")
        resp = client.get("/api/v1/simulation/sim_nc/config")
        assert resp.status_code == 404

    def test_config_success(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_c")
        resp = client.get("/api/v1/simulation/sim_c/config")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "time_config" in data


class TestConfigRealtime:
    """GET /api/simulation/<id>/config/realtime"""

    def test_config_realtime(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_cr")
        resp = client.get("/api/v1/simulation/sim_cr/config/realtime")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["file_exists"] is True
        assert data["config"] is not None
        assert "summary" in data


class TestConfigDownload:
    """GET /api/simulation/<id>/config/download"""

    def test_download_not_found(self, client, make_simulation):
        make_simulation(simulation_id="sim_dl")
        resp = client.get("/api/v1/simulation/sim_dl/config/download")
        assert resp.status_code == 404

    def test_download_success(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_dl2")
        resp = client.get("/api/v1/simulation/sim_dl2/config/download")
        assert resp.status_code == 200
        assert resp.content_type in ("application/json", "application/octet-stream")


class TestActions:
    """GET /api/simulation/<id>/actions"""

    @patch("app.api.simulation.SimulationRunner")
    def test_actions_empty(self, mock_runner_cls, client):
        mock_runner_cls.get_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/actions")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 0
        assert data["actions"] == []

    @patch("app.api.simulation.SimulationRunner")
    def test_actions_with_filters(self, mock_runner_cls, client):
        mock_action = MagicMock()
        mock_action.to_dict.return_value = {
            "round_num": 1,
            "platform": "twitter",
            "agent_id": 0,
            "action_type": "CREATE_POST",
        }
        mock_runner_cls.get_actions.return_value = [mock_action]
        resp = client.get(
            "/api/v1/simulation/sim_x/actions?platform=twitter&limit=10&offset=0"
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1


class TestTimeline:
    """GET /api/simulation/<id>/timeline"""

    @patch("app.api.simulation.SimulationRunner")
    def test_timeline_empty(self, mock_runner_cls, client):
        mock_runner_cls.get_timeline.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/timeline")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["rounds_count"] == 0

    @patch("app.api.simulation.SimulationRunner")
    def test_timeline_with_range(self, mock_runner_cls, client):
        mock_runner_cls.get_timeline.return_value = [{"round": 2}, {"round": 3}]
        resp = client.get("/api/v1/simulation/sim_x/timeline?start_round=2&end_round=3")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["rounds_count"] == 2


class TestAgentStats:
    """GET /api/simulation/<id>/agent-stats"""

    @patch("app.api.simulation.SimulationRunner")
    def test_agent_stats(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_stats.return_value = [
            {"agent_id": 0, "total_actions": 10},
        ]
        resp = client.get("/api/v1/simulation/sim_x/agent-stats")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["agents_count"] == 1


def _sim_dir_for_endpoint(tmp_uploads):
    """Return a patcher that redirects the posts/comments endpoint's hardcoded
    ``os.path.dirname(__file__) + '../../uploads/simulations'`` to our tmp dir.

    The endpoints compute sim_dir via os.path.join(os.path.dirname(__file__), '../../uploads/simulations/...')
    We redirect os.path.dirname inside the simulation module to a fake directory
    that, after applying the ../../ traversal, resolves to tmp_uploads.
    """
    import os
    # os.path.dirname(__file__) → .../app/api
    # Then ../../uploads/simulations → .../uploads/simulations
    # We want the result to be tmp_uploads/simulations/<id>
    # So we fake dirname to return tmp_uploads / "x" / "y"
    # then ../../uploads/simulations resolves to tmp_uploads/uploads/simulations — wrong
    #
    # Simpler: just patch os.path.join in the simulation module.
    real_join = os.path.join
    real_dirname = os.path.dirname

    # The endpoint calls: os.path.join(os.path.dirname(__file__), f'../../uploads/simulations/{sim_id}')
    # We intercept os.path.join specifically for the uploads/simulations pattern.
    def patched_join(*args):
        result = real_join(*args)
        if "../../uploads/simulations/" in str(args):
            # Replace the backend-relative path with tmp_uploads
            sim_id = args[-1].split("/")[-1]
            return real_join(str(tmp_uploads), "simulations", sim_id)
        return result

    return patch("app.api.simulation.os.path.join", side_effect=patched_join)


class TestPosts:
    """GET /api/simulation/<id>/posts"""

    def test_posts_no_db(self, client, make_simulation):
        make_simulation(simulation_id="sim_posts")
        resp = client.get("/api/v1/simulation/sim_posts/posts?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 0

    def test_posts_from_db(self, client, make_simulation, tmp_uploads):
        make_simulation(simulation_id="sim_db")
        db_path = tmp_uploads / "simulations" / "sim_db" / "reddit_simulation.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE post (
                id INTEGER PRIMARY KEY,
                content TEXT,
                created_at TEXT,
                user_id INTEGER
            )
        """)
        conn.execute(
            "INSERT INTO post (content, created_at, user_id) VALUES (?, ?, ?)",
            ("Hello world", datetime.now().isoformat(), 0),
        )
        conn.commit()
        conn.close()

        with _sim_dir_for_endpoint(tmp_uploads):
            resp = client.get("/api/v1/simulation/sim_db/posts?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total"] == 1
        assert data["count"] == 1
        assert data["posts"][0]["content"] == "Hello world"


class TestComments:
    """GET /api/simulation/<id>/comments"""

    def test_comments_no_db(self, client, make_simulation):
        make_simulation(simulation_id="sim_com")
        resp = client.get("/api/v1/simulation/sim_com/comments")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["count"] == 0

    def test_comments_from_db(self, client, make_simulation, tmp_uploads):
        make_simulation(simulation_id="sim_com2")
        db_path = tmp_uploads / "simulations" / "sim_com2" / "reddit_simulation.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE comment (
                id INTEGER PRIMARY KEY,
                post_id INTEGER,
                content TEXT,
                created_at TEXT
            )
        """)
        conn.execute(
            "INSERT INTO comment (post_id, content, created_at) VALUES (?, ?, ?)",
            (1, "Nice post", datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        with _sim_dir_for_endpoint(tmp_uploads):
            resp = client.get("/api/v1/simulation/sim_com2/comments")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1

    def test_comments_filter_by_post_id(self, client, make_simulation, tmp_uploads):
        make_simulation(simulation_id="sim_com3")
        db_path = tmp_uploads / "simulations" / "sim_com3" / "reddit_simulation.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE comment (
                id INTEGER PRIMARY KEY,
                post_id INTEGER,
                content TEXT,
                created_at TEXT
            )
        """)
        conn.execute(
            "INSERT INTO comment (post_id, content, created_at) VALUES (?, ?, ?)",
            (1, "Comment A", datetime.now().isoformat()),
        )
        conn.execute(
            "INSERT INTO comment (post_id, content, created_at) VALUES (?, ?, ?)",
            (2, "Comment B", datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        with _sim_dir_for_endpoint(tmp_uploads):
            resp = client.get("/api/v1/simulation/sim_com3/comments?post_id=1")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1


# ============================================================
# 5. Entity Endpoints
# ============================================================

class TestEntities:
    """GET /api/simulation/entities/<graph_id>"""

    @patch("app.api.simulation.ZepEntityReader")
    def test_entities_success(self, mock_reader_cls, client):
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "filtered_count": 3,
            "entity_types": ["Student"],
            "entities": [],
        }
        mock_instance.filter_defined_entities.return_value = mock_result
        mock_reader_cls.return_value = mock_instance

        resp = client.get("/api/v1/simulation/entities/graph_123")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["filtered_count"] == 3

    @patch("app.api.simulation.Config")
    def test_entities_no_zep_key(self, mock_config, client):
        mock_config.ZEP_API_KEY = None
        resp = client.get("/api/v1/simulation/entities/graph_123")
        assert resp.status_code == 500


class TestEntityDetail:
    """GET /api/simulation/entities/<graph_id>/<entity_uuid>"""

    @patch("app.api.simulation.ZepEntityReader")
    def test_entity_found(self, mock_reader_cls, client):
        mock_instance = MagicMock()
        mock_entity = MagicMock()
        mock_entity.to_dict.return_value = {"uuid": "abc", "name": "Student A"}
        mock_instance.get_entity_with_context.return_value = mock_entity
        mock_reader_cls.return_value = mock_instance

        resp = client.get("/api/v1/simulation/entities/graph_1/abc")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["uuid"] == "abc"

    @patch("app.api.simulation.ZepEntityReader")
    def test_entity_not_found(self, mock_reader_cls, client):
        mock_instance = MagicMock()
        mock_instance.get_entity_with_context.return_value = None
        mock_reader_cls.return_value = mock_instance

        resp = client.get("/api/v1/simulation/entities/graph_1/missing")
        assert resp.status_code == 404


class TestEntitiesByType:
    """GET /api/simulation/entities/<graph_id>/by-type/<entity_type>"""

    @patch("app.api.simulation.ZepEntityReader")
    def test_by_type(self, mock_reader_cls, client):
        mock_instance = MagicMock()
        mock_entity = MagicMock()
        mock_entity.to_dict.return_value = {"name": "A"}
        mock_instance.get_entities_by_type.return_value = [mock_entity]
        mock_reader_cls.return_value = mock_instance

        resp = client.get("/api/v1/simulation/entities/graph_1/by-type/Student")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["entity_type"] == "Student"
        assert data["count"] == 1


# ============================================================
# 6. Interview Endpoints
# ============================================================

class TestInterview:
    """POST /api/simulation/interview"""

    def test_interview_missing_fields(self, client):
        resp = client.post("/api/v1/simulation/interview", json={})
        assert resp.status_code == 400

        resp = client.post("/api/v1/simulation/interview", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 400

        resp = client.post("/api/v1/simulation/interview", json={
            "simulation_id": "sim_x",
            "agent_id": 0,
        })
        assert resp.status_code == 400

    def test_interview_invalid_platform(self, client):
        resp = client.post("/api/v1/simulation/interview", json={
            "simulation_id": "sim_x",
            "agent_id": 0,
            "prompt": "test",
            "platform": "facebook",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_interview_env_not_running(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        resp = client.post("/api/v1/simulation/interview", json={
            "simulation_id": "sim_x",
            "agent_id": 0,
            "prompt": "How do you feel?",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_interview_success(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = True
        mock_runner_cls.interview_agent.return_value = {
            "success": True,
            "agent_id": 0,
            "response": "I think...",
        }
        resp = client.post("/api/v1/simulation/interview", json={
            "simulation_id": "sim_x",
            "agent_id": 0,
            "prompt": "How do you feel?",
            "platform": "twitter",
        })
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


class TestInterviewBatch:
    """POST /api/simulation/interview/batch"""

    def test_batch_missing_interviews(self, client):
        resp = client.post("/api/v1/simulation/interview/batch", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 400

    def test_batch_invalid_item(self, client):
        resp = client.post("/api/v1/simulation/interview/batch", json={
            "simulation_id": "sim_x",
            "interviews": [{"prompt": "hi"}],
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_batch_env_not_running(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        resp = client.post("/api/v1/simulation/interview/batch", json={
            "simulation_id": "sim_x",
            "interviews": [{"agent_id": 0, "prompt": "hi"}],
        })
        assert resp.status_code == 400


class TestInterviewAll:
    """POST /api/simulation/interview/all"""

    def test_all_missing_prompt(self, client):
        resp = client.post("/api/v1/simulation/interview/all", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_all_env_not_running(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        resp = client.post("/api/v1/simulation/interview/all", json={
            "simulation_id": "sim_x",
            "prompt": "test",
        })
        assert resp.status_code == 400


class TestInterviewHistory:
    """POST /api/simulation/interview/history"""

    def test_history_missing_id(self, client):
        resp = client.post("/api/v1/simulation/interview/history", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_history_success(self, mock_runner_cls, client):
        mock_runner_cls.get_interview_history.return_value = [
            {"agent_id": 0, "response": "test"},
        ]
        resp = client.post("/api/v1/simulation/interview/history", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1


# ============================================================
# 7. Environment Status & Script Download
# ============================================================

class TestEnvStatus:
    """POST /api/simulation/env-status"""

    def test_env_status_missing_id(self, client):
        resp = client.post("/api/v1/simulation/env-status", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_env_status_alive(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = True
        mock_runner_cls.get_env_status_detail.return_value = {
            "twitter_available": True,
            "reddit_available": True,
        }
        resp = client.post("/api/v1/simulation/env-status", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["env_alive"] is True

    @patch("app.api.simulation.SimulationRunner")
    def test_env_status_dead(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        mock_runner_cls.get_env_status_detail.return_value = {
            "twitter_available": False,
            "reddit_available": False,
        }
        resp = client.post("/api/v1/simulation/env-status", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 200
        assert resp.get_json()["data"]["env_alive"] is False


class TestCloseEnv:
    """POST /api/simulation/close-env"""

    def test_close_missing_id(self, client):
        resp = client.post("/api/v1/simulation/close-env", json={})
        assert resp.status_code == 400


class TestScriptDownload:
    """GET /api/simulation/script/<name>/download"""

    def test_invalid_script_name(self, client):
        resp = client.get("/api/v1/simulation/script/evil.py/download")
        assert resp.status_code == 400

    def test_script_not_found(self, client):
        resp = client.get(
            "/api/v1/simulation/script/run_twitter_simulation.py/download"
        )
        # 404 if the file doesn't exist on disk
        assert resp.status_code in (200, 404)


class TestGenerateProfiles:
    """POST /api/simulation/generate-profiles"""

    def test_missing_graph_id(self, client):
        resp = client.post("/api/v1/simulation/generate-profiles", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.OasisProfileGenerator")
    @patch("app.api.simulation.ZepEntityReader")
    def test_no_entities(self, mock_reader_cls, mock_gen_cls, client):
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.filtered_count = 0
        mock_instance.filter_defined_entities.return_value = mock_result
        mock_reader_cls.return_value = mock_instance

        resp = client.post("/api/v1/simulation/generate-profiles", json={
            "graph_id": "graph_test",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.OasisProfileGenerator")
    @patch("app.api.simulation.ZepEntityReader")
    def test_generate_success(self, mock_reader_cls, mock_gen_cls, client):
        mock_reader = MagicMock()
        mock_result = MagicMock()
        mock_result.filtered_count = 2
        mock_result.entities = [MagicMock(), MagicMock()]
        mock_result.entity_types = {"Student"}
        mock_reader.filter_defined_entities.return_value = mock_result
        mock_reader_cls.return_value = mock_reader

        mock_profile = MagicMock()
        mock_profile.to_reddit_format.return_value = {"username": "agent_0"}
        mock_gen = MagicMock()
        mock_gen.generate_profiles_from_entities.return_value = [mock_profile]
        mock_gen_cls.return_value = mock_gen

        resp = client.post("/api/v1/simulation/generate-profiles", json={
            "graph_id": "graph_test",
            "platform": "reddit",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1
        assert data["platform"] == "reddit"


# ============================================================
# Demo App Simulation Tests
# ============================================================

class TestDemoSimulationLifecycle:
    def test_create_simulation(self, demo_client):
        resp = demo_client.post("/api/simulation/create")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"].startswith("demo-sim-")
        assert data["status"] == "created"

    def test_prepare_simulation(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        resp = demo_client.post("/api/simulation/prepare", json={"simulation_id": sim_id})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "prepared"

    def test_prepare_without_body(self, demo_client):
        demo_client.post("/api/simulation/create")
        resp = demo_client.post("/api/simulation/prepare", json={})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "prepared"

    def test_start_simulation(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        resp = demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "running"

    def test_start_resets_timer(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        status = demo_client.get(f"/api/simulation/{sim_id}/run-status").get_json()["data"]
        assert status["progress_percent"] < 50


class TestDemoSimulationRunStatus:
    def test_run_status_fields(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        resp = demo_client.get(f"/api/simulation/{sim_id}/run-status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "runner_status" in data
        assert "progress_percent" in data
        assert "current_round" in data
        assert data["total_rounds"] == 144
        assert "twitter_actions_count" in data
        assert "reddit_actions_count" in data
        assert data["total_simulation_hours"] == 72

    def test_run_status_completes_after_skip(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        demo_client.post("/api/demo/skip/simulation")
        status = demo_client.get(f"/api/simulation/{sim_id}/run-status").get_json()["data"]
        assert status["runner_status"] == "completed"
        assert status["progress_percent"] == 100
        assert status["twitter_completed"] is True
        assert status["reddit_completed"] is True

    def test_run_status_unknown_sim_auto_creates(self, demo_client):
        resp = demo_client.get("/api/simulation/unknown-sim/run-status")
        assert resp.status_code == 200


class TestDemoSimulationDetail:
    def test_run_status_detail(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        resp = demo_client.get(f"/api/simulation/{sim_id}/run-status/detail")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "recent_actions" in data
        assert "all_actions" in data

    def test_actions_have_required_fields(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        demo_client.post("/api/demo/skip/simulation")
        data = demo_client.get(f"/api/simulation/{sim_id}/run-status/detail").get_json()["data"]
        actions = data["recent_actions"]
        assert len(actions) > 0
        action = actions[0]
        assert "agent_name" in action
        assert "action_type" in action
        assert action["platform"] in ("twitter", "reddit")
        assert "round_num" in action
        assert "timestamp" in action


class TestDemoSimulationTimeline:
    def test_timeline_returns_rounds(self, demo_client):
        create = demo_client.post("/api/simulation/create").get_json()["data"]
        sim_id = create["simulation_id"]
        demo_client.post("/api/simulation/start", json={"simulation_id": sim_id})
        demo_client.post("/api/demo/skip/simulation")
        resp = demo_client.get(f"/api/simulation/{sim_id}/timeline")
        assert resp.status_code == 200
        timeline = resp.get_json()["data"]["timeline"]
        assert len(timeline) == 144
        entry = timeline[0]
        assert "round_num" in entry
        assert "twitter_actions" in entry
        assert "reddit_actions" in entry
        assert "total_actions" in entry


class TestDemoSimulationGet:
    def test_sim_get(self, demo_client):
        resp = demo_client.get("/api/simulation/any-sim-id")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"] == "any-sim-id"
        assert "config" in data

    def test_sim_list(self, demo_client):
        resp = demo_client.get("/api/simulation/list")
        assert resp.status_code == 200

    def test_sim_history(self, demo_client):
        resp = demo_client.get("/api/simulation/history")
        assert resp.status_code == 200


class TestDemoSimulationActions:
    def test_sim_actions(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/actions")
        assert resp.status_code == 200
        actions = resp.get_json()["data"]["actions"]
        assert len(actions) > 0

    def test_sim_agent_stats(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/agent-stats")
        assert resp.status_code == 200

    def test_sim_posts(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/posts")
        assert resp.status_code == 200

    def test_sim_comments(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/comments")
        assert resp.status_code == 200


class TestDemoSimulationEntities:
    def test_entities_returns_graph_nodes(self, demo_client):
        resp = demo_client.get("/api/simulation/entities/graph-1")
        assert resp.status_code == 200
        entities = resp.get_json()["data"]["entities"]
        assert len(entities) == 55

    def test_entity_by_uuid(self, demo_client):
        resp = demo_client.get("/api/simulation/entities/graph-1/entity-1")
        assert resp.status_code == 200

    def test_entities_by_type(self, demo_client):
        resp = demo_client.get("/api/simulation/entities/graph-1/by-type/persona")
        assert resp.status_code == 200


class TestDemoSimulationStubs:
    def test_prepare_status(self, demo_client):
        resp = demo_client.post("/api/simulation/prepare/status")
        assert resp.status_code == 200

    def test_stop(self, demo_client):
        resp = demo_client.post("/api/simulation/stop")
        assert resp.status_code == 200

    def test_profiles(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/profiles")
        assert resp.status_code == 200

    def test_profiles_realtime(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/profiles/realtime")
        assert resp.status_code == 200

    def test_config(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/config")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["config"]["total_hours"] == 72

    def test_config_realtime(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/config/realtime")
        assert resp.status_code == 200

    def test_config_download(self, demo_client):
        resp = demo_client.get("/api/simulation/sim-1/config/download")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("Content-Disposition", "")

    def test_script_download(self, demo_client):
        resp = demo_client.get("/api/simulation/script/test.py/download")
        assert resp.status_code == 200

    def test_generate_profiles(self, demo_client):
        resp = demo_client.post("/api/simulation/generate-profiles")
        assert resp.status_code == 200

    def test_env_status(self, demo_client):
        resp = demo_client.post("/api/simulation/env-status")
        assert resp.status_code == 200

    def test_close_env(self, demo_client):
        resp = demo_client.post("/api/simulation/close-env")
        assert resp.status_code == 200


# ============================================================
# 8. Pause / Resume (SimulationRegistry-based)
# ============================================================

class TestPauseSimulation:
    """POST /api/simulation/<id>/pause"""

    @patch("app.api.simulation.SimulationRegistry")
    def test_pause_not_in_registry(self, mock_registry, client):
        mock_registry.get.return_value = None
        resp = client.post("/api/v1/simulation/sim_x/pause")
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    @patch("app.api.simulation.SimulationManager")
    @patch("app.api.simulation.SimulationRegistry")
    def test_pause_success(self, mock_registry, mock_mgr_cls, client, make_simulation):
        make_simulation(simulation_id="sim_p", status="running")
        mock_orch = MagicMock()
        mock_orch.pause.return_value = {"status": "paused"}
        mock_registry.get.return_value = mock_orch

        mock_mgr = MagicMock()
        mock_mgr.get_simulation.return_value = MagicMock()
        mock_mgr_cls.return_value = mock_mgr

        resp = client.post("/api/v1/simulation/sim_p/pause")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    @patch("app.api.simulation.SimulationRegistry")
    def test_pause_value_error(self, mock_registry, client):
        mock_orch = MagicMock()
        mock_orch.pause.side_effect = ValueError("Cannot pause: not running")
        mock_registry.get.return_value = mock_orch
        resp = client.post("/api/v1/simulation/sim_x/pause")
        assert resp.status_code == 400


class TestResumeSimulation:
    """POST /api/simulation/<id>/resume"""

    @patch("app.api.simulation.SimulationRegistry")
    def test_resume_not_in_registry(self, mock_registry, client):
        mock_registry.get.return_value = None
        resp = client.post("/api/v1/simulation/sim_x/resume")
        assert resp.status_code == 404

    @patch("app.api.simulation.SimulationManager")
    @patch("app.api.simulation.SimulationRegistry")
    def test_resume_success(self, mock_registry, mock_mgr_cls, client):
        mock_orch = MagicMock()
        mock_orch.resume.return_value = {"status": "running"}
        mock_registry.get.return_value = mock_orch
        mock_mgr = MagicMock()
        mock_mgr.get_simulation.return_value = MagicMock()
        mock_mgr_cls.return_value = mock_mgr

        resp = client.post("/api/v1/simulation/sim_x/resume")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


# ============================================================
# 9. Round Data & Metrics (SimulationRegistry-based)
# ============================================================

class TestRoundData:
    """GET /api/simulation/<id>/round/<round_num>"""

    @patch("app.api.simulation.SimulationRegistry")
    def test_round_not_in_registry(self, mock_registry, client):
        mock_registry.get.return_value = None
        resp = client.get("/api/v1/simulation/sim_x/round/1")
        assert resp.status_code == 404

    @patch("app.api.simulation.SimulationRegistry")
    def test_round_not_reached(self, mock_registry, client):
        mock_orch = MagicMock()
        mock_orch.get_round.return_value = None
        mock_registry.get.return_value = mock_orch
        resp = client.get("/api/v1/simulation/sim_x/round/999")
        assert resp.status_code == 404
        assert "not available" in resp.get_json()["error"]

    @patch("app.api.simulation.SimulationRegistry")
    def test_round_success(self, mock_registry, client):
        mock_orch = MagicMock()
        mock_orch.get_round.return_value = {"actions": [], "stats": {}}
        mock_registry.get.return_value = mock_orch
        mock_registry.get_mode.return_value = "parallel"
        resp = client.get("/api/v1/simulation/sim_x/round/5")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"] == "sim_x"
        assert data["mode"] == "parallel"
        assert "round" in data


class TestMetrics:
    """GET /api/simulation/<id>/metrics"""

    @patch("app.api.simulation.SimulationRegistry")
    def test_metrics_not_found(self, mock_registry, client):
        mock_registry.get_metrics.return_value = None
        resp = client.get("/api/v1/simulation/sim_x/metrics")
        assert resp.status_code == 404

    @patch("app.api.simulation.SimulationRegistry")
    def test_metrics_success(self, mock_registry, client):
        mock_metrics = MagicMock()
        mock_metrics.get_summary.return_value = {
            "total_actions": 100,
            "total_rounds": 50,
        }
        mock_registry.get_metrics.return_value = mock_metrics
        mock_registry.get_mode.return_value = "parallel"
        resp = client.get("/api/v1/simulation/sim_x/metrics")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total_actions"] == 100
        assert data["mode"] == "parallel"


# ============================================================
# 10. Agent Personalities (fallback to mock data)
# ============================================================

class TestAgentPersonalities:
    """GET /api/simulation/<id>/agent-personalities"""

    @patch("app.api.simulation.SimulationRunner")
    def test_personalities_mock_fallback(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_stats.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/agent-personalities")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "traits" in data
        assert "agents" in data

    @patch("app.api.simulation.SimulationRunner")
    def test_personalities_from_stats(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_stats.return_value = [
            {"agent_id": 0, "agent_name": "Agent 0", "total_actions": 10},
            {"agent_id": 1, "agent_name": "Agent 1", "total_actions": 5},
        ]
        resp = client.get("/api/v1/simulation/sim_x/agent-personalities")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data["agents"]) == 2
        agent = data["agents"][0]
        assert "initial_personality" in agent
        assert "current_personality" in agent


class TestAgentSentimentTimeline:
    """GET /api/simulation/<id>/agent-sentiment-timeline"""

    @patch("app.api.simulation.SimulationRunner")
    def test_sentiment_timeline_success(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_sentiment_timeline.return_value = {
            "agents": [{"agent_id": 0, "agent_name": "Agent 0"}],
            "rounds": [1, 2, 3],
            "series": {"0": [{"round": 1, "sentiment": 0.5, "actions": 2}]},
        }
        resp = client.get("/api/v1/simulation/sim_x/agent-sentiment-timeline")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    @patch("app.api.simulation.SimulationRunner")
    def test_sentiment_timeline_error(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_sentiment_timeline.side_effect = Exception("fail")
        resp = client.get("/api/v1/simulation/sim_x/agent-sentiment-timeline")
        assert resp.status_code == 500


# ============================================================
# 11. Agent Network
# ============================================================

class TestAgentNetwork:
    """GET /api/simulation/<id>/agent-network"""

    @patch("app.api.simulation.SimulationRunner")
    def test_network_empty(self, mock_runner_cls, client):
        mock_runner_cls.get_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/agent-network")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["nodes"] == []
        assert data["links"] == []

    @patch("app.api.simulation.SimulationRunner")
    def test_network_with_actions(self, mock_runner_cls, client):
        action1 = MagicMock()
        action1.agent_id = 0
        action1.agent_name = "Agent 0"
        action1.platform = "twitter"
        action1.action_type = "CREATE_POST"
        action1.round_num = 1

        action2 = MagicMock()
        action2.agent_id = 1
        action2.agent_name = "Agent 1"
        action2.platform = "twitter"
        action2.action_type = "REPLY"
        action2.round_num = 1

        mock_runner_cls.get_actions.return_value = [action1, action2]
        resp = client.get("/api/v1/simulation/sim_x/agent-network")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data["nodes"]) == 2
        assert len(data["links"]) == 1


# ============================================================
# 12. Replay
# ============================================================

class TestReplay:
    """GET /api/simulation/<id>/replay"""

    @patch("app.api.simulation.SimulationRunner")
    def test_replay_no_actions(self, mock_runner_cls, client):
        mock_runner_cls.get_run_state.return_value = None
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/replay")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    @patch("app.api.simulation.SimulationRunner")
    def test_replay_with_actions(self, mock_runner_cls, client):
        action = MagicMock()
        action.round_num = 1
        action.timestamp = "2025-01-01T00:00:00"
        action.platform = "twitter"
        action.agent_name = "Agent 0"
        action.agent_id = 0
        action.to_dict.return_value = {
            "round_num": 1, "platform": "twitter", "agent_id": 0,
            "action_type": "CREATE_POST",
        }
        mock_runner_cls.get_run_state.return_value = None
        mock_runner_cls.get_all_actions.return_value = [action]
        resp = client.get("/api/v1/simulation/sim_x/replay")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "rounds" in data


# ============================================================
# 13. Agent Journeys (Sankey)
# ============================================================

class TestAgentJourneys:
    """GET /api/simulation/<id>/agent-journeys"""

    @patch("app.api.simulation.SimulationRunner")
    def test_journeys_fallback_mock(self, mock_runner_cls, client):
        mock_runner_cls.get_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/agent-journeys")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "nodes" in data
        assert "links" in data


# ============================================================
# 14. Personality Dynamics (PersonalityDynamicsService)
# ============================================================

class TestAgentPersonalityDetail:
    """GET /api/simulation/<id>/agents/<agent_id>/personality"""

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_personality")
    def test_personality_success(self, mock_get, client):
        mock_get.return_value = {"agent_id": 0, "traits": {"analytical": 70}}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/personality")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["agent_id"] == 0

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_personality")
    def test_personality_error(self, mock_get, client):
        mock_get.side_effect = Exception("not found")
        resp = client.get("/api/v1/simulation/sim_x/agents/0/personality")
        assert resp.status_code == 500


class TestAgentPersonalityHistory:
    """GET /api/simulation/<id>/agents/<agent_id>/personality/history"""

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_personality_history")
    def test_history_success(self, mock_get, client):
        mock_get.return_value = {"history": [{"round": 1, "traits": {}}]}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/personality/history")
        assert resp.status_code == 200


class TestAgentSentimentHistory:
    """GET /api/simulation/<id>/agents/<agent_id>/sentiment/history"""

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_sentiment_history")
    def test_sentiment_history(self, mock_get, client):
        mock_get.return_value = {"history": [{"round": 1, "sentiment": 7}]}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/sentiment/history")
        assert resp.status_code == 200


class TestPersonalityComparison:
    """GET /api/simulation/<id>/personality/comparison"""

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_personality_comparison")
    def test_comparison(self, mock_get, client):
        mock_get.return_value = {"agents": []}
        resp = client.get("/api/v1/simulation/sim_x/personality/comparison")
        assert resp.status_code == 200


# ============================================================
# 15. Mood & Mood Swings
# ============================================================

class TestGroupMood:
    """GET /api/simulation/<id>/mood"""

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_group_mood")
    def test_mood(self, mock_get, client):
        mock_get.return_value = {"average": 6.5, "agents": []}
        resp = client.get("/api/v1/simulation/sim_x/mood")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["average"] == 6.5


class TestMoodSwings:
    """GET /api/simulation/<id>/mood-swings"""

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_mood_swings")
    def test_mood_swings_default_threshold(self, mock_get, client):
        mock_get.return_value = {"swings": []}
        resp = client.get("/api/v1/simulation/sim_x/mood-swings")
        assert resp.status_code == 200
        mock_get.assert_called_once_with("sim_x", threshold=2.0)

    @patch("app.services.personality_dynamics.PersonalityDynamicsService.get_mood_swings")
    def test_mood_swings_custom_threshold(self, mock_get, client):
        mock_get.return_value = {"swings": []}
        resp = client.get("/api/v1/simulation/sim_x/mood-swings?threshold=3.5")
        assert resp.status_code == 200
        mock_get.assert_called_once_with("sim_x", threshold=3.5)


# ============================================================
# 16. Orchestrator Endpoints
# ============================================================

class TestOrchestratorStatus:
    """GET /api/simulation/<id>/orchestrator/status"""

    @patch("app.api.simulation._orchestrators", {})
    def test_no_orchestrator(self, client):
        resp = client.get("/api/v1/simulation/sim_x/orchestrator/status")
        assert resp.status_code == 404

    @patch("app.api.simulation._orchestrators")
    def test_orchestrator_status_success(self, mock_orchs, client):
        mock_orch = MagicMock()
        mock_orch.get_status.return_value = {
            "state": "running", "current_round": 42,
        }
        mock_orchs.get.return_value = mock_orch
        resp = client.get("/api/v1/simulation/sim_x/orchestrator/status")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["state"] == "running"


class TestOrchestratorResults:
    """GET /api/simulation/<id>/orchestrator/results"""

    @patch("app.api.simulation._orchestrators", {})
    def test_no_orchestrator(self, client):
        resp = client.get("/api/v1/simulation/sim_x/orchestrator/results")
        assert resp.status_code == 404


class TestOrchestratorPause:
    """POST /api/simulation/<id>/orchestrator/pause"""

    @patch("app.api.simulation._orchestrators", {})
    def test_pause_no_orchestrator(self, client):
        resp = client.post("/api/v1/simulation/sim_x/orchestrator/pause")
        assert resp.status_code == 404

    @patch("app.api.simulation._orchestrators")
    def test_pause_success(self, mock_orchs, client):
        mock_orch = MagicMock()
        mock_orch.get_status.return_value = {"state": "paused"}
        mock_orchs.get.return_value = mock_orch
        resp = client.post("/api/v1/simulation/sim_x/orchestrator/pause")
        assert resp.status_code == 200
        mock_orch.pause.assert_called_once()


class TestOrchestratorResume:
    """POST /api/simulation/<id>/orchestrator/resume"""

    @patch("app.api.simulation._orchestrators", {})
    def test_resume_no_orchestrator(self, client):
        resp = client.post("/api/v1/simulation/sim_x/orchestrator/resume")
        assert resp.status_code == 404


class TestOrchestratorStop:
    """POST /api/simulation/<id>/orchestrator/stop"""

    @patch("app.api.simulation._orchestrators", {})
    def test_stop_no_orchestrator(self, client):
        resp = client.post("/api/v1/simulation/sim_x/orchestrator/stop")
        assert resp.status_code == 404


# ============================================================
# 17. What-If Analysis
# ============================================================

class TestWhatIf:
    """POST /api/simulation/whatif"""

    def test_whatif_missing_base_id(self, client):
        resp = client.post("/api/v1/simulation/whatif", json={})
        assert resp.status_code == 400
        assert "base_simulation_id" in resp.get_json()["error"]

    def test_whatif_missing_modifications(self, client):
        resp = client.post("/api/v1/simulation/whatif", json={
            "base_simulation_id": "sim_x",
        })
        assert resp.status_code == 400
        assert "modifications" in resp.get_json()["error"]

    def test_whatif_empty_modifications(self, client):
        resp = client.post("/api/v1/simulation/whatif", json={
            "base_simulation_id": "sim_x",
            "modifications": [],
        })
        assert resp.status_code == 400

    @patch("app.services.whatif_engine.SUPPORTED_PARAMETERS", {"agent_count": {}})
    @patch("app.services.whatif_engine.create_whatif_variant")
    def test_whatif_unsupported_param(self, mock_create, client):
        resp = client.post("/api/v1/simulation/whatif", json={
            "base_simulation_id": "sim_x",
            "modifications": [{"parameter": "nonsense", "value": 5}],
        })
        assert resp.status_code == 400
        assert "Unsupported" in resp.get_json()["error"]

    @patch("app.services.whatif_engine.SUPPORTED_PARAMETERS", {"agent_count": {}})
    @patch("app.services.whatif_engine.create_whatif_variant")
    def test_whatif_missing_value(self, mock_create, client):
        resp = client.post("/api/v1/simulation/whatif", json={
            "base_simulation_id": "sim_x",
            "modifications": [{"parameter": "agent_count"}],
        })
        assert resp.status_code == 400
        assert "Missing 'value'" in resp.get_json()["error"]


class TestWhatIfVariants:
    """GET /api/simulation/<id>/whatif/variants"""

    @patch("app.services.whatif_engine.list_whatif_variants")
    def test_variants_success(self, mock_list, client):
        mock_list.return_value = [{"variant_id": "v1"}]
        resp = client.get("/api/v1/simulation/sim_x/whatif/variants")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1
        assert data["base_simulation_id"] == "sim_x"


# ============================================================
# 18. Sensitivity Analysis
# ============================================================

class TestSensitivityAnalysis:
    """POST /api/simulation/sensitivity"""

    def test_missing_base_id(self, client):
        resp = client.post("/api/v1/simulation/sensitivity", json={})
        assert resp.status_code == 400

    def test_missing_parameter(self, client):
        resp = client.post("/api/v1/simulation/sensitivity", json={
            "base_simulation_id": "sim_x",
        })
        assert resp.status_code == 400

    def test_missing_range(self, client):
        resp = client.post("/api/v1/simulation/sensitivity", json={
            "base_simulation_id": "sim_x",
            "parameter": "agent_count",
        })
        assert resp.status_code == 400

    def test_non_numeric_range(self, client):
        resp = client.post("/api/v1/simulation/sensitivity", json={
            "base_simulation_id": "sim_x",
            "parameter": "agent_count",
            "min_value": "abc",
            "max_value": "xyz",
        })
        assert resp.status_code == 400
        assert "numeric" in resp.get_json()["error"]

    def test_min_gte_max(self, client):
        resp = client.post("/api/v1/simulation/sensitivity", json={
            "base_simulation_id": "sim_x",
            "parameter": "agent_count",
            "min_value": 10,
            "max_value": 5,
        })
        assert resp.status_code == 400
        assert "less than" in resp.get_json()["error"]

    @patch("app.api.simulation.SensitivityAnalyzer")
    def test_sensitivity_success(self, mock_analyzer, client):
        mock_analyzer.run_sensitivity.return_value = {"points": []}
        resp = client.post("/api/v1/simulation/sensitivity", json={
            "base_simulation_id": "sim_x",
            "parameter": "agent_count",
            "min_value": 2,
            "max_value": 15,
            "steps": 5,
        })
        assert resp.status_code == 200


class TestSensitivityGet:
    """GET /api/simulation/<id>/sensitivity"""

    @patch("app.api.simulation.SensitivityAnalyzer")
    def test_get_sensitivity(self, mock_analyzer, client):
        mock_analyzer.get_sensitivity.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/sensitivity")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 0


# ============================================================
# 19. Coalitions
# ============================================================

class TestCoalitions:
    """GET /api/simulation/<id>/coalitions"""

    @patch("app.services.coalition_labeler.CoalitionLabeler")
    @patch("app.services.coalition_detector.CoalitionDetector")
    def test_coalitions_success(self, mock_detector_cls, mock_labeler_cls, client):
        mock_c = MagicMock()
        mock_c.to_dict.return_value = {"name": "Coalition A", "members": []}
        mock_detector = MagicMock()
        mock_detector.detect_coalitions.return_value = [mock_c]
        mock_detector_cls.return_value = mock_detector
        mock_labeler = MagicMock()
        mock_labeler.label_all.return_value = [mock_c]
        mock_labeler_cls.return_value = mock_labeler

        resp = client.get("/api/v1/simulation/sim_x/coalitions")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["coalition_count"] == 1


class TestCoalitionEvolution:
    """GET /api/simulation/<id>/coalitions/evolution"""

    @patch("app.services.coalition_labeler.CoalitionLabeler")
    @patch("app.services.coalition_detector.CoalitionDetector")
    def test_evolution_success(self, mock_detector_cls, mock_labeler_cls, client):
        mock_evo = MagicMock()
        mock_evo.coalitions = []
        mock_evo.to_dict.return_value = {"round": 1, "coalitions": []}
        mock_detector = MagicMock()
        mock_detector.track_coalition_evolution.return_value = [mock_evo]
        mock_detector_cls.return_value = mock_detector
        mock_labeler_cls.return_value = MagicMock()

        resp = client.get("/api/v1/simulation/sim_x/coalitions/evolution")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["rounds_count"] == 1


class TestPolarization:
    """GET /api/simulation/<id>/coalitions/polarization"""

    @patch("app.services.coalition_detector.CoalitionDetector")
    def test_polarization(self, mock_detector_cls, client):
        mock_detector = MagicMock()
        mock_detector.compute_polarization_index.return_value = [
            {"round": 1, "index": 0.3},
        ]
        mock_detector_cls.return_value = mock_detector
        resp = client.get("/api/v1/simulation/sim_x/coalitions/polarization")
        assert resp.status_code == 200
        assert len(resp.get_json()["data"]["timeline"]) == 1


class TestSwingAgents:
    """GET /api/simulation/<id>/coalitions/swing-agents"""

    @patch("app.services.coalition_detector.CoalitionDetector")
    def test_swing_agents(self, mock_detector_cls, client):
        mock_sa = MagicMock()
        mock_sa.to_dict.return_value = {"agent_id": 0, "transitions": 2}
        mock_detector = MagicMock()
        mock_detector.identify_swing_agents.return_value = [mock_sa]
        mock_detector_cls.return_value = mock_detector
        resp = client.get("/api/v1/simulation/sim_x/coalitions/swing-agents")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["swing_agent_count"] == 1


# ============================================================
# 20. Interaction Network
# ============================================================

class TestInteractionNetwork:
    """GET /api/simulation/<id>/network"""

    @patch("app.services.interaction_graph.InteractionGraphBuilder")
    @patch("app.api.simulation.SimulationRunner")
    def test_network_success(self, mock_runner_cls, mock_builder_cls, client):
        mock_runner_cls.get_actions.return_value = []
        mock_builder = MagicMock()
        mock_builder.build_from_simulation.return_value = {"nodes": [], "edges": []}
        mock_builder_cls.return_value = mock_builder
        resp = client.get("/api/v1/simulation/sim_x/network")
        assert resp.status_code == 200

    @patch("app.services.interaction_graph.InteractionGraphBuilder")
    @patch("app.api.simulation.SimulationRunner")
    def test_network_with_centrality(self, mock_runner_cls, mock_builder_cls, client):
        mock_runner_cls.get_actions.return_value = []
        mock_builder = MagicMock()
        mock_builder.build_from_simulation.return_value = {"nodes": [], "edges": []}
        mock_builder.compute_centrality.return_value = {"0": 0.5}
        mock_builder_cls.return_value = mock_builder
        resp = client.get("/api/v1/simulation/sim_x/network?include_centrality=true")
        assert resp.status_code == 200


class TestInteractionNetworkAtRound:
    """GET /api/simulation/<id>/network/round/<round_num>"""

    @patch("app.services.interaction_graph.InteractionGraphBuilder")
    @patch("app.api.simulation.SimulationRunner")
    def test_network_at_round(self, mock_runner_cls, mock_builder_cls, client):
        mock_runner_cls.get_actions.return_value = []
        mock_builder = MagicMock()
        mock_builder.build_temporal_graph.return_value = {"nodes": [], "edges": []}
        mock_builder_cls.return_value = mock_builder
        resp = client.get("/api/v1/simulation/sim_x/network/round/5")
        assert resp.status_code == 200


# ============================================================
# 21. Decisions & Reasoning
# ============================================================

class TestDecisions:
    """GET /api/simulation/<id>/decisions"""

    def test_decisions_list(self, client):
        resp = client.get("/api/v1/simulation/sim_x/decisions")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "decisions" in data
        assert data["simulation_id"] == "sim_x"


class TestDecisionExplain:
    """GET /api/simulation/<id>/decisions/<decision_id>/explain"""

    def test_explain_not_found(self, client):
        resp = client.get("/api/v1/simulation/sim_x/decisions/nonexistent/explain")
        assert resp.status_code == 404

    def test_explain_success(self, client):
        # First get a valid decision_id from the decisions list
        list_resp = client.get("/api/v1/simulation/sim_x/decisions")
        decisions = list_resp.get_json()["data"]["decisions"]
        if decisions:
            did = decisions[0]["decision_id"]
            resp = client.get(f"/api/v1/simulation/sim_x/decisions/{did}/explain")
            assert resp.status_code == 200
            data = resp.get_json()["data"]
            assert "explanation" in data
            assert data["decision_id"] == did


class TestDecisionCounterfactual:
    """GET /api/simulation/<id>/decisions/<decision_id>/counterfactual"""

    def test_counterfactual_not_found(self, client):
        resp = client.get("/api/v1/simulation/sim_x/decisions/nonexistent/counterfactual")
        assert resp.status_code == 404

    def test_counterfactual_success(self, client):
        list_resp = client.get("/api/v1/simulation/sim_x/decisions")
        decisions = list_resp.get_json()["data"]["decisions"]
        if decisions:
            did = decisions[0]["decision_id"]
            resp = client.get(f"/api/v1/simulation/sim_x/decisions/{did}/counterfactual")
            assert resp.status_code == 200
            data = resp.get_json()["data"]
            assert "counterfactual_scenarios" in data


# ============================================================
# 22. Reasoning Traces
# ============================================================

class TestRoundReasoning:
    """GET /api/simulation/<id>/round/<round_num>/reasoning"""

    def test_reasoning_valid_round(self, client):
        resp = client.get("/api/v1/simulation/sim_x/round/1/reasoning")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["round"] == 1
        assert "traces" in data

    def test_reasoning_invalid_round(self, client):
        resp = client.get("/api/v1/simulation/sim_x/round/0/reasoning")
        assert resp.status_code == 400


class TestAgentReasoning:
    """GET /api/simulation/<id>/agents/<agent_id>/reasoning"""

    def test_agent_reasoning_not_found(self, client):
        resp = client.get("/api/v1/simulation/sim_x/agents/99999/reasoning")
        assert resp.status_code == 404


# ============================================================
# 23. Argument Map
# ============================================================

class TestArgumentMap:
    """GET /api/simulation/<id>/argument-map/<topic>"""

    def test_argument_map(self, client):
        resp = client.get("/api/v1/simulation/sim_x/argument-map/AI-Adoption")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["topic"] == "AI-Adoption"
        assert "argument_map" in data
        assert "nodes" in data["argument_map"]
        assert "edges" in data["argument_map"]


# ============================================================
# 24. Agent Beliefs
# ============================================================

class TestAgentBeliefs:
    """GET /api/simulation/<id>/agents/<agent_id>/beliefs"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_beliefs_success(self, mock_ai, client):
        mock_ai.get_agent_beliefs.return_value = {"beliefs": []}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/beliefs")
        assert resp.status_code == 200

    @patch("app.api.simulation.AgentIntelligence")
    def test_beliefs_error(self, mock_ai, client):
        mock_ai.get_agent_beliefs.side_effect = Exception("fail")
        resp = client.get("/api/v1/simulation/sim_x/agents/0/beliefs")
        assert resp.status_code == 500


class TestAgentBeliefsHistory:
    """GET /api/simulation/<id>/agents/<agent_id>/beliefs/history"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_beliefs_history(self, mock_ai, client):
        mock_ai.get_belief_history.return_value = {"history": []}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/beliefs/history")
        assert resp.status_code == 200


# ============================================================
# 25. Relationships
# ============================================================

class TestRelationshipTrackerGraph:
    """GET /api/simulation/<id>/relationship-tracker/graph"""

    @patch("app.api.simulation.SimulationRunner")
    def test_graph_demo_mode(self, mock_runner_cls, client):
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/relationship-tracker/graph")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["demo"] is True


class TestAgentRelationships:
    """GET /api/simulation/<id>/agents/<agent_id>/relationships"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_agent_relationships(self, mock_ai, client):
        mock_ai.get_agent_relationships.return_value = {"relationships": []}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/relationships")
        assert resp.status_code == 200

    @patch("app.api.simulation.AgentIntelligence")
    def test_agent_relationships_not_found(self, mock_ai, client):
        mock_ai.get_agent_relationships.return_value = {"error": "Agent not found"}
        resp = client.get("/api/v1/simulation/sim_x/agents/99/relationships")
        assert resp.status_code == 404


class TestAllRelationships:
    """GET /api/simulation/<id>/relationships"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_all_relationships(self, mock_ai, client):
        mock_ai.get_all_relationships.return_value = {"nodes": [], "edges": []}
        resp = client.get("/api/v1/simulation/sim_x/relationships")
        assert resp.status_code == 200


class TestRelationshipTrackerAgent:
    """GET /api/simulation/<id>/relationship-tracker/agents/<agent_id>"""

    @patch("app.api.simulation.SimulationRunner")
    def test_agent_demo_mode(self, mock_runner_cls, client):
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/relationship-tracker/agents/0")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["demo"] is True


class TestRelationshipTrackerAlliances:
    """GET /api/simulation/<id>/relationship-tracker/alliances"""

    @patch("app.api.simulation.SimulationRunner")
    def test_alliances_demo_mode(self, mock_runner_cls, client):
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/relationship-tracker/alliances")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["demo"] is True


class TestRelationshipTrackerConflicts:
    """GET /api/simulation/<id>/relationship-tracker/conflicts"""

    @patch("app.api.simulation.SimulationRunner")
    def test_conflicts_demo_mode(self, mock_runner_cls, client):
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/relationship-tracker/conflicts")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["demo"] is True


class TestAlliances:
    """GET /api/simulation/<id>/alliances"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_alliances(self, mock_ai, client):
        mock_ai.get_alliances.return_value = {"alliances": []}
        resp = client.get("/api/v1/simulation/sim_x/alliances")
        assert resp.status_code == 200


class TestConflicts:
    """GET /api/simulation/<id>/conflicts"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_conflicts(self, mock_ai, client):
        mock_ai.get_conflicts.return_value = {"conflicts": []}
        resp = client.get("/api/v1/simulation/sim_x/conflicts")
        assert resp.status_code == 200


# ============================================================
# 26. Agent Memory
# ============================================================

class TestAgentMemory:
    """GET /api/simulation/<id>/agents/<agent_id>/memory/consolidated"""

    @patch("app.api.simulation.AgentIntelligence")
    def test_memory_success(self, mock_ai, client):
        mock_ai.get_consolidated_memory.return_value = {"memories": []}
        resp = client.get("/api/v1/simulation/sim_x/agents/0/memory/consolidated")
        assert resp.status_code == 200

    @patch("app.api.simulation.AgentIntelligence")
    def test_memory_not_found(self, mock_ai, client):
        mock_ai.get_consolidated_memory.return_value = {"error": "Agent not found"}
        resp = client.get("/api/v1/simulation/sim_x/agents/99/memory/consolidated")
        assert resp.status_code == 404


# ============================================================
# 27. Consensus
# ============================================================

class TestConsensus:
    """GET /api/simulation/<id>/consensus"""

    @patch("app.api.simulation.SimulationRunner")
    def test_consensus_demo_mode(self, mock_runner_cls, client):
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/consensus")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


class TestConsensusResolved:
    """GET /api/simulation/<id>/consensus/resolved"""

    @patch("app.services.coalition_detector.CoalitionDetector")
    def test_resolved(self, mock_detector_cls, client):
        mock_detector = MagicMock()
        mock_detector.get_consensus_resolved.return_value = {"topics": []}
        mock_detector_cls.return_value = mock_detector
        resp = client.get("/api/v1/simulation/sim_x/consensus/resolved")
        assert resp.status_code == 200


# ============================================================
# 28. Tornado
# ============================================================

class TestTornado:
    """GET /api/simulation/<id>/tornado"""

    @patch("app.api.simulation.SensitivityAnalyzer")
    def test_tornado_success(self, mock_analyzer, client):
        mock_analyzer.generate_tornado_data.return_value = {"bars": []}
        resp = client.get("/api/v1/simulation/sim_x/tornado")
        assert resp.status_code == 200

    @patch("app.api.simulation.SensitivityAnalyzer")
    def test_tornado_with_params(self, mock_analyzer, client):
        mock_analyzer.generate_tornado_data.return_value = {"bars": []}
        resp = client.get(
            "/api/v1/simulation/sim_x/tornado?metric=engagement&parameters=agent_count,temperature"
        )
        assert resp.status_code == 200
        mock_analyzer.generate_tornado_data.assert_called_once_with(
            base_simulation_id="sim_x",
            parameters=["agent_count", "temperature"],
            target_metric="engagement",
        )

    @patch("app.api.simulation.SensitivityAnalyzer")
    def test_tornado_value_error(self, mock_analyzer, client):
        mock_analyzer.generate_tornado_data.side_effect = ValueError("bad param")
        resp = client.get("/api/v1/simulation/sim_x/tornado")
        assert resp.status_code == 400


# ============================================================
# 29. Personality Evolution
# ============================================================

class TestPersonalityEvolution:
    """GET /api/simulation/<id>/personality"""

    @patch("app.api.simulation.SimulationRunner")
    def test_personality_demo_mode(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_stats.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/personality")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "traits" in data
        assert "agents" in data
        assert data["total_rounds"] == 10


# ============================================================
# 30. Influence
# ============================================================

class TestInfluence:
    """GET /api/simulation/<id>/influence"""

    @patch("app.api.simulation.SimulationRunner")
    def test_influence(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_stats.return_value = []
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/influence")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


# ============================================================
# 31. Counterfactual Analysis (POST)
# ============================================================

class TestCounterfactualAnalysis:
    """POST /api/simulation/<id>/counterfactual"""

    def test_counterfactual_missing_fields(self, client):
        resp = client.post("/api/v1/simulation/sim_x/counterfactual", json={})
        assert resp.status_code == 400
        assert "agent_name" in resp.get_json()["error"]

    def test_counterfactual_missing_round(self, client):
        resp = client.post("/api/v1/simulation/sim_x/counterfactual", json={
            "agent_name": "Agent X",
        })
        assert resp.status_code == 400

    @patch("app.services.counterfactual_service.analyze_counterfactual")
    @patch("app.api.simulation.SimulationRunner")
    def test_counterfactual_success(self, mock_runner_cls, mock_cf, client):
        mock_runner_cls.get_actions.return_value = []
        mock_runner_cls.get_profiles.return_value = []
        mock_cf.return_value = {"comparison": "test"}
        resp = client.post("/api/v1/simulation/sim_x/counterfactual", json={
            "agent_name": "Agent X",
            "round_num": 3,
            "action_type": "REPLY",
            "content": "original",
            "alternative": "what if",
        })
        assert resp.status_code == 200


# ============================================================
# 32. Anomalies
# ============================================================

class TestAnomalies:
    """GET /api/simulation/<id>/anomalies"""

    def test_anomalies_demo_mode(self, client):
        resp = client.get("/api/v1/simulation/sim_x/anomalies")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "anomalies" in data
        assert "summary" in data
        assert data["demo_mode"] is True

    def test_anomalies_with_round_filter(self, client):
        resp = client.get("/api/v1/simulation/sim_x/anomalies?round_num=3")
        assert resp.status_code == 200


class TestAnomalyExplanation:
    """GET /api/simulation/<id>/anomalies/<anomaly_id>/explanation"""

    @patch("app.api.simulation.SimulationRunner")
    def test_anomaly_not_found(self, mock_runner_cls, client):
        mock_runner_cls.get_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/anomalies/nonexistent/explanation")
        assert resp.status_code == 404


# ============================================================
# 33. Sentiment Dynamics
# ============================================================

class TestSentimentDynamics:
    """GET /api/simulation/<id>/sentiment-dynamics"""

    @patch("app.api.simulation._get_or_build_sentiment_engine")
    def test_sentiment_dynamics(self, mock_engine_fn, client):
        mock_engine = MagicMock()
        mock_engine.get_all_agents_snapshot.return_value = [
            {"agent_id": "a0", "agent_name": "Agent 0"},
        ]
        mock_engine.get_agent_sentiment_history.return_value = []
        mock_engine.detect_mood_swings.return_value = []
        mock_engine.get_group_mood.return_value = {"average": 5}
        mock_engine_fn.return_value = mock_engine
        resp = client.get("/api/v1/simulation/sim_x/sentiment-dynamics")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "agents" in data
        assert "group_mood" in data


class TestSentimentDynamicsPrompt:
    """GET /api/simulation/<id>/sentiment-dynamics/prompt"""

    @patch("app.api.simulation._get_or_build_sentiment_engine")
    def test_sentiment_prompt(self, mock_engine_fn, client):
        mock_engine = MagicMock()
        mock_engine.get_all_agents_snapshot.return_value = [
            {"agent_id": "a0"},
        ]
        mock_engine.get_prompt_injection.return_value = "Your mood is neutral."
        mock_engine_fn.return_value = mock_engine
        resp = client.get("/api/v1/simulation/sim_x/sentiment-dynamics/prompt")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "prompts" in data


# ============================================================
# 34. Sentiment Analysis
# ============================================================

class TestSentimentAnalysis:
    """GET /api/simulation/<id>/sentiment"""

    @patch("app.api.simulation.SimulationRunner")
    def test_sentiment_demo_fallback(self, mock_runner_cls, client):
        mock_runner_cls.get_all_actions.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/sentiment")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


# ============================================================
# 35. Branch Points
# ============================================================

class TestBranchPoints:
    """GET /api/simulation/<id>/branch-points"""

    def test_branch_points(self, client):
        resp = client.get("/api/v1/simulation/sim_x/branch-points")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "branch_points" in data


# ============================================================
# 36. Knowledge Timeline
# ============================================================

class TestKnowledgeTimeline:
    """GET /api/simulation/<id>/knowledge-timeline"""

    @patch("app.api.simulation.SimulationRunner")
    def test_knowledge_timeline(self, mock_runner_cls, client):
        mock_runner_cls.get_knowledge_timeline.return_value = []
        resp = client.get("/api/v1/simulation/sim_x/knowledge-timeline")
        assert resp.status_code == 200
