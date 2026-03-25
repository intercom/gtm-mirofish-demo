"""
GTM Scenario API
Serves pre-built GTM simulation scenario templates and seed data,
and provides a unified simulation endpoint that bridges the frontend
ScenarioBuilder with the backend ontology/graph pipeline.
"""

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


WALKTHROUGH_TIPS = {
    'outbound': {
        'seed': 'Outbound seed documents should include specific messaging angles, subject lines, and pain points. The richer the detail, the more nuanced agent reactions will be.',
        'personas': 'For outbound campaigns, include a mix of decision-makers (VP/Director) and evaluators (IT/Technical) to capture both strategic and tactical objections.',
        'config': 'Parallel platform mode lets you compare how the same message lands on Twitter vs Reddit — useful for multi-channel outbound strategy.',
        'outcomes': 'Watch for which subject line variants trigger engagement vs spam perception across different persona types.',
    },
    'inbound': {
        'seed': 'Inbound scenarios work best with real product copy or feature announcements that prospects would encounter organically.',
        'personas': 'Include end users alongside decision-makers — inbound motions often start bottom-up with champions who discover the product.',
        'config': 'Longer durations (72h+) reveal how inbound interest compounds or decays over time.',
        'outcomes': 'Look for which personas become champions and how word-of-mouth spreads through the simulated population.',
    },
    'product': {
        'seed': 'Include specific feature details and pricing context. Vague announcements produce vague reactions.',
        'personas': 'Product launches benefit from a broad persona mix — existing customers, prospects, and competitive users all react differently.',
        'config': 'Both platforms capture different conversation styles: Twitter for quick reactions, Reddit for deeper discussion threads.',
        'outcomes': 'Pay attention to feature adoption signals and which segments show the strongest upgrade intent.',
    },
    'signal': {
        'seed': 'Signal definitions should be specific and measurable. Include the behavioral triggers you expect to correlate with buying intent.',
        'personas': 'Technical evaluators and data-driven personas will stress-test signal accuracy more rigorously.',
        'config': 'More agents (300+) produce statistically significant signal validation across diverse firmographics.',
        'outcomes': 'The simulation reveals which signals actually predict engagement vs which are noise.',
    },
    'pricing': {
        'seed': 'Include current pricing, proposed changes, and the rationale. Agents react to perceived value, not just numbers.',
        'personas': 'CFOs and budget holders are critical for pricing simulations — they evaluate total cost of ownership differently than end users.',
        'config': 'Shorter durations capture immediate reactions; longer durations reveal churn risk and competitive switching behavior.',
        'outcomes': 'Watch for price sensitivity thresholds by segment and which packaging changes reduce objections.',
    },
}

DEFAULT_TIPS = {
    'seed': 'A detailed seed document produces more realistic and nuanced agent reactions.',
    'personas': 'Select persona types that match your real target audience for the most actionable insights.',
    'config': 'Default settings work well for most scenarios. Adjust agent count and duration based on how much statistical confidence you need.',
    'outcomes': 'The simulation generates multi-chapter reports with engagement predictions, objection analysis, and segment-specific insights.',
}


def _build_walkthrough(data):
    """Build walkthrough steps from scenario data."""
    category = data.get('category', 'general')
    tips = WALKTHROUGH_TIPS.get(category, DEFAULT_TIPS)
    agent_config = data.get('agent_config', {})
    sim_config = data.get('simulation_config', {})
    firmographics = agent_config.get('firmographic_mix', {})

    total_hours = sim_config.get('total_hours', 72)
    mins_per_round = sim_config.get('minutes_per_round', 30)
    total_rounds = int(total_hours * 60 / mins_per_round) if mins_per_round else 144

    return {
        'scenario_id': data.get('id'),
        'scenario_name': data.get('name'),
        'total_steps': 5,
        'steps': [
            {
                'step': 1,
                'key': 'overview',
                'title': 'What This Scenario Tests',
                'description': data.get('description', ''),
                'detail': f"This {category} scenario simulates how {agent_config.get('count', 200)} AI agents — each with a unique professional persona — react to your GTM content. The agents interact on simulated social platforms, producing realistic engagement data you can analyze before going live.",
                'tip': f"Category: {category.replace('_', ' ').title()}. {tips.get('seed', DEFAULT_TIPS['seed'])}",
            },
            {
                'step': 2,
                'key': 'seed_document',
                'title': 'The Seed Document',
                'description': 'This is the campaign content that feeds the simulation. Agents read, interpret, and react to this document based on their persona.',
                'seed_text': data.get('seed_text', ''),
                'seed_preview': data.get('seed_text', '')[:300] + ('...' if len(data.get('seed_text', '')) > 300 else ''),
                'word_count': len(data.get('seed_text', '').split()),
                'tip': tips.get('seed', DEFAULT_TIPS['seed']),
            },
            {
                'step': 3,
                'key': 'agent_population',
                'title': 'Agent Population',
                'description': f"{agent_config.get('count', 200)} AI agents will be generated with unique professional profiles drawn from your configured persona types and firmographic mix.",
                'personas': agent_config.get('persona_types', []),
                'industries': firmographics.get('industries', []),
                'company_sizes': firmographics.get('company_sizes', []),
                'regions': firmographics.get('regions', []),
                'agent_count': agent_config.get('count', 200),
                'tip': tips.get('personas', DEFAULT_TIPS['personas']),
            },
            {
                'step': 4,
                'key': 'simulation_config',
                'title': 'Simulation Settings',
                'description': f"The simulation runs for {total_hours} simulated hours across {total_rounds} rounds, with agents posting on {'Twitter and Reddit simultaneously' if sim_config.get('platform_mode') == 'parallel' else sim_config.get('platform_mode', 'parallel').title()}.",
                'duration_hours': total_hours,
                'minutes_per_round': mins_per_round,
                'total_rounds': total_rounds,
                'platform_mode': sim_config.get('platform_mode', 'parallel'),
                'tip': tips.get('config', DEFAULT_TIPS['config']),
            },
            {
                'step': 5,
                'key': 'expected_outcomes',
                'title': 'What You\'ll Learn',
                'description': 'After the simulation completes, MiroFish generates a multi-chapter predictive report with these insights:',
                'outcomes': data.get('expected_outputs', []),
                'tip': tips.get('outcomes', DEFAULT_TIPS['outcomes']),
            },
        ],
    }


@gtm_bp.route('/scenarios/<scenario_id>/walkthrough', methods=['GET'])
def get_scenario_walkthrough(scenario_id):
    """Get structured walkthrough steps for a guided scenario tour."""
    filepath = os.path.join(SCENARIOS_DIR, f'{scenario_id}.json')
    data = _load_json(filepath)
    if not data:
        return jsonify({'error': f'Scenario {scenario_id} not found'}), 404
    return jsonify(_build_walkthrough(data))


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
