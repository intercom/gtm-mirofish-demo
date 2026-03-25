"""
Shared test fixtures for MiroFish backend API integration tests.
"""

import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    """Test configuration — no real API keys, isolated upload dir."""
    TESTING = True
    DEBUG = False
    LLM_API_KEY = "test-key"
    ZEP_API_KEY = "test-zep-key"
    LLM_BASE_URL = "https://api.openai.com/v1/"
    LLM_MODEL_NAME = "gpt-4o-mini"


@pytest.fixture
def tmp_uploads(tmp_path):
    """Provide an isolated uploads directory for each test."""
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (uploads / "simulations").mkdir()
    (uploads / "projects").mkdir()
    return uploads


@pytest.fixture
def app(tmp_uploads):
    """Create a Flask application configured for testing.

    Patches class-level directory attributes that are resolved at import time
    so all managers read/write to the isolated tmp_uploads directory.
    """
    uploads_str = str(tmp_uploads)
    sims_str = str(tmp_uploads / "simulations")
    projs_str = str(tmp_uploads / "projects")

    TestConfig.UPLOAD_FOLDER = uploads_str
    TestConfig.OASIS_SIMULATION_DATA_DIR = sims_str

    patches = [
        patch("app.services.simulation_runner.SimulationRunner.register_cleanup"),
        # ProjectManager resolves PROJECTS_DIR from Config.UPLOAD_FOLDER at class level
        patch("app.models.project.ProjectManager.PROJECTS_DIR", projs_str),
        # SimulationManager resolves SIMULATION_DATA_DIR at class level
        patch("app.services.simulation_manager.SimulationManager.SIMULATION_DATA_DIR", sims_str),
        # Config.OASIS_SIMULATION_DATA_DIR is used directly by some endpoints
        patch("app.api.simulation.Config.OASIS_SIMULATION_DATA_DIR", sims_str),
    ]
    for p in patches:
        p.start()

    application = create_app(TestConfig)
    application.config["UPLOAD_FOLDER"] = uploads_str

    yield application

    for p in patches:
        p.stop()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# --------------- helper factories ---------------

@pytest.fixture
def make_project(tmp_uploads):
    """Factory that writes a project.json to disk so ProjectManager can find it."""
    def _make(project_id="proj_test123", name="Test Project", graph_id="mirofish_test",
              simulation_requirement="Test simulation requirement", status="graph_completed"):
        proj_dir = tmp_uploads / "projects" / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "files").mkdir(exist_ok=True)
        now = datetime.now().isoformat()
        meta = {
            "project_id": project_id,
            "name": name,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "files": [{"filename": "test.pdf"}],
            "total_text_length": 1000,
            "graph_id": graph_id,
            "simulation_requirement": simulation_requirement,
        }
        with open(proj_dir / "project.json", "w") as f:
            json.dump(meta, f)
        # extracted text
        with open(proj_dir / "extracted_text.txt", "w") as f:
            f.write("Sample extracted text for testing.")
        return meta
    return _make


@pytest.fixture
def make_simulation(tmp_uploads):
    """Factory that writes a simulation state.json to disk."""
    def _make(simulation_id="sim_test123", project_id="proj_test123",
              graph_id="mirofish_test", status="created", config_generated=False,
              entities_count=10, profiles_count=10, entity_types=None):
        sim_dir = tmp_uploads / "simulations" / simulation_id
        sim_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().isoformat()
        state = {
            "simulation_id": simulation_id,
            "project_id": project_id,
            "graph_id": graph_id,
            "enable_twitter": True,
            "enable_reddit": True,
            "status": status,
            "entities_count": entities_count,
            "profiles_count": profiles_count,
            "entity_types": entity_types or ["Student", "Professor"],
            "config_generated": config_generated,
            "config_reasoning": "",
            "current_round": 0,
            "twitter_status": "not_started",
            "reddit_status": "not_started",
            "created_at": now,
            "updated_at": now,
            "error": None,
        }
        with open(sim_dir / "state.json", "w") as f:
            json.dump(state, f)
        return state
    return _make


@pytest.fixture
def make_ready_simulation(make_simulation, tmp_uploads):
    """Create a fully-prepared simulation with all required files."""
    def _make(simulation_id="sim_ready", **kwargs):
        state = make_simulation(
            simulation_id=simulation_id,
            status="ready",
            config_generated=True,
            **kwargs,
        )
        sim_dir = tmp_uploads / "simulations" / simulation_id
        # profiles
        with open(sim_dir / "reddit_profiles.json", "w") as f:
            json.dump([{"username": "agent_0", "persona": "Student"}], f)
        # twitter profiles CSV
        with open(sim_dir / "twitter_profiles.csv", "w") as f:
            f.write("username,bio\nagent_0,A student\n")
        # config
        config = {
            "time_config": {"total_simulation_hours": 24, "minutes_per_round": 30},
            "agent_configs": [{"agent_id": 0}],
            "event_config": {"initial_posts": [], "hot_topics": []},
            "generated_at": datetime.now().isoformat(),
            "llm_model": "test",
            "simulation_requirement": "test",
        }
        with open(sim_dir / "simulation_config.json", "w") as f:
            json.dump(config, f)
        return state
    return _make
