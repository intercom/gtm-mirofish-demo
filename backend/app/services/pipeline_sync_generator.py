"""
Pipeline sync generator service.
Produces realistic, deterministic demo data for Fivetran/Census sync jobs,
dbt models (with DAG dependencies), dbt tests, and data freshness checks.
"""

import hashlib
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..models.data_pipeline import SyncJob, DbtModel, DbtTest, DataFreshness


# ---------------------------------------------------------------------------
# Connector definitions
# ---------------------------------------------------------------------------

FIVETRAN_CONNECTORS = [
    {"name": "salesforce_crm", "source": "Salesforce", "destination": "Snowflake",
     "schedule_minutes": 60, "avg_rows": 12_500},
    {"name": "stripe_payments", "source": "Stripe", "destination": "Snowflake",
     "schedule_minutes": 30, "avg_rows": 45_000},
    {"name": "hubspot_marketing", "source": "HubSpot", "destination": "Snowflake",
     "schedule_minutes": 120, "avg_rows": 8_200},
    {"name": "zendesk_support", "source": "Zendesk", "destination": "Snowflake",
     "schedule_minutes": 60, "avg_rows": 22_000},
    {"name": "intercom_messaging", "source": "Intercom", "destination": "Snowflake",
     "schedule_minutes": 30, "avg_rows": 31_000},
]

CENSUS_CONNECTORS = [
    {"name": "lead_scoring_sync", "source": "Snowflake", "destination": "Salesforce",
     "schedule_minutes": 360, "avg_rows": 3_400,
     "description": "Lead scoring model output → Salesforce Lead.score__c"},
    {"name": "segment_sync", "source": "Snowflake", "destination": "HubSpot",
     "schedule_minutes": 720, "avg_rows": 1_800,
     "description": "Audience segments → HubSpot contact lists"},
    {"name": "intercom_tag_sync", "source": "Snowflake", "destination": "Intercom",
     "schedule_minutes": 360, "avg_rows": 5_600,
     "description": "Product-usage tags → Intercom user tags"},
]

ALL_CONNECTORS = FIVETRAN_CONNECTORS + CENSUS_CONNECTORS

# ---------------------------------------------------------------------------
# Realistic failure messages
# ---------------------------------------------------------------------------

SYNC_ERRORS = [
    "Connection timeout after 30s — Salesforce API rate limit (1000 req/hr) exceeded",
    "OAuth token expired for HubSpot connector; re-authorize in Fivetran dashboard",
    "Snowflake warehouse TRANSFORM_WH suspended due to inactivity — auto-resume failed",
    "Schema drift detected: column `deal_stage` changed from VARCHAR(50) to VARCHAR(100)",
    "Census API 429: Salesforce bulk API daily limit (10,000 batches) reached",
    "Stripe webhook verification failed — secret key mismatch after rotation",
    "Zendesk API returned 503 Service Unavailable during maintenance window",
    "Row count validation failed: source=52,341 vs destination=52,103 (238 row delta)",
    "Intercom rate limit hit: 83 requests/10s exceeded for /contacts endpoint",
    "Snowflake query timeout on CENSUS_WH: SELECT from mart_lead_scores took >300s",
]

# ---------------------------------------------------------------------------
# dbt model definitions (30 models forming a DAG)
# ---------------------------------------------------------------------------

