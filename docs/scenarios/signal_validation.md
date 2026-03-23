# Sales Signal Validation

**Scenario ID:** `signal_validation`
**Category:** Signals
**Simulated agents:** 500
**Simulated duration:** 72 hours (30-minute rounds)

## Business Context

Intercom's Sales Signal system generates buying intent signals from DBT models in Snowflake, delivered to reps via custom Salesforce LWC inbox and Slack notifications. The system was designed to help reps prioritize outreach, but adoption has collapsed — unactioned accounts increased from 11% at launch to 76% currently.

The fundamental question: **are the signals actually predictive, or are reps ignoring them because they've learned the signals are noise?**

Current operational problems:

- **Misaligned priorities** — Signal setup doesn't support current business priorities (P5 migration, Fin-focused selling)
- **Accuracy concerns** — Accuracy is described as "hit or miss" with the current tool stack
- **Channel overload** — Multiple competing notification channels (Salesforce LWC, Slack) make prioritization difficult
- **Unmeasurable ROI** — Low adoption means signals go unactioned, making it impossible to measure whether they actually work

## What the Simulation Tests

The simulation creates 500 account-level agents across 5 persona types (Decision Maker, Champion, Technical Evaluator, Blocker, End User) spanning SaaS, Healthcare, Fintech, E-commerce, and Manufacturing industries at companies of 50-5000 employees.

Eight signal types are evaluated:

| Signal | Category | Current Adoption | What It Detects |
|--------|----------|-----------------|-----------------|
| Product Usage Surge | Usage | 24% | Account adds 10+ support agents in 30 days |
| Competitor Research | Intent | 18% | Visits Intercom pricing after visiting Zendesk/Freshdesk |
| Feature Exploration | Usage | 31% | Activates 3+ new features in a week |
| Contract Approaching | Lifecycle | 42% | Renewal within 90 days with declining usage |
| Expansion Indicator | Usage | 22% | Usage exceeds current plan limits by 20%+ |
| Champion Change | People | 15% | Key contact role change or departure detected |
| Technographic Match | Firmographic | 29% | Company uses complementary tools (Salesforce, HubSpot) |
| Third-Party Intent | Intent | 12% | Third-party intent data shows active evaluation |

The simulation tests two populations: accounts that receive signal-triggered outreach and a control group that doesn't. This reveals whether signal-informed outreach actually produces better engagement and pipeline outcomes.

## Expected Insights

| Output | What It Tells You |
|--------|-------------------|
| Signal-to-buying correlation matrix | How strongly each signal correlates with actual buying behavior in simulation |
| Top 3 most predictive signals | The signals reps should prioritize — the rest may be safe to deprecate |
| Signal combination effectiveness | Which pairs or triples of signals together are more predictive than any single signal |
| False positive rate per signal type | How often each signal fires without corresponding buying intent |
| Recommended signal priority ranking | Ordered list of signals by predictive value, ready to configure in the rep inbox |

## How to Interpret Results

### Correlation Matrix

The correlation matrix maps each signal to simulated buying outcomes (engagement, meeting booked, pipeline created). Scores range from -1 to +1:

- **> 0.5:** Strong positive correlation — this signal is genuinely predictive. Reps should act on it.
- **0.2 to 0.5:** Moderate correlation — useful in combination with other signals but not strong enough alone.
- **-0.2 to 0.2:** No meaningful correlation — this signal is noise. Consider deprecating it.
- **< -0.2:** Negative correlation — accounts showing this signal are actually *less* likely to buy. Investigate why.

### Top 3 Signals

The top 3 is the actionable takeaway for sales leadership. If only 3 signals matter, the rep experience can be radically simplified — one focused inbox instead of 8 notification types competing for attention. This directly addresses the adoption collapse.

Typical patterns from similar simulations:

- **Lifecycle signals** (Contract Approaching, Expansion Indicator) tend to be more predictive than intent signals because they're based on first-party usage data
- **People signals** (Champion Change) often have high predictive power but low volume
- **Firmographic signals** (Technographic Match) tend to have high false positive rates because they describe static attributes, not dynamic behavior

### Signal Combinations

Individual signals may be weak predictors, but combinations can be strong. For example, "Contract Approaching" alone might have moderate correlation, but "Contract Approaching + Feature Exploration" might be highly predictive of expansion. The combinations report shows the top 5 multi-signal patterns ranked by lift over single-signal baseline.

### False Positive Rates

A signal with 80% false positives means 4 out of 5 times a rep acts on it, nothing happens. This directly explains adoption collapse — reps learn to ignore signals that waste their time. The threshold for rep trust is roughly:

- **< 30% false positive:** Reps will trust and act on this signal
- **30-50% false positive:** Reps will act selectively (high-value accounts only)
- **> 50% false positive:** Reps will ignore this signal regardless of occasional true positives

### Priority Ranking

The final ranking combines correlation strength, false positive rate, and signal volume into a single priority score. Use this to reconfigure the Salesforce LWC inbox — show high-priority signals prominently and suppress or remove low-priority ones.

## Running This Scenario

```bash
# Load the scenario
curl http://localhost:5001/api/gtm/scenarios/signal_validation

# Get just the seed text for the knowledge graph
curl http://localhost:5001/api/gtm/scenarios/signal_validation/seed-text

# View related seed data
curl http://localhost:5001/api/gtm/seed-data/signal_definitions
curl http://localhost:5001/api/gtm/seed-data/account_profiles
curl http://localhost:5001/api/gtm/seed-data/persona_templates
```

Or select **"Sales Signal Validation"** from the Scenario Builder in the frontend.
