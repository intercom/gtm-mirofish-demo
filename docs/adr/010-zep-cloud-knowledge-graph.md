# ADR-010: Zep Cloud for Knowledge Graph Storage

## Status

Accepted

## Date

2026-03-25

## Context

The MiroFish simulation pipeline requires a knowledge graph to store entities, relationships, and facts extracted from seed data. The graph is built from LLM-parsed text and later queried during simulation and report generation. We needed a knowledge graph backend that supports:

- Entity and relationship storage with typed edges
- Semantic search across graph contents
- Community detection for entity clustering
- Temporal fact filtering for simulation rounds
- Optional availability — the system must work without it in demo mode

We considered:
1. **Neo4j (self-hosted)** — Full-featured graph database, requires infrastructure management.
2. **Local vector DB (ChromaDB/Qdrant)** — Lightweight embedding storage, no native graph relationships.
3. **Zep Cloud** — Managed knowledge graph service with built-in entity extraction and semantic search.

## Decision

We use **Zep Cloud** as the managed knowledge graph backend, accessed through a thread-safe singleton client with graceful degradation when unavailable.

**Implementation:**

1. **Singleton client** (`backend/app/services/zep_client.py`) — Thread-safe lazy initialization with three access modes:
   - `get_zep_client()` — Returns client or `None` if unavailable (for optional features)
   - `require_zep_client()` — Returns client or raises an error (for required operations)
   - `is_zep_available()` — Boolean check for feature gating

2. **Graph memory service** (`backend/app/services/zep_graph_memory.py`) — Maps simulation data to Zep's episode model:
   - `add_episode()` — Stores agent messages as graph episodes
   - `build_graph()` — Triggers async graph construction from episodes
   - `query_graph()` — Hybrid search (semantic + BM25) with cross-encoder reranking
   - `get_entity_relationships()` — Retrieves typed edges between entities
   - `get_community_summary()` — Community detection grouped by entity type
   - `get_temporal_facts()` — Facts filtered by time windows
   - Built-in retry logic (3 attempts, exponential backoff starting at 2s)

3. **Entity reader** (`backend/app/services/zep_entity_reader.py`) — Filters and enriches graph nodes:
   - Excludes generic labels ("Entity", "Node") for meaningful results
   - Enriches entities with related edges and connected nodes
   - Paginated API access via `zep_paging.py` utility

4. **Demo fallback** — All graph services return mock data when `ZEP_API_KEY` is not configured, providing realistic entity structures and relationships without external dependencies.

## Consequences

**Easier:**
- No graph database infrastructure to manage — Zep Cloud handles storage, indexing, and search
- Built-in semantic search with reranking eliminates custom embedding pipeline
- Community detection and temporal queries come out of the box
- Demo mode works without any external services

**Harder:**
- Vendor dependency on Zep Cloud — no self-hosted option currently
- Episode-based API requires mapping simulation rounds to Zep's data model
- Network latency for graph queries during simulation (mitigated by retry logic)
- Zep's entity extraction may differ from LLM-generated ontology, requiring reconciliation
