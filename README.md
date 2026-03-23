# MiroFish for GTM — Swarm Intelligence Demo

> Predict campaign outcomes before they happen. Simulate how prospects react to your outbound, signals, and pricing changes.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node 18+](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)

An Intercom-branded fork of [MiroFish](https://github.com/666ghj/MiroFish) — an open-source swarm intelligence engine (40K+ GitHub stars) — customized for Intercom's GTM Systems team. Pre-test automated outbound campaigns, validate sales signals, simulate pricing changes, and optimize personalization before they hit real prospects.

---

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Screenshots](#screenshots)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [GTM Scenarios](#gtm-scenarios)
- [Development Guide](#development-guide)
- [Deployment to Railway](#deployment-to-railway)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

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

## Screenshots

> Screenshots will be added after the UI is finalized.

| View | Description |
|------|-------------|
| **Landing** | Dark hero with scenario cards and "How It Works" section |
| **Scenario Builder** | Seed document upload, agent count slider, persona multiselect |
| **Knowledge Graph** | D3.js force-directed graph with colored entity nodes |
| **Simulation** | Real-time dashboard with metrics, activity feed, timeline chart |
| **Report** | Multi-chapter report with sidebar navigation and markdown rendering |
| **Chat** | Full-height chat interface for Q&A with simulated agents |
| **Settings** | LLM provider selection, API key management, theme toggle |

<!-- To add screenshots:
1. Capture each view at 1280x800
2. Save to docs/screenshots/ as landing.png, builder.png, graph.png, etc.
3. Replace this section with:
   ![Landing](docs/screenshots/landing.png)
   ![Scenario Builder](docs/screenshots/builder.png)
   etc.
-->

---

## Features

- **4 Pre-Built GTM Scenarios** — Outbound campaign pre-testing (hero), signal validation, pricing simulation, personalization optimization
- **Multi-LLM Support** — Claude (Anthropic), OpenAI (GPT-4o), Google Gemini — switchable in settings
- **Intercom Branding** — Full Intercom design language with brand colors (#2068FF blue, #050505 navy, #ff5600 fin orange)
- **Real GTM Seed Data** — Anonymized data from Intercom's actual GTM models (accounts, signals, templates, personas)
- **8 Interactive Views** — Landing, Scenario Builder, Knowledge Graph, Live Simulation, Report Explorer, Chat, Settings, Login
- **D3.js Knowledge Graphs** — Force-directed graph visualization with entity type coloring and click-to-inspect
- **Async Task System** — All long-running operations (graph build, simulation, report gen) return task IDs for progress polling
- **Agent Interviews** — Chat with individual simulated agents or batch-interview entire populations
- **Report Agent** — AI-powered report generation with section-by-section streaming and tool-call logging
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

All configuration is via `.env` file (see [.env.example](.env.example)).

### LLM Provider

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `anthropic` | LLM provider: `anthropic`, `openai`, or `gemini` |
| `LLM_API_KEY` | Yes | — | API key for chosen provider |
| `LLM_BASE_URL` | No | Auto-configured | Override provider's default API URL |
| `LLM_MODEL_NAME` | No | Auto-configured | Override provider's default model |

Setting `LLM_PROVIDER` auto-configures the base URL and model:

| Provider | Base URL | Default Model |
|----------|----------|---------------|
| `anthropic` | `https://api.anthropic.com/v1/` | `claude-sonnet-4-20250514` |
| `openai` | `https://api.openai.com/v1/` | `gpt-4o` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` |

### Knowledge Graph

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ZEP_API_KEY` | Yes | — | [Zep Cloud](https://app.getzep.com/) API key (free tier sufficient for PoC) |

### Authentication (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_ENABLED` | No | `false` | Enable OAuth login (for production) |
| `AUTH_PROVIDER` | No | `google` | OAuth provider: `google` or `okta` |
| `AUTH_ALLOWED_DOMAIN` | No | `intercom.io` | Allowed email domain |
| `GOOGLE_CLIENT_ID` | No | — | Google OAuth client ID (when `AUTH_PROVIDER=google`) |
| `GOOGLE_CLIENT_SECRET` | No | — | Google OAuth client secret |
| `OKTA_ISSUER` | No | — | Okta issuer URL (when `AUTH_PROVIDER=okta`) |
| `OKTA_CLIENT_ID` | No | — | Okta client ID |

### Accelerated LLM (Optional)

For parallel processing with a secondary LLM provider:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_BOOST_API_KEY` | No | — | API key for accelerated provider |
| `LLM_BOOST_BASE_URL` | No | — | Base URL for accelerated provider |
| `LLM_BOOST_MODEL_NAME` | No | — | Model name for accelerated provider |

### Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_PORT` | No | `5001` | Backend Flask server port |
| `FRONTEND_PORT` | No | `3000` | Frontend Vite dev server port |
| `FLASK_DEBUG` | No | `true` | Enable Flask debug mode |
| `SECRET_KEY` | No | `change-me-in-production` | Flask session secret key |

---

## Architecture

```
+-----------------------------------+     +-----------------------------------+
|  Frontend                         |     |  Backend                          |
|  Vue 3 + Vite + Tailwind CSS      |---->|  Flask + OASIS + Zep              |
|  D3.js + Pinia + Vue Router       |     |  (MiroFish Fork + GTM Extensions) |
|  Port 3000                        |     |  Port 5001                        |
+-----------------------------------+     +---------+-----------+-------------+
                                                    |           |
                          +-------------------------+           |
                          |                         |           |
                     +----+----+          +---------+----+ +----+--------+
                     |Zep Cloud|          |LLM Provider  | |GTM Seed    |
                     |Temporal |          |Claude / GPT  | |Data (JSON) |
                     |Knowledge|          |/ Gemini      | |Scenarios,  |
                     |Graphs   |          |(OpenAI-compat| |Personas,   |
                     +---------+          | API)         | |Signals     |
                                          +--------------+ +------------+
```

### Request Flow

All long-running operations follow the same async pattern:

```
Client                         Server
  |-- POST /api/*/start -------->|  (returns task_id immediately)
  |                              |  [background thread starts]
  |-- GET /api/*/status -------->|  (poll for progress)
  |<-------- {progress: 45%} ----|
  |-- GET /api/*/status -------->|
  |<-------- {status: complete} -|
  |-- GET /api/*/result -------->|  (fetch completed data)
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Vue 3.5 + Vite 8 + Tailwind CSS 4 + Pinia + Vue Router |
| Visualization | D3.js v7 (force-directed knowledge graphs) |
| Markdown | marked v17 (report rendering) |
| Backend | Flask 3.0+ (Python 3.11-3.12) |
| Simulation | OASIS (camel-oasis 0.2.5) — up to 1M agents |
| AI Framework | CAMEL-AI 0.2.78 (multi-agent orchestration) |
| Memory | Zep Cloud 3.13.0 (temporal knowledge graphs) |
| LLM | Any OpenAI-compatible API (via openai SDK) |
| Auth | Google OAuth / Okta SSO (optional) |
| Deploy | Docker Compose + Railway |

---

## GTM Scenarios

Four pre-built scenarios ship in `backend/gtm_scenarios/`. Each includes seed text, agent configuration, simulation parameters, and expected output types.

### 1. Outbound Campaign Pre-Testing (Hero)

Simulate how AI-generated outbound emails land with synthetic prospect populations.

- **Seeds:** Email copy, target segment description, firmographic data
- **Agents:** 200 synthetic prospects across 4 persona types
- **Tests:** 4 subject line variants
- **Outputs:** Engagement prediction by persona, subject line effectiveness, objection mapping by industry, optimal cadence

### 2. Sales Signal Validation

Test whether sales signals actually predict buying behavior.

- **Seeds:** 8 signal definitions from Intercom's DBT models
- **Agents:** 500 synthetic prospects
- **Signals tested:** Product Usage Surge, Competitor Research, Feature Exploration, Contract Approaching, Expansion Indicator, Champion Change, Technographic Match, Third-Party Intent
- **Outputs:** Signal-to-buying correlation, false positive rates, recommended priority ranking

### 3. Pricing Change Simulation

Predict customer reactions to P5 pricing migration.

- **Seeds:** Pricing scenarios and customer mix (4 account archetypes)
- **Agents:** 500 synthetic customers across segments
- **Tests:** 4 pricing scenarios
- **Outputs:** Churn probability by segment, public sentiment risk, competitive switch likelihood, optimal migration strategy

### 4. Personalization Optimization

Rank email personalization variants by simulated engagement.

- **Seeds:** 10 message variants across dimensions (tone, length, personalization depth, CTA style)
- **Agents:** 200 synthetic prospects
- **Outputs:** Variant ranking, most impactful personalization dimensions, segment-specific recommendations

### Seed Data

Pre-built seed data lives in `backend/gtm_seed_data/`:

| File | Contents |
|------|----------|
| `account_profiles.json` | 4 representative account archetypes (Mid-Market SaaS, Enterprise Healthcare, SMB Fintech, Mid-Market E-commerce) |
| `persona_templates.json` | 4 decision-maker personas (VP of Support, CX Director, IT Leader, Head of Operations) with priorities, objections, communication style |
| `signal_definitions.json` | 8 sales signal types with category, accuracy, and adoption metrics |
| `email_templates.json` | Sample email templates for campaign testing |

---

## Development Guide

### Prerequisites

- **Node.js** 18+ (with pnpm)
- **Python** 3.11-3.12
- **uv** (Python package manager) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Docker** (optional, for containerized development)

### Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Run the dev server (port 5001)
uv run python run.py
```

The backend validates `LLM_API_KEY` and `ZEP_API_KEY` on startup. If either is missing, it exits with an error.

Key directories:

| Directory | Purpose |
|-----------|---------|
| `app/api/` | Flask route blueprints (graph, simulation, report, gtm_scenarios) |
| `app/services/` | Business logic (graph builder, simulation runner, report agent, etc.) |
| `app/models/` | Data models (project state, task lifecycle) |
| `app/utils/` | Utilities (LLM client, logger, file parser, retry) |
| `gtm_scenarios/` | Pre-built scenario JSON files |
| `gtm_seed_data/` | Anonymized seed data for agent generation |
| `auth/` | OAuth middleware (Google/Okta) |

### Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Run dev server (port 3000, proxies /api to backend)
pnpm dev

# Production build
pnpm build

# Preview production build
pnpm preview
```

The Vite dev server proxies all `/api` requests to `http://localhost:5001` (configurable via `VITE_API_URL`).

### Frontend Views

| Route | View | Purpose |
|-------|------|---------|
| `/` | LandingView | Scenario cards, "How It Works" section |
| `/scenarios/:id` | ScenarioBuilderView | Configure and launch a simulation |
| `/graph/:taskId` | GraphView | D3.js knowledge graph visualization |
| `/simulation/:taskId` | SimulationView | Real-time simulation dashboard |
| `/report/:taskId` | ReportView | Multi-chapter report explorer |
| `/chat/:taskId` | ChatView | Q&A with simulated world |
| `/settings` | SettingsView | LLM provider, API keys, theme |
| `/login` | LoginView | OAuth login (when `AUTH_ENABLED=true`) |

### Brand Tokens

Intercom design tokens are defined in `frontend/src/assets/brand-tokens.css`:

| Token | Value | Usage |
|-------|-------|-------|
| Primary Blue | `#2068FF` | Buttons, links, active states |
| Navy | `#050505` | Dark backgrounds, text |
| Fin Orange | `#ff5600` | Accents, alerts |
| Accent Purple | `#A0F` | Highlights |
| Success Green | `#090` | Status indicators |

### Running with Docker

```bash
# Build and start both services
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build

# Stop
docker compose down
```

The Docker setup mounts source code as volumes for hot-reloading during development.

---

## Deployment to Railway

### Setup

```bash
# Install Railway CLI
pnpm add -g @railway/cli

# Login and initialize
railway login
railway init
```

### Configure Environment Variables

```bash
# Required
railway variables set LLM_PROVIDER=anthropic
railway variables set LLM_API_KEY=your-key
railway variables set ZEP_API_KEY=your-key

# Production auth
railway variables set AUTH_ENABLED=true
railway variables set AUTH_PROVIDER=google
railway variables set GOOGLE_CLIENT_ID=your-client-id
railway variables set GOOGLE_CLIENT_SECRET=your-client-secret
railway variables set SECRET_KEY=$(openssl rand -hex 32)

# Server
railway variables set FLASK_DEBUG=false
```

### Deploy

```bash
railway up
```

Railway auto-detects the `docker-compose.yml` and provisions both services. The frontend service depends on the backend and connects via the internal Docker network.

### Post-Deploy Checklist

1. Verify health check: `curl https://your-app.railway.app/health`
2. Test frontend loads at the Railway-provided URL
3. Confirm OAuth redirect URLs are configured for your Railway domain
4. Run a quick scenario to verify LLM and Zep connectivity

---

## API Reference

All endpoints are prefixed with `/api`. The frontend proxies requests to the Flask backend.

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Backend health check |

### Graph (Knowledge Graph Construction)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/graph/ontology/generate` | Upload files and generate ontology definition |
| POST | `/api/graph/build` | Build knowledge graph from project (async, returns `task_id`) |
| GET | `/api/graph/task/:taskId` | Check task progress |
| GET | `/api/graph/tasks` | List all tasks |
| GET | `/api/graph/data/:graphId` | Get graph data (nodes and edges) |
| DELETE | `/api/graph/delete/:graphId` | Delete a Zep graph |
| GET | `/api/graph/project/:projectId` | Get project details |
| GET | `/api/graph/project/list` | List all projects |
| DELETE | `/api/graph/project/:projectId` | Delete a project |
| POST | `/api/graph/project/:projectId/reset` | Reset project state |

### Simulation (OASIS Agent Execution)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulation/create` | Create a new simulation |
| POST | `/api/simulation/prepare` | Prepare simulation environment (async, LLM-generated config) |
| POST | `/api/simulation/prepare/status` | Check preparation progress |
| POST | `/api/simulation/start` | Start running the simulation (async) |
| POST | `/api/simulation/stop` | Stop a running simulation |
| GET | `/api/simulation/:simId` | Get simulation state |
| GET | `/api/simulation/list` | List all simulations |
| GET | `/api/simulation/history` | Get simulation history with project details |
| GET | `/api/simulation/entities/:graphId` | Get graph entities (filtered) |
| GET | `/api/simulation/entities/:graphId/:uuid` | Get single entity details |
| GET | `/api/simulation/entities/:graphId/by-type/:type` | Get entities by type |
| GET | `/api/simulation/:simId/profiles` | Get agent profiles |
| GET | `/api/simulation/:simId/profiles/realtime` | Get profiles in real-time during generation |
| GET | `/api/simulation/:simId/config` | Get simulation config |
| GET | `/api/simulation/:simId/config/realtime` | Get config in real-time during generation |
| GET | `/api/simulation/:simId/config/download` | Download simulation config file |
| GET | `/api/simulation/:simId/run-status` | Get run status (for polling) |
| GET | `/api/simulation/:simId/run-status/detail` | Get detailed run status with all actions |
| GET | `/api/simulation/:simId/actions` | Get agent action history |
| GET | `/api/simulation/:simId/timeline` | Get timeline grouped by round |
| GET | `/api/simulation/:simId/agent-stats` | Get per-agent statistics |
| GET | `/api/simulation/:simId/posts` | Get simulation posts |
| GET | `/api/simulation/:simId/comments` | Get simulation comments (Reddit only) |
| POST | `/api/simulation/generate-profiles` | Generate OASIS agent profiles from graph |
| POST | `/api/simulation/interview` | Interview a single agent |
| POST | `/api/simulation/interview/batch` | Batch interview multiple agents |
| POST | `/api/simulation/interview/all` | Interview all agents with the same question |
| POST | `/api/simulation/interview/history` | Get interview history |
| POST | `/api/simulation/env-status` | Get simulation environment status |
| POST | `/api/simulation/close-env` | Close simulation environment |

### Report (AI-Powered Analysis)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/report/generate` | Generate predictive report (async) |
| POST | `/api/report/generate/status` | Check report generation progress |
| GET | `/api/report/:reportId` | Get report details |
| GET | `/api/report/by-simulation/:simId` | Get report by simulation ID |
| GET | `/api/report/list` | List all reports |
| GET | `/api/report/:reportId/download` | Download report as Markdown |
| DELETE | `/api/report/:reportId` | Delete a report |
| POST | `/api/report/chat` | Chat with Report Agent (Q&A with simulated world) |
| GET | `/api/report/:reportId/progress` | Get real-time generation progress |
| GET | `/api/report/:reportId/sections` | Get generated sections (for streaming display) |
| GET | `/api/report/:reportId/section/:index` | Get a single section |
| GET | `/api/report/check/:simId` | Check if simulation has a report |
| GET | `/api/report/:reportId/agent-log` | Get Report Agent execution log |
| GET | `/api/report/:reportId/agent-log/stream` | Get full agent log |
| GET | `/api/report/:reportId/console-log` | Get console output log |
| GET | `/api/report/:reportId/console-log/stream` | Get full console log |

### GTM Extensions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gtm/scenarios` | List all GTM scenario templates |
| GET | `/api/gtm/scenarios/:id` | Get scenario with full config |
| GET | `/api/gtm/scenarios/:id/seed-text` | Get scenario seed text |
| GET | `/api/gtm/seed-data/:type` | Get seed data by type (`account_profiles`, `persona_templates`, `signal_definitions`, `email_templates`) |

---

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run linting and tests
5. Commit with a descriptive message
6. Push and open a pull request

### Guidelines

- **Frontend:** All Vue components use Composition API with `<script setup>`. Use Tailwind CSS utility classes from `frontend/src/assets/brand-tokens.css`.
- **Backend:** Services in `backend/app/services/` are core MiroFish logic — avoid modifying them unless necessary. Add new GTM-specific logic in `backend/app/api/gtm_scenarios.py` or new blueprint files.
- **API routes:** All frontend API requests use the `/api` prefix, which Vite proxies to the Flask backend.
- **Brand consistency:** Use Intercom brand tokens (primary blue `#2068FF`, navy `#050505`, fin orange `#ff5600`, accent purple `#A0F`).
- **Package manager:** Use `pnpm` for the frontend, `uv` for the backend.

### Project Structure

```
gtm-mirofish-demo/
├── backend/
│   ├── app/
│   │   ├── api/              # Flask route blueprints
│   │   ├── services/         # Business logic (read-only core)
│   │   ├── models/           # Data models
│   │   ├── utils/            # Utilities
│   │   └── config.py         # Configuration
│   ├── auth/                 # OAuth middleware
│   ├── gtm_scenarios/        # Pre-built scenario JSON files
│   ├── gtm_seed_data/        # Anonymized seed data
│   └── run.py                # Entry point
├── frontend/
│   ├── src/
│   │   ├── views/            # 8 page components
│   │   ├── components/       # Layout components (AppNav, AppFooter)
│   │   ├── assets/           # Brand tokens, images
│   │   └── main.js           # Vue app setup with routing
│   ├── tailwind.config.js
│   └── vite.config.js
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
└── README.md
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
