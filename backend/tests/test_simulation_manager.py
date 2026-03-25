"""Tests for app.services.simulation_manager — SimulationManager state management."""

import os
import json
import pytest
from unittest.mock import patch

from app.services.simulation_manager import (
    SimulationManager,
    SimulationState,
    SimulationStatus,
    PlatformType,
)


@pytest.fixture()
def sim_manager(tmp_path):
    """Create a SimulationManager with isolated temp storage."""
    mgr = SimulationManager()
    mgr.SIMULATION_DATA_DIR = str(tmp_path / "simulations")
    os.makedirs(mgr.SIMULATION_DATA_DIR, exist_ok=True)
    mgr._simulations.clear()
    return mgr


class TestSimulationStatus:
    def test_enum_values(self):
        assert SimulationStatus.CREATED.value == "created"
        assert SimulationStatus.RUNNING.value == "running"
        assert SimulationStatus.COMPLETED.value == "completed"
        assert SimulationStatus.FAILED.value == "failed"


class TestPlatformType:
    def test_enum_values(self):
        assert PlatformType.TWITTER.value == "twitter"
        assert PlatformType.REDDIT.value == "reddit"


class TestSimulationState:
    def test_to_dict(self):
        state = SimulationState(
            simulation_id="sim_test",
            project_id="proj_1",
            graph_id="graph_1",
            status=SimulationStatus.READY,
        )
        d = state.to_dict()
        assert d["simulation_id"] == "sim_test"
        assert d["status"] == "ready"
        assert d["enable_twitter"] is True
        assert d["enable_reddit"] is True

    def test_to_simple_dict(self):
        state = SimulationState(
            simulation_id="sim_test",
            project_id="proj_1",
            graph_id="graph_1",
        )
        simple = state.to_simple_dict()
        assert "simulation_id" in simple
        assert "current_round" not in simple
        assert "config_reasoning" not in simple


class TestSimulationManagerCreateAndGet:
    def test_create_simulation(self, sim_manager):
        state = sim_manager.create_simulation(
            project_id="proj_1",
            graph_id="graph_1",
            enable_twitter=True,
            enable_reddit=False,
        )
        assert state.simulation_id.startswith("sim_")
        assert state.project_id == "proj_1"
        assert state.graph_id == "graph_1"
        assert state.enable_twitter is True
        assert state.enable_reddit is False
        assert state.status == SimulationStatus.CREATED

    def test_get_simulation(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        fetched = sim_manager.get_simulation(state.simulation_id)
        assert fetched is not None
        assert fetched.simulation_id == state.simulation_id

    def test_get_nonexistent_returns_none(self, sim_manager):
        assert sim_manager.get_simulation("nonexistent") is None

    def test_state_persisted_to_disk(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        # Clear in-memory cache
        sim_manager._simulations.clear()
        # Should reload from disk
        reloaded = sim_manager.get_simulation(state.simulation_id)
        assert reloaded is not None
        assert reloaded.project_id == "p1"


class TestSimulationManagerList:
    def test_list_all(self, sim_manager):
        sim_manager.create_simulation("p1", "g1")
        sim_manager.create_simulation("p2", "g2")
        sims = sim_manager.list_simulations()
        assert len(sims) == 2

    def test_list_filtered_by_project(self, sim_manager):
        sim_manager.create_simulation("p1", "g1")
        sim_manager.create_simulation("p2", "g2")
        sim_manager.create_simulation("p1", "g3")
        sims = sim_manager.list_simulations(project_id="p1")
        assert len(sims) == 2
        assert all(s.project_id == "p1" for s in sims)


class TestSimulationManagerConfig:
    def test_get_simulation_config_missing(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        assert sim_manager.get_simulation_config(state.simulation_id) is None

    def test_get_simulation_config_exists(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        sim_dir = sim_manager._get_simulation_dir(state.simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        with open(config_path, "w") as f:
            json.dump({"max_rounds": 10}, f)

        cfg = sim_manager.get_simulation_config(state.simulation_id)
        assert cfg == {"max_rounds": 10}

    def test_get_run_instructions(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        instructions = sim_manager.get_run_instructions(state.simulation_id)
        assert "commands" in instructions
        assert "twitter" in instructions["commands"]
        assert "reddit" in instructions["commands"]


class TestSimulationManagerProfiles:
    def test_get_profiles_empty(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        profiles = sim_manager.get_profiles(state.simulation_id, "reddit")
        assert profiles == []

    def test_get_profiles_with_data(self, sim_manager):
        state = sim_manager.create_simulation("p1", "g1")
        sim_dir = sim_manager._get_simulation_dir(state.simulation_id)
        profile_data = [{"name": "Agent1"}, {"name": "Agent2"}]
        with open(os.path.join(sim_dir, "reddit_profiles.json"), "w") as f:
            json.dump(profile_data, f)

        profiles = sim_manager.get_profiles(state.simulation_id, "reddit")
        assert len(profiles) == 2
        assert profiles[0]["name"] == "Agent1"

    def test_get_profiles_nonexistent_simulation_raises(self, sim_manager):
        with pytest.raises(ValueError, match="模拟不存在"):
            sim_manager.get_profiles("nonexistent")
