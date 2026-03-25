# ADR 004: Multi-Provider LLM Integration with Fallback

## Status

Accepted

## Context

The demo requires LLM capabilities for seed text generation, report chat, and simulation narrative enrichment. Different stakeholders have access to different LLM providers, and the demo must function convincingly without any API keys configured.

The team evaluated two approaches:

- **Single provider** — commit to one LLM (e.g., Claude) and require that API key
- **Multi-provider with fallback** — support multiple providers, degrade gracefully without keys

## Decision

We implemented a **multi-provider LLM strategy** with three tiers: Anthropic (Claude), OpenAI (GPT-4o), and Google Gemini — plus a keyword-matching fallback when no API key is configured.

Architecture:

1. **Unified client via OpenAI SDK** — All three providers are accessed through the OpenAI Python SDK's compatible interface (`llm_client.py`). Anthropic and Gemini both expose OpenAI-compatible endpoints, so a single client class handles all providers by varying `base_url` and `api_key`. Provider-specific quirks (e.g., Anthropic not supporting `response_format`, MiniMax emitting `<think>` tags) are handled with targeted conditionals.

2. **Environment-driven configuration** — `LLM_PROVIDER` selects the provider (`anthropic|openai|gemini`), `LLM_API_KEY` provides authentication, and `LLM_MODEL_NAME` optionally overrides the default model. Configuration is centralized in `app/config.py` with sensible defaults: Claude Sonnet for Anthropic, GPT-4o for OpenAI, Gemini 2.5 Flash for Google.

3. **Graceful fallback** — When no `LLM_API_KEY` is set, chat endpoints use keyword matching against simulation data to generate contextual responses. Seed text generation returns pre-built scenarios from `gtm_scenarios/`. Streaming endpoints simulate token-by-token delivery with delays. The demo remains fully functional and deterministic.

4. **Token tracking** — Usage is tracked per-provider and per-endpoint with cost estimation, exposed via `/api/settings/llm-usage`. This enables cost visibility during demos and internal testing.

## Consequences

- **Positive**: Demo works out-of-the-box without API keys — critical for quick setup at conferences and stakeholder meetings
- **Positive**: Provider switching via a single env var enables cost optimization (Gemini Flash for development, Claude for production demos)
- **Positive**: Unified SDK approach minimizes dependency surface — no separate client libraries per provider
- **Negative**: OpenAI SDK compatibility layer obscures provider-specific features (e.g., Anthropic's extended thinking, Gemini's grounding)
- **Negative**: Fallback keyword matching produces lower-quality responses that may underwhelm compared to LLM-powered mode
