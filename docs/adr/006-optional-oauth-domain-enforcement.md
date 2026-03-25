# ADR-006: Optional OAuth with Domain Enforcement

## Status

Accepted

## Date

2026-03-25

## Context

The application needs to support two deployment modes:
1. **Demo/development** — Open access for stakeholder presentations, local development, and testing
2. **Production** — Restricted to Intercom employees via corporate identity provider

We needed an authentication approach that doesn't add friction in demo mode but can be activated for internal deployments.

We considered:
1. **Always-on auth with bypass tokens** — Auth middleware on every request, demo uses a hardcoded token.
2. **Separate auth service** — External auth gateway (e.g., OAuth2 Proxy) in front of the app.
3. **Feature-flagged auth middleware** — Auth is off by default, enabled via environment variable.

## Decision

We use **optional OAuth middleware** controlled by the `AUTH_ENABLED` environment variable (default: `false`).

**Implementation** (`backend/auth/oauth_middleware.py`):
- `AUTH_ENABLED=false` (default): All endpoints are publicly accessible
- `AUTH_ENABLED=true`: The `require_auth()` decorator validates OAuth tokens on protected endpoints
- `AUTH_PROVIDER` selects the identity provider (`google` supported, `okta` planned)
- `AUTH_ALLOWED_DOMAIN` restricts login to a specific email domain (default: `intercom.io`)
- Google OAuth uses `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables
- Email domain is validated server-side via `validate_email_domain()` after OAuth flow

**Frontend integration:**
- `useAuthStore` Pinia store manages user/token state with localStorage persistence
- Settings view exposes auth status and configuration
- `/api/settings/auth-status` endpoint lets the frontend check if auth is active

## Consequences

**Easier:**
- Zero-config demo mode — no auth setup needed for presentations or development
- Production lockdown is a single env var change (`AUTH_ENABLED=true`)
- Domain enforcement prevents unauthorized access even if OAuth is compromised
- Adding new identity providers (Okta, SAML) follows the same decorator pattern

**Harder:**
- Developers must test both auth-on and auth-off code paths
- The `require_auth()` decorator must be manually applied to new endpoints
- No role-based access control — it's all-or-nothing domain gating
- Token refresh and session management add complexity when auth is enabled
