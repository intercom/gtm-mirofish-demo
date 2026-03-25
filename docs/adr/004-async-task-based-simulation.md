# ADR-004: Async Task-Based Simulation with Polling

## Status

Accepted

## Date

2026-03-25

## Context

The MiroFish simulation pipeline involves multiple long-running operations:
1. **Graph building** — LLM-powered ontology generation + Zep knowledge graph construction
2. **Simulation preparation** — OASIS agent profile generation from graph entities
3. **Simulation execution** — Multi-round agent interaction (up to 144 rounds)
4. **Report generation** — LLM-powered analysis of simulation results

Each step can take seconds to minutes. HTTP requests would time out, and the frontend needs to show real-time progress to the user.

We considered:
1. **WebSockets** — Bidirectional real-time communication for progress updates.
2. **Server-Sent Events (SSE)** — Server push for progress, used for chat streaming.
3. **Task ID + polling** — Return a task ID immediately, frontend polls for status.

## Decision

We use an **async task model with frontend polling** for all long-running operations. The simulation also uses SSE for the chat streaming endpoint.

**Backend pattern:**
- Each long-running operation spawns a background thread
- A task ID is returned immediately in the HTTP response
- `TaskManager` (`backend/app/models/`) tracks task state: `pending → running → complete | error`
- `ProjectManager` tracks overall project lifecycle: `idle → building_graph → preparing → running → complete`
- The simulation subprocess communicates via IPC for inter-process updates

**Frontend pattern:**
- `useSimulationPolling()` composable handles polling with configurable interval
- Polls `GET /api/graph/task/:taskId` or `GET /api/simulation/status`
- Progress object includes: `percent`, `message`, `currentRound`, `totalRounds`
- `useSimulationStore` updates reactive state from poll responses, driving UI updates

**SSE is used separately** for the chat streaming endpoint (`POST /api/report/chat/stream`) where token-by-token delivery improves perceived responsiveness.

## Consequences

**Easier:**
- No WebSocket infrastructure to maintain (simpler deployment, no sticky sessions)
- Task IDs enable the user to navigate away and return to check progress
- Polling is resilient to network interruptions (stateless reconnection)
- Each pipeline stage is independently trackable and restartable
- SSE for chat gives real-time token streaming where it matters most

**Harder:**
- Polling introduces latency (up to one poll interval) before UI updates
- Server must maintain in-memory task state (lost on restart unless persisted)
- Multiple concurrent simulations require careful task ID management
- Background threads in Flask need care to avoid request context issues
