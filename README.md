# MiroFish for GTM — Swarm Intelligence Demo

> Predict campaign outcomes before they happen. Simulate how prospects react to your outbound, signals, and pricing changes.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node 18+](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)

An Intercom-branded fork of [MiroFish](https://github.com/666ghj/MiroFish) — an open-source swarm intelligence engine (40K+ GitHub stars) — customized for Intercom's GTM Systems team. Pre-test automated outbound campaigns, validate sales signals, simulate pricing changes, and optimize personalization before they hit real prospects.

---

## The Problem

Intercom's GTM operations face a fundamental challenge: **we can't predict how our outbound messaging, pricing changes, and campaign strategies will land before we execute them.**

| Challenge | Impact |
|-----------|--------|
| Data trust is critically low | Reps spend 5-30 minutes per account validating data |
| 56K incorrect website records | Enrichment accuracy only 25-32% |
| Signal adoption collapsed | 11% unactioned at launch to 76% now |
| No campaign staging environment | Every campaign is a production deployment |
| Churn prediction: 87% recall, 16% precision | Model predicts who, not how to prevent |

## The Solution

MiroFish creates **digital sandboxes** populated with AI agents that simulate real social behavior. Instead of asking "what happened last time?" it answers **"what would happen if we did this?"**

```
Your Scenario (email copy, signals, pricing)
    -> Knowledge Graph Construction (Zep GraphRAG)
        -> Agent Population (hundreds of AI personas)
            -> Social Simulation (Twitter + Reddit, 23 action types)
                -> Predictive Report (evidence-based analysis)
                    -> Interactive Chat (Q&A with simulated world)
```

---

## Features

- **4 Pre-Built GTM Scenarios** — Outbound campaign pre-testing (hero), signal validation, pricing simulation, personalization optimization
- **Multi-LLM Support** — Claude (Anthropic), OpenAI (GPT-4o), Google Gemini — switchable in settings
- **Intercom Branding** — Full Intercom design language with brand colors, typography, and logo
- **Real GTM Seed Data** — Anonymized data from Intercom's actual GTM models (accounts, signals, templates, personas)
- **7 Interactive Views** — Landing, Scenario Builder, Knowledge Graph, Live Simulation, Report Explorer, Chat, Settings
- **Optional Auth** — Google OAuth / Okta SSO with @intercom.io email enforcement (toggle via `.env`)
- **Docker Deployment** — Single `docker compose up` for Railway or local development

---

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/intercom/gtm-mirofish-demo.git
cd gtm-mirofish-demo
cp .env.example .env
# Edit .env with your LLM_API_KEY and ZEP_API_KEY
docker compose up -d
```

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5001

### Manual Development

```bash
# Backend
cd backend && uv sync && uv run python run.py

# Frontend (separate terminal)
cd frontend && pnpm install && pnpm dev
```

---

## Configuration

All configuration is via `.env` file (see [.env.example](.env.example)):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `anthropic` | LLM provider: `anthropic`, `openai`, or `gemini` |
| `LLM_API_KEY` | Yes | — | API key for chosen provider |
| `ZEP_API_KEY` | Yes | — | [Zep Cloud](https://app.getzep.com/) API key |
| `AUTH_ENABLED` | No | `false` | Enable OAuth login (for production) |
| `AUTH_PROVIDER` | No | `google` | OAuth provider: `google` or `okta` |
| `AUTH_ALLOWED_DOMAIN` | No | `intercom.io` | Allowed email domain |

---

## Architecture

```
+--------------------------+     +---------------------------+
|  Vue 3 + Vite + Tailwind |---->|  Flask + OASIS + Zep      |
|  (Complete Rebuild)      |     |  (MiroFish Backend Fork)  |
|  Port 3000               |     |  Port 5001                |
+--------------------------+     +-------------+-------------+
                                               |
                            +------------------+------------------+
                            |                  |                  |
                       +----+----+     +-------+-------+   +-----+-----+
                       |Zep Cloud|     |LLM Provider   |   |GTM Seed   |
                       |(Memory) |     |Claude/GPT/    |   |Data       |
                       |         |     |Gemini         |   |           |
                       +---------+     +---------------+   +-----------+
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Vue 3 + Vite + Tailwind CSS + Pinia + Vue Router |
| Visualization | D3.js v7 (force-directed knowledge graphs) |
| Backend | Flask 3.0+ (Python 3.11-3.12) |
| Simulation | OASIS (camel-oasis 0.2.5) — up to 1M agents |
| Memory | Zep Cloud 3.13.0 (temporal knowledge graphs) |
| LLM | Any OpenAI-compatible API |
| Auth | Google OAuth / Okta SSO (optional) |
| Deploy | Docker Compose + Railway |

---

## GTM Scenarios

### 1. Outbound Campaign Pre-Testing (Hero)

Simulate how AI-generated outbound emails land with synthetic prospect populations. Seeds with email copy, target segment description, and firmographic data. Reveals engagement prediction by persona type, subject line effectiveness, objection mapping by industry, and optimal cadence.

### 2. Sales Signal Validation

Test whether sales signals actually predict buying behavior. Seeds with signal definitions from Intercom's DBT models. Reveals signal-to-buying correlation, false positive rates, and recommended signal priority ranking.

### 3. Pricing Change Simulation

Predict customer reactions to P5 pricing migration. Seeds with pricing scenarios and customer mix. Reveals churn probability by segment, public sentiment risk, competitive switch likelihood, and optimal migration strategy.

### 4. Personalization Optimization

Rank email personalization variants by simulated engagement. Seeds with 10 message variants. Reveals which personalization dimensions matter most by segment.

---

## API Reference

### MiroFish Core (unchanged)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/graph/build` | Build knowledge graph from seed text |
| GET | `/api/graph/status/:taskId` | Check graph build progress |
| POST | `/api/simulation/start` | Start OASIS simulation |
| GET | `/api/simulation/status/:taskId` | Check simulation progress |
| POST | `/api/report/generate` | Generate predictive report |
| POST | `/api/chat` | Chat with simulated world |

### GTM Extensions (new)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gtm/scenarios` | List all GTM scenario templates |
| GET | `/api/gtm/scenarios/:id` | Get scenario with full config |
| GET | `/api/gtm/seed-data/:type` | Get seed data by type |

---

## Building the Full MVP

This repo uses [Ralphy](https://github.com/michaelshimeles/ralphy) for parallel task orchestration. See [implementation.md](implementation.md) for the complete build guide including:

- Parallel group execution order (5 groups, 22 tasks)
- How to use Ralphy for outer-loop orchestration
- How to use Ralph Loop for inner-loop iteration on individual components
- Post-deploy monitoring with `/loop`

---

## Deployment to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Set environment variables
railway variables set LLM_PROVIDER=anthropic
railway variables set LLM_API_KEY=your-key
railway variables set ZEP_API_KEY=your-key
railway variables set AUTH_ENABLED=true

# Deploy
railway up
```

---

## License

AGPL-3.0 — inherited from [MiroFish](https://github.com/666ghj/MiroFish). See [LICENSE](LICENSE).

---

## Credits

- **[MiroFish](https://github.com/666ghj/MiroFish)** by Shanda Group — the swarm intelligence engine powering this demo
- **[OASIS](https://github.com/camel-ai/oasis)** — social simulation framework
- **[Zep Cloud](https://www.getzep.com/)** — temporal knowledge graph memory
- **Intercom GTM Systems Team** — Spenser Wellen, Spencer Cross, Bil Erdenekhuyag
