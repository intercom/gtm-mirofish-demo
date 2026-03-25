# ADR 005: Lightweight Demo Backend over Full OASIS Stack

## Status

Accepted

## Context

The original MiroFish engine runs on the OASIS framework (built on camel-ai) for multi-agent simulations with real LLM-powered interactions. The full stack requires camel-ai, camel-oasis, PyTorch, transformers, and GPU-accelerated inference — producing a Docker image of approximately **5.8 GB** with significant startup time.

## Decision

We built a **lightweight demo backend** (`demo_app.py`) that serves pre-computed simulation data with realistic progressive timing, replacing the full OASIS simulation stack for demo purposes.

Architecture:

1. **In-memory state machine** — The demo backend tracks simulation lifecycle through dictionaries (`_graph_tasks`, `_simulations`, `_reports`). Each operation progresses through states (pending → processing → complete) with configurable timing via the `DEMO_SPEED` environment variable (default: 1.0x, set lower for faster demos).

2. **Pre-built scenario data** — Four GTM simulation scenarios in `gtm_scenarios/` provide realistic agent actions, posts, and interactions. The 15 simulated agents have distinct personas (CMO, VP Sales, Product Manager, etc.) with deterministic behavior seeded by agent name hashes. This ensures consistent demo behavior across runs.

3. **Progressive endpoint simulation** — Graph building (6s base), simulation execution (35s base), and report generation (18s base) all simulate real processing time. Status polling endpoints return percentage progress, creating an authentic experience of a running simulation.

4. **LLM passthrough** — Chat and seed generation endpoints still call the real LLM when an API key is configured, providing genuine AI responses within the lightweight demo shell. Only the heavy simulation orchestration is mocked.

5. **Minimal Docker image** — The demo backend requires only Flask, flask-cors, python-dotenv, and the LLM SDKs. No PyTorch, no GPU drivers, no ML model weights. The resulting image is approximately **150 MB** — a 97% reduction from the full stack.

## Consequences

- **Positive**: 97% Docker image size reduction (5.8 GB → 150 MB), enabling fast deployment on Railway without GPU instances
- **Positive**: Deterministic demo behavior — no LLM variability in simulation results, consistent for stakeholder presentations
- **Positive**: Instant startup — no model loading or GPU initialization delay
- **Positive**: Zero infrastructure cost for simulation — LLM costs only incurred for optional chat/generation features
- **Negative**: Simulation results are static, not dynamically generated — cannot demonstrate truly novel scenarios without the full OASIS stack
- **Negative**: Agent interactions are scripted rather than emergent — loses the "swarm intelligence" authenticity that makes MiroFish compelling
