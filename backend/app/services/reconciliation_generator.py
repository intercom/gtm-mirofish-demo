"""
Reconciliation data generator.

Generates realistic three-way MRR reconciliation data:
  - 500 customer accounts with Salesforce, Billing, and Snowflake MRR values
  - Configurable discrepancy distribution (default: 85/8/5/2%)
  - 4 weekly ReconciliationRuns showing improvement trend
  - 10 ReconciliationRules covering common reconciliation checks

All data is deterministically seeded so results are consistent across calls.
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..models.reconciliation import (
    DiscrepancyType,
    ReconciliationRecord,
    ReconciliationRule,
    ReconciliationRun,
    ReconciliationStatus,
    RuleAction,
)
from ..utils.logger import get_logger

logger = get_logger('mirofish.reconciliation')

NUM_ACCOUNTS = 500

# Discrepancy distribution (percentages must sum to 100)
DIST_MATCH = 0.85
DIST_SMALL = 0.08       # < $100
DIST_MODERATE = 0.05    # $100 - $1000
DIST_LARGE = 0.02       # > $1000

# MRR ranges by segment
MRR_RANGES = {
    "SMB":        (500, 5_000),
    "Mid-Market": (5_000, 50_000),
    "Enterprise": (50_000, 500_000),
}

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.50, 0.35, 0.15]

INDUSTRIES = [
    "SaaS", "Fintech", "Healthcare", "E-commerce", "Education",
    "Media", "Manufacturing", "Logistics", "Real Estate", "Cybersecurity",
]

COMPANY_PREFIXES = [
    "Apex", "Nova", "Helix", "Vertex", "Orbit", "Pulse", "Nexus", "Flux",
    "Crest", "Spark", "Vanta", "Reva", "Drift", "Quanta", "Lyric",
    "Cobalt", "Fern", "Tidal", "Ember", "Aura", "Prism", "Slate",
    "Cedar", "Onyx", "Zephyr", "Nimbus", "Echo", "Atlas", "Forge",
    "Coral", "Haven", "Lumen", "Sage", "Summit", "Wren", "Cove",
    "Beacon", "Ridge", "Dune", "Glyph", "Halo", "Jade", "Kite",
    "Maple", "Opal", "Pike", "Quill", "Reed", "Silo", "Trek",
]

COMPANY_SUFFIXES = [
    "Labs", "Systems", "AI", "Tech", "Cloud", "Works", "HQ",
    "Digital", "Solutions", "Analytics", "IO", "Platform", "Data",
    "Ops", "Networks", "Software", "Group", "Dynamics", "Logic", "Health",
]


def _seed_rng(seed_str: str) -> random.Random:
    """Create a deterministic Random instance from a string seed."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


def _generate_company_name(rng: random.Random, index: int) -> str:
    prefix = rng.choice(COMPANY_PREFIXES)
    suffix = rng.choice(COMPANY_SUFFIXES)
    return f"{prefix} {suffix}"


def _pick_segment(rng: random.Random) -> str:
    return rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]


def _generate_base_mrr(rng: random.Random, segment: str) -> float:
    lo, hi = MRR_RANGES[segment]
    return round(rng.uniform(lo, hi), 2)


