"""Tests for Settings API endpoints."""

from unittest.mock import patch, MagicMock


class TestTestLLM:
    """POST /api/settings/test-llm"""

    def test_missing_api_key(self, client):
        resp = client.post(
            "/api/settings/test-llm",
            json={"provider": "openai"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    def test_unknown_provider(self, client):
        resp = client.post(
            "/api/settings/test-llm",
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
            "/api/settings/test-llm",
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
            "/api/settings/test-llm",
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
            "/api/settings/test-llm",
            json={"provider": "gemini", "apiKey": "gm-test"},
            content_type="application/json",
        )
        call_kwargs = mock_openai_cls.call_args[1]
        assert "generativelanguage.googleapis.com" in call_kwargs["base_url"]

    def test_empty_body(self, client):
        resp = client.post(
            "/api/settings/test-llm",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestTestZep:
    """POST /api/settings/test-zep"""

    def test_missing_api_key(self, client):
        resp = client.post(
            "/api/settings/test-zep",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    @patch("httpx.get")
    def test_successful_connection(self, mock_get, client):
        mock_get.return_value = MagicMock(status_code=200)

        resp = client.post(
            "/api/settings/test-zep",
            json={"apiKey": "z_test_key"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    @patch("httpx.get")
    def test_zep_404_still_ok(self, mock_get, client):
        """Zep returns 404 when no users exist yet — that's a valid connection."""
        mock_get.return_value = MagicMock(status_code=404)

        resp = client.post(
            "/api/settings/test-zep",
            json={"apiKey": "z_test_key"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    @patch("httpx.get")
    def test_zep_401_fails(self, mock_get, client):
        mock_get.return_value = MagicMock(status_code=401)

        resp = client.post(
            "/api/settings/test-zep",
            json={"apiKey": "bad-key"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("httpx.get")
    def test_zep_network_error(self, mock_get, client):
        mock_get.side_effect = Exception("DNS resolution failed")

        resp = client.post(
            "/api/settings/test-zep",
            json={"apiKey": "z_test"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "DNS resolution failed" in resp.get_json()["error"]


class TestAuthStatus:
    """GET /api/settings/auth-status"""

    def test_auth_disabled(self, client):
        resp = client.get("/api/settings/auth-status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["authEnabled"] is False
        assert data["provider"] is None
        assert data["user"] is None

    def test_auth_enabled_no_session(self, client, app):
        app.config["AUTH_ENABLED"] = True
        app.config["AUTH_PROVIDER"] = "google"
        app.config["AUTH_ALLOWED_DOMAIN"] = "intercom.io"

        resp = client.get("/api/settings/auth-status")
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

        resp = client.get("/api/settings/auth-status")
        data = resp.get_json()
        assert data["user"]["email"] == "dev@intercom.io"
        assert data["user"]["name"] == "Test User"
