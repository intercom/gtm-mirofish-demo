# ADR-007: Vue 3 + Vite for Frontend Framework

## Status

Accepted

## Date

2026-03-25

## Context

The GTM MiroFish Demo needed a frontend framework to build an interactive simulation dashboard with complex data visualizations (force-directed graphs, heatmaps, sentiment timelines) and real-time streaming updates. The primary candidates were:

- **React + Next.js** — dominant ecosystem, large community, SSR support
- **Vue 3 + Vite** — lightweight, fast dev server, Composition API
- **Svelte/SvelteKit** — minimal bundle size, compiled approach

The frontend has 7 views (Landing, Scenario Builder, Knowledge Graph, Simulation, Report, Chat, Settings) with heavy D3.js integration for SVG-based visualizations. The team needed rapid prototyping speed for a demo product, not a production SaaS app.

## Decision

We chose **Vue 3 (v3.5) with Vite (v8.x), Tailwind CSS 4, and Pinia** for state management.

Key factors:

1. **D3 integration** — Vue's reactivity system and explicit DOM ownership (`<template>` vs JSX) makes it easier to hand off SVG container elements to D3 without fighting the framework's virtual DOM diffing. React's concurrent rendering and strict diffing can conflict with D3's direct DOM manipulation.

2. **Composition API** — `<script setup>` syntax enables clean composable extraction for shared logic (API polling, simulation state, chart lifecycle), keeping visualization code modular without class hierarchies or HOC wrappers.

3. **Vite dev speed** — Sub-100ms HMR with native ESM. For a demo that undergoes frequent branding and layout iteration, instant feedback is critical. Next.js dev server adds SSR compilation overhead unnecessary for a client-rendered SPA.

4. **Bundle simplicity** — No SSR, no server components, no hydration complexity. The frontend is a static SPA served by a lightweight `serve` process in production, keeping the Docker image minimal.

5. **Tailwind 4 + design tokens** — Intercom brand tokens (`#2068FF`, `#050505`, `#ff5600`) are defined in `brand-tokens.css` and consumed directly by Tailwind's utility classes, enabling consistent theming without a component library dependency.

## Consequences

- **Positive**: Fast iteration, clean D3 integration via composables, small production bundle, simple static deployment
- **Positive**: Pinia stores provide predictable state management without Redux boilerplate
- **Negative**: Smaller hiring pool compared to React — less relevant for a demo/internal tool
- **Negative**: Fewer pre-built component libraries than React ecosystem, requiring more custom UI work
