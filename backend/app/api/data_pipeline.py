"""
Data Pipeline API Blueprint.
Serves sync job history, connector status, dbt model/test data,
data freshness checks, and aggregate pipeline statistics.
All data is generated deterministically for demo purposes.
"""

from flask import Blueprint, jsonify, request

from ..services.pipeline_sync_generator import PipelineSyncGenerator
from ..utils.logger import get_logger

logger = get_logger('mirofish.pipeline')

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/pipeline')

# Lazily-initialized generator + cached data (generated once per process)
_generator = None
_cache: dict = {}


def _get_data():
    """Return cached pipeline data, generating on first access."""
    global _generator, _cache
    if _cache:
        return _cache

    _generator = PipelineSyncGenerator()
    jobs = _generator.generate_sync_jobs(count=100)
    models = _generator.generate_dbt_models()
    tests = _generator.generate_dbt_tests(models, count=50)
    _cache = {
        "jobs": jobs,
        "connectors": _generator.generate_connectors(jobs),
        "models": models,
        "dag": _generator.generate_dbt_dag(models),
        "tests": tests,
        "freshness": _generator.generate_freshness(models),
        "stats": _generator.compute_stats(jobs, tests),
    }
    return _cache


# ---------------------------------------------------------------------------
# Sync endpoints
# ---------------------------------------------------------------------------

@pipeline_bp.route('/syncs', methods=['GET'])
def list_syncs():
    """Sync job history with optional connector and status filters."""
    data = _get_data()
    jobs = data["jobs"]

    connector = request.args.get('connector')
    status = request.args.get('status')

    if connector:
        jobs = [j for j in jobs if j.connector_name == connector]
    if status:
        jobs = [j for j in jobs if j.status == status]

    return jsonify({"syncs": [j.to_dict() for j in jobs]})


@pipeline_bp.route('/syncs/<sync_id>', methods=['GET'])
def get_sync(sync_id):
    """Single sync job details."""
    data = _get_data()
    for job in data["jobs"]:
        if job.id == sync_id:
            return jsonify(job.to_dict())
    return jsonify({"error": f"Sync job {sync_id} not found"}), 404


# ---------------------------------------------------------------------------
# Connector endpoints
# ---------------------------------------------------------------------------

@pipeline_bp.route('/connectors', methods=['GET'])
def list_connectors():
    """List connectors with last sync status and schedule."""
    data = _get_data()
    return jsonify({"connectors": data["connectors"]})


# ---------------------------------------------------------------------------
# dbt endpoints
# ---------------------------------------------------------------------------

@pipeline_bp.route('/dbt/models', methods=['GET'])
def list_dbt_models():
    """List dbt models with status and dependencies."""
    data = _get_data()
    return jsonify({"models": [m.to_dict() for m in data["models"]]})


@pipeline_bp.route('/dbt/dag', methods=['GET'])
def get_dbt_dag():
    """DAG structure (nodes + edges) for visualization."""
    data = _get_data()
    return jsonify(data["dag"])


@pipeline_bp.route('/dbt/tests', methods=['GET'])
def list_dbt_tests():
    """Test results with optional status filter."""
    data = _get_data()
    tests = data["tests"]

    status = request.args.get('status')
    if status:
        tests = [t for t in tests if t.status == status]

    return jsonify({"tests": [t.to_dict() for t in tests]})


# ---------------------------------------------------------------------------
# Freshness & stats
# ---------------------------------------------------------------------------

@pipeline_bp.route('/freshness', methods=['GET'])
def get_freshness():
    """Data freshness check for all monitored tables."""
    data = _get_data()
    return jsonify({"freshness": [f.to_dict() for f in data["freshness"]]})


@pipeline_bp.route('/stats', methods=['GET'])
def get_stats():
    """Aggregate pipeline statistics."""
    data = _get_data()
    return jsonify(data["stats"])
