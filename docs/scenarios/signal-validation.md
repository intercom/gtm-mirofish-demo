# Sales Signal Validation

**ID:** `signal_validation` | **Category:** Signals | **API:** `GET /api/gtm/scenarios/signal_validation`

## Business Context

Intercom's Sales Signal system generates buying intent signals from DBT models in Snowflake, delivered to reps via custom Salesforce LWC inbox and Slack notifications. The system is failing: **unactioned accounts have grown from 11% at launch to 76%** — reps have effectively stopped trusting the signals.

Root causes:
- **Signal accuracy is "hit or miss"** — no validated correlation between signals and actual buying behavior
- **Signal setup doesn't align with current priorities** (P5 migration, Fin-focused selling)
- **Multiple competing notification channels** make prioritization impossible
- **Low adoption creates a measurement death spiral** — signals go unactioned, so ROI can't be measured, so trust erodes further

This scenario tests whether the 8 signal types actually predict buying behavior by simulating 1000 accounts with varying signal exposure and observing conversion patterns.

## What the Simulation Tests

The simulation creates **500 synthetic agents** across five buying committee roles and tests signal-triggered outreach against a control group.

### Signal Types Under Test

| Signal | Category | Description | Current Adoption |
|--------|----------|-------------|------------------|
| Product Usage Surge | Usage | Account adds 10+ agents in 30 days | 24% |
| Competitor Research | Intent | Visits pricing after visiting Zendesk/Freshdesk | 18% |
| Feature Exploration | Usage | Activates 3+ new features in a week | 31% |
| Contract Approaching | Lifecycle | Renewal within 90 days with declining usage | 42% |
| Expansion Indicator | Usage | Usage exceeds plan limits by 20%+ | 22% |
| Champion Change | People | Key contact role change or departure | 15% |
| Technographic Match | Firmographic | Uses complementary tools (Salesforce, HubSpot) | 29% |
| Third-Party Intent | Intent | Third-party data shows active evaluation | 12% |

### Agent Personas (Buying Committee)
- Decision Maker
- Champion
- Technical Evaluator
- Blocker
- End User

### Firmographic Distribution
- **Industries:** SaaS, Healthcare, Fintech, E-commerce, Manufacturing
- **Company sizes:** 50–200, 200–500, 500–1,000, 1,000–5,000 employees

### Simulation Parameters
- **Duration:** 72 hours simulated time
- **Round interval:** 30 minutes
- **Mode:** Parallel (all agents active simultaneously)

## Expected Insights

1. **Signal-to-buying correlation matrix** — Correlation coefficient for each signal type against conversion
2. **Top 3 most predictive signals** — Ranked by predictive power, not current adoption
3. **Signal combination effectiveness** — Which pairs or triples of signals compound to higher confidence
4. **False positive rate per signal type** — How often each signal fires without corresponding buying intent
5. **Recommended signal priority ranking** — New prioritization order to replace current setup

## How to Interpret Results

### Correlation Matrix
The matrix shows how strongly each signal correlates with buying behavior across segments. Key things to look for:

- **High correlation + low adoption** signals are the biggest opportunity — if "Expansion Indicator" (22% adoption) turns out to be highly predictive, getting reps to act on it would have outsized impact
- **Low correlation + high adoption** signals are the noise problem — if "Contract Approaching" (42% adoption) is weakly predictive, it's contributing to alert fatigue without driving pipeline
- **Signals that correlate only for specific segments** may be useful with better targeting but harmful as broadcast alerts

### Top Predictive Signals
The ranked list identifies the 3 signals most worth investing in. Compare this ranking against current adoption rates — the gap between "most predictive" and "most acted upon" represents the largest efficiency gain.

If the top signals are all in the same category (e.g., all usage-based), that suggests the signal infrastructure should be deepened in that category rather than spread across many weak signal types.

### Signal Combinations
Individual signals may be weak predictors, but combinations can be strong. Common high-value patterns:
- **Usage Surge + Feature Exploration** — Active expansion behavior
- **Competitor Research + Contract Approaching** — Evaluation-stage prospect at a decision point
- **Champion Change + Expansion Indicator** — New stakeholder inheriting a growing account

The report identifies which specific combinations exceed a confidence threshold. These compound signals should be prioritized over any individual signal.

### False Positive Rates
A signal with 80% false positive rate means 4 out of 5 alerts are noise. This directly maps to rep trust:

| False Positive Rate | Rep Impact |
|---------------------|------------|
| <20% | High trust — reps will act consistently |
| 20–40% | Moderate trust — reps will triage selectively |
| 40–60% | Low trust — reps will ignore most alerts |
| >60% | No trust — signal is actively harmful to adoption |

Use this to set alert thresholds. A signal can be valuable for analytics (understanding pipeline) without being useful for real-time alerting (triggering rep action).

### Priority Ranking
The final recommendation reorders signals by a composite score of predictive power, false positive rate, and actionability. Use this to:

1. **Retire** signals ranked at the bottom — removing noise improves trust in remaining signals
2. **Promote** top-ranked signals to primary notification channels
3. **Combine** mid-ranked signals into compound triggers rather than alerting on each individually
4. **Restrict** segment-specific signals to only fire for segments where they're predictive

The goal is fewer, better signals rather than comprehensive coverage. Moving from 8 signal types to 3–4 high-confidence ones should reverse the adoption decline.
