# Implementation Guide — GTM MiroFish Demo

> How to build and complete this MVP using Ralphy for outer-loop task orchestration and Ralph Loop for inner-loop iteration.

## Prerequisites

- **Node.js** 18+ and pnpm
- **Python** 3.11-3.12 and [uv](https://docs.astral.sh/uv/)
- **Docker** and Docker Compose
- **Ralphy CLI** — `pnpm add -g ralphy` ([GitHub](https://github.com/michaelshimeles/ralphy))
- **Claude Code** with Ralph Loop plugin (for inner-loop iteration)
- **API Keys**: LLM provider (Anthropic/OpenAI/Google) + Zep Cloud

## Architecture Overview

```
┌─────────────────────────────┐     ┌────────────────────────────┐
│   Vue 3 + Vite + Tailwind   │────▶│   Flask + OASIS + Zep      │
│   (Complete Frontend Rebuild)│     │   (MiroFish Backend Fork)  │
│   Port 3000                 │     │   Port 5001                │
└─────────────────────────────┘     └────────────┬───────────────┘
                                                  │
                              ┌───────────────────┼───────────────────┐
                              │                   │                   │
                        ┌─────┴─────┐    ┌───────┴───────┐   ┌──────┴──────┐
                        │ Zep Cloud │    │ LLM Provider  │   │ GTM Seed    │
                        │ (Memory)  │    │ Claude/GPT/   │   │ Data        │
                        │           │    │ Gemini        │   │             │
                        └───────────┘    └───────────────┘   └─────────────┘
```

## Step 1: Initial Setup (already done)

The repo is already scaffolded with Vue 3 + Vite + Tailwind frontend, MiroFish Flask backend, GTM scenarios, and Ralphy config. Group 0 of the PRD is complete.

```bash
cd /Users/spenser.wellen/Documents/GitHub/gtm-mirofish-demo
```

## Step 2: Run Ralphy — Full Build

Open a **new terminal** and run:

```bash
cd /Users/spenser.wellen/Documents/GitHub/gtm-mirofish-demo
ralphy --json PRD.json --parallel --max-parallel 4 --fast
```

**Flag reference:**
- `--json PRD.json` — reads the JSON task file (not `--prd` which expects markdown)
- `--parallel` — enables parallel execution via git worktrees
- `--max-parallel 4` — up to 4 Claude Code agents running simultaneously
- `--fast` — skips lint/test checks (no test suite yet)

**Optional flags you can add:**
- `--branch-per-task` — creates a git branch per task (useful for review)
- `--draft-pr` — auto-creates draft PRs for each task
- `--verbose` — show detailed execution output
- `--dry-run` — preview what would run without executing

### Parallel Group Execution Order

| Group | Phase | Tasks | Can Parallelize? | Dependencies |
|-------|-------|-------|-----------------|--------------|
| **0** | Setup | 1 task | Sequential | None — must complete first |
| **1** | Foundation | 6 tasks | Yes (all 6 in parallel) | After Group 0 |
| **2** | Views | 8 tasks | Yes (all 8 in parallel) | After Group 1 |
| **3** | Integration | 4 tasks | Yes (all 4 in parallel) | After Group 2 |
| **4** | Polish & Docs | 3 tasks | Yes (all 3 in parallel) | After Group 3 |

**Total: 22 tasks across 5 parallel groups**

### What Happens During Execution

1. **Group 0** (sequential): Initializes Vue project scaffolding
2. **Group 1** (6 parallel agents): Brand tokens, layout components, UI components, Pinia stores, API client, router — all build simultaneously in isolated worktrees
3. **Group 2** (8 parallel agents): All 8 views (Landing, Scenario Builder, Graph, Simulation, Report, Chat, Settings, Login) build simultaneously
4. **Group 3** (4 parallel agents): End-to-end wiring, error handling, animations, responsive design
5. **Group 4** (3 parallel agents): README, scenario docs, final polish

## Step 3: Ralph Loop — Inner Iteration

For iterating on individual tasks that need refinement (e.g., the D3.js graph view isn't quite right):

```bash
# In Claude Code, use the /ralph-loop skill:
/ralph-loop

# Provide a focused prompt like:
# "Refine the GraphView.vue D3.js visualization:
#  - Nodes should have smooth enter animations
#  - Add zoom controls overlay
#  - Fix force simulation parameters for better layout
#  - Add node tooltip on hover"
```

Ralph Loop will iterate autonomously — making changes, checking results, and refining until the task meets quality criteria.

### When to Use Ralph Loop vs Ralphy

| Situation | Use |
|-----------|-----|
| Building the full MVP from scratch | **Ralphy** (`ralphy --prd PRD.json`) |
| Iterating on a specific component | **Ralph Loop** (`/ralph-loop`) |
| Fixing a bug in one view | **Ralph Loop** |
| Adding a new feature across files | **Ralphy** (add task to PRD.json) |
| Post-deploy monitoring | **`/loop`** (cron-style) |

## Step 4: Post-Build Monitoring

```bash
# After deploying to Railway, use /loop for health checks:
/loop 10m "Check Railway deployment health: verify frontend loads, backend /api/gtm/scenarios returns 200, Docker containers are running"
```

## Development Commands

### Backend
```bash
cd backend
uv sync                    # Install Python dependencies
uv run python run.py       # Start Flask backend on :5001
```

### Frontend
```bash
cd frontend
npm install                # Install Node dependencies
npm run dev                # Start Vite dev server on :3000
```

### Docker
```bash
docker compose build       # Build both images
docker compose up -d       # Start both services
docker compose logs -f     # Tail logs
docker compose down        # Stop services
```

### Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## Troubleshooting

### Ralphy tasks fail with merge conflicts
```bash
# Ralphy creates isolated worktrees — conflicts happen when parallel tasks
# modify the same files. Resolution:
ralphy --prd PRD.json --parallel --max-parallel 2  # Reduce parallelism
# Or run conflicting tasks sequentially by setting parallel_group: 0
```

### Frontend can't reach backend
```bash
# Check VITE_API_URL in frontend environment
# Docker: should be http://backend:5001 (service name)
# Local dev: should be http://localhost:5001
```

### LLM provider connection fails
```bash
# Verify LLM_PROVIDER matches your API key type
# Anthropic keys start with sk-ant-
# OpenAI keys start with sk-
# Gemini keys are alphanumeric
```

## File Structure Reference

```
gtm-mirofish-demo/
├── backend/                 ← MiroFish Flask (forked)
│   ├── app/
│   │   ├── config.py       ← Multi-LLM provider routing
│   │   ├── api/
│   │   │   └── gtm_scenarios.py  ← GTM scenario API
│   │   └── services/       ← Core simulation (unchanged)
│   ├── gtm_scenarios/      ← 4 pre-built GTM scenarios
│   └── gtm_seed_data/      ← Anonymized GTM data
├── frontend/                ← Complete Vue 3 rebuild
│   ├── src/
│   │   ├── views/          ← 7 views + Login
│   │   ├── components/     ← UI component library
│   │   ├── api/            ← Backend API client
│   │   └── store/          ← Pinia state management
├── PRD.json                 ← Ralphy task graph
├── implementation.md        ← This file
├── docker-compose.yml       ← Railway deployment
└── .env.example             ← Configuration template
```
