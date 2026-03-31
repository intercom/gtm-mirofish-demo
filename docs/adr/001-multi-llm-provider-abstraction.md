# ADR-001: Multi-LLM Provider Abstraction via OpenAI SDK

## Status

Accepted

## Date

2026-03-25

## Context

The GTM MiroFish Demo requires LLM capabilities for ontology generation, agent persona creation, report generation, and chat. Different stakeholders have access to different LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini), and we need the flexibility to switch providers without code changes.

We considered three approaches:
1. **Native SDKs per provider** — Import `anthropic`, `openai`, and `google-generativeai` separately with provider-specific code paths.
2. **Third-party abstraction layer** — Use LiteLLM or LangChain to abstract provider differences.
3. **OpenAI SDK as universal interface** — Leverage the fact that Anthropic and Gemini both expose OpenAI-compatible API endpoints, using the OpenAI Python SDK with configurable `base_url`.

## Decision

We use the **OpenAI Python SDK as a universal LLM interface**, configuring it with provider-specific base URLs and models via environment variables.

The implementation in `backend/app/utils/llm_client.py` wraps the OpenAI SDK and selects the correct configuration based on the `LLM_PROVIDER` environment variable. Provider defaults are defined in `backend/app/config.py`:

- `anthropic` → `https://api.anthropic.com/v1/` with `claude-sonnet-4-20250514`
- `openai` → `https://api.openai.com/v1/` with `gpt-4o`
- `gemini` → `https://generativelanguage.googleapis.com/v1beta/openai/` with `gemini-2.5-flash`

The `LLM_BASE_URL` and `LLM_MODEL_NAME` environment variables allow overriding defaults for custom deployments or model selection.

Provider-specific quirks are handled inside the client:
- Anthropic system messages are extracted and passed separately
- Extended-reasoning thinking blocks are stripped from responses

## Consequences

**Easier:**
- Switching LLM providers is a single env var change (`LLM_PROVIDER=gemini`)
- Only one SDK dependency to manage for the common path
- Custom/self-hosted endpoints work via `LLM_BASE_URL` override
- All service code calls one unified `chat_completion()` interface

**Harder:**
- Provider-specific features (e.g., Anthropic tool use, Gemini grounding) require special handling in the client wrapper
- Debugging API errors requires understanding which provider is active
- The OpenAI SDK may lag behind in supporting new provider-specific features
