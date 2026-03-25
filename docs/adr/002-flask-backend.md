# ADR 002: Flask for Backend Framework

## Status

Accepted

## Context

The backend serves two roles: (1) a REST API for the Vue frontend, and (2) an orchestration layer for LLM calls, knowledge graph construction, and simulation management. The primary candidates were:

- **Flask** — lightweight Python micro-framework, mature ecosystem
- **FastAPI** — modern Python, async-native, auto-generated OpenAPI docs
- **Express.js** — JavaScript/TypeScript, shared language with frontend

The original MiroFish engine uses Python-based libraries (camel-ai, camel-oasis) for OASIS multi-agent simulation, and all major LLM SDKs (Anthropic, OpenAI, Google GenAI) have first-class Python clients.

## Decision

We chose **Flask 3.x** with Blueprints for API organization and `flask-cors` for cross-origin support.

Key factors:

1. **Python LLM ecosystem** — The Anthropic SDK, OpenAI SDK, and `google-generativeai` all provide idiomatic Python clients. Flask lets us call these directly without async wrappers or bridge layers. The unified LLM client (`llm_client.py`) uses the OpenAI SDK as a compatibility layer across all three providers.

2. **MiroFish compatibility** — The upstream MiroFish codebase is Python. Staying with Flask minimizes the diff between the fork and upstream, making it easier to pull in future simulation engine improvements.

3. **Demo simplicity** — Flask's synchronous request model is sufficient for a demo backend. The app serves pre-built JSON scenarios, manages in-memory simulation state, and proxies LLM calls. There are no long-lived WebSocket connections or high-concurrency requirements that would justify FastAPI's async model.

4. **Rapid prototyping** — Flask's minimal boilerplate (no schema generation, no dependency injection framework) allows fast endpoint iteration. Marshmallow handles request validation where needed without requiring the full Pydantic integration FastAPI enforces.

5. **Deployment** — Gunicorn with 4 workers provides adequate concurrency for demo traffic. The backend Dockerfile installs Flask via `pip` directly — no build step, no compiled extensions, resulting in a slim ~150MB image.

## Consequences

- **Positive**: Minimal framework overhead, direct access to Python LLM SDKs, easy upstream sync with MiroFish
- **Positive**: Simple deployment with gunicorn, small Docker image
- **Negative**: No automatic OpenAPI spec generation — API documentation is manual
- **Negative**: Synchronous model limits throughput under concurrent LLM calls; acceptable for demo scale but would require async migration (or FastAPI) for production load
