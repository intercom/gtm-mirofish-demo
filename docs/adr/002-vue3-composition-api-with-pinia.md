# ADR-002: Vue 3 Composition API with Pinia State Management

## Status

Accepted

## Date

2026-03-25

## Context

The frontend is a complete rebuild of the original MiroFish UI, re-branded for Intercom. We needed to choose a frontend framework and state management approach that supports:
- Complex simulation workflows with multiple interconnected views (7+ views)
- Real-time polling for async backend operations
- Reusable logic across views (theme, polling, toasts, demo mode)
- Fast iteration during the demo-building phase

We considered:
1. **React + Redux/Zustand** — Larger ecosystem, but the team has more Vue experience.
2. **Vue 3 Options API + Vuex** — Familiar but verbose; Vuex is in maintenance mode.
3. **Vue 3 Composition API + Pinia** — Modern Vue standard with better TypeScript support and simpler API.

## Decision

We use **Vue 3 with the Composition API (`<script setup>` syntax) and Pinia** for state management, built with **Vite** and styled with **Tailwind CSS**.

**State management** is split into focused Pinia stores:
- `useSimulationStore` — Simulation lifecycle, progress, metrics, and run history (localStorage-backed)
- `useAuthStore` — User/token persistence with localStorage
- `useScenariosStore` — GTM scenario template list and selection
- `useSettingsStore` — LLM provider and user preferences
- `useToastStore` — Queue-based notification system

**Reusable logic** is extracted into composables (`frontend/src/composables/`):
- `useSimulationPolling()` — Polls backend task status with backoff
- `useTheme()` — Dark/light mode toggle with localStorage persistence
- `useCountUp()` — Animated number display for metrics
- `useDemoMode()` — Feature flags for demo mode
- `useToast()` — Toast notification API

**Routing** uses Vue Router with lazy-loaded views and URL-param-based task/scenario propagation.

## Consequences

**Easier:**
- `<script setup>` reduces boilerplate significantly vs Options API
- Pinia stores are simpler than Vuex (no mutations, direct state access)
- Composables allow clean logic reuse without mixins or renderless components
- Vite provides fast HMR for rapid frontend iteration
- Tailwind utility classes keep styling co-located with templates

**Harder:**
- Composition API has a steeper learning curve for developers used to Options API
- Multiple small stores require discipline to avoid state duplication
- localStorage-backed state (auth, run history) needs manual cache invalidation
