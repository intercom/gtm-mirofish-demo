"""Tests for app.utils.llm_client — LLMClient wrapper."""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.utils.llm_client import LLMClient


@pytest.fixture()
def mock_openai():
    """Patch OpenAI constructor so no real HTTP calls are made."""
    with patch("app.utils.llm_client.OpenAI") as MockCls:
        mock_client = MagicMock()
        MockCls.return_value = mock_client
        yield mock_client


def _make_chat_response(content: str):
    """Build a minimal OpenAI-style chat completion response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestLLMClientInit:
    def test_requires_api_key(self):
        with patch("app.utils.llm_client.Config") as cfg:
            cfg.LLM_API_KEY = None
            cfg.LLM_BASE_URL = "http://x"
            cfg.LLM_MODEL_NAME = "m"
            with pytest.raises(ValueError, match="LLM_API_KEY"):
                LLMClient(api_key=None)

    def test_accepts_explicit_params(self, mock_openai):
        client = LLMClient(api_key="k", base_url="http://x", model="m")
        assert client.api_key == "k"
        assert client.model == "m"


class TestChat:
    def test_returns_content(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_chat_response("Hello!")
        client = LLMClient(api_key="k", base_url="http://x", model="m")
        result = client.chat([{"role": "user", "content": "hi"}])
        assert result == "Hello!"

    def test_strips_think_tags(self, mock_openai):
        content = "<think>internal reasoning</think>Final answer"
        mock_openai.chat.completions.create.return_value = _make_chat_response(content)
        client = LLMClient(api_key="k", base_url="http://x", model="m")
        result = client.chat([{"role": "user", "content": "q"}])
        assert result == "Final answer"
        assert "<think>" not in result

    def test_skips_response_format_for_anthropic(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_chat_response("ok")
        client = LLMClient(api_key="k", base_url="https://api.anthropic.com/v1/", model="m")
        client.chat(
            [{"role": "user", "content": "q"}],
            response_format={"type": "json_object"},
        )
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert "response_format" not in call_kwargs

    def test_passes_response_format_for_openai(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_chat_response("ok")
        client = LLMClient(api_key="k", base_url="https://api.openai.com/v1/", model="m")
        client.chat(
            [{"role": "user", "content": "q"}],
            response_format={"type": "json_object"},
        )
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}


class TestChatJson:
    def test_parses_json_response(self, mock_openai):
        payload = json.dumps({"entity_types": [], "edge_types": []})
        mock_openai.chat.completions.create.return_value = _make_chat_response(payload)
        client = LLMClient(api_key="k", base_url="http://x", model="m")
        result = client.chat_json([{"role": "user", "content": "q"}])
        assert result == {"entity_types": [], "edge_types": []}

    def test_strips_markdown_code_fences(self, mock_openai):
        payload = '```json\n{"key": "value"}\n```'
        mock_openai.chat.completions.create.return_value = _make_chat_response(payload)
        client = LLMClient(api_key="k", base_url="http://x", model="m")
        result = client.chat_json([{"role": "user", "content": "q"}])
        assert result == {"key": "value"}

    def test_raises_on_invalid_json(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_chat_response("not json")
        client = LLMClient(api_key="k", base_url="http://x", model="m")
        with pytest.raises(ValueError, match="JSON格式无效"):
            client.chat_json([{"role": "user", "content": "q"}])
