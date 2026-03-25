# Deployment Guide

This guide covers all deployment options for the GTM MiroFish Demo — from local development to production on Railway.

---

## Table of Contents

- [Local Development](#local-development)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
  - [Manual Services](#manual-services)
- [Docker Production](#docker-production)
- [Railway Deployment](#railway-deployment)
  - [Initial Setup](#initial-setup)
  - [Environment Variables](#railway-environment-variables)
  - [Custom Domains](#custom-domains)
  - [Redeployment](#redeployment)
- [Environment Variables Reference](#environment-variables-reference)
  - [Required](#required)
  - [LLM Provider](#llm-provider)
  - [Authentication (Optional)](#authentication-optional)
  - [Accelerated LLM (Optional)](#accelerated-llm-optional)
  - [Server](#server)
  - [Frontend Build Args](#frontend-build-args)
- [Troubleshooting](#troubleshooting)

---

## Local Development

### Docker Compose (Recommended)

The fastest way to run both services locally:

```bash
cp .env.example .env
# Edit .env — set LLM_API_KEY and ZEP_API_KEY at minimum

docker compose up -d
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000         |
| Backend  | http://localhost:5001         |
| Health   | http://localhost:5001/api/health |

The compose file builds from per-service Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`). A named volume `sim_data` persists simulation data in `backend/uploads` across container restarts.

**Common commands:**

```bash
# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

**Notes:**
- The backend health check uses Python `urllib` (not `curl`) because the image is `python:3.11-slim`.
- The frontend waits for the backend health check to pass before starting (`depends_on: condition: service_healthy`).
- Default ports can be changed via `BACKEND_PORT` and `FRONTEND_PORT` in `.env`.

### Manual Services

Run each service directly for hot-reload during development.

**Prerequisites:**
- Python 3.11+ with [uv](https://docs.astral.sh/uv/) (or venv + pip)
- Node 18+ with [pnpm](https://pnpm.io/)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — set LLM_API_KEY and ZEP_API_KEY

# 2. Create upload directories
mkdir -p backend/uploads/simulations backend/uploads/projects backend/uploads/reports

# 3. Start backend (terminal 1)
cd backend
uv sync
uv run python run.py
# Runs on http://localhost:5001

# 4. Start frontend (terminal 2)
cd frontend
pnpm install
VITE_DEMO_MODE=false pnpm dev
# Runs on http://localhost:3000
```

The Vite dev server proxies `/api/*` requests to `http://localhost:5001` automatically. Set `VITE_DEMO_MODE=false` so the frontend calls the real backend instead of using mock data.

**Alternative (venv + pip):**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

---

## Docker Production

For production Docker deployments, use the compose file with production-appropriate settings:

```bash
# 1. Configure production environment
cp .env.example .env
```

Set these values in `.env` for production:

```env
FLASK_DEBUG=false
SECRET_KEY=<generate-a-random-secret>
AUTH_ENABLED=true
AUTH_PROVIDER=google
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
```

```bash
# 2. Build and start
docker compose up -d --build

# 3. Verify
curl http://localhost:5001/api/health
```

**Production checklist:**

- [ ] `FLASK_DEBUG=false`
- [ ] `SECRET_KEY` set to a unique random value (not the default)
- [ ] `AUTH_ENABLED=true` with OAuth credentials configured
- [ ] `LLM_API_KEY` and `ZEP_API_KEY` set to real values
- [ ] Firewall rules restrict port access as needed
- [ ] Persistent volume for `sim_data` backed up if data retention is required

**Backend Dockerfile overview:**
- Base image: `python:3.11-slim`
- Installs Flask, flask-cors, python-dotenv, anthropic, openai
- Runs `demo_app.py` — a lightweight mock backend
- Port: 5001

**Frontend Dockerfile overview:**
- Multi-stage build: `node:20-slim` builder + `node:20-slim` runtime
- Uses pnpm with `--frozen-lockfile` for reproducible builds
- Accepts `VITE_API_URL`, `VITE_DEMO_MODE`, `VITE_INTERCOM_APP_ID` as build args
- Serves static files via `serve` on port 3000

---

## Railway Deployment

The project is deployed to Railway as two separate services in the `gtm-mirofish-demo` project.

| Service  | URL |
|----------|-----|
| Backend  | https://backend-production-e9d7.up.railway.app |
| Frontend | https://frontend-production-86ea.up.railway.app |

### Initial Setup

1. **Create a Railway project** at [railway.app](https://railway.app)

2. **Add the backend service:**
   - Connect your GitHub repo
   - Set the root directory to `backend/`
   - Railway auto-detects the Dockerfile at `backend/Dockerfile` and reads `railway.toml` for build/deploy configuration
   - Set the required environment variables (see [Railway Environment Variables](#railway-environment-variables))

3. **Add the frontend service:**
   - Add a second service in the same Railway project
   - Connect the same GitHub repo
   - Set the root directory to `frontend/`
   - Railway auto-detects the Dockerfile at `frontend/Dockerfile` and reads `railway.toml` for build/deploy configuration
   - Set `VITE_API_URL` to the backend's Railway URL (e.g., `https://backend-production-e9d7.up.railway.app/api`)

4. **Verify deployment:**
   ```bash
   curl https://backend-production-e9d7.up.railway.app/api/health
   # Expected: {"status":"ok","service":"MiroFish Backend"}
   ```

### Railway Environment Variables

**Backend service:**

| Variable | Value |
|----------|-------|
| `LLM_PROVIDER` | `anthropic` (or `openai`, `gemini`) |
| `LLM_API_KEY` | Your LLM provider API key |
| `ZEP_API_KEY` | Your Zep Cloud API key |
| `SECRET_KEY` | A unique random string |
| `FLASK_DEBUG` | `false` |
| `AUTH_ENABLED` | `true` |
| `AUTH_PROVIDER` | `google` |
| `AUTH_ALLOWED_DOMAIN` | `intercom.io` |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth client secret |
| `PORT` | `5001` (injected automatically by Railway — do not set manually) |

**Frontend service:**

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | Backend Railway URL + `/api` |
| `VITE_DEMO_MODE` | `true` or `false` |
| `VITE_INTERCOM_APP_ID` | Intercom app ID (optional) |

> **Note:** `VITE_*` variables are baked into the frontend at build time. Changing them requires a redeploy.

### Custom Domains

To add a custom domain in Railway:
1. Go to your service's Settings tab
2. Under "Domains", click "Add Custom Domain"
3. Add a CNAME record pointing to Railway's provided target
4. Railway auto-provisions TLS certificates

### Redeployment

Railway redeploys automatically on push to the connected branch. To trigger a manual redeploy:
- Go to the service in the Railway dashboard and click "Redeploy"
- Or use the Railway CLI: `railway up`

---

## Environment Variables Reference

All configuration is via environment variables. Copy `.env.example` to `.env` to get started.

### Required

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | API key for the configured LLM provider |
| `ZEP_API_KEY` | — | [Zep Cloud](https://app.getzep.com/) API key for knowledge graph memory |

### LLM Provider

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `anthropic` | Provider: `anthropic`, `openai`, or `gemini` |
| `LLM_BASE_URL` | Auto-configured | Override the provider's default API base URL |
| `LLM_MODEL_NAME` | Auto-configured | Override the provider's default model |

Setting `LLM_PROVIDER` auto-configures the base URL and model:

| Provider | Base URL | Default Model |
|----------|----------|---------------|
| `anthropic` | `https://api.anthropic.com/v1/` | `claude-sonnet-4-20250514` |
| `openai` | `https://api.openai.com/v1/` | `gpt-4o` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` |

### Authentication (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_ENABLED` | `false` | Enable OAuth login gate |
| `AUTH_PROVIDER` | `google` | OAuth provider: `google` or `okta` |
| `AUTH_ALLOWED_DOMAIN` | `intercom.io` | Restrict login to this email domain |
| `GOOGLE_CLIENT_ID` | — | Google OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth 2.0 client secret |
| `OKTA_ISSUER` | — | Okta SSO issuer URL (if using Okta) |
| `OKTA_CLIENT_ID` | — | Okta client ID (if using Okta) |

### Accelerated LLM (Optional)

For parallel processing with a secondary LLM provider:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BOOST_API_KEY` | — | API key for boost provider |
| `LLM_BOOST_BASE_URL` | — | Base URL for boost provider |
| `LLM_BOOST_MODEL_NAME` | — | Model name for boost provider |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | `5001` | Backend port (Docker and manual) |
| `FRONTEND_PORT` | `3000` | Frontend port (Docker only) |
| `FLASK_DEBUG` | `true` | Enable Flask debug mode (set `false` in production) |
| `SECRET_KEY` | `change-me-in-production` | Flask session secret key |
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | Maximum simulation rounds |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | Max tool calls per report generation |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` | Max reflection rounds for report agent |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | LLM temperature for report generation |

### Frontend Build Args

These are set at build time (Docker `--build-arg` or Vite environment):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/api` (production) / `http://localhost:5001/api` (dev) | Backend API URL |
| `VITE_DEMO_MODE` | `true` (Docker) / `false` (dev) | Use mock data instead of real backend |
| `VITE_INTERCOM_APP_ID` | — | Intercom widget app ID |

---

## Troubleshooting

### Port 5001 in use (macOS)

macOS AirPlay Receiver uses port 5001. Disable it in **System Settings > General > AirDrop & Handoff**, or change `BACKEND_PORT` in `.env`:

```env
BACKEND_PORT=5002
```

### Port 3000 in use

Change the frontend port:

```bash
# Manual development
pnpm dev --port 3001

# Docker
FRONTEND_PORT=3001 docker compose up -d
```

### Missing uploads directories

If the backend crashes with `FileNotFoundError`:

```bash
mkdir -p backend/uploads/simulations backend/uploads/projects backend/uploads/reports
```

This only affects manual development — the Docker volume handles this automatically.

### API key validation errors

The backend validates `LLM_API_KEY` and `ZEP_API_KEY` on startup. Ensure your `.env` has real keys, not placeholders:

```env
LLM_API_KEY=sk-ant-...      # not "your-api-key-here"
ZEP_API_KEY=z_...            # not "your-zep-api-key-here"
```

### `ERR_NAME_NOT_RESOLVED` in Docker

The Docker frontend is built with `VITE_API_URL=http://backend:5001/api` — the Docker-internal hostname. This works for container-to-container communication but not from a host browser.

For local development with hot-reload, use the [Manual Services](#manual-services) setup where Vite's dev proxy routes `/api` to `localhost:5001`.

### Railway deploy fails

1. **Check build logs** in the Railway dashboard for the failing service
2. **Verify root directory** is set correctly (`backend/` or `frontend/`)
3. **Check environment variables** — `VITE_*` variables must be set before the build, not just at runtime
4. **Docker build context** — ensure the Dockerfile path matches (`backend/Dockerfile` or `frontend/Dockerfile`)

### Railway backend returns 502

1. Check that `PORT` environment variable matches what the app listens on (Railway injects `PORT` automatically)
2. Verify the health endpoint responds: `curl <railway-url>/api/health`
3. Check Railway logs for startup errors (usually missing API keys)

### CORS errors in production

The backend uses `flask-cors` which allows all origins by default. If you need to restrict origins, set `FRONTEND_URL` in the backend environment and update the CORS configuration in `backend/app/__init__.py`.

### Auth not working on Railway

If authentication fails after deploying, ensure `AUTH_ENABLED=true` and the OAuth provider variables are configured. The OAuth redirect URI must match the Railway domain exactly.

### Frontend shows stale data after env change

`VITE_*` variables are baked into the frontend at build time. After changing them, you must rebuild:

```bash
# Docker
docker compose up -d --build

# Railway
# Trigger a redeploy from the dashboard
```
