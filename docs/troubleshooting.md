# Troubleshooting FAQ

Common issues and solutions for the GTM MiroFish Demo, organized by category.

---

## Setup Issues

### API key not working

**Symptoms:** LLM-powered features (chat, seed generation) return generic/keyword-matched responses instead of AI-generated content.

**Solutions:**

1. **Check key format matches the provider.** Anthropic keys start with `sk-ant-`, OpenAI keys start with `sk-`. Gemini keys are alphanumeric strings from Google AI Studio.

2. **Ensure `LLM_PROVIDER` matches your key type.** If you have an OpenAI key but `LLM_PROVIDER=anthropic`, calls will fail silently and fall back to keyword matching.

   ```bash
   # In your .env (project root, NOT backend/):
   LLM_PROVIDER=anthropic
   LLM_API_KEY=sk-ant-your-key-here
   ```

3. **Verify `.env` is in the project root**, not inside `backend/`. The backend loads it from one directory up:
   ```
   gtm-mirofish-demo/
   ├── .env          ← correct location
   ├── backend/
   └── frontend/
   ```

4. **Make sure the key isn't the placeholder value.** The LLM client ignores the key `your-api-key-here` and returns `None`.

5. **Test your connection** via the Settings page "Test Connection" button, or directly:
   ```bash
   curl -X POST http://localhost:5001/api/settings/test-llm \
     -H "Content-Type: application/json" \
     -d '{"provider": "anthropic", "apiKey": "sk-ant-..."}'
   ```

### Docker build fails

**Symptoms:** `docker compose up` exits with build errors.

**Solutions:**

1. **Ensure Docker Desktop is running.** On macOS, check the menu bar for the Docker icon.

2. **Check available disk space.** Docker images can consume significant space:
   ```bash
   docker system df
   # Free up space if needed:
   docker system prune
   ```

3. **Rebuild without cache** if a previous build is corrupted:
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

4. **Check Docker Compose version.** This project uses the `services:` top-level key (Compose V2):
   ```bash
   docker compose version
   # Should be v2.x+
   ```

### Port already in use

**Symptoms:** `Error: address already in use :::5001` or `:::3000`.

**Solutions:**

1. **Find what's using the port:**
   ```bash
   # macOS/Linux
   lsof -i :5001
   lsof -i :3000
   ```

2. **Stop the conflicting process**, or use custom ports via environment variables:
   ```bash
   # In .env
   BACKEND_PORT=5002
   FRONTEND_PORT=3001
   ```
   Docker Compose reads these automatically. For local development without Docker:
   ```bash
   # Backend
   PORT=5002 python demo_app.py

   # Frontend — update frontend/.env
   VITE_API_URL=http://localhost:5002/api
   ```

3. **Stop leftover Docker containers** from a previous run:
   ```bash
   docker compose down
   ```

---

## Runtime Issues

### CORS errors in browser console

**Symptoms:** Browser console shows `Access to fetch has been blocked by CORS policy` or `No 'Access-Control-Allow-Origin' header`.

**Solutions:**

1. **Ensure the frontend URL matches** what the backend expects. The demo backend currently uses `CORS(app)` with wildcard origins, but production deployments with `AUTH_ENABLED=true` may restrict origins.

2. **Check that your frontend URL includes the port.** `http://localhost:3000` and `http://localhost:5173` are different origins. If running Vite dev mode (port 5173), verify `VITE_API_URL` points to the backend:
   ```bash
   # frontend/.env
   VITE_API_URL=http://localhost:5001/api
   ```

3. **In Docker**, the frontend is pre-built with `VITE_API_URL=http://backend:5001/api` (the Docker service name). If accessing from the host, the browser needs to reach the backend at `http://localhost:5001`, not `http://backend:5001`. Check the `docker-compose.yml` port mappings.

4. **Check for proxy/reverse-proxy interference.** If using nginx or Railway, ensure it forwards CORS headers.

### LLM responses not working

**Symptoms:** Chat gives generic responses, seed text generation returns template data, report chat lacks depth.

**Solutions:**

1. **Verify both `LLM_PROVIDER` and `LLM_API_KEY` are set.** The LLM client requires both — if either is missing, it returns `None` and the app falls back to keyword matching without any error.

2. **Check `VITE_DEMO_MODE`.** If the frontend has `VITE_DEMO_MODE=true`, it may bypass LLM calls entirely.

3. **Test the LLM directly:**
   ```bash
   curl http://localhost:5001/api/health
   # Returns: {"status": "ok", "mode": "demo"}
   ```

4. **Check backend logs** for `LLM call failed` messages:
   ```bash
   # If running locally:
   cd backend && python demo_app.py
   # Errors print to stderr

   # If running in Docker:
   docker logs gtm-mirofish-backend
   ```

