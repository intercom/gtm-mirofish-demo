"""Tests for Unified Service Availability API (/api/v1/services/status)."""

from unittest.mock import patch, MagicMock


class TestServiceStatus:
    """GET /api/v1/services/status — checks backend, LLM, and Zep availability."""

    @patch("app.api.services._check_zep")
    @patch("app.api.services._check_llm")
    def test_all_ok(self, mock_llm, mock_zep, client):
        mock_llm.return_value = {"status": "ok"}
        mock_zep.return_value = {"status": "ok"}

        resp = client.get("/api/v1/services/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["demo"] is False
        assert data["services"]["backend"]["status"] == "ok"
        assert data["services"]["llm"]["status"] == "ok"
        assert data["services"]["zep"]["status"] == "ok"

    @patch("app.api.services._check_zep")
    @patch("app.api.services._check_llm")
    def test_both_unconfigured_is_demo(self, mock_llm, mock_zep, client):
        mock_llm.return_value = {"status": "unconfigured", "message": "LLM_API_KEY not set"}
        mock_zep.return_value = {"status": "unconfigured", "message": "ZEP_API_KEY not set"}

        resp = client.get("/api/v1/services/status")
        data = resp.get_json()
        assert data["ok"] is False
        assert data["demo"] is True
        assert data["services"]["llm"]["status"] == "unconfigured"
        assert data["services"]["zep"]["status"] == "unconfigured"

    @patch("app.api.services._check_zep")
    @patch("app.api.services._check_llm")
    def test_partial_unconfigured_is_demo(self, mock_llm, mock_zep, client):
        """demo=True when any service is unconfigured, even if others work."""
        mock_llm.return_value = {"status": "ok"}
        mock_zep.return_value = {"status": "unconfigured", "message": "ZEP_API_KEY not set"}

        resp = client.get("/api/v1/services/status")
        data = resp.get_json()
        assert data["ok"] is False
        assert data["demo"] is True

    @patch("app.api.services._check_zep")
    @patch("app.api.services._check_llm")
    def test_llm_error(self, mock_llm, mock_zep, client):
        mock_llm.return_value = {"status": "error", "message": "Connection refused"}
        mock_zep.return_value = {"status": "ok"}

        resp = client.get("/api/v1/services/status")
        data = resp.get_json()
        assert data["ok"] is False
        assert data["demo"] is False
        assert data["services"]["llm"]["status"] == "error"
        assert "Connection refused" in data["services"]["llm"]["message"]

    @patch("app.api.services._check_zep")
    @patch("app.api.services._check_llm")
    def test_zep_error(self, mock_llm, mock_zep, client):
        mock_llm.return_value = {"status": "ok"}
        mock_zep.return_value = {"status": "error", "message": "HTTP 401"}

        resp = client.get("/api/v1/services/status")
        data = resp.get_json()
        assert data["ok"] is False
        assert data["services"]["zep"]["status"] == "error"

    @patch("app.api.services._check_zep")
    @patch("app.api.services._check_llm")
    def test_backend_always_ok(self, mock_llm, mock_zep, client):
        """Backend status is always 'ok' if the endpoint is reachable."""
        mock_llm.return_value = {"status": "error", "message": "fail"}
        mock_zep.return_value = {"status": "error", "message": "fail"}

        resp = client.get("/api/v1/services/status")
        data = resp.get_json()
        assert data["services"]["backend"]["status"] == "ok"


class TestCheckLLM:
    """Unit tests for _check_llm helper."""

    def test_unconfigured_when_no_key(self, app):
        with app.app_context():
            app.config["LLM_API_KEY"] = ""
            from app.api.services import _check_llm
            result = _check_llm()
            assert result["status"] == "unconfigured"

    @patch("app.api.services.OpenAI")
    def test_ok_when_models_list_succeeds(self, mock_openai_cls, app):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        with app.app_context():
            app.config["LLM_API_KEY"] = "test-key"
            app.config["LLM_BASE_URL"] = "https://api.openai.com/v1/"
            from app.api.services import _check_llm
            result = _check_llm()
            assert result["status"] == "ok"
            mock_client.models.list.assert_called_once()

    @patch("app.api.services.OpenAI")
    def test_error_when_models_list_fails(self, mock_openai_cls, app):
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Timeout")
        mock_openai_cls.return_value = mock_client

        with app.app_context():
            app.config["LLM_API_KEY"] = "test-key"
            app.config["LLM_BASE_URL"] = "https://api.openai.com/v1/"
            from app.api.services import _check_llm
            result = _check_llm()
            assert result["status"] == "error"
            assert "Timeout" in result["message"]


class TestCheckZep:
    """Unit tests for _check_zep helper."""

    def test_unconfigured_when_no_key(self, app):
        with app.app_context():
            app.config["ZEP_API_KEY"] = ""
            from app.api.services import _check_zep
            result = _check_zep()
            assert result["status"] == "unconfigured"

    @patch("httpx.get")
    def test_ok_on_200(self, mock_get, app):
        mock_get.return_value = MagicMock(status_code=200)
        with app.app_context():
            app.config["ZEP_API_KEY"] = "test-zep-key"
            from app.api.services import _check_zep
            result = _check_zep()
            assert result["status"] == "ok"

    @patch("httpx.get")
    def test_ok_on_404(self, mock_get, app):
        """Zep returns 404 when no users exist — still a valid connection."""
        mock_get.return_value = MagicMock(status_code=404)
        with app.app_context():
            app.config["ZEP_API_KEY"] = "test-zep-key"
            from app.api.services import _check_zep
            result = _check_zep()
            assert result["status"] == "ok"

    @patch("httpx.get")
    def test_error_on_401(self, mock_get, app):
        mock_get.return_value = MagicMock(status_code=401)
        with app.app_context():
            app.config["ZEP_API_KEY"] = "test-zep-key"
            from app.api.services import _check_zep
            result = _check_zep()
            assert result["status"] == "error"
            assert "401" in result["message"]

    @patch("httpx.get")
    def test_error_on_network_failure(self, mock_get, app):
        mock_get.side_effect = Exception("DNS resolution failed")
        with app.app_context():
            app.config["ZEP_API_KEY"] = "test-zep-key"
            from app.api.services import _check_zep
            result = _check_zep()
            assert result["status"] == "error"
            assert "DNS resolution failed" in result["message"]
