# ADR-003: Intercom Design Token System via CSS Variables

## Status

Accepted

## Date

2026-03-25

## Context

As an Intercom-branded fork of MiroFish, the frontend must visually align with Intercom's design language while remaining maintainable. We needed a design system approach that:
- Enforces consistent use of Intercom's brand palette across all components
- Supports dark mode without duplicating styles
- Integrates with Tailwind CSS utility classes
- Allows designers to update tokens in one place

We considered:
1. **Tailwind config only** — Define colors/spacing directly in `tailwind.config.js`.
2. **CSS-in-JS tokens** — Use a JavaScript token object imported by components.
3. **CSS custom properties (variables)** — A single CSS file as the source of truth, referenced by Tailwind.

## Decision

We use a **centralized CSS custom properties file** (`frontend/src/assets/brand-tokens.css`) as the single source of truth for design tokens, with Tailwind configured to reference these variables.

The token system is organized in layers:
- **Brand palette**: Primary (#2068FF), Navy (#050505), Fin Orange (#ff5600), Accent (#AA00FF) with tint/shade scales
- **Semantic colors**: Success, warning, error, info mapped to brand-appropriate hues
- **Typography**: System font stack with 8 size variables (xs through 6xl)
- **Spacing**: 11-step scale (space-1 through space-20)
- **Elevation**: 4 shadow levels for depth hierarchy
- **Component tokens**: Pre-composed button, card, input, and badge variants
- **Dark mode**: Complete variable overrides under `.dark` selector

Tailwind's config (`frontend/tailwind.config.js`) references these CSS variables, bridging the token system with utility classes.

## Consequences

**Easier:**
- Changing a brand color updates every component at once (single source of truth)
- Dark mode is a CSS class toggle — no JavaScript re-rendering needed
- Designers can read/edit `brand-tokens.css` without understanding Tailwind or Vue
- Component tokens (e.g., `--btn-primary-bg`) prevent ad-hoc color usage

**Harder:**
- Two layers of indirection (CSS var → Tailwind class) can confuse new contributors
- CSS variables lack the type safety of a JavaScript token object
- Token file (256 lines) requires manual maintenance as the design system grows
