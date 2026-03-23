# Pricing Change Simulation

**Scenario ID:** `pricing_simulation`
**Category:** Pricing
**Simulated agents:** 500
**Simulated duration:** 72 hours (30-minute rounds)

## Business Context

Intercom is executing a major P5 pricing migration that restructures pricing for existing customers. This is the highest-risk GTM scenario in the suite — pricing changes directly affect revenue retention and public brand perception.

Historical context that makes this simulation critical:

- **P5.1 already reduced prices** for email, SMS, and PSP based on customer feedback that prices were 3x-20x competitors
- **Customer dissatisfaction** surfaced as "budget uncertainty and unclear ROI" during early P5 rollout
- **Legal risk** was flagged around phone transcript pricing changes mid-subscription
- **No prediction mechanism** exists to estimate customer reactions before rolling out price changes

Leadership identified the core risk as: *"Customer reaction to price increase — customers may be unwilling to accept price increase and churn or share their frustration publicly."*

## What the Simulation Tests

The simulation creates 500 customer personas spanning three segments (SMB, Mid-Market, Enterprise) with five stakeholder roles (CFO, VP Operations, CX Leader, Product Manager, Support Manager). Each persona has a contract value, usage pattern, tenure, and existing sentiment.

Four pricing scenarios are tested against this population:

| Scenario | Description | Risk Profile |
|----------|-------------|-------------|
| 10% across-the-board increase | Simple, uniform price hike | High churn risk for price-sensitive SMB |
| 15% increase with 12-month grandfathering | Higher increase, delayed impact | Lower short-term churn but cliff risk at month 13 |
| Usage-based repricing | Some customers go up, some go down | Complex communication but fairer perception |
| Feature-gated increase | New features require upgrade | Lowest churn risk but limits adoption of new features |

Personas react based on their segment, contract value, tenure, competitive alternatives awareness, and existing satisfaction.

## Expected Insights

| Output | What It Tells You |
|--------|-------------------|
| Churn prediction by segment and price increase | Which segments are most price-sensitive and at what thresholds churn accelerates |
| Public sentiment risk assessment | Likelihood of negative social media or review activity by segment |
| Competitive switch likelihood matrix | Which competitors each segment would consider and at what price delta |
| Optimal migration strategy recommendation | Which of the 4 pricing scenarios minimizes churn while maximizing revenue |
| Revenue impact forecast per scenario | Net revenue change accounting for churn, expansion, and new pricing |

## How to Interpret Results

### Churn Probability Curves

The churn prediction isn't a single number — it's a curve per segment. Look for **inflection points** where small price increases cause disproportionate churn. For example, Enterprise accounts may tolerate a 10% increase with minimal churn but show a sharp cliff at 15%. SMB accounts may show linear churn scaling with any increase.

Key thresholds to watch:

- **< 5% predicted churn:** Safe to proceed with standard communication
- **5-15% predicted churn:** Proceed with mitigation (grandfathering, value-add messaging)
- **> 15% predicted churn:** Reconsider the pricing scenario for this segment

### Public Sentiment Risk

This is the most unique output of the pricing simulation. Agent personas with "at-risk" existing sentiment and high social media propensity (typically SMB and mid-market) are flagged for public backlash risk. The sentiment risk score ranges from 1-10:

- **1-3:** Unlikely to generate public complaints
- **4-6:** May share frustration in private communities (Slack groups, forums)
- **7-10:** High risk of public posts on X/Twitter, G2 reviews, or LinkedIn complaints

A few high-sentiment-risk accounts can cause outsized brand damage, so this metric matters even if aggregate churn is low.

### Competitive Switch Matrix

The matrix shows which competitors each segment would evaluate. If 40% of mid-market personas indicate they'd evaluate Zendesk after a 15% price increase, that's actionable intelligence for the competitive positioning in migration communications.

Watch for asymmetries — Enterprise customers may not switch due to integration depth even if dissatisfied, while SMB customers with shallow integrations can move quickly.

### Revenue Impact Forecasting

The revenue forecast combines:

- **Lost revenue** from predicted churn
- **Gained revenue** from the price increase on retained customers
- **Expansion opportunity** from usage-based repricing (some accounts discover they're under-utilizing)

The net number is what matters. A scenario with 10% churn but 20% revenue uplift on retained customers may outperform a zero-churn scenario with only 5% uplift.

## Running This Scenario

```bash
# Load the scenario
curl http://localhost:5001/api/gtm/scenarios/pricing_simulation

# Get just the seed text for the knowledge graph
curl http://localhost:5001/api/gtm/scenarios/pricing_simulation/seed-text

# View related seed data
curl http://localhost:5001/api/gtm/seed-data/account_profiles
curl http://localhost:5001/api/gtm/seed-data/persona_templates
```

Or select **"Pricing Change Simulation"** from the Scenario Builder in the frontend.