def _apply_discrepancy(
    rng: random.Random,
    base_mrr: float,
    category: str,
) -> Tuple[float, float, float, Optional[DiscrepancyType]]:
    """
    Given a base MRR and discrepancy category, return
    (sf_mrr, billing_mrr, snowflake_mrr, discrepancy_type).
    """
    if category == "match":
        return base_mrr, base_mrr, base_mrr, None

    if category == "small":
        # Timing lags or rounding — affects 1–2 sources
        disc_type = rng.choice([DiscrepancyType.TIMING_LAG, DiscrepancyType.CURRENCY_ROUNDING])
        delta = round(rng.uniform(0.01, 99.99), 2)
    elif category == "moderate":
        disc_type = rng.choice([DiscrepancyType.TIMING_LAG, DiscrepancyType.MISSING_IN_SOURCE])
        delta = round(rng.uniform(100.0, 999.99), 2)
    else:  # large
        disc_type = DiscrepancyType.AMOUNT_MISMATCH
        delta = round(rng.uniform(1000.0, 10_000.0), 2)

    # Randomly decide which source(s) diverge
    sf = base_mrr
    billing = base_mrr
    snow = base_mrr

    divergence = rng.choice(["billing", "snowflake", "both"])
    sign = rng.choice([1, -1])

    if divergence == "billing":
        billing = round(base_mrr + sign * delta, 2)
    elif divergence == "snowflake":
        snow = round(base_mrr + sign * delta, 2)
    else:
        billing = round(base_mrr + sign * delta * rng.uniform(0.3, 0.7), 2)
        snow = round(base_mrr - sign * delta * rng.uniform(0.3, 0.7), 2)

    # Ensure no negative MRR values
    sf = max(sf, 0.0)
    billing = max(billing, 0.0)
    snow = max(snow, 0.0)

    return sf, billing, snow, disc_type


def _classify_category(rng: random.Random) -> str:
    """Pick a discrepancy category based on the distribution."""
    r = rng.random()
    if r < DIST_MATCH:
        return "match"
    elif r < DIST_MATCH + DIST_SMALL:
        return "small"
    elif r < DIST_MATCH + DIST_SMALL + DIST_MODERATE:
        return "moderate"
    return "large"


def generate_accounts(seed: str = "recon-v1") -> List[Dict]:
    """Generate 500 account stubs with id, name, segment, industry."""
    rng = _seed_rng(seed)
    accounts = []
    seen_names = set()
    for i in range(NUM_ACCOUNTS):
        name = _generate_company_name(rng, i)
        # Guarantee unique names by appending index on collision
        if name in seen_names:
            name = f"{name} {i}"
        seen_names.add(name)
        accounts.append({
            "account_id": f"ACC-{i+1:04d}",
            "account_name": name,
            "segment": _pick_segment(rng),
            "industry": rng.choice(INDUSTRIES),
        })
    return accounts


def generate_records_for_run(
    accounts: List[Dict],
    run_index: int,
    total_runs: int = 4,
    seed: str = "recon-v1",
) -> List[ReconciliationRecord]:
    """
    Generate reconciliation records for a single run.

    Later runs show improvement: the effective match rate increases
    linearly from the base distribution to ~95% by the final run.
    """
    rng = _seed_rng(f"{seed}-run-{run_index}")

    # Improvement factor: 0.0 for first run → 1.0 for last run
    improvement = run_index / max(total_runs - 1, 1)
    # Boost match probability: interpolate toward 95% match
    effective_match = DIST_MATCH + improvement * (0.95 - DIST_MATCH)

    records = []
    for acct in accounts:
        acct_rng = _seed_rng(f"{seed}-run-{run_index}-{acct['account_id']}")
        base_mrr = _generate_base_mrr(acct_rng, acct["segment"])

        # Determine category with improvement-adjusted distribution
        r = acct_rng.random()
        remaining = 1.0 - effective_match
        # Scale non-match categories proportionally
        scale = remaining / (1.0 - DIST_MATCH) if DIST_MATCH < 1.0 else 0
        if r < effective_match:
            category = "match"
        elif r < effective_match + DIST_SMALL * scale:
            category = "small"
        elif r < effective_match + (DIST_SMALL + DIST_MODERATE) * scale:
            category = "moderate"
        else:
            category = "large"

        sf, billing, snow, disc_type = _apply_discrepancy(acct_rng, base_mrr, category)

        status = ReconciliationStatus.MATCHED if category == "match" else ReconciliationStatus.DISCREPANCY

        records.append(ReconciliationRecord(
            record_id=f"REC-{run_index+1}-{acct['account_id']}",
            account_id=acct["account_id"],
            account_name=acct["account_name"],
            sf_mrr=sf,
            billing_mrr=billing,
            snowflake_mrr=snow,
            sf_vs_billing_diff=round(sf - billing, 2),
            sf_vs_snowflake_diff=round(sf - snow, 2),
            billing_vs_snowflake_diff=round(billing - snow, 2),
            status=status,
            discrepancy_type=disc_type,
        ))

    return records


