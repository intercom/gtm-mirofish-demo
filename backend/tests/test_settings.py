"""Tests for Settings API endpoints."""

from unittest.mock import patch, MagicMock


class TestTestLLM:
    """POST /api/v1/settings/test-llm"""

    def test_missing_api_key(self, client):
        resp = client.post(
            "/api/v1/settings/test-llm",
            json={"provider": "openai"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    def test_unknown_provider(self, client):
        resp = client.post(
            "/api/v1/settings/test-llm",
            json={"provider": "unknown_provider", "apiKey": "sk-test"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Unknown provider" in resp.get_json()["error"]

    @patch("app.api.settings.OpenAI")
    def test_successful_connection(self, mock_openai_cls, client):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        resp = client.post(
            "/api/v1/settings/test-llm",
            json={"provider": "openai", "apiKey": "sk-test-key"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        mock_client.models.list.assert_called_once()

    @patch("app.api.settings.OpenAI")
    def test_connection_failure(self, mock_openai_cls, client):
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Connection refused")
        mock_openai_cls.return_value = mock_client

        resp = client.post(
            "/api/v1/settings/test-llm",
            json={"provider": "anthropic", "apiKey": "sk-ant-test"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["ok"] is False
        assert "Connection refused" in body["error"]

    @patch("app.api.settings.OpenAI")
    def test_provider_base_url_passed(self, mock_openai_cls, client):
        mock_openai_cls.return_value = MagicMock()

        client.post(
            "/api/v1/settings/test-llm",
            json={"provider": "gemini", "apiKey": "gm-test"},
            content_type="application/json",
        )
        call_kwargs = mock_openai_cls.call_args[1]
        assert "generativelanguage.googleapis.com" in call_kwargs["base_url"]

    def test_empty_body(self, client):
        resp = client.post(
            "/api/v1/settings/test-llm",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestTestZep:
    """POST /api/v1/settings/test-zep"""

    def test_missing_api_key(self, client):
        resp = client.post(
            "/api/v1/settings/test-zep",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    @patch("app.api.settings.test_zep", wraps=None)
    @patch("zep_cloud.client.Zep")
    def test_successful_connection(self, mock_zep_cls, _wrap, client):
        mock_client = MagicMock()
        mock_zep_cls.return_value = mock_client

        resp = client.post(
            "/api/v1/settings/test-zep",
            json={"apiKey": "z_test_key"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    @patch("zep_cloud.client.Zep")
    def test_zep_connection_failure(self, mock_zep_cls, client):
        mock_client = MagicMock()
        mock_client.user.list.side_effect = Exception("Connection refused")
        mock_zep_cls.return_value = mock_client

        resp = client.post(
            "/api/v1/settings/test-zep",
            json={"apiKey": "bad-key"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Connection refused" in resp.get_json()["error"]

    @patch("zep_cloud.client.Zep")
    def test_zep_network_error(self, mock_zep_cls, client):
        mock_zep_cls.side_effect = Exception("DNS resolution failed")

        resp = client.post(
            "/api/v1/settings/test-zep",
            json={"apiKey": "z_test"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "DNS resolution failed" in resp.get_json()["error"]


class TestAuthStatus:
    """GET /api/v1/settings/auth-status"""

    def test_auth_disabled(self, client):
        resp = client.get("/api/v1/settings/auth-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["authEnabled"] is False
        assert data["provider"] is None
        assert data["user"] is None

    def test_auth_enabled_no_session(self, client, app):
        app.config["AUTH_ENABLED"] = True
        app.config["AUTH_PROVIDER"] = "google"
        app.config["AUTH_ALLOWED_DOMAIN"] = "intercom.io"

        resp = client.get("/api/v1/settings/auth-status")
        data = resp.get_json()
        assert data["authEnabled"] is True
        assert data["provider"] == "google"
        assert data["allowedDomain"] == "intercom.io"
        assert data["user"] is None

    def test_auth_enabled_with_session(self, client, app):
        app.config["AUTH_ENABLED"] = True
        app.config["AUTH_PROVIDER"] = "google"

        with client.session_transaction() as sess:
            sess["user"] = {
                "email": "dev@intercom.io",
                "name": "Test User",
                "picture": "https://example.com/pic.jpg",
            }

        resp = client.get("/api/v1/settings/auth-status")
        data = resp.get_json()
        assert data["user"]["email"] == "dev@intercom.io"
        assert data["user"]["name"] == "Test User"


class TestServiceStatus:
    """GET /api/v1/settings/service-status"""

    def test_service_status_with_keys(self, client):
        resp = client.get("/api/v1/settings/service-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["overall"] == "healthy"
        assert data["data"]["services"]["llm"]["status"] == "connected"
        assert data["data"]["services"]["zep"]["status"] == "connected"

    def test_service_status_demo_mode(self, client, app):
        """When no keys are set, service status reports demo mode."""
        app.config["LLM_API_KEY"] = ""
        app.config["ZEP_API_KEY"] = ""
        with patch("app.api.settings.Config") as mock_config:
            mock_config.LLM_API_KEY = ""
            mock_config.ZEP_API_KEY = ""
            mock_config.LLM_MODEL_NAME = None
            resp = client.get("/api/v1/settings/service-status")
        data = resp.get_json()
        assert data["data"]["overall"] == "demo"
        assert data["data"]["services"]["llm"]["status"] == "demo"
        assert data["data"]["services"]["zep"]["status"] == "demo"

    def test_service_status_degraded(self, client, app):
        """When only one key is set, status is degraded."""
        with patch("app.api.settings.Config") as mock_config:
            mock_config.LLM_API_KEY = "test-key"
            mock_config.ZEP_API_KEY = ""
            mock_config.LLM_MODEL_NAME = "gpt-4o"
            resp = client.get("/api/v1/settings/service-status")
        data = resp.get_json()
        assert data["data"]["overall"] == "degraded"
        assert data["data"]["services"]["llm"]["status"] == "connected"
        assert data["data"]["services"]["zep"]["status"] == "demo"


class TestCacheManagement:
    """Cache management endpoints under /api/v1/settings/cache"""

    def test_cache_stats(self, client):
        resp = client.get("/api/v1/settings/cache")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_cache_clear(self, client):
        resp = client.delete("/api/v1/settings/cache")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_cache_evict(self, client):
        resp = client.post(
            "/api/v1/settings/cache/evict",
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
