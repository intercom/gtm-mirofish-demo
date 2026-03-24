# Pricing Change Simulation

**ID:** `pricing_simulation` | **Category:** Pricing | **API:** `GET /api/gtm/scenarios/pricing_simulation`

## Business Context

Intercom is executing a major P5 pricing migration that restructures pricing for existing customers. This follows P5.1, which already reduced email, SMS, and PSP prices after customer feedback that prices were 3–20x competitors.

Key risks identified by leadership:
- **Customer churn** — customers may refuse price increases and leave
- **Public backlash** — frustrated customers sharing experiences on social media
- **Legal exposure** — phone transcription pricing changes mid-subscription raised legal concerns
- **Budget uncertainty** — customers reported "unclear ROI" contributing to dissatisfaction

There is currently no systematic mechanism to predict customer reactions before rollout. This scenario fills that gap by simulating 2000 customer personas through four pricing scenarios, producing churn predictions and migration strategy recommendations.

## What the Simulation Tests

The simulation creates **500 synthetic agents** representing customers across all segments, then exposes them to four pricing change scenarios.

### Pricing Scenarios

1. **10% across-the-board increase** — Uniform increase, simplest to communicate
2. **15% increase with 12-month grandfathering** — Higher increase softened by transition period
3. **Usage-based repricing** — Some customers pay more, some pay less based on actual usage
4. **Feature-gated increase** — New features require an upgrade; base price unchanged

### Customer Personas
- CFO
- VP Operations
- CX Leader
- Product Manager
- Support Manager

### Firmographic Distribution
- **Segments:** SMB, Mid-Market, Enterprise
- **Contract values:** $500–2,000/mo, $2,000–10,000/mo, $10,000–50,000/mo
- **Customer tenure:** <1 year, 1–3 years, 3+ years

### Simulation Parameters
- **Duration:** 72 hours simulated time
- **Round interval:** 30 minutes
- **Mode:** Parallel (all agents active simultaneously)

## Expected Insights

1. **Churn prediction by segment and price increase** — Probability matrix across all segment × scenario combinations
2. **Public sentiment risk assessment** — Likelihood and severity of negative social media/review activity
3. **Competitive switch likelihood matrix** — Which competitors each segment would evaluate (Zendesk, Freshdesk, HubSpot Service Hub)
4. **Optimal migration strategy recommendation** — Which of the four scenarios minimizes churn while achieving revenue targets
5. **Revenue impact forecast per scenario** — Net revenue change accounting for churn, expansion, and new pricing

## How to Interpret Results

### Churn Prediction Matrix
The primary output is a segment × scenario matrix showing predicted churn probability:

```
                    10% flat  15% + grandfather  Usage-based  Feature-gated
SMB (<$2K/mo)         ?%          ?%                ?%            ?%
Mid-Market            ?%          ?%                ?%            ?%
Enterprise (>$10K)    ?%          ?%                ?%            ?%
```

Key patterns to watch for:
- **SMB is typically most price-sensitive** — even small increases can trigger churn when alternatives exist
- **Enterprise with 3+ year tenure** often has high switching costs that suppress churn even at higher price points
- **Usage-based repricing** tends to split the customer base — look for bimodal reaction patterns (some love it, some hate it)

### Sentiment Risk
Scores reflect both likelihood and severity of public negative response. High-value Enterprise customers who churn quietly are a revenue risk but not a PR risk. Mid-Market customers with active social presence who feel mistreated are a PR risk. The report separates these dimensions.

Watch for **cascade risk**: a few vocal customers can trigger broader negative sentiment. The simulation models this by allowing agent conversations to influence each other's reactions.

### Competitive Switch Analysis
The report maps which competitors each segment would evaluate. This is actionable for:
- **Retention playbooks** — prepare competitive battlecards for the specific alternatives each segment considers
- **Win-back offers** — understand what would need to be true for a churned customer to return
- **Feature gap analysis** — if customers cite specific competitor features, that's product intelligence

### Migration Strategy Recommendation
The recommended strategy balances three objectives:
1. **Revenue protection** — minimize churn-driven revenue loss
2. **Expansion opportunity** — some customers may expand if pricing aligns with value delivered
3. **Sentiment preservation** — maintain customer trust for long-term retention

The recommendation may be a hybrid — for example, "usage-based for Mid-Market, feature-gated for Enterprise, grandfather SMB for 12 months." Evaluate whether the operational complexity of a hybrid approach is worth the predicted improvement.

### Revenue Impact
Net revenue forecasts incorporate:
- Lost revenue from predicted churns
- Incremental revenue from price increases on retained customers
- Expansion revenue from customers who upgrade under the new model

Compare the net impact across scenarios. A scenario with higher gross revenue but also higher churn may yield less net revenue than a conservative approach. Time horizon matters — short-term revenue gain from aggressive pricing may underperform a gradual approach over 12–24 months.
