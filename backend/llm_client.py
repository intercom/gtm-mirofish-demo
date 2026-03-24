"""
Thin LLM wrapper — supports Anthropic and OpenAI providers.

Reads LLM_PROVIDER and LLM_API_KEY from env.  Returns None when no key is
configured or on any error, so the caller can fall back to keyword matching.
"""

import os
import logging

log = logging.getLogger(__name__)

_DEFAULTS = {
    "anthropic": {"model": "claude-sonnet-4-20250514"},
    "openai": {"model": "gpt-4o"},
}


def chat_completion(messages, model=None, max_tokens=1024):
    """Send messages to the configured LLM provider.

    Args:
        messages: list of {"role": str, "content": str} dicts.
                  For Anthropic the first system message is extracted automatically.
        model:    override the default model name.
        max_tokens: max response tokens.

    Returns:
        The assistant's response text, or None on any failure.
    """
    provider = (os.environ.get("LLM_PROVIDER") or "").lower().strip()
    api_key = (os.environ.get("LLM_API_KEY") or "").strip()

    if not api_key or api_key == "your-api-key-here":
        return None

    if not provider:
        provider = "anthropic"

    model_name = (
        model
        or (os.environ.get("LLM_MODEL_NAME") or "").strip()
        or _DEFAULTS.get(provider, {}).get("model", "gpt-4o")
    )

    try:
        if provider == "anthropic":
            return _call_anthropic(messages, model_name, max_tokens, api_key)
        elif provider == "openai":
            return _call_openai(messages, model_name, max_tokens, api_key)
        else:
            log.warning("Unknown LLM_PROVIDER: %s", provider)
            return None
    except Exception:
        log.exception("LLM call failed (provider=%s)", provider)
        return None


def _call_anthropic(messages, model, max_tokens, api_key):
    import anthropic

    system_text = None
    user_messages = []
    for m in messages:
        if m["role"] == "system":
            system_text = m["content"]
        else:
            user_messages.append({"role": m["role"], "content": m["content"]})

    client = anthropic.Anthropic(api_key=api_key)
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": user_messages,
    }
    if system_text:
        kwargs["system"] = system_text

    response = client.messages.create(**kwargs)
    return response.content[0].text


def _call_openai(messages, model, max_tokens, api_key):
    import openai

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
    )
    return response.choices[0].message.content
