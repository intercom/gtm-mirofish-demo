"""
Pipeline sync data generator.
Produces realistic mock data for Fivetran syncs, Census reverse syncs,
dbt models/tests, and data freshness monitoring.
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..models.data_pipeline import SyncJob, DbtModel, DbtTest, DataFreshness


# ---------------------------------------------------------------------------
# Connector definitions
# ---------------------------------------------------------------------------

FIVETRAN_CONNECTORS = [
    {"name": "salesforce", "source": "Salesforce", "destination": "Snowflake", "schedule_minutes": 60},
    {"name": "stripe", "source": "Stripe", "destination": "Snowflake", "schedule_minutes": 360},
    {"name": "hubspot", "source": "HubSpot", "destination": "Snowflake", "schedule_minutes": 120},
    {"name": "zendesk", "source": "Zendesk", "destination": "Snowflake", "schedule_minutes": 180},
    {"name": "intercom", "source": "Intercom", "destination": "Snowflake", "schedule_minutes": 60},
]

CENSUS_CONNECTORS = [
    {"name": "census_lead_scoring", "source": "Snowflake", "destination": "Salesforce", "schedule_minutes": 360},
    {"name": "census_segments", "source": "Snowflake", "destination": "HubSpot", "schedule_minutes": 720},
    {"name": "census_tags", "source": "Snowflake", "destination": "Intercom", "schedule_minutes": 360},
]

ALL_CONNECTORS = FIVETRAN_CONNECTORS + CENSUS_CONNECTORS

# ---------------------------------------------------------------------------
# dbt model definitions (sources → staging → intermediate → marts)
# ---------------------------------------------------------------------------

DBT_MODELS: List[Dict[str, Any]] = [
    # Sources (raw layer)
    {"name": "src_salesforce_accounts", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_salesforce_opportunities", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_salesforce_contacts", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_stripe_charges", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_stripe_subscriptions", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_hubspot_companies", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_hubspot_deals", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_zendesk_tickets", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_intercom_conversations", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    {"name": "src_intercom_users", "schema": "raw", "materialization": "view", "depends_on": [], "tier": "source"},
    # Staging
    {"name": "stg_accounts", "schema": "staging", "materialization": "view", "depends_on": ["src_salesforce_accounts", "src_hubspot_companies"], "tier": "staging"},
    {"name": "stg_contacts", "schema": "staging", "materialization": "view", "depends_on": ["src_salesforce_contacts", "src_intercom_users"], "tier": "staging"},
    {"name": "stg_opportunities", "schema": "staging", "materialization": "view", "depends_on": ["src_salesforce_opportunities"], "tier": "staging"},
    {"name": "stg_charges", "schema": "staging", "materialization": "view", "depends_on": ["src_stripe_charges"], "tier": "staging"},
    {"name": "stg_subscriptions", "schema": "staging", "materialization": "view", "depends_on": ["src_stripe_subscriptions"], "tier": "staging"},
    {"name": "stg_deals", "schema": "staging", "materialization": "view", "depends_on": ["src_hubspot_deals"], "tier": "staging"},
    {"name": "stg_tickets", "schema": "staging", "materialization": "view", "depends_on": ["src_zendesk_tickets"], "tier": "staging"},
    {"name": "stg_conversations", "schema": "staging", "materialization": "view", "depends_on": ["src_intercom_conversations"], "tier": "staging"},
    # Intermediate
    {"name": "int_account_enriched", "schema": "intermediate", "materialization": "table", "depends_on": ["stg_accounts", "stg_contacts"], "tier": "intermediate"},
    {"name": "int_billing_events", "schema": "intermediate", "materialization": "incremental", "depends_on": ["stg_charges", "stg_subscriptions"], "tier": "intermediate"},
    {"name": "int_support_metrics", "schema": "intermediate", "materialization": "table", "depends_on": ["stg_tickets", "stg_conversations"], "tier": "intermediate"},
    {"name": "int_pipeline_stages", "schema": "intermediate", "materialization": "table", "depends_on": ["stg_opportunities", "stg_deals"], "tier": "intermediate"},
    # Marts
    {"name": "dim_accounts", "schema": "marts", "materialization": "table", "depends_on": ["int_account_enriched"], "tier": "mart"},
    {"name": "dim_contacts", "schema": "marts", "materialization": "table", "depends_on": ["stg_contacts", "int_account_enriched"], "tier": "mart"},
    {"name": "fct_opportunities", "schema": "marts", "materialization": "incremental", "depends_on": ["int_pipeline_stages", "dim_accounts"], "tier": "mart"},
    {"name": "fct_billing_events", "schema": "marts", "materialization": "incremental", "depends_on": ["int_billing_events", "dim_accounts"], "tier": "mart"},
    {"name": "fct_support_interactions", "schema": "marts", "materialization": "incremental", "depends_on": ["int_support_metrics", "dim_accounts", "dim_contacts"], "tier": "mart"},
    {"name": "mart_revenue", "schema": "marts", "materialization": "table", "depends_on": ["fct_billing_events", "dim_accounts"], "tier": "mart"},
    {"name": "mart_pipeline", "schema": "marts", "materialization": "table", "depends_on": ["fct_opportunities", "dim_accounts"], "tier": "mart"},
    {"name": "mart_customer_health", "schema": "marts", "materialization": "table", "depends_on": ["mart_revenue", "fct_support_interactions", "dim_accounts"], "tier": "mart"},
]

# ---------------------------------------------------------------------------
# Sync error templates
# ---------------------------------------------------------------------------

SYNC_ERRORS = [
    "API rate limit exceeded (429). Retry scheduled.",
    "Authentication token expired. Re-authorize connector.",
    "Snowflake warehouse COMPUTE_WH suspended. Resume warehouse.",
    "Source table schema changed — column 'status' type mismatch.",
    "Connection timeout after 300s. Check network/firewall rules.",
]

# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def _seed_rng(seed: str) -> random.Random:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return random.Random(h)


class PipelineSyncGenerator:
    """Generates deterministic mock pipeline data."""

    def __init__(self, seed: str = "mirofish-pipeline"):
        self._rng = _seed_rng(seed)
        self._now = datetime.utcnow()

    # -- Sync Jobs -----------------------------------------------------------

    def generate_sync_jobs(self, count: int = 100) -> List[SyncJob]:
        jobs: List[SyncJob] = []
        for i in range(count):
            connector = self._rng.choice(ALL_CONNECTORS)
            status = self._rng.choices(
                ["success", "failed", "running", "scheduled"],
                weights=[92, 5, 2, 1],
            )[0]

            days_ago = self._rng.uniform(0, 30)
            started = self._now - timedelta(days=days_ago)
            duration = self._rng.uniform(15, 600) if status != "scheduled" else None
            completed = (started + timedelta(seconds=duration)) if status in ("success", "failed") else None
            rows = self._rng.randint(500, 250_000) if status == "success" else 0
            error = self._rng.choice(SYNC_ERRORS) if status == "failed" else None

            jobs.append(SyncJob(
                id=f"sync_{i:04d}",
                connector_name=connector["name"],
                source=connector["source"],
                destination=connector["destination"],
                status=status,
                rows_synced=rows,
                started_at=started,
                completed_at=completed,
                duration_seconds=round(duration, 1) if duration else None,
                error_message=error,
            ))

        jobs.sort(key=lambda j: j.started_at, reverse=True)
        return jobs

    # -- Connectors ----------------------------------------------------------

    def generate_connectors(self, jobs: List[SyncJob]) -> List[Dict[str, Any]]:
        last_by_connector: Dict[str, SyncJob] = {}
        for job in jobs:
            if job.connector_name not in last_by_connector:
                last_by_connector[job.connector_name] = job
            elif job.started_at > last_by_connector[job.connector_name].started_at:
                last_by_connector[job.connector_name] = job

        connectors = []
        for c in ALL_CONNECTORS:
            last = last_by_connector.get(c["name"])
            connectors.append({
                "name": c["name"],
                "source": c["source"],
                "destination": c["destination"],
                "schedule_minutes": c["schedule_minutes"],
                "last_sync_status": last.status if last else "scheduled",
                "last_sync_at": last.started_at.isoformat() if last else None,
            })
        return connectors

    # -- dbt Models ----------------------------------------------------------

    def generate_dbt_models(self) -> List[DbtModel]:
        models: List[DbtModel] = []
        base_time = self._now - timedelta(hours=2)

        for i, spec in enumerate(DBT_MODELS):
            status = self._rng.choices(
                ["success", "error", "skipped"],
                weights=[93, 5, 2],
            )[0]
            exec_time = self._rng.uniform(0.5, 45.0) if spec["materialization"] != "view" else self._rng.uniform(0.1, 2.0)
            rows = self._rng.randint(100, 500_000) if status == "success" else 0

            models.append(DbtModel(
                name=spec["name"],
                schema=spec["schema"],
                materialization=spec["materialization"],
                depends_on=list(spec["depends_on"]),
                status=status,
                rows_affected=rows,
                execution_time_seconds=round(exec_time, 2),
                last_run=base_time + timedelta(seconds=i * 8),
            ))
        return models

    # -- dbt DAG -------------------------------------------------------------

    def generate_dbt_dag(self, models: List[DbtModel]) -> Dict[str, Any]:
        nodes = []
        edges = []
        for m in models:
            tier = "unknown"
            for spec in DBT_MODELS:
                if spec["name"] == m.name:
                    tier = spec["tier"]
                    break
            nodes.append({
                "id": m.name,
                "schema": m.schema,
                "materialization": m.materialization,
                "status": m.status,
                "execution_time_seconds": m.execution_time_seconds,
                "rows_affected": m.rows_affected,
                "tier": tier,
            })
            for dep in m.depends_on:
                edges.append({"source": dep, "target": m.name})
        return {"nodes": nodes, "edges": edges}

    # -- dbt Tests -----------------------------------------------------------

    def generate_dbt_tests(self, models: List[DbtModel], count: int = 50) -> List[DbtTest]:
        test_types = ["not_null", "unique", "relationships", "accepted_values"]
        tests: List[DbtTest] = []
        model_names = [m.name for m in models]
        base_time = self._now - timedelta(hours=1)

        for i in range(count):
            model_name = self._rng.choice(model_names)
            test_type = self._rng.choice(test_types)
            status = self._rng.choices(["pass", "fail", "warn"], weights=[95, 3, 2])[0]
            severity = "error" if test_type in ("not_null", "unique") else "warn"

            message = ""
            if status == "fail":
                message = f"Got 3 results, configured to fail if != 0"
            elif status == "warn":
                message = f"Got 1 result, configured to warn if != 0"

            tests.append(DbtTest(
                name=f"{test_type}_{model_name}_{i}",
                model=model_name,
                status=status,
                severity=severity,
                message=message,
                last_run=base_time + timedelta(seconds=i * 3),
            ))
        return tests

    # -- Data Freshness ------------------------------------------------------

    def generate_freshness(self, models: List[DbtModel]) -> List[DataFreshness]:
        mart_models = [m for m in models if m.schema == "marts"]
        freshness: List[DataFreshness] = []
        for m in mart_models:
            interval = self._rng.choice([1.0, 2.0, 6.0, 12.0, 24.0])
            hours_since = self._rng.uniform(0.1, 30.0)
            last_updated = self._now - timedelta(hours=hours_since)
            freshness.append(DataFreshness(
                table_name=m.name,
                last_updated=last_updated,
                expected_interval_hours=interval,
                is_stale=hours_since > interval,
            ))
        return freshness

    # -- Aggregate Stats -----------------------------------------------------

    def compute_stats(
        self,
        jobs: List[SyncJob],
        tests: List[DbtTest],
    ) -> Dict[str, Any]:
        completed = [j for j in jobs if j.status == "success"]
        total_rows = sum(j.rows_synced for j in completed)
        avg_duration = (
            sum(j.duration_seconds for j in completed if j.duration_seconds) / len(completed)
            if completed else 0
        )
        success_rate = len(completed) / len(jobs) * 100 if jobs else 0
        pass_count = sum(1 for t in tests if t.status == "pass")
        dbt_pass_rate = pass_count / len(tests) * 100 if tests else 0

        return {
            "total_syncs": len(jobs),
            "sync_success_rate": round(success_rate, 1),
            "avg_sync_duration_seconds": round(avg_duration, 1),
            "total_rows_synced": total_rows,
            "dbt_test_count": len(tests),
            "dbt_pass_rate": round(dbt_pass_rate, 1),
        }
