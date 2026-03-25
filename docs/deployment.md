# Railway Deployment Guide

## Architecture

The project deploys as two Railway services from a single monorepo:

| Service    | Root Directory | Dockerfile          | Port | Health Check   |
|------------|---------------|----------------------|------|----------------|
| **Backend**  | `/backend`    | `backend/Dockerfile`  | `PORT` env var (default 5001) | `GET /api/health` |
| **Frontend** | `/frontend`   | `frontend/Dockerfile` | `PORT` env var (default 3000) | `GET /`         |

## Setup

### 1. Create Railway Project

Create a new project in [Railway](https://railway.app) and add two services, both connected to this GitHub repo.

### 2. Configure Service Root Directories

In each service's **Settings > Source**:
- Backend service: set **Root Directory** to `/backend`
- Frontend service: set **Root Directory** to `/frontend`

Railway reads the `railway.toml` in each service's root directory for build and deploy configuration.

### 3. Set Environment Variables

#### Backend Service

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | No | `anthropic`, `openai`, or `gemini` (defaults to demo mode if unset) |
| `LLM_API_KEY` | No | API key for chosen LLM provider |
| `ZEP_API_KEY` | No | Zep Cloud API key for knowledge graph |
| `AUTH_ENABLED` | No | Set `true` for production auth |
| `AUTH_PROVIDER` | No | `google` or `okta` |
| `AUTH_ALLOWED_DOMAIN` | No | Email domain restriction (e.g., `intercom.io`) |
| `GOOGLE_CLIENT_ID` | If auth=google | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | If auth=google | Google OAuth client secret |
| `SECRET_KEY` | Yes | Flask secret key — generate a random value |
| `FLASK_DEBUG` | No | Set `false` for production |

> **Note:** `PORT` is injected automatically by Railway. Do not set it manually.

#### Frontend Service

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend service URL (e.g., `https://backend-production-e9d7.up.railway.app/api`) |
| `VITE_DEMO_MODE` | No | Set `true` to enable demo mode |
| `VITE_INTERCOM_APP_ID` | No | Intercom widget app ID |

> **Note:** Vite env vars are baked in at build time. Redeploy the frontend after changing these.

### 4. Deploy

Push to the connected branch. Railway auto-builds both services using their Dockerfiles.

## Existing Deployments

- Backend: https://backend-production-e9d7.up.railway.app
- Frontend: https://frontend-production-86ea.up.railway.app

## Troubleshooting

**Health check failing:** The backend health check hits `GET /api/health`. Ensure the backend starts and binds to `PORT`. Check Railway deploy logs for startup errors.

**Frontend shows API errors:** Verify `VITE_API_URL` points to the backend's Railway URL. This is a build-time variable — redeploy after changing it.

**CORS errors:** The backend uses `flask-cors` with permissive defaults. For production, configure `FRONTEND_URL` on the backend to restrict origins.

**Auth not working:** Set `AUTH_ENABLED=true` and configure the OAuth provider variables. Ensure the OAuth redirect URI matches the Railway domain.