DBT_MODELS: List[Dict[str, Any]] = [
    # --- Sources (raw tables, materialized as views pointing at raw schema) ---
    {"name": "src_salesforce_accounts", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 14_200, "avg_time": 0.3},
    {"name": "src_salesforce_contacts", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 42_600, "avg_time": 0.3},
    {"name": "src_salesforce_opportunities", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 8_900, "avg_time": 0.2},
    {"name": "src_stripe_charges", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 215_000, "avg_time": 0.4},
    {"name": "src_stripe_subscriptions", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 6_300, "avg_time": 0.2},
    {"name": "src_hubspot_contacts", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 38_400, "avg_time": 0.3},
    {"name": "src_zendesk_tickets", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 97_000, "avg_time": 0.5},
    {"name": "src_intercom_conversations", "schema": "raw", "mat": "view", "deps": [],
     "avg_rows": 124_000, "avg_time": 0.6},

    # --- Staging (cleaned, typed, renamed) ---
    {"name": "stg_accounts", "schema": "staging", "mat": "view", "deps": ["src_salesforce_accounts"],
     "avg_rows": 14_200, "avg_time": 1.2},
    {"name": "stg_contacts", "schema": "staging", "mat": "view",
     "deps": ["src_salesforce_contacts", "src_hubspot_contacts"],
     "avg_rows": 58_000, "avg_time": 2.1},
    {"name": "stg_opportunities", "schema": "staging", "mat": "view",
     "deps": ["src_salesforce_opportunities"],
     "avg_rows": 8_900, "avg_time": 0.9},
    {"name": "stg_charges", "schema": "staging", "mat": "view", "deps": ["src_stripe_charges"],
     "avg_rows": 215_000, "avg_time": 3.4},
    {"name": "stg_subscriptions", "schema": "staging", "mat": "view",
     "deps": ["src_stripe_subscriptions"],
     "avg_rows": 6_300, "avg_time": 0.7},
    {"name": "stg_tickets", "schema": "staging", "mat": "view", "deps": ["src_zendesk_tickets"],
     "avg_rows": 97_000, "avg_time": 2.8},
    {"name": "stg_conversations", "schema": "staging", "mat": "view",
     "deps": ["src_intercom_conversations"],
     "avg_rows": 124_000, "avg_time": 3.1},

    # --- Intermediate (joins & business logic) ---
    {"name": "int_account_contacts", "schema": "intermediate", "mat": "table",
     "deps": ["stg_accounts", "stg_contacts"],
     "avg_rows": 58_000, "avg_time": 8.5},
    {"name": "int_opportunity_pipeline", "schema": "intermediate", "mat": "table",
     "deps": ["stg_opportunities", "stg_accounts"],
     "avg_rows": 8_900, "avg_time": 4.2},
    {"name": "int_billing_events", "schema": "intermediate", "mat": "incremental",
     "deps": ["stg_charges", "stg_subscriptions", "stg_accounts"],
     "avg_rows": 215_000, "avg_time": 12.6},
    {"name": "int_support_metrics", "schema": "intermediate", "mat": "table",
     "deps": ["stg_tickets", "stg_conversations", "stg_accounts"],
     "avg_rows": 221_000, "avg_time": 15.3},
    {"name": "int_contact_engagement", "schema": "intermediate", "mat": "table",
     "deps": ["stg_contacts", "stg_conversations", "stg_tickets"],
     "avg_rows": 58_000, "avg_time": 9.7},

    # --- Dimension tables ---
    {"name": "dim_accounts", "schema": "marts", "mat": "table",
     "deps": ["int_account_contacts"],
     "avg_rows": 14_200, "avg_time": 3.4},
    {"name": "dim_contacts", "schema": "marts", "mat": "table",
     "deps": ["int_account_contacts", "int_contact_engagement"],
     "avg_rows": 58_000, "avg_time": 6.1},
    {"name": "dim_products", "schema": "marts", "mat": "table",
     "deps": ["stg_subscriptions"],
     "avg_rows": 42, "avg_time": 0.8},

    # --- Fact tables ---
    {"name": "fct_opportunities", "schema": "marts", "mat": "incremental",
     "deps": ["int_opportunity_pipeline", "dim_accounts"],
     "avg_rows": 8_900, "avg_time": 5.2},
    {"name": "fct_billing_events", "schema": "marts", "mat": "incremental",
     "deps": ["int_billing_events", "dim_accounts", "dim_products"],
     "avg_rows": 215_000, "avg_time": 18.4},
    {"name": "fct_support_interactions", "schema": "marts", "mat": "incremental",
     "deps": ["int_support_metrics", "dim_accounts", "dim_contacts"],
     "avg_rows": 221_000, "avg_time": 16.9},

    # --- Mart / reporting tables ---
    {"name": "mart_revenue", "schema": "marts", "mat": "table",
     "deps": ["fct_billing_events", "dim_accounts"],
     "avg_rows": 14_200, "avg_time": 7.3},
    {"name": "mart_pipeline", "schema": "marts", "mat": "table",
     "deps": ["fct_opportunities", "dim_accounts"],
     "avg_rows": 14_200, "avg_time": 4.8},
    {"name": "mart_lead_scores", "schema": "marts", "mat": "table",
     "deps": ["dim_contacts", "fct_opportunities", "fct_support_interactions"],
     "avg_rows": 58_000, "avg_time": 11.2},
    {"name": "mart_customer_health", "schema": "marts", "mat": "table",
     "deps": ["dim_accounts", "fct_billing_events", "fct_support_interactions"],
     "avg_rows": 14_200, "avg_time": 8.9},
]

