# ADR-011: Railway Per-Service Docker Deployment

## Status

Accepted

## Date

2026-03-25

## Context

The application consists of two services (Flask backend, Vue SPA frontend) that need to be deployed for demos and internal use. We needed a deployment platform that:

- Supports Docker-based deployments with per-service configuration
- Provides quick setup without complex infrastructure (no Kubernetes, no Terraform)
- Handles HTTPS termination and custom domains automatically
- Fits within a reasonable cost envelope for a demo/internal tool
- Allows environment-variable-driven configuration for LLM keys and feature flags

We considered:
1. **AWS ECS / Fargate** — Full control, but heavy infrastructure setup for a demo project.
2. **Vercel + separate backend** — Great for frontend, but the Python backend doesn't fit Vercel's serverless model.
3. **Railway** — Docker-native PaaS with per-service configuration and automatic HTTPS.
4. **Render** — Similar to Railway, but less flexible Docker build configuration.

## Decision

We deploy both services to **Railway** using per-service Dockerfiles with `railway.toml` configuration files.

**Backend deployment** (`backend/Dockerfile`):
- Base image: `python:3.11-slim`
- Installs lightweight demo dependencies only (Flask, flask-cors, LLM SDKs)
- Runs `demo_app.py` as the default entrypoint
- Health check: `GET /api/health` with 120s timeout
- Restart policy: `ON_FAILURE` with max 5 retries

**Frontend deployment** (`frontend/Dockerfile`):
- Multi-stage build: `node:20-slim` for build, then serves static `dist/` via `serve`
- Build args (`VITE_API_URL`, `VITE_DEMO_MODE`) configure environment at build time
- Uses `pnpm --frozen-lockfile` for reproducible builds
- Health check: `GET /` with 120s timeout

**Railway configuration** (`railway.toml` in each service directory):
- Builder: `DOCKERFILE` (not Nixpacks) for full control over build steps
- Health checks ensure services are ready before receiving traffic
- Environment variables set per-service in Railway dashboard (LLM keys, Zep keys, auth config)

**Local development** (`docker-compose.yml`):
- Mirrors Railway's service topology for dev/prod parity
- Backend health check gates frontend startup (depends_on with health condition)
- Optional nginx reverse proxy via Docker Compose profiles (production profile)
- Shared volume for simulation data uploads

## Consequences

**Easier:**
- Zero-to-deployed in minutes — `railway up` from each service directory
- Automatic HTTPS, domain management, and log aggregation
- Per-service environment variables keep secrets isolated
- Docker Compose provides identical topology for local development
- Independent scaling — backend and frontend can be sized separately

**Harder:**
- Two Railway services = two billing units (acceptable for demo scale)
- Build args for frontend require redeployment to change API URLs
- No built-in CI/CD — relies on Railway's GitHub integration for auto-deploy
- CORS configuration must be maintained for cross-origin requests between services
