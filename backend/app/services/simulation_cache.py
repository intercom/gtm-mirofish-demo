"""
Simulation result cache for offline replay.

Snapshots a completed simulation's run state, actions, and timeline
into a single JSON file that can be served without Zep/LLM dependencies.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner, RunnerStatus

logger = get_logger('mirofish.simulation_cache')

CACHE_DIR = os.path.join(Config.UPLOAD_FOLDER, 'cache', 'simulations')


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(simulation_id: str) -> str:
    return os.path.join(CACHE_DIR, f'{simulation_id}.json')


def _load_simulation_state(simulation_id: str) -> Optional[Dict[str, Any]]:
    """Load the SimulationManager state.json for metadata."""
    state_file = os.path.join(Config.UPLOAD_FOLDER, 'simulations', simulation_id, 'state.json')
    if not os.path.exists(state_file):
        return None
    with open(state_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def cache_simulation(simulation_id: str) -> Dict[str, Any]:
    """
    Snapshot a completed simulation into the cache.

    Reads run_state.json, actions.jsonl, and state.json from the
    simulation directory and bundles them into a single cache file.

    Returns the cache entry metadata (without the full actions payload).
    """
    run_state = SimulationRunner.get_run_state(simulation_id)
    if not run_state:
        raise ValueError(f'No run state found for simulation {simulation_id}')

    if run_state.runner_status not in (RunnerStatus.COMPLETED, RunnerStatus.STOPPED):
        raise ValueError(
            f'Simulation {simulation_id} is not complete '
            f'(status: {run_state.runner_status.value})'
        )

    actions = SimulationRunner.get_actions(simulation_id, limit=100_000)
    actions_list = [a.to_dict() for a in actions]
    timeline = SimulationRunner.get_timeline(simulation_id)
    sim_state = _load_simulation_state(simulation_id)

    entry = {
        'id': simulation_id,
        'cached_at': datetime.now().isoformat(),
        'metadata': {
            'scenario_name': (sim_state or {}).get('scenario_name', ''),
            'project_id': (sim_state or {}).get('project_id', ''),
            'graph_id': (sim_state or {}).get('graph_id', ''),
            'entities_count': (sim_state or {}).get('entities_count', 0),
            'profiles_count': (sim_state or {}).get('profiles_count', 0),
            'entity_types': (sim_state or {}).get('entity_types', []),
        },
        'run_state': run_state.to_dict(),
        'actions': actions_list,
        'timeline': timeline,
    }

    _ensure_cache_dir()
    with open(_cache_path(simulation_id), 'w', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False)

    logger.info(f'Cached simulation {simulation_id} ({len(actions_list)} actions)')
    return _summary(entry)


def get_cached_simulation(simulation_id: str) -> Optional[Dict[str, Any]]:
    """Load a full cache entry (including actions) for replay."""
    path = _cache_path(simulation_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_cached_simulations() -> List[Dict[str, Any]]:
    """Return summaries of all cached simulations (without actions)."""
    _ensure_cache_dir()
    results = []
    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith('.json'):
            continue
        path = os.path.join(CACHE_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                entry = json.load(f)
            results.append(_summary(entry))
        except (json.JSONDecodeError, KeyError):
            logger.warning(f'Skipping corrupt cache file: {filename}')
    results.sort(key=lambda e: e.get('cached_at', ''), reverse=True)
    return results


def delete_cached_simulation(simulation_id: str) -> bool:
    """Remove a cache entry. Returns True if it existed."""
    path = _cache_path(simulation_id)
    if os.path.exists(path):
        os.remove(path)
        logger.info(f'Deleted cache for simulation {simulation_id}')
        return True
    return False


def _summary(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a lightweight summary (no actions) from a cache entry."""
    rs = entry.get('run_state', {})
    return {
        'id': entry['id'],
        'cached_at': entry.get('cached_at', ''),
        'metadata': entry.get('metadata', {}),
        'total_rounds': rs.get('total_rounds', 0),
        'total_actions': rs.get('total_actions_count', 0),
        'twitter_actions': rs.get('twitter_actions_count', 0),
        'reddit_actions': rs.get('reddit_actions_count', 0),
        'started_at': rs.get('started_at', ''),
        'completed_at': rs.get('completed_at', ''),
        'runner_status': rs.get('runner_status', 'unknown'),
    }