# ---------------------------------------------------------------------------
# dbt test definitions (50 tests)
# ---------------------------------------------------------------------------

_TEST_TEMPLATES: List[Dict[str, Any]] = [
    # not_null tests (16)
    {"test": "not_null", "model": "dim_accounts", "col": "account_id"},
    {"test": "not_null", "model": "dim_accounts", "col": "account_name"},
    {"test": "not_null", "model": "dim_contacts", "col": "contact_id"},
    {"test": "not_null", "model": "dim_contacts", "col": "email"},
    {"test": "not_null", "model": "dim_products", "col": "product_id"},
    {"test": "not_null", "model": "fct_opportunities", "col": "opportunity_id"},
    {"test": "not_null", "model": "fct_opportunities", "col": "account_id"},
    {"test": "not_null", "model": "fct_billing_events", "col": "charge_id"},
    {"test": "not_null", "model": "fct_billing_events", "col": "amount_cents"},
    {"test": "not_null", "model": "fct_support_interactions", "col": "interaction_id"},
    {"test": "not_null", "model": "mart_revenue", "col": "account_id"},
    {"test": "not_null", "model": "mart_revenue", "col": "mrr_cents"},
    {"test": "not_null", "model": "mart_pipeline", "col": "account_id"},
    {"test": "not_null", "model": "mart_lead_scores", "col": "contact_id"},
    {"test": "not_null", "model": "mart_lead_scores", "col": "score"},
    {"test": "not_null", "model": "stg_accounts", "col": "account_id"},

    # unique tests (12)
    {"test": "unique", "model": "dim_accounts", "col": "account_id"},
    {"test": "unique", "model": "dim_contacts", "col": "contact_id"},
    {"test": "unique", "model": "dim_products", "col": "product_id"},
    {"test": "unique", "model": "fct_opportunities", "col": "opportunity_id"},
    {"test": "unique", "model": "fct_billing_events", "col": "charge_id"},
    {"test": "unique", "model": "fct_support_interactions", "col": "interaction_id"},
    {"test": "unique", "model": "stg_accounts", "col": "account_id"},
    {"test": "unique", "model": "stg_contacts", "col": "contact_id"},
    {"test": "unique", "model": "stg_charges", "col": "charge_id"},
    {"test": "unique", "model": "stg_tickets", "col": "ticket_id"},
    {"test": "unique", "model": "stg_conversations", "col": "conversation_id"},
    {"test": "unique", "model": "stg_subscriptions", "col": "subscription_id"},

    # relationships tests (12)
    {"test": "relationships", "model": "fct_opportunities",
     "col": "account_id", "to": "dim_accounts.account_id"},
    {"test": "relationships", "model": "fct_billing_events",
     "col": "account_id", "to": "dim_accounts.account_id"},
    {"test": "relationships", "model": "fct_billing_events",
     "col": "product_id", "to": "dim_products.product_id"},
    {"test": "relationships", "model": "fct_support_interactions",
     "col": "account_id", "to": "dim_accounts.account_id"},
    {"test": "relationships", "model": "fct_support_interactions",
     "col": "contact_id", "to": "dim_contacts.contact_id"},
    {"test": "relationships", "model": "dim_contacts",
     "col": "account_id", "to": "dim_accounts.account_id"},
    {"test": "relationships", "model": "mart_revenue",
     "col": "account_id", "to": "dim_accounts.account_id"},
    {"test": "relationships", "model": "mart_pipeline",
     "col": "account_id", "to": "dim_accounts.account_id"},
    {"test": "relationships", "model": "mart_lead_scores",
     "col": "contact_id", "to": "dim_contacts.contact_id"},
    {"test": "relationships", "model": "int_account_contacts",
     "col": "account_id", "to": "stg_accounts.account_id"},
    {"test": "relationships", "model": "int_opportunity_pipeline",
     "col": "account_id", "to": "stg_accounts.account_id"},
    {"test": "relationships", "model": "int_billing_events",
     "col": "account_id", "to": "stg_accounts.account_id"},

    # accepted_values tests (10)
    {"test": "accepted_values", "model": "fct_opportunities",
     "col": "stage", "values": ["Prospect", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]},
    {"test": "accepted_values", "model": "fct_billing_events",
     "col": "event_type", "values": ["charge", "refund", "dispute", "payout"]},
    {"test": "accepted_values", "model": "fct_billing_events",
     "col": "currency", "values": ["usd", "eur", "gbp"]},
    {"test": "accepted_values", "model": "dim_accounts",
     "col": "tier", "values": ["Enterprise", "Mid-Market", "SMB", "Free"]},
    {"test": "accepted_values", "model": "dim_accounts",
     "col": "region", "values": ["NA", "EMEA", "APAC", "LATAM"]},
    {"test": "accepted_values", "model": "dim_contacts",
     "col": "lifecycle_stage", "values": ["Lead", "MQL", "SQL", "Opportunity", "Customer", "Churned"]},
    {"test": "accepted_values", "model": "fct_support_interactions",
     "col": "channel", "values": ["email", "chat", "phone", "messenger"]},
    {"test": "accepted_values", "model": "fct_support_interactions",
     "col": "priority", "values": ["low", "normal", "high", "urgent"]},
    {"test": "accepted_values", "model": "mart_lead_scores",
     "col": "score_bucket", "values": ["Hot", "Warm", "Cool", "Cold"]},
    {"test": "accepted_values", "model": "mart_pipeline",
     "col": "forecast_category", "values": ["Commit", "Best Case", "Pipeline", "Omitted"]},
]


