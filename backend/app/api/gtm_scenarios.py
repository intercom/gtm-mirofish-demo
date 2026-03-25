"""
GTM Scenario API
Serves pre-built GTM simulation scenario templates and seed data,
and provides a unified simulation endpoint that bridges the frontend
ScenarioBuilder with the backend ontology/graph pipeline.
"""

import hashlib
import json
import os
import traceback
import threading

from flask import Blueprint, jsonify, request

from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

logger = get_logger('mirofish.gtm')

gtm_bp = Blueprint('gtm', __name__, url_prefix='/api/gtm')

SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_scenarios')
SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')


def _load_json(filepath):
    """Load a JSON file, return None if not found."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


@gtm_bp.route('/scenarios', methods=['GET'])
def list_scenarios():
    """List all available GTM scenario templates."""
    scenarios = []
    if os.path.exists(SCENARIOS_DIR):
        for filename in sorted(os.listdir(SCENARIOS_DIR)):
            if filename.endswith('.json'):
                data = _load_json(os.path.join(SCENARIOS_DIR, filename))
                if data:
                    scenarios.append({
                        'id': data.get('id', filename.replace('.json', '')),
                        'name': data.get('name', ''),
                        'description': data.get('description', ''),
                        'category': data.get('category', 'general'),
                        'icon': data.get('icon', ''),
                    })
    return jsonify({'scenarios': scenarios})


@gtm_bp.route('/scenarios/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    """Get a specific scenario template with full configuration."""
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    data = _load_json(filepath)
    if data:
        return jsonify(data)
    return jsonify({'error': f'Scenario {scenario_id} not found'}), 404


@gtm_bp.route('/seed-data/<data_type>', methods=['GET'])
def get_seed_data(data_type):
    """Get GTM seed data by type (account_profiles, signal_definitions, etc.)."""
    filepath = os.path.join(SEED_DATA_DIR, f'{data_type}.json')
    data = _load_json(filepath)
    if data:
        return jsonify(data)
    return jsonify({'error': f'Seed data {data_type} not found'}), 404


@gtm_bp.route('/scenarios/<scenario_id>/seed-text', methods=['GET'])
def get_scenario_seed_text(scenario_id):
    """Get the seed text for a scenario, ready to paste into graph building."""
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    data = _load_json(filepath)
    if data and 'seed_text' in data:
        return jsonify({'seed_text': data['seed_text']})
    return jsonify({'error': 'Seed text not found'}), 404


# ============== Leaderboard Endpoint ==============

# Score weights for composite ranking
SCORE_WEIGHTS = {
    'sentiment': 0.35,
    'consensus': 0.30,
    'decision_quality': 0.35,
}

MOCK_SCENARIO_NAMES = [
    'Enterprise Onboarding Flow',
    'Competitive Win/Loss Analysis',
    'Pipeline Acceleration Sprint',
    'Churn Risk Triage',
    'Expansion Revenue Strategy',
    'Product-Led Growth Review',
    'Support Escalation Workflow',
    'Quarterly Business Review',
]


def _deterministic_hash(value):
    """Return a stable integer hash from any string."""
    return int(hashlib.md5(value.encode('utf-8')).hexdigest()[:8], 16)


def _compute_run_scores(run):
    """Compute sentiment, consensus, and decision quality scores for a run.

    Uses deterministic seeding from the run ID so scores are stable across
    calls.  Observable metrics (totalActions, totalRounds, agentCount) nudge
    the scores so runs with more activity genuinely score differently.
    """
    seed = _deterministic_hash(run.get('id', str(run.get('timestamp', 0))))
    actions = run.get('totalActions', 0) or 0
    rounds = run.get('totalRounds', 0) or 0
    agents = run.get('agentCount', 0) or 0

    # Sentiment: 0-100
    sentiment_base = ((seed % 40) + 50) / 100
    sentiment_boost = min(actions / 2000, 0.10)
    sentiment = min(round((sentiment_base + sentiment_boost) * 100), 100)

    # Consensus: 0-100
    consensus_base = (((seed * 7) % 35) + 45) / 100
    round_boost = min(rounds / 200, 0.15)
    agent_boost = min(agents / 30, 0.05)
    consensus = min(round((consensus_base + round_boost + agent_boost) * 100), 100)

    # Decision quality: 0-100
    quality_base = (((seed * 13) % 30) + 55) / 100
    density = min((actions / max(rounds, 1)) / 20, 0.10) if actions and rounds else 0
    decision_quality = min(round((quality_base + density) * 100), 100)

    composite = round(
        sentiment * SCORE_WEIGHTS['sentiment']
        + consensus * SCORE_WEIGHTS['consensus']
        + decision_quality * SCORE_WEIGHTS['decision_quality']
    )

    return {
        'sentiment': sentiment,
        'consensus': consensus,
        'decisionQuality': decision_quality,
        'composite': composite,
    }


def _build_mock_leaderboard():
    """Generate a demo leaderboard when no run data is provided."""
    import time
    entries = []
    now = int(time.time() * 1000)
    for i, name in enumerate(MOCK_SCENARIO_NAMES):
        mock_id = f'mock-{i:04d}'
        run = {
            'id': mock_id,
            'scenarioName': name,
            'totalActions': 400 + (i * 137) % 600,
            'totalRounds': 80 + (i * 23) % 64,
            'agentCount': 8 + i % 8,
            'twitterActions': 200 + (i * 71) % 300,
            'redditActions': 100 + (i * 53) % 200,
            'timestamp': now - (i * 86400000),
            'status': 'completed',
            'scenarioId': f'scenario-{i}',
        }
        scores = _compute_run_scores(run)
        entries.append({**run, 'scores': scores})
    entries.sort(key=lambda e: e['scores']['composite'], reverse=True)
    for rank, entry in enumerate(entries, 1):
        entry['rank'] = rank
    return entries


@gtm_bp.route('/scenarios/leaderboard', methods=['POST'])
def scenarios_leaderboard():
    """Score and rank simulation runs.

    Accepts a JSON body with a ``runs`` array of simulation run objects.
    Returns the same runs augmented with ``scores`` and ``rank``.

    When called with an empty or missing ``runs`` array, returns demo data.
    """
    data = request.get_json(silent=True) or {}
    runs = data.get('runs')

    if not runs:
        return jsonify({'success': True, 'data': _build_mock_leaderboard()})

    entries = []
    for run in runs:
        scores = _compute_run_scores(run)
        entries.append({**run, 'scores': scores})

    entries.sort(key=lambda e: e['scores']['composite'], reverse=True)
    for rank, entry in enumerate(entries, 1):
        entry['rank'] = rank

    return jsonify({'success': True, 'data': entries})


# ============== Unified Simulation Endpoint ==============

@gtm_bp.route('/simulate', methods=['POST'])
def simulate():
    """
    Unified GTM simulation endpoint.

    Accepts the frontend's simulation config (seed_text + parameters),
    creates a project, generates ontology, and kicks off async graph
    building -- all in one call.

    Request (JSON):
        {
            "seed_text": "...",               // required
            "agent_count": 200,               // optional, stored as metadata
            "persona_types": [...],           // optional, stored as metadata
            "industries": [...],              // optional, stored as metadata
            "company_sizes": [...],           // optional, stored as metadata
            "regions": [...],                 // optional, stored as metadata
            "duration_hours": 72,             // optional, stored as metadata
            "minutes_per_round": 30,          // optional, stored as metadata
            "platform_mode": "parallel"       // optional, stored as metadata
        }

    Returns:
        {
            "success": true,
            "data": {
                "task_id": "...",
                "project_id": "..."
            }
        }

    The frontend can then poll GET /api/graph/task/<task_id> for progress.
    On completion the task result contains project_id, graph_id, and task_id.
    """
    try:
        data = request.get_json() or {}
        seed_text = data.get('seed_text', '').strip()

        if not seed_text:
            return jsonify({
                "success": False,
                "error": "seed_text is required"
            }), 400

        # Validate Zep key early so we fail fast
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY is not configured"
            }), 500

        # Capture simulation metadata from the frontend config
        sim_metadata = {
            k: data[k] for k in (
                'agent_count', 'persona_types', 'industries',
                'company_sizes', 'regions', 'duration_hours',
                'minutes_per_round', 'platform_mode',
            ) if k in data
        }

        # Create project
        project = ProjectManager.create_project(name="GTM Simulation")
        project.simulation_requirement = seed_text
        project_id = project.project_id
        logger.info(f"[simulate] Created project {project_id}")

        # Save seed_text as extracted text (no file upload needed)
        preprocessed = TextProcessor.preprocess_text(seed_text)
        project.total_text_length = len(preprocessed)
        ProjectManager.save_extracted_text(project_id, preprocessed)

        # Create async task
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            "GTM Simulation",
            metadata={"project_id": project_id, **sim_metadata},
        )

        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)

        # ---- background thread ----
        def _run():
            build_logger = get_logger('mirofish.gtm.build')
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    message="Generating ontology from seed text...",
                    progress=5,
                )

                # 1. Generate ontology
                generator = OntologyGenerator()
                ontology = generator.generate(
                    document_texts=[preprocessed],
                    simulation_requirement=seed_text,
                )

                entity_count = len(ontology.get("entity_types", []))
                edge_count = len(ontology.get("edge_types", []))
                build_logger.info(
                    f"[{task_id}] Ontology generated: "
                    f"{entity_count} entity types, {edge_count} edge types"
                )

                # Persist ontology on the project
                proj = ProjectManager.get_project(project_id)
                proj.ontology = {
                    "entity_types": ontology.get("entity_types", []),
                    "edge_types": ontology.get("edge_types", []),
                }
                proj.analysis_summary = ontology.get("analysis_summary", "")
                proj.status = ProjectStatus.ONTOLOGY_GENERATED
                ProjectManager.save_project(proj)

                task_manager.update_task(
                    task_id,
                    message="Ontology generated. Creating graph...",
                    progress=15,
                )

                # 2. Build graph (mirrors graph.py build_task logic)
                text = ProjectManager.get_extracted_text(project_id)
                chunk_size = proj.chunk_size or Config.DEFAULT_CHUNK_SIZE
                chunk_overlap = proj.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP
                graph_name = proj.name or "GTM Simulation Graph"

                builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)

                # Split text
                chunks = TextProcessor.split_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
                total_chunks = len(chunks)

                task_manager.update_task(
                    task_id,
                    message=f"Text split into {total_chunks} chunks. Creating Zep graph...",
                    progress=20,
                )

                graph_id = builder.create_graph(name=graph_name)

                proj = ProjectManager.get_project(project_id)
                proj.graph_id = graph_id
                proj.status = ProjectStatus.GRAPH_BUILDING
                ProjectManager.save_project(proj)

                # Set ontology on the Zep graph
                task_manager.update_task(task_id, message="Setting ontology...", progress=25)
                builder.set_ontology(graph_id, proj.ontology)

                # Add text batches
                def add_progress_cb(msg, ratio):
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=25 + int(ratio * 35),  # 25-60%
                    )

                task_manager.update_task(
                    task_id,
                    message=f"Adding {total_chunks} text chunks...",
                    progress=25,
                )
                episode_uuids = builder.add_text_batches(
                    graph_id, chunks, batch_size=3, progress_callback=add_progress_cb,
                )

                # Wait for Zep processing
                task_manager.update_task(
                    task_id, message="Waiting for Zep processing...", progress=60,
                )

                def wait_progress_cb(msg, ratio):
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=60 + int(ratio * 30),  # 60-90%
                    )

                builder._wait_for_episodes(episode_uuids, wait_progress_cb)

                # Fetch final graph data
                task_manager.update_task(
                    task_id, message="Fetching graph data...", progress=95,
                )
                graph_data = builder.get_graph_data(graph_id)

                # Mark project complete
                proj = ProjectManager.get_project(project_id)
                proj.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(proj)

                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(
                    f"[{task_id}] Graph complete: graph_id={graph_id}, "
                    f"nodes={node_count}, edges={edge_count}"
                )

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="Simulation graph built successfully",
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "task_id": task_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks,
                    },
                )

            except Exception as e:
                build_logger.error(f"[{task_id}] Simulation failed: {e}")
                build_logger.debug(traceback.format_exc())

                proj = ProjectManager.get_project(project_id)
                if proj:
                    proj.status = ProjectStatus.FAILED
                    proj.error = str(e)
                    ProjectManager.save_project(proj)

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Simulation failed: {e}",
                    error=traceback.format_exc(),
                )

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "task_id": task_id,
                "project_id": project_id,
            },
        })

    except Exception as e:
        logger.error(f"[simulate] Request error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500