def generate_runs(seed: str = "recon-v1", num_runs: int = 4) -> List[ReconciliationRun]:
    """Generate weekly reconciliation runs with improvement trend."""
    accounts = generate_accounts(seed)
    runs = []

    # Runs are weekly, most recent first
    base_date = datetime(2026, 3, 24)

    for i in range(num_runs):
        run_date = base_date - timedelta(weeks=num_runs - 1 - i)
        records = generate_records_for_run(accounts, i, num_runs, seed)

        matched = sum(1 for r in records if r.status == ReconciliationStatus.MATCHED)
        discrepancies = [r for r in records if r.status != ReconciliationStatus.MATCHED]

        disc_values = []
        for r in discrepancies:
            disc_values.append(max(
                abs(r.sf_vs_billing_diff),
                abs(r.sf_vs_snowflake_diff),
                abs(r.billing_vs_snowflake_diff),
            ))

        total_disc = sum(disc_values)
        largest = max(disc_values) if disc_values else 0.0
        avg_disc = (total_disc / len(disc_values)) if disc_values else 0.0

        # Simulate run duration: 45–90 seconds
        rng = _seed_rng(f"{seed}-duration-{i}")
        duration = round(rng.uniform(45.0, 90.0), 1)

        runs.append(ReconciliationRun(
            run_id=f"RUN-{i+1:03d}",
            run_date=run_date.strftime("%Y-%m-%d"),
            total_accounts=len(records),
            matched_count=matched,
            discrepancy_count=len(discrepancies),
            total_discrepancy_value=total_disc,
            largest_discrepancy=largest,
            avg_discrepancy=avg_disc,
            run_duration_seconds=duration,
            records=records,
        ))

    return runs


def generate_rules() -> List[ReconciliationRule]:
    """Generate 10 reconciliation rules covering common checks."""
    return [
        ReconciliationRule(
            rule_id="RULE-001",
            name="Amount Tolerance",
            description="Flag differences exceeding $5 between any two sources",
            check_type="absolute_threshold",
            threshold=5.0,
            action=RuleAction.FLAG,
        ),
        ReconciliationRule(
            rule_id="RULE-002",
            name="Percentage Tolerance",
            description="Flag differences exceeding 1% of the base MRR",
            check_type="percentage_threshold",
            threshold=1.0,
            action=RuleAction.FLAG,
        ),
        ReconciliationRule(
            rule_id="RULE-003",
            name="Missing Record Check",
            description="Escalate when an account exists in one source but not others",
            check_type="missing_record",
            threshold=0.0,
            action=RuleAction.ESCALATE,
        ),
        ReconciliationRule(
            rule_id="RULE-004",
            name="Currency Normalization",
            description="Auto-resolve rounding differences under $0.50",
            check_type="rounding_tolerance",
            threshold=0.50,
            action=RuleAction.AUTO_RESOLVE,
        ),
        ReconciliationRule(
            rule_id="RULE-005",
            name="Timing Window (48h)",
            description="Auto-resolve discrepancies when billing timestamp is within 48 hours of sync",
            check_type="timing_window",
            threshold=48.0,
            action=RuleAction.AUTO_RESOLVE,
        ),
        ReconciliationRule(
            rule_id="RULE-006",
            name="Large Discrepancy Alert",
            description="Escalate any single-account discrepancy over $1,000",
            check_type="absolute_threshold",
            threshold=1000.0,
            action=RuleAction.ESCALATE,
        ),
        ReconciliationRule(
            rule_id="RULE-007",
            name="Duplicate Entry Detection",
            description="Flag accounts appearing more than once in the same run",
            check_type="duplicate_check",
            threshold=1.0,
            action=RuleAction.FLAG,
        ),
        ReconciliationRule(
            rule_id="RULE-008",
            name="Negative MRR Guard",
            description="Escalate records where any source reports negative MRR",
            check_type="negative_value",
            threshold=0.0,
            action=RuleAction.ESCALATE,
        ),
        ReconciliationRule(
            rule_id="RULE-009",
            name="Stale Data Detection",
            description="Flag when Snowflake data is more than 72 hours behind billing",
            check_type="staleness_window",
            threshold=72.0,
            action=RuleAction.FLAG,
        ),
        ReconciliationRule(
            rule_id="RULE-010",
            name="High-Value Account Priority",
            description="Escalate discrepancies on accounts with MRR above $50,000",
            check_type="value_threshold",
            threshold=50_000.0,
            action=RuleAction.ESCALATE,
        ),
    ]


