# GTM Simulation Scenarios

Pre-built scenario templates for simulating Go-To-Market operations using MiroFish's OASIS swarm intelligence engine. Each scenario creates a population of AI agents that role-play realistic buyer personas, letting you test GTM strategies before deploying them to real prospects and customers.

## Available Scenarios

| Scenario | Category | Agents | Duration | Use Case |
|----------|----------|--------|----------|----------|
| [Outbound Campaign Pre-Testing](./outbound_campaign.md) | Outbound | 200 | 72 hrs simulated | Test messaging and cadence before sending to real prospects |
| [Personalization Optimization](./personalization.md) | Personalization | 200 | 48 hrs simulated | Rank email variants by predicted engagement, not LLM self-scoring |
| [Pricing Change Simulation](./pricing_simulation.md) | Pricing | 500 | 72 hrs simulated | Predict customer reactions to pricing migrations |
| [Sales Signal Validation](./signal_validation.md) | Signals | 500 | 72 hrs simulated | Identify which sales signals actually predict buying behavior |

## How Scenarios Work

1. **Select a scenario** from the Scenario Builder view or via `GET /api/gtm/scenarios`
2. **Seed text** is fed into the MiroFish knowledge graph builder (`POST /api/graph/build`)
3. **Agent personas** are generated from the scenario's agent config and seed data in `backend/gtm_seed_data/`
4. **OASIS simulation** runs agents through interaction rounds at the configured cadence
5. **Reports** are generated with predictions mapped to the scenario's expected outputs

## Seed Data

Scenarios reference shared seed data files in `backend/gtm_seed_data/`:

- **account_profiles.json** — Representative account profiles across SMB, Mid-Market, and Enterprise segments
- **persona_templates.json** — Agent persona templates based on Intercom ICP roles (VP of Support, CX Director, IT Leader, Head of Operations)
- **signal_definitions.json** — Sales signal type definitions with current accuracy and adoption metrics
- **email_templates.json** — Outbound email templates with tone, length, and personalization metadata
