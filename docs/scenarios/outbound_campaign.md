# Outbound Campaign Pre-Testing

**Scenario ID:** `outbound_campaign`
**Category:** Outbound
**Simulated agents:** 200
**Simulated duration:** 72 hours (30-minute rounds)

## Business Context

Intercom's outbound team targets mid-market SaaS companies (500-2000 employees) currently using Zendesk, pitching Fin AI agent as a superior alternative that resolves 50% of support conversations automatically. However, launching outbound campaigns has historically been a "send and pray" exercise — there's no way to test messaging effectiveness before it hits real inboxes.

Key operational challenges that motivated this scenario:

- **Data quality:** 56K incorrect website records in account data; Clay enrichment accuracy is only 25-32% for support tool data
- **Prior failures:** A previous AI SDR (Conversica) achieved a 74% open rate but 0% conversion — high engagement doesn't mean pipeline
- **Rep time cost:** Reps spend 5-30 minutes per account validating data before engaging

## What the Simulation Tests

The simulation creates 200 synthetic prospect agents across 4 persona types (VP of Support, CX Director, IT Leader, Head of Operations) distributed across SaaS, Healthcare, Fintech, and E-commerce industries at companies of 200-5000 employees in NA, EMEA, and APAC.

These agents receive outbound email sequences and react based on their persona's priorities, objections, and communication style. The simulation tests:

1. **Messaging resonance by persona** — Which of the 4 value propositions (ROI, Speed, Quality, Scale) lands with each role?
2. **Subject line effectiveness** — Do subject lines like "Your Zendesk bill is 3x what it should be" drive opens or trigger spam perception?
3. **Industry sensitivity to competitive displacement** — How do Healthcare buyers react to aggressive Zendesk displacement messaging vs. SaaS buyers?
4. **Cadence optimization** — What's the ideal email spacing across a 72-hour sequence?

## Expected Insights

The simulation report produces five outputs:

| Output | What It Tells You |
|--------|-------------------|
| Engagement prediction by persona type | Which roles are most receptive to outreach and which messaging angles they prefer |
| Subject line effectiveness ranking | Ordered list of subject lines by predicted open rate, with spam-risk flags |
| Objection mapping by industry | The top 3 objections each industry vertical raises, useful for sequence follow-ups |
| Optimal sequence cadence recommendation | Recommended timing between touches based on simulated reply patterns |
| Competitive messaging sensitivity analysis | How aggressively you can position against Zendesk by segment before triggering backlash |

## How to Interpret Results

### Engagement Scores

Agent engagement is scored on a 0-100 scale per interaction round. Look for:

- **Scores > 70:** Strong interest — the messaging resonates. These persona/industry combos are your best targets.
- **Scores 40-70:** Neutral engagement — the agent didn't reject the message but isn't compelled. Iterate on the value prop for this segment.
- **Scores < 40:** Low receptivity — the persona either found the message irrelevant or actively negative. Check the objection mapping for why.

### Subject Line Rankings

Subject lines are ranked by a composite of simulated open rate and reply rate. Watch for divergence — a subject line with high opens but low replies may be clickbait that doesn't convert. The "spam perception" flag indicates subject lines that agents marked as too aggressive or sales-y.

### Objection Maps

Objections are clustered by theme (cost, risk, switching effort, feature gaps). If the same objection dominates across multiple industries, it signals a messaging gap in the core pitch. Industry-specific objections inform vertical-specific follow-up sequences.

### Cadence Patterns

The simulation tracks reply timing. If most replies come within 4 hours, tighter cadence works. If replies cluster at 24+ hours, aggressive follow-ups will feel pushy. The recommendation accounts for persona seniority — executives typically have longer response cycles.

## Running This Scenario

```bash
# Load the scenario
curl http://localhost:5001/api/gtm/scenarios/outbound_campaign

# Get just the seed text for the knowledge graph
curl http://localhost:5001/api/gtm/scenarios/outbound_campaign/seed-text

# View related seed data
curl http://localhost:5001/api/gtm/seed-data/email_templates
curl http://localhost:5001/api/gtm/seed-data/persona_templates
curl http://localhost:5001/api/gtm/seed-data/account_profiles
```

Or select **"Outbound Campaign Pre-Testing"** from the Scenario Builder in the frontend.