# ---------------------------------------------------------------------------
# Deterministic pseudo-random helpers
# ---------------------------------------------------------------------------

def _seed_int(seed_str: str) -> int:
    """Derive a deterministic integer from a string seed."""
    return int(hashlib.md5(seed_str.encode()).hexdigest(), 16)


def _seeded_float(seed_str: str) -> float:
    """Return a deterministic float in [0, 1) from a string seed."""
    return (_seed_int(seed_str) % 10_000_000) / 10_000_000


def _vary(base: float, seed_str: str, pct: float = 0.25) -> float:
    """Return base ± pct variation, seeded deterministically."""
    f = _seeded_float(seed_str)
    return base * (1.0 + (f * 2 - 1) * pct)


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class PipelineSyncGenerator:
    """
    Generates deterministic, realistic pipeline data for demo purposes.
    All data is generated on-the-fly from fixed seeds — no database needed.
    """

    def __init__(self, reference_time: datetime | None = None):
        self._now = reference_time or datetime.utcnow()

    # ---- Sync jobs ----------------------------------------------------------

    def generate_sync_jobs(self, count: int = 100) -> List[SyncJob]:
        """
        Generate *count* sync jobs spread over the last 30 days.
        Distribution: 92% success, 5% failed, 3% running.
        """
        jobs: List[SyncJob] = []
        n_connectors = len(ALL_CONNECTORS)

        for i in range(count):
            connector = ALL_CONNECTORS[i % n_connectors]
            seed = f"sync_{connector['name']}_{i}"

            # Spread start times over last 30 days
            offset_hours = _vary(30 * 24 * (i / count), seed + "_t", pct=0.15)
            started = self._now - timedelta(hours=offset_hours)

            # Determine status based on position in the list (deterministic distribution)
            bucket = _seeded_float(seed + "_status")
            if bucket < 0.03:
                status = "running"
            elif bucket < 0.08:
                status = "failed"
            else:
                status = "success"

            rows = int(_vary(connector["avg_rows"], seed + "_rows", pct=0.35))
            duration = _vary(connector["schedule_minutes"] * 0.4, seed + "_dur", pct=0.5)

            error_msg = None
            completed_at = None

            if status == "success":
                completed_at = (started + timedelta(seconds=duration)).isoformat()
            elif status == "failed":
                duration = _vary(duration * 0.6, seed + "_fail_dur", pct=0.3)
                completed_at = (started + timedelta(seconds=duration)).isoformat()
                error_idx = _seed_int(seed + "_err") % len(SYNC_ERRORS)
                error_msg = SYNC_ERRORS[error_idx]
                rows = int(rows * _seeded_float(seed + "_partial"))
            else:
                # running — started recently, no completion yet
                started = self._now - timedelta(seconds=_vary(120, seed + "_run", pct=0.8))
                duration = None

            jobs.append(SyncJob(
                id=f"sync_{hashlib.md5(seed.encode()).hexdigest()[:12]}",
                connector_name=connector["name"],
                source=connector["source"],
                destination=connector["destination"],
                status=status,
                rows_synced=max(0, rows),
                started_at=started.isoformat(),
                completed_at=completed_at,
                duration_seconds=round(duration, 1) if duration else None,
                error_message=error_msg,
            ))

        jobs.sort(key=lambda j: j.started_at, reverse=True)
        return jobs

    # ---- Connectors summary -------------------------------------------------

    def get_connectors(self) -> List[Dict[str, Any]]:
        """Return connector metadata with latest sync status."""
        jobs = self.generate_sync_jobs()
        latest: Dict[str, SyncJob] = {}
        for job in jobs:
            if job.connector_name not in latest:
                latest[job.connector_name] = job

        connectors = []
        for c in ALL_CONNECTORS:
            last_job = latest.get(c["name"])
            connectors.append({
                "name": c["name"],
                "source": c["source"],
                "destination": c["destination"],
                "schedule_minutes": c["schedule_minutes"],
                "description": c.get("description", f"{c['source']} → {c['destination']}"),
                "last_sync_status": last_job.status if last_job else "scheduled",
                "last_sync_at": last_job.started_at if last_job else None,
            })
        return connectors

    # ---- dbt models ---------------------------------------------------------

    def generate_dbt_models(self) -> List[DbtModel]:
        """Generate 30 dbt models with DAG dependencies."""
        last_run = (self._now - timedelta(minutes=47)).isoformat()
        models: List[DbtModel] = []

        for i, m in enumerate(DBT_MODELS):
            seed = f"dbt_model_{m['name']}"
            bucket = _seeded_float(seed + "_status")

            if bucket < 0.03:
                status = "error"
            elif bucket < 0.06:
                status = "skipped"
            else:
                status = "success"

            # If a dependency has error, this model is skipped
            dep_statuses = [
                _seeded_float(f"dbt_model_{d}_status") for d in m["deps"]
            ]
            if any(s < 0.03 for s in dep_statuses):
                status = "skipped"

            rows = int(_vary(m["avg_rows"], seed + "_rows", pct=0.10))
            exec_time = round(_vary(m["avg_time"], seed + "_time", pct=0.20), 2)

            models.append(DbtModel(
                name=m["name"],
                schema=m["schema"],
                materialization=m["mat"],
                depends_on=list(m["deps"]),
                status=status,
                rows_affected=rows if status == "success" else 0,
                execution_time_seconds=exec_time if status != "skipped" else 0.0,
                last_run=last_run,
            ))

        return models

    def get_dbt_dag(self) -> Dict[str, Any]:
        """Return the dbt DAG as nodes + edges for visualization."""
        models = self.generate_dbt_models()
        model_map = {m.name: m for m in models}

        nodes = []
        edges = []

        for m in models:
            nodes.append({
                "id": m.name,
                "schema": m.schema,
                "materialization": m.materialization,
                "status": m.status,
            })
            for dep in m.depends_on:
                edges.append({"source": dep, "target": m.name})

        return {"nodes": nodes, "edges": edges}

    # ---- dbt tests ----------------------------------------------------------

    def generate_dbt_tests(self) -> List[DbtTest]:
        """
        Generate 50 dbt tests.
        Distribution: 95% pass, 3% fail, 2% warn.
        """
        last_run = (self._now - timedelta(minutes=47)).isoformat()
        tests: List[DbtTest] = []

        for i, t in enumerate(_TEST_TEMPLATES):
            seed = f"dbt_test_{t['test']}_{t['model']}_{t['col']}"
            bucket = _seeded_float(seed + "_status")

            if bucket < 0.02:
                status = "warn"
                severity = "warn"
            elif bucket < 0.05:
                status = "fail"
                severity = "error"
            else:
                status = "pass"
                severity = "error" if t["test"] in ("not_null", "unique") else "warn"

            message = None
            if status == "fail":
                message = self._failure_message(t)
            elif status == "warn":
                message = self._warn_message(t)

            test_name = self._test_name(t)

            tests.append(DbtTest(
                name=test_name,
                model=t["model"],
                status=status,
                severity=severity,
                message=message,
                last_run=last_run,
            ))

        return tests

    # ---- Data freshness -----------------------------------------------------

    def generate_freshness(self) -> List[DataFreshness]:
        """Check freshness for key tables based on connector schedules."""
        entries: List[DataFreshness] = []
        freshness_targets = [
            ("raw.salesforce_accounts", 1.5),
            ("raw.salesforce_contacts", 1.5),
            ("raw.salesforce_opportunities", 1.5),
            ("raw.stripe_charges", 1.0),
            ("raw.stripe_subscriptions", 1.0),
            ("raw.hubspot_contacts", 3.0),
            ("raw.zendesk_tickets", 1.5),
            ("raw.intercom_conversations", 1.0),
            ("marts.dim_accounts", 2.0),
            ("marts.dim_contacts", 2.0),
            ("marts.fct_billing_events", 2.0),
            ("marts.mart_revenue", 4.0),
            ("marts.mart_pipeline", 4.0),
            ("marts.mart_lead_scores", 4.0),
        ]

        for table, expected_hours in freshness_targets:
            seed = f"freshness_{table}"
            hours_ago = _vary(expected_hours * 0.6, seed, pct=0.5)
            last_updated = self._now - timedelta(hours=hours_ago)
            is_stale = hours_ago > expected_hours

            entries.append(DataFreshness(
                table_name=table,
                last_updated=last_updated.isoformat(),
                expected_interval_hours=expected_hours,
                is_stale=is_stale,
            ))

        return entries

    # ---- Aggregate stats ----------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return high-level pipeline health stats."""
        jobs = self.generate_sync_jobs()
        models = self.generate_dbt_models()
        tests = self.generate_dbt_tests()
        freshness = self.generate_freshness()

        success_jobs = [j for j in jobs if j.status == "success"]
        completed_jobs = [j for j in jobs if j.status in ("success", "failed")]

        total_rows = sum(j.rows_synced for j in jobs)
        avg_duration = (
            sum(j.duration_seconds for j in completed_jobs if j.duration_seconds) /
            max(len(completed_jobs), 1)
        )

        test_pass = sum(1 for t in tests if t.status == "pass")
        stale_count = sum(1 for f in freshness if f.is_stale)

        return {
            "sync_success_rate": round(len(success_jobs) / max(len(jobs), 1) * 100, 1),
            "total_syncs": len(jobs),
            "total_rows_synced": total_rows,
            "avg_sync_duration_seconds": round(avg_duration, 1),
            "dbt_model_count": len(models),
            "dbt_models_success": sum(1 for m in models if m.status == "success"),
            "dbt_models_error": sum(1 for m in models if m.status == "error"),
            "dbt_test_pass_rate": round(test_pass / max(len(tests), 1) * 100, 1),
            "dbt_test_count": len(tests),
            "dbt_tests_failing": sum(1 for t in tests if t.status == "fail"),
            "stale_tables": stale_count,
            "total_freshness_checks": len(freshness),
        }

    # ---- Private helpers ----------------------------------------------------

    @staticmethod
    def _test_name(t: Dict[str, Any]) -> str:
        test_type = t["test"]
        if test_type == "relationships":
            return f"{test_type}_{t['model']}_{t['col']}__{t['to'].replace('.', '_')}"
        if test_type == "accepted_values":
            return f"{test_type}_{t['model']}_{t['col']}"
        return f"{test_type}_{t['model']}_{t['col']}"

    @staticmethod
    def _failure_message(t: Dict[str, Any]) -> str:
        test_type = t["test"]
        if test_type == "not_null":
            return f"Got 23 rows with null values for {t['model']}.{t['col']}"
        if test_type == "unique":
            return f"Got 7 duplicate values for {t['model']}.{t['col']}"
        if test_type == "relationships":
            return f"Got 12 orphaned rows in {t['model']}.{t['col']} not found in {t['to']}"
        if test_type == "accepted_values":
            return f"Got unexpected values for {t['model']}.{t['col']}: ['UNKNOWN', '']"
        return "Test failed"

    @staticmethod
    def _warn_message(t: Dict[str, Any]) -> str:
        test_type = t["test"]
        if test_type == "not_null":
            return f"Got 2 rows with null values for {t['model']}.{t['col']} (warn threshold)"
        if test_type == "unique":
            return f"Got 1 duplicate value for {t['model']}.{t['col']} (warn threshold)"
        if test_type == "relationships":
            return f"Got 3 orphaned rows in {t['model']}.{t['col']} (warn threshold)"
        if test_type == "accepted_values":
            return f"Got 1 unexpected value for {t['model']}.{t['col']}: ['']"
        return "Test warned"
