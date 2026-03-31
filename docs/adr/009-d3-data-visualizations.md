# ADR-009: D3.js v7 for Data Visualizations

## Status

Accepted

## Date

2026-03-25

## Context

The GTM simulation dashboard requires several complex, interactive visualizations:

- **Knowledge graph** — force-directed node-link diagram with drag, zoom, and tooltip interactions
- **Agent influence network** — directed graph with weighted edges showing agent-to-agent influence
- **Engagement heatmap** — matrix visualization with color-scaled cells (agents x rounds)
- **Sentiment timeline** — multi-series line chart tracking per-agent sentiment over simulation rounds
- **Competitive mentions** — stacked bar/area charts for competitor mention frequency

The candidates were:

- **D3.js v7** — low-level SVG/Canvas library, full control over rendering
- **Chart.js** — canvas-based, declarative config, limited chart types
- **Recharts / vue-chartjs** — React/Vue wrappers around charting libraries, higher-level API

## Decision

We chose **D3.js v7** as the sole visualization library.

Key factors:

1. **Force-directed graphs** — D3's `d3-force` module is the standard for interactive node-link layouts. Neither Chart.js nor Recharts support force simulation natively. The knowledge graph and influence network are core features that require precise control over node positioning, link rendering, and physics parameters.

2. **Custom heatmap rendering** — D3's data-join pattern (`enter/update/exit`) maps directly to the heatmap's matrix structure. Each cell is an SVG `<rect>` with data-driven color from `d3-scale-chromatic`, supporting smooth transitions when data updates. Chart.js matrix plugins exist but lack the customization depth needed (custom color scales using Intercom brand colors `#1e3a5f` to `#ff5600`).

3. **SVG export** — All D3 visualizations render to SVG, enabling screenshot/export functionality for the report view. Canvas-based libraries (Chart.js) require additional tooling for image export.

4. **Animation control** — D3 transitions provide frame-level control for simulation playback animations (agents appearing, posts flowing, sentiment shifting). This enables the "progressive reveal" experience during live simulation viewing.

5. **Vue integration via composables** — D3 operates on DOM references passed from Vue `<template>` elements. Each visualization is encapsulated in a composable that accepts a ref to an SVG container, keeping D3 code separate from Vue reactivity. This avoids the dual-rendering conflicts that plague React + D3 integrations.

## Consequences

- **Positive**: Full creative control over every visual element, consistent Intercom branding across all charts
- **Positive**: Single library for all visualization types — no mixing Chart.js for simple charts with D3 for complex ones
- **Negative**: Higher implementation cost per chart compared to declarative libraries — a simple bar chart requires more code than Chart.js
- **Negative**: Steeper learning curve for contributors unfamiliar with D3's data-join paradigm
