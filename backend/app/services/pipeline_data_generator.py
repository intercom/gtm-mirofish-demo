"""
Pipeline Data Generator Service

Generates realistic B2B SaaS pipeline data for demo visualizations:
- 6 months of monthly FunnelSnapshots with seasonal variance
- 200 ConversionEvents tracking individual leads through stages
- Velocity metrics (avg days per stage, total cycle time)
"""

import random
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.pipeline')

# ---------------------------------------------------------------------------
# Pipeline stage definitions
# ---------------------------------------------------------------------------

PIPELINE_STAGES = [
    'Lead',
    'MQL',
    'SQL',
    'Opportunity',
    'Proposal',
    'Negotiation',
    'Closed Won',
]

# Base conversion rates between consecutive stages
BASE_CONVERSION_RATES = {
    'Lead→MQL': 0.30,
    'MQL→SQL': 0.40,
    'SQL→Opportunity': 0.60,
    'Opportunity→Proposal': 0.50,
    'Proposal→Negotiation': 0.70,
    'Negotiation→Closed Won': 0.40,
}

# Average days a lead spends in each stage
BASE_STAGE_DAYS = {
    'Lead': 7,
    'MQL': 12,
    'SQL': 15,
    'Opportunity': 20,
    'Proposal': 10,
    'Negotiation': 18,
}

# Company names for generating realistic conversion events
COMPANY_NAMES = [
    'Acme Corp', 'TechFlow', 'DataBridge', 'CloudNine Systems', 'Pinnacle AI',
    'NexGen Labs', 'Velocity SaaS', 'Quantum Digital', 'FusionWorks', 'Apex Analytics',
    'BlueShift Inc', 'Catalyst IO', 'DriftWave', 'EchoPoint', 'FlareStack',
    'GreenField Tech', 'HyperLoop Co', 'InnoVate', 'JetStream AI', 'Kinetica',
    'LightPath', 'MeshLogic', 'NovaStar', 'OmniLayer', 'PulseMetrics',
    'Radiant Labs', 'SignalHQ', 'TrueNorth', 'UplinkData', 'VortexSystems',
    'WarpSpeed', 'XenoTech', 'YieldForce', 'ZenithOps', 'AlphaWave',
    'BrightEdge', 'CoreStack', 'DeepVault', 'ElasticPath', 'ForgeAI',
]

BASE_LEADS_PER_MONTH = 1000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FunnelSnapshot:
    """Monthly snapshot of the pipeline funnel."""
    month: str  # YYYY-MM
    stages: Dict[str, int] = field(default_factory=dict)
    conversion_rates: Dict[str, float] = field(default_factory=dict)
    total_leads_in: int = 0
    cumulative_won: int = 0
    cumulative_lost: int = 0
    cumulative_value: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ConversionEvent:
    """A single lead/opportunity moving between pipeline stages."""
    event_id: str
    lead_id: str
    company_name: str
    from_stage: str
    to_stage: str
    timestamp: str  # ISO 8601
    days_in_stage: int
    deal_value: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VelocityMetrics:
    """Stage-by-stage velocity statistics."""
    stage_metrics: List[Dict] = field(default_factory=list)
    total_cycle_days: float = 0.0
    median_cycle_days: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Seasonal helpers
# ---------------------------------------------------------------------------

def _seasonal_lead_multiplier(month: int) -> float:
    """Q4 (Oct-Dec) gets 20% more leads."""
    if month in (10, 11, 12):
        return 1.20
    return 1.0


