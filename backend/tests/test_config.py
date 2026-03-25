"""Tests for app.config — LLM provider resolution and Config class."""

import os
import pytest
from unittest.mock import patch

from app.config import Config


class TestGetLlmConfig:
    """Test get_llm_config() provider resolution."""

    def test_anthropic_provider(self):
        env = {
            "LLM_PROVIDER": "anthropic",
            "LLM_API_KEY": "sk-ant-test",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.config import get_llm_config
            cfg = get_llm_config()
            assert cfg["api_key"] == "sk-ant-test"
            assert "anthropic" in cfg["base_url"]
            assert "claude" in cfg["model_name"]

    def test_openai_provider(self):
        env = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-openai-test",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.config import get_llm_config
            cfg = get_llm_config()
            assert cfg["api_key"] == "sk-openai-test"
            assert "openai" in cfg["base_url"]
            assert "gpt" in cfg["model_name"]

    def test_gemini_provider(self):
        env = {
            "LLM_PROVIDER": "gemini",
            "LLM_API_KEY": "gemini-test",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.config import get_llm_config
            cfg = get_llm_config()
            assert cfg["api_key"] == "gemini-test"
            assert "generativelanguage" in cfg["base_url"]
            assert "gemini" in cfg["model_name"]

    def test_unknown_provider_fallback(self):
        env = {
            "LLM_PROVIDER": "unknown",
            "LLM_API_KEY": "some-key",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.config import get_llm_config
            cfg = get_llm_config()
            assert cfg["api_key"] == "some-key"
            assert "openai.com" in cfg["base_url"]

    def test_explicit_base_url_overrides_provider(self):
        env = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "k",
            "LLM_BASE_URL": "https://custom.example.com/v1",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.config import get_llm_config
            cfg = get_llm_config()
            assert cfg["base_url"] == "https://custom.example.com/v1"
        # Clean up
        os.environ.pop("LLM_BASE_URL", None)

    def test_explicit_model_overrides_provider(self):
        env = {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "k",
            "LLM_MODEL_NAME": "gpt-4-turbo",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.config import get_llm_config
            cfg = get_llm_config()
            assert cfg["model_name"] == "gpt-4-turbo"
        os.environ.pop("LLM_MODEL_NAME", None)


class TestConfigValidation:
    """Test Config.validate()."""

    def test_validate_missing_keys(self):
        with patch.object(Config, "LLM_API_KEY", None), \
             patch.object(Config, "ZEP_API_KEY", None):
            errors = Config.validate()
            assert len(errors) == 2
            assert any("LLM_API_KEY" in e for e in errors)
            assert any("ZEP_API_KEY" in e for e in errors)

    def test_validate_all_present(self):
        with patch.object(Config, "LLM_API_KEY", "key"), \
             patch.object(Config, "ZEP_API_KEY", "key"):
            errors = Config.validate()
            assert errors == []
