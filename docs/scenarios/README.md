# GTM Scenario Documentation

Pre-built simulation scenarios for Intercom GTM operations. Each scenario defines a business problem, populates a synthetic world of agent personas, and produces predictive insights through the MiroFish OASIS engine.

## Available Scenarios

| Scenario | Category | Agents | Duration | Description |
|----------|----------|--------|----------|-------------|
| [Outbound Campaign Pre-Testing](./outbound-campaign.md) | Outbound | 200 | 72h simulated | Test messaging and cadence before sending to real prospects |
| [Personalization Optimization](./personalization.md) | Personalization | 200 | 48h simulated | Rank email variants by simulated engagement, not LLM self-scoring |
| [Pricing Change Simulation](./pricing-simulation.md) | Pricing | 500 | 72h simulated | Predict customer reactions to P5 pricing migration |
| [Sales Signal Validation](./signal-validation.md) | Signals | 500 | 72h simulated | Test which sales signals actually predict buying behavior |

## How Scenarios Work

1. **Select a scenario** via the Scenario Builder UI or `GET /api/gtm/scenarios`
2. **Seed text** is fed into the knowledge graph builder (`POST /api/graph/build`) — this defines the "world" the agents inhabit
3. **Agent personas** are generated from the scenario's `agent_config` combined with seed data from `backend/gtm_seed_data/`
4. **OASIS simulation** runs for the configured duration with agents interacting in parallel or threaded mode
5. **Report generation** (`POST /api/report/generate`) produces the expected outputs listed in each scenario

## Seed Data

Scenarios draw from shared seed data in `backend/gtm_seed_data/`:

- **account_profiles.json** — Representative company profiles (segment, industry, health score, churn risk)
- **persona_templates.json** — Role-based persona archetypes with priorities, concerns, and typical objections
- **email_templates.json** — Outbound email variants with tone, length, and CTA metadata
- **signal_definitions.json** — Sales signal types with current accuracy and adoption rates
