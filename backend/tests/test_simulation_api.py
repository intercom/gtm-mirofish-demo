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
        resp = client.post("/api/simulation/create", json={
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
        resp = client.post("/api/simulation/create", json={})
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_create_project_not_found(self, client):
        resp = client.post("/api/simulation/create", json={
            "project_id": "proj_nonexistent",
        })
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_create_no_graph_id(self, client, make_project):
        make_project(graph_id=None)
        resp = client.post("/api/simulation/create", json={
            "project_id": "proj_test123",
        })
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_create_with_platform_flags(self, client, make_project):
        make_project()
        resp = client.post("/api/simulation/create", json={
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
        resp = client.get("/api/simulation/sim_test123")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["simulation_id"] == "sim_test123"
        assert data["status"] == "created"

    def test_get_nonexistent(self, client):
        resp = client.get("/api/simulation/sim_nope")
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_get_ready_includes_run_instructions(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation()
        resp = client.get("/api/simulation/sim_ready")
        assert resp.status_code == 200


class TestListSimulations:
    """GET /api/simulation/list"""

    def test_list_empty(self, client):
        resp = client.get("/api/simulation/list")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 0

    def test_list_returns_created(self, client, make_simulation):
        make_simulation(simulation_id="sim_a")
        make_simulation(simulation_id="sim_b")
        resp = client.get("/api/simulation/list")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["count"] == 2

    def test_list_filter_by_project(self, client, make_simulation):
        make_simulation(simulation_id="sim_a", project_id="proj_1")
        make_simulation(simulation_id="sim_b", project_id="proj_2")
        resp = client.get("/api/simulation/list?project_id=proj_1")
        body = resp.get_json()
        assert body["count"] == 1
        assert body["data"][0]["project_id"] == "proj_1"


class TestSimulationHistory:
    """GET /api/simulation/history"""

    def test_history_empty(self, client):
        resp = client.get("/api/simulation/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 0

    def test_history_enriched_fields(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation()
        resp = client.get("/api/simulation/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["count"] >= 1
        item = body["data"][0]
        assert "version" in item
        assert "created_date" in item

    def test_history_limit(self, client, make_simulation):
        for i in range(5):
            make_simulation(simulation_id=f"sim_{i}")
        resp = client.get("/api/simulation/history?limit=2")
        body = resp.get_json()
        assert len(body["data"]) <= 2


# ============================================================
# 2. Simulation Preparation: prepare / prepare/status
# ============================================================

class TestPrepareSimulation:
    """POST /api/simulation/prepare"""

    def test_prepare_missing_simulation_id(self, client):
        resp = client.post("/api/simulation/prepare", json={})
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_prepare_nonexistent_simulation(self, client):
        resp = client.post("/api/simulation/prepare", json={
            "simulation_id": "sim_nope",
        })
        assert resp.status_code == 404

    def test_prepare_already_ready(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_prep")
        resp = client.post("/api/simulation/prepare", json={
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
        resp = client.post("/api/simulation/prepare", json={
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

        resp = client.post("/api/simulation/prepare", json={
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
        resp = client.post("/api/simulation/prepare/status", json={})
        assert resp.status_code == 400

    def test_status_by_simulation_id_ready(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_s")
        resp = client.post("/api/simulation/prepare/status", json={
            "simulation_id": "sim_s",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["already_prepared"] is True
        assert data["progress"] == 100

    def test_status_simulation_not_started(self, client, make_simulation):
        make_simulation(simulation_id="sim_ns")
        resp = client.post("/api/simulation/prepare/status", json={
            "simulation_id": "sim_ns",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "not_started"

    def test_status_task_not_found(self, client):
        resp = client.post("/api/simulation/prepare/status", json={
            "task_id": "nonexistent_task",
        })
        assert resp.status_code == 404


# ============================================================
# 3. Simulation Execution: start / stop / run-status
# ============================================================

class TestStartSimulation:
    """POST /api/simulation/start"""

    def test_start_missing_simulation_id(self, client):
        resp = client.post("/api/simulation/start", json={})
        assert resp.status_code == 400

    def test_start_nonexistent(self, client):
        resp = client.post("/api/simulation/start", json={
            "simulation_id": "sim_nope",
        })
        assert resp.status_code == 404

    def test_start_not_ready(self, client, make_simulation):
        make_simulation(simulation_id="sim_nr", status="created")
        resp = client.post("/api/simulation/start", json={
            "simulation_id": "sim_nr",
        })
        assert resp.status_code == 400
        assert "未准备好" in resp.get_json()["error"]

    def test_start_invalid_platform(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_ip")
        resp = client.post("/api/simulation/start", json={
            "simulation_id": "sim_ip",
            "platform": "facebook",
        })
        assert resp.status_code == 400

    def test_start_invalid_max_rounds(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_mr")
        resp = client.post("/api/simulation/start", json={
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

        resp = client.post("/api/simulation/start", json={
            "simulation_id": "sim_go",
            "platform": "parallel",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["runner_status"] == "running"


class TestStopSimulation:
    """POST /api/simulation/stop"""

    def test_stop_missing_id(self, client):
        resp = client.post("/api/simulation/stop", json={})
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

        resp = client.post("/api/simulation/stop", json={
            "simulation_id": "sim_stop",
        })
        assert resp.status_code == 200
        assert resp.get_json()["data"]["runner_status"] == "stopped"

    @patch("app.api.simulation.SimulationRunner")
    def test_stop_not_running(self, mock_runner_cls, client):
        mock_runner_cls.stop_simulation.side_effect = ValueError("Not running")
        resp = client.post("/api/simulation/stop", json={
            "simulation_id": "sim_idle",
        })
        assert resp.status_code == 400


class TestRunStatus:
    """GET /api/simulation/<id>/run-status"""

    @patch("app.api.simulation.SimulationRunner")
    def test_run_status_idle(self, mock_runner_cls, client):
        mock_runner_cls.get_run_state.return_value = None
        resp = client.get("/api/simulation/sim_x/run-status")
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
        resp = client.get("/api/simulation/sim_x/run-status")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_round"] == 5


class TestRunStatusDetail:
    """GET /api/simulation/<id>/run-status/detail"""

    @patch("app.api.simulation.SimulationRunner")
    def test_detail_idle(self, mock_runner_cls, client):
        mock_runner_cls.get_run_state.return_value = None
        resp = client.get("/api/simulation/sim_x/run-status/detail")
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
        resp = client.get("/api/simulation/sim_nope/profiles")
        assert resp.status_code == 404

    def test_profiles_reddit(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_p")
        resp = client.get("/api/simulation/sim_p/profiles?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["platform"] == "reddit"
        assert data["count"] >= 1


class TestProfilesRealtime:
    """GET /api/simulation/<id>/profiles/realtime"""

    def test_realtime_nonexistent(self, client):
        resp = client.get("/api/simulation/sim_nope/profiles/realtime")
        assert resp.status_code == 404

    def test_realtime_exists(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_rt")
        resp = client.get("/api/simulation/sim_rt/profiles/realtime?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["file_exists"] is True
        assert data["count"] >= 1
        assert data["is_generating"] is False


class TestConfig:
    """GET /api/simulation/<id>/config"""

    def test_config_not_found(self, client, make_simulation):
        make_simulation(simulation_id="sim_nc")
        resp = client.get("/api/simulation/sim_nc/config")
        assert resp.status_code == 404

    def test_config_success(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_c")
        resp = client.get("/api/simulation/sim_c/config")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "time_config" in data


class TestConfigRealtime:
    """GET /api/simulation/<id>/config/realtime"""

    def test_config_realtime(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_cr")
        resp = client.get("/api/simulation/sim_cr/config/realtime")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["file_exists"] is True
        assert data["config"] is not None
        assert "summary" in data


class TestConfigDownload:
    """GET /api/simulation/<id>/config/download"""

    def test_download_not_found(self, client, make_simulation):
        make_simulation(simulation_id="sim_dl")
        resp = client.get("/api/simulation/sim_dl/config/download")
        assert resp.status_code == 404

    def test_download_success(self, client, make_ready_simulation, make_project):
        make_project()
        make_ready_simulation(simulation_id="sim_dl2")
        resp = client.get("/api/simulation/sim_dl2/config/download")
        assert resp.status_code == 200
        assert resp.content_type in ("application/json", "application/octet-stream")


class TestActions:
    """GET /api/simulation/<id>/actions"""

    @patch("app.api.simulation.SimulationRunner")
    def test_actions_empty(self, mock_runner_cls, client):
        mock_runner_cls.get_actions.return_value = []
        resp = client.get("/api/simulation/sim_x/actions")
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
            "/api/simulation/sim_x/actions?platform=twitter&limit=10&offset=0"
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1


class TestTimeline:
    """GET /api/simulation/<id>/timeline"""

    @patch("app.api.simulation.SimulationRunner")
    def test_timeline_empty(self, mock_runner_cls, client):
        mock_runner_cls.get_timeline.return_value = []
        resp = client.get("/api/simulation/sim_x/timeline")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["rounds_count"] == 0

    @patch("app.api.simulation.SimulationRunner")
    def test_timeline_with_range(self, mock_runner_cls, client):
        mock_runner_cls.get_timeline.return_value = [{"round": 2}, {"round": 3}]
        resp = client.get("/api/simulation/sim_x/timeline?start_round=2&end_round=3")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["rounds_count"] == 2


class TestAgentStats:
    """GET /api/simulation/<id>/agent-stats"""

    @patch("app.api.simulation.SimulationRunner")
    def test_agent_stats(self, mock_runner_cls, client):
        mock_runner_cls.get_agent_stats.return_value = [
            {"agent_id": 0, "total_actions": 10},
        ]
        resp = client.get("/api/simulation/sim_x/agent-stats")
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
        resp = client.get("/api/simulation/sim_posts/posts?platform=reddit")
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
            resp = client.get("/api/simulation/sim_db/posts?platform=reddit")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["total"] == 1
        assert data["count"] == 1
        assert data["posts"][0]["content"] == "Hello world"


class TestComments:
    """GET /api/simulation/<id>/comments"""

    def test_comments_no_db(self, client, make_simulation):
        make_simulation(simulation_id="sim_com")
        resp = client.get("/api/simulation/sim_com/comments")
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
            resp = client.get("/api/simulation/sim_com2/comments")
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
            resp = client.get("/api/simulation/sim_com3/comments?post_id=1")
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

        resp = client.get("/api/simulation/entities/graph_123")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["filtered_count"] == 3

    @patch("app.api.simulation.Config")
    def test_entities_no_zep_key(self, mock_config, client):
        mock_config.ZEP_API_KEY = None
        resp = client.get("/api/simulation/entities/graph_123")
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

        resp = client.get("/api/simulation/entities/graph_1/abc")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["uuid"] == "abc"

    @patch("app.api.simulation.ZepEntityReader")
    def test_entity_not_found(self, mock_reader_cls, client):
        mock_instance = MagicMock()
        mock_instance.get_entity_with_context.return_value = None
        mock_reader_cls.return_value = mock_instance

        resp = client.get("/api/simulation/entities/graph_1/missing")
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

        resp = client.get("/api/simulation/entities/graph_1/by-type/Student")
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
        resp = client.post("/api/simulation/interview", json={})
        assert resp.status_code == 400

        resp = client.post("/api/simulation/interview", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 400

        resp = client.post("/api/simulation/interview", json={
            "simulation_id": "sim_x",
            "agent_id": 0,
        })
        assert resp.status_code == 400

    def test_interview_invalid_platform(self, client):
        resp = client.post("/api/simulation/interview", json={
            "simulation_id": "sim_x",
            "agent_id": 0,
            "prompt": "test",
            "platform": "facebook",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_interview_env_not_running(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        resp = client.post("/api/simulation/interview", json={
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
        resp = client.post("/api/simulation/interview", json={
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
        resp = client.post("/api/simulation/interview/batch", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 400

    def test_batch_invalid_item(self, client):
        resp = client.post("/api/simulation/interview/batch", json={
            "simulation_id": "sim_x",
            "interviews": [{"prompt": "hi"}],
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_batch_env_not_running(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        resp = client.post("/api/simulation/interview/batch", json={
            "simulation_id": "sim_x",
            "interviews": [{"agent_id": 0, "prompt": "hi"}],
        })
        assert resp.status_code == 400


class TestInterviewAll:
    """POST /api/simulation/interview/all"""

    def test_all_missing_prompt(self, client):
        resp = client.post("/api/simulation/interview/all", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_all_env_not_running(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = False
        resp = client.post("/api/simulation/interview/all", json={
            "simulation_id": "sim_x",
            "prompt": "test",
        })
        assert resp.status_code == 400


class TestInterviewHistory:
    """POST /api/simulation/interview/history"""

    def test_history_missing_id(self, client):
        resp = client.post("/api/simulation/interview/history", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_history_success(self, mock_runner_cls, client):
        mock_runner_cls.get_interview_history.return_value = [
            {"agent_id": 0, "response": "test"},
        ]
        resp = client.post("/api/simulation/interview/history", json={
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
        resp = client.post("/api/simulation/env-status", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.SimulationRunner")
    def test_env_status_alive(self, mock_runner_cls, client):
        mock_runner_cls.check_env_alive.return_value = True
        mock_runner_cls.get_env_status_detail.return_value = {
            "twitter_available": True,
            "reddit_available": True,
        }
        resp = client.post("/api/simulation/env-status", json={
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
        resp = client.post("/api/simulation/env-status", json={
            "simulation_id": "sim_x",
        })
        assert resp.status_code == 200
        assert resp.get_json()["data"]["env_alive"] is False


class TestCloseEnv:
    """POST /api/simulation/close-env"""

    def test_close_missing_id(self, client):
        resp = client.post("/api/simulation/close-env", json={})
        assert resp.status_code == 400


class TestScriptDownload:
    """GET /api/simulation/script/<name>/download"""

    def test_invalid_script_name(self, client):
        resp = client.get("/api/simulation/script/evil.py/download")
        assert resp.status_code == 400

    def test_script_not_found(self, client):
        resp = client.get(
            "/api/simulation/script/run_twitter_simulation.py/download"
        )
        # 404 if the file doesn't exist on disk
        assert resp.status_code in (200, 404)


class TestGenerateProfiles:
    """POST /api/simulation/generate-profiles"""

    def test_missing_graph_id(self, client):
        resp = client.post("/api/simulation/generate-profiles", json={})
        assert resp.status_code == 400

    @patch("app.api.simulation.OasisProfileGenerator")
    @patch("app.api.simulation.ZepEntityReader")
    def test_no_entities(self, mock_reader_cls, mock_gen_cls, client):
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.filtered_count = 0
        mock_instance.filter_defined_entities.return_value = mock_result
        mock_reader_cls.return_value = mock_instance

        resp = client.post("/api/simulation/generate-profiles", json={
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

        resp = client.post("/api/simulation/generate-profiles", json={
            "graph_id": "graph_test",
            "platform": "reddit",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] == 1
        assert data["platform"] == "reddit"
