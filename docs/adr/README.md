# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the GTM MiroFish Demo project.

ADRs capture the key architectural decisions made during the project, along with their context and consequences. They follow the format proposed by [Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [001](001-multi-llm-provider-abstraction.md) | Multi-LLM Provider Abstraction via OpenAI SDK | Accepted | 2026-03-25 |
| [002](002-vue3-composition-api-with-pinia.md) | Vue 3 Composition API with Pinia State Management | Accepted | 2026-03-25 |
| [003](003-intercom-design-token-system.md) | Intercom Design Token System via CSS Variables | Accepted | 2026-03-25 |
| [004](004-async-task-based-simulation.md) | Async Task-Based Simulation with Polling | Accepted | 2026-03-25 |
| [005](005-lightweight-demo-mode-docker.md) | Lightweight Demo Mode Docker Deployment | Accepted | 2026-03-25 |
| [006](006-optional-oauth-domain-enforcement.md) | Optional OAuth with Domain Enforcement | Accepted | 2026-03-25 |
| [007](007-vue3-vite-frontend-framework.md) | Vue 3 + Vite for Frontend Framework | Accepted | 2026-03-25 |
| [008](008-flask-backend-framework.md) | Flask for Backend Framework | Accepted | 2026-03-25 |
| [009](009-d3-data-visualizations.md) | D3.js v7 for Data Visualizations | Accepted | 2026-03-25 |
| [010](010-zep-cloud-knowledge-graph.md) | Zep Cloud for Knowledge Graph Storage | Accepted | 2026-03-25 |
| [011](011-railway-per-service-deployment.md) | Railway Per-Service Docker Deployment | Accepted | 2026-03-25 |

## Creating a New ADR

1. Copy the template below into a new file named `NNN-short-title.md`
2. Fill in each section
3. Add an entry to the index table above
4. Submit via pull request

### Template

```markdown
# ADR-NNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-NNN](NNN-title.md)

## Date

YYYY-MM-DD

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```