5. **Common provider-specific issues:**
   - **Anthropic:** Ensure your plan has API access enabled (not just Claude.ai chat access)
   - **OpenAI:** Check that your API key has billing set up and hasn't hit rate limits
   - **Gemini:** Verify the key was generated from Google AI Studio, not Google Cloud Console

### Zep connection failed

**Symptoms:** Knowledge graph features don't work, entities aren't persisted.

**Solutions:**

1. **Verify `ZEP_API_KEY`** is set in `.env`. Sign up at [app.getzep.com](https://app.getzep.com/) — the free tier is sufficient.

2. **Check Zep Cloud status** at [status.getzep.com](https://status.getzep.com/) for outages.

3. **Test the connection** from Settings, or:
   ```bash
   curl -X POST http://localhost:5001/api/settings/test-zep \
     -H "Content-Type: application/json" \
     -d '{"apiKey": "your-zep-key"}'
   ```

4. **Without Zep**, the app still works — simulation and reporting use in-memory data. Zep adds persistent knowledge graph memory across sessions.

---

## UI Issues

### Charts not rendering

**Symptoms:** Visualization panels show blank areas or loading spinners that never resolve.

**Solutions:**

1. **Check the browser console** (F12 → Console) for D3.js errors. Common causes:
   - Data endpoint returned an error instead of chart data
   - SVG container has zero width/height (responsive layout issue)

2. **Verify data endpoints return correctly:**
   ```bash
   # Replace {sim_id} with your simulation ID
   curl http://localhost:5001/api/simulation/{sim_id}/sentiment
   curl http://localhost:5001/api/simulation/{sim_id}/heatmap
   curl http://localhost:5001/api/simulation/{sim_id}/competitive
   ```

3. **Try resizing the browser window.** Some D3 charts initialize dimensions on mount — if the container was hidden (e.g., in a tab) during mount, the chart may have zero dimensions.

4. **Hard refresh** to clear cached JavaScript: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R` (Windows/Linux).

### Simulation stuck at 0%

**Symptoms:** Simulation starts but progress bar never advances.

**Solutions:**

1. **Check backend logs** for errors during graph build or simulation start:
   ```bash
   # Docker
   docker logs gtm-mirofish-backend --tail 50

   # Local
   # Check the terminal where demo_app.py is running
   ```

2. **Verify the backend is responding:**
   ```bash
   curl http://localhost:5001/api/health
   ```

3. **Try refreshing the page.** The frontend polls for progress — a stale WebSocket or network hiccup can break the polling loop.

4. **Check `DEMO_SPEED`** in `.env`. If set to a very low value (e.g., `0.1`), the simulation will appear to take 10x longer than normal:
   ```bash
   # Default speed
   DEMO_SPEED=1.0

   # Faster for demos
   DEMO_SPEED=3.0
   ```

5. **Start a fresh simulation.** Navigate back to the landing page and try a new scenario. Previous simulation state may be corrupted in memory.

### Blank page after navigation

**Symptoms:** Clicking a link leads to a white screen with no content.

**Solutions:**

1. **Clear localStorage.** Corrupted stored state can prevent views from rendering:
   ```javascript
   // In browser console (F12 → Console):
   localStorage.clear()
   location.reload()
   ```

2. **Check for JavaScript errors** in the browser console (F12 → Console). Look for:
   - `Cannot read properties of undefined` — usually a missing API response
   - `ChunkLoadError` — Vite code-splitting failed to load a lazy route

3. **Hard refresh** the page: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R`.

4. **If using Vue Router history mode**, ensure your server (nginx, Railway) serves `index.html` for all routes. The frontend Dockerfile's nginx config handles this, but custom setups may not.

5. **Check that the backend is reachable.** Some views fetch data on mount and show nothing if the request fails silently. Verify with:
   ```bash
   curl http://localhost:5001/api/health
   ```

---

## Useful Commands

| Task | Command |
|---|---|
| Check backend health | `curl http://localhost:5001/api/health` |
| View backend logs (Docker) | `docker logs gtm-mirofish-backend --tail 100` |
| View frontend logs (Docker) | `docker logs gtm-mirofish-frontend --tail 100` |
| Restart all services | `docker compose restart` |
| Full rebuild | `docker compose down && docker compose up --build -d` |
| Reset demo state | `curl -X POST http://localhost:5001/api/demo/reset` |
| Check running containers | `docker ps` |
| Clear simulation data | `docker volume rm gtm-mirofish-demo_sim_data` |

## Log Locations

| Component | Location |
|---|---|
| Backend (local) | Terminal stdout/stderr where `demo_app.py` runs |
| Backend (Docker) | `docker logs gtm-mirofish-backend` |
| Frontend (dev) | Terminal where `npm run dev` / `pnpm dev` runs |
| Frontend (browser) | Browser DevTools → Console (F12) |
| Frontend (Docker/nginx) | `docker logs gtm-mirofish-frontend` |
| Docker build | Inline during `docker compose up --build` |