class ReconciliationGenerator:
    """
    Facade for generating and caching reconciliation data.

    Data is generated once on first access and cached in memory.
    Thread-safe via lazy initialization with a consistent seed.
    """

    def __init__(self, seed: str = "recon-v1"):
        self._seed = seed
        self._accounts: Optional[List[Dict]] = None
        self._runs: Optional[List[ReconciliationRun]] = None
        self._rules: Optional[List[ReconciliationRule]] = None

    @property
    def accounts(self) -> List[Dict]:
        if self._accounts is None:
            self._accounts = generate_accounts(self._seed)
            logger.info(f"Generated {len(self._accounts)} reconciliation accounts")
        return self._accounts

    @property
    def runs(self) -> List[ReconciliationRun]:
        if self._runs is None:
            self._runs = generate_runs(self._seed)
            logger.info(f"Generated {len(self._runs)} reconciliation runs")
        return self._runs

    @property
    def rules(self) -> List[ReconciliationRule]:
        if self._rules is None:
            self._rules = generate_rules()
        return self._rules

    def get_current_run(self) -> ReconciliationRun:
        """Return the most recent run (last in the list)."""
        return self.runs[-1]

    def get_run(self, run_id: str) -> Optional[ReconciliationRun]:
        for run in self.runs:
            if run.run_id == run_id:
                return run
        return None

    def get_discrepancies(self, run_id: Optional[str] = None) -> List[ReconciliationRecord]:
        """Return discrepancy records, sorted by magnitude (largest first)."""
        run = self.get_run(run_id) if run_id else self.get_current_run()
        if not run:
            return []
        discs = [r for r in run.records if r.status != ReconciliationStatus.MATCHED]
        discs.sort(key=lambda r: max(
            abs(r.sf_vs_billing_diff),
            abs(r.sf_vs_snowflake_diff),
            abs(r.billing_vs_snowflake_diff),
        ), reverse=True)
        return discs

    def get_account_history(self, account_id: str) -> List[Dict]:
        """Return reconciliation history for a specific account across all runs."""
        history = []
        for run in self.runs:
            for record in run.records:
                if record.account_id == account_id:
                    entry = record.to_dict()
                    entry["run_id"] = run.run_id
                    entry["run_date"] = run.run_date
                    history.append(entry)
                    break
        return history

    def get_stats(self) -> Dict:
        """Return overall reconciliation health metrics."""
        current = self.get_current_run()
        trend = []
        for run in self.runs:
            trend.append({
                "run_id": run.run_id,
                "run_date": run.run_date,
                "match_rate": round(run.matched_count / run.total_accounts * 100, 2),
                "discrepancy_count": run.discrepancy_count,
                "total_discrepancy_value": round(run.total_discrepancy_value, 2),
            })

        first_run = self.runs[0]
        improving = current.matched_count > first_run.matched_count

        return {
            "current_match_rate": round(current.matched_count / current.total_accounts * 100, 2),
            "total_discrepancy_value": round(current.total_discrepancy_value, 2),
            "unresolved_count": current.discrepancy_count,
            "trend_direction": "improving" if improving else "stable",
            "total_accounts": current.total_accounts,
            "trend": trend,
        }

    def resolve_discrepancy(self, record_id: str, notes: str) -> Optional[ReconciliationRecord]:
        """Mark a discrepancy record as resolved with notes."""
        for run in self.runs:
            for record in run.records:
                if record.record_id == record_id:
                    record.status = ReconciliationStatus.RESOLVED
                    record.resolution_notes = notes
                    return record
        return None