def _seasonal_conversion_multiplier(month: int) -> float:
    """Q1 (Jan-Mar) has 10% lower conversion rates."""
    if month in (1, 2, 3):
        return 0.90
    return 1.0


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class PipelineDataGenerator:
    """Generates deterministic pipeline data for demo/mock mode."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def _vary(self, base: float, pct: float = 0.10) -> float:
        """Apply ±pct random variance to a base value."""
        return base * (1 + self._rng.uniform(-pct, pct))

    # ------------------------------------------------------------------
    # Funnel snapshots
    # ------------------------------------------------------------------

    def generate_funnel_history(self, months: int = 6) -> List[FunnelSnapshot]:
        """Generate *months* monthly funnel snapshots ending at current month."""
        now = datetime.utcnow()
        snapshots: List[FunnelSnapshot] = []
        cumulative_won = 0
        cumulative_lost = 0
        cumulative_value = 0.0

        for i in range(months):
            # Walk backwards so index 0 is oldest
            offset = months - 1 - i
            dt = now - timedelta(days=30 * offset)
            month_label = dt.strftime('%Y-%m')
            cal_month = dt.month

            # Seasonal lead volume
            raw_leads = int(self._vary(BASE_LEADS_PER_MONTH) * _seasonal_lead_multiplier(cal_month))
            conv_mult = _seasonal_conversion_multiplier(cal_month)

            # Walk leads through each stage
            stages: Dict[str, int] = {}
            rates: Dict[str, float] = {}
            current_count = raw_leads

            for idx, stage in enumerate(PIPELINE_STAGES):
                stages[stage] = current_count
                if idx < len(PIPELINE_STAGES) - 1:
                    next_stage = PIPELINE_STAGES[idx + 1]
                    key = f'{stage}→{next_stage}'
                    base_rate = BASE_CONVERSION_RATES[key]
                    rate = min(self._vary(base_rate, 0.10) * conv_mult, 0.99)
                    rates[key] = round(rate, 4)
                    current_count = int(current_count * rate)

            won = stages['Closed Won']
            lost = stages['Negotiation'] - won
            cumulative_won += won
            cumulative_lost += lost
            avg_deal = self._vary(45000, 0.15)
            cumulative_value += won * avg_deal

            snapshots.append(FunnelSnapshot(
                month=month_label,
                stages=stages,
                conversion_rates=rates,
                total_leads_in=raw_leads,
                cumulative_won=cumulative_won,
                cumulative_lost=cumulative_lost,
                cumulative_value=round(cumulative_value, 2),
            ))

        return snapshots

    # ------------------------------------------------------------------
    # Conversion events
    # ------------------------------------------------------------------

    def generate_conversion_events(self, count: int = 200) -> List[ConversionEvent]:
        """Generate *count* individual conversion events over the past 6 months."""
        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=180)
        events: List[ConversionEvent] = []

        # Pre-generate a pool of leads (over-provision to account for
        # leads whose later transitions get clipped by the `now` boundary)
        num_leads = count // 2 + 30
        leads = []
        for i in range(num_leads):
            company = self._rng.choice(COMPANY_NAMES)
            lead_id = f'lead-{i+1:04d}'
            deal_value = round(self._rng.uniform(15000, 120000), 2)
            # Random entry point in the 6-month window
            entry_offset = self._rng.randint(0, 150)
            entry_date = six_months_ago + timedelta(days=entry_offset)
            leads.append({
                'lead_id': lead_id,
                'company': company,
                'deal_value': deal_value,
                'entry_date': entry_date,
            })

        event_counter = 0
        for lead in leads:
            if event_counter >= count:
                break

            current_date = lead['entry_date']
            # Determine how far this lead progresses (weighted toward earlier drop-off)
            max_stage_idx = self._rng.choices(
                range(1, len(PIPELINE_STAGES)),
                weights=[30, 20, 18, 15, 10, 7],
                k=1,
            )[0]

            for stage_idx in range(max_stage_idx):
                if event_counter >= count:
                    break

                from_stage = PIPELINE_STAGES[stage_idx]
                to_stage = PIPELINE_STAGES[stage_idx + 1]
                days_in = max(1, int(self._vary(BASE_STAGE_DAYS[from_stage], 0.30)))
                current_date += timedelta(days=days_in)

                if current_date > now:
                    break

                event_id = hashlib.md5(
                    f'{lead["lead_id"]}-{from_stage}-{to_stage}'.encode()
                ).hexdigest()[:12]

                events.append(ConversionEvent(
                    event_id=event_id,
                    lead_id=lead['lead_id'],
                    company_name=lead['company'],
                    from_stage=from_stage,
                    to_stage=to_stage,
                    timestamp=current_date.isoformat() + 'Z',
                    days_in_stage=days_in,
                    deal_value=lead['deal_value'],
                ))
                event_counter += 1

        # Sort chronologically
        events.sort(key=lambda e: e.timestamp)
        return events

    # ------------------------------------------------------------------
    # Velocity metrics
    # ------------------------------------------------------------------

    def generate_velocity_metrics(
        self, events: Optional[List[ConversionEvent]] = None,
    ) -> VelocityMetrics:
        """Calculate velocity metrics from conversion events."""
        if events is None:
            events = self.generate_conversion_events()

        # Collect days-in-stage grouped by from_stage
        stage_days: Dict[str, List[int]] = {s: [] for s in PIPELINE_STAGES[:-1]}
        lead_total_days: Dict[str, int] = {}

        for ev in events:
            if ev.from_stage in stage_days:
                stage_days[ev.from_stage].append(ev.days_in_stage)
            lead_total_days.setdefault(ev.lead_id, 0)
            lead_total_days[ev.lead_id] += ev.days_in_stage

        stage_metrics = []
        for stage in PIPELINE_STAGES[:-1]:
            days_list = stage_days[stage]
            if days_list:
                avg = sum(days_list) / len(days_list)
                sorted_d = sorted(days_list)
                median = sorted_d[len(sorted_d) // 2]
            else:
                avg = BASE_STAGE_DAYS.get(stage, 0)
                median = avg
            stage_metrics.append({
                'stage': stage,
                'avg_days': round(avg, 1),
                'median_days': median,
                'sample_size': len(days_list),
            })

        all_totals = list(lead_total_days.values()) or [0]
        total_avg = sum(all_totals) / len(all_totals)
        sorted_totals = sorted(all_totals)
        total_median = sorted_totals[len(sorted_totals) // 2]

        return VelocityMetrics(
            stage_metrics=stage_metrics,
            total_cycle_days=round(total_avg, 1),
            median_cycle_days=float(total_median),
        )

    # ------------------------------------------------------------------
    # Forecast (simple probability-weighted)
    # ------------------------------------------------------------------

    def generate_forecast(self, snapshot: Optional[FunnelSnapshot] = None) -> Dict:
        """Simple forecast: current pipeline × stage probability."""
        if snapshot is None:
            snapshots = self.generate_funnel_history(months=1)
            snapshot = snapshots[0]

        # Stage win probabilities (cumulative conversion from stage to Closed Won)
        stage_probabilities = {
            'Lead': 0.005,
            'MQL': 0.017,
            'SQL': 0.042,
            'Opportunity': 0.070,
            'Proposal': 0.140,
            'Negotiation': 0.400,
            'Closed Won': 1.0,
        }

        avg_deal = self._vary(45000, 0.10)
        forecast_items = []
        total_weighted = 0.0

        for stage, count in snapshot.stages.items():
            prob = stage_probabilities.get(stage, 0)
            weighted = count * prob * avg_deal
            total_weighted += weighted
            forecast_items.append({
                'stage': stage,
                'count': count,
                'probability': prob,
                'weighted_value': round(weighted, 2),
            })

        return {
            'month': snapshot.month,
            'avg_deal_value': round(avg_deal, 2),
            'total_weighted_pipeline': round(total_weighted, 2),
            'stages': forecast_items,
        }

    # ------------------------------------------------------------------
    # All-in-one convenience
    # ------------------------------------------------------------------

    def generate_all(self, months: int = 6, event_count: int = 200) -> Dict:
        """Generate complete pipeline dataset."""
        snapshots = self.generate_funnel_history(months)
        events = self.generate_conversion_events(event_count)
        velocity = self.generate_velocity_metrics(events)
        forecast = self.generate_forecast(snapshots[-1] if snapshots else None)

        return {
            'funnel_history': [s.to_dict() for s in snapshots],
            'conversion_events': [e.to_dict() for e in events],
            'velocity': velocity.to_dict(),
            'forecast': forecast,
            'current_funnel': snapshots[-1].to_dict() if snapshots else None,
        }
