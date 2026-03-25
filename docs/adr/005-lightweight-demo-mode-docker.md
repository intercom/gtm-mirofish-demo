# ADR-005: Lightweight Demo Mode Docker Deployment

## Status

Accepted

## Date

2026-03-25

## Context

The full MiroFish backend includes heavy dependencies: CAMEL OASIS (social simulation framework), Zep Cloud SDK, PyMuPDF, and multiple LLM SDKs. Together these produce a Docker image exceeding 5 GB. For demo and presentation contexts, we need a deployment that:
- Starts quickly and runs on minimal infrastructure (Railway free tier, laptops)
- Works without LLM API keys or Zep credentials
- Demonstrates the full UI workflow with realistic-looking data
- Can optionally connect to real LLM providers when keys are available

We considered:
1. **Full backend in Docker** — Ship everything, mock at runtime when keys are missing.
2. **Separate demo app** — A stripped-down Flask server with pre-built responses.
3. **Static mock server** — Serve JSON fixtures without any Python runtime.

## Decision

We maintain a **lightweight `demo_app.py`** alongside the full backend, and the Docker deployment runs this demo app by default.

**Backend Dockerfile** (`backend/Dockerfile`):
- Based on `python:3.11-slim` (~150 MB vs ~5.8 GB for full stack)
- Installs only Flask, flask-cors, python-dotenv, anthropic, and openai
- Copies `demo_app.py`, `llm_client.py`, and `gtm_scenarios/` directory
- Runs `demo_app.py` as the entrypoint

**Demo app behavior:**
- Serves all API endpoints with deterministic mock data
- Pre-built GTM scenario templates from `gtm_scenarios/*.json` provide realistic content
- When `LLM_API_KEY` is configured, routes like chat and seed generation use the real LLM
- Simulation progress is simulated with timed responses to drive the frontend workflow

**Frontend Dockerfile** (`frontend/Dockerfile`):
- Multistage build: `node:20-slim` for build, then serves `dist/` via `serve`
- Build args (`VITE_API_URL`, `VITE_DEMO_MODE`) configure environment at build time
- Uses pnpm with `--frozen-lockfile` for reproducible builds

**Docker Compose** orchestrates both services with health checks ensuring the backend is ready before the frontend starts.

## Consequences

**Easier:**
- Demo deployments start in seconds, not minutes
- No API keys needed for a full UI walkthrough
- Railway free tier handles the lightweight images comfortably
- Frontend developers can work against the demo backend without configuring Zep or LLMs
- Graceful upgrade path: add API keys to unlock real LLM features

**Harder:**
- Two backend entrypoints (`demo_app.py` vs `run.py`) must be kept in sync for API compatibility
- Demo mock data may drift from real backend response shapes over time
- Full backend requires a separate deployment process (not covered by default Dockerfile)
