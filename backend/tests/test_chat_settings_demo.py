"""Integration tests for Chat, Interview, Settings, Auth, and Demo Control endpoints."""

from unittest.mock import patch


class TestReportChat:
    def test_chat_keyword_match(self, demo_client):
        resp = demo_client.post("/api/report/chat", json={"message": "Tell me about subject line performance"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "response" in data
        assert "subject line" in data["response"].lower() or "open rate" in data["response"].lower()
        assert "sources" in data

    def test_chat_default_response(self, demo_client):
        resp = demo_client.post("/api/report/chat", json={"message": "random unmatched query xyz"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "response" in data
        assert len(data["response"]) > 0

    def test_chat_with_history(self, demo_client):
        resp = demo_client.post("/api/report/chat", json={
            "message": "What about personas?",
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
            ],
        })
        assert resp.status_code == 200
        assert "response" in resp.get_json()["data"]

    def test_chat_tool_calls_present(self, demo_client):
        resp = demo_client.post("/api/report/chat", json={"message": "roi analysis"})
        data = resp.get_json()["data"]
        assert "tool_calls" in data
        assert len(data["tool_calls"]) > 0
        assert "name" in data["tool_calls"][0]

    def test_chat_each_keyword(self, demo_client):
        keywords = ["subject line", "persona", "healthcare", "objection", "roi", "cadence", "fin"]
        for kw in keywords:
            resp = demo_client.post("/api/report/chat", json={"message": kw})
            assert resp.status_code == 200, f"Failed for keyword: {kw}"
            data = resp.get_json()["data"]
            assert len(data["response"]) > 50, f"Short response for keyword: {kw}"


class TestInterview:
    def test_interview_keyword_fallback(self, demo_client):
        resp = demo_client.post("/api/simulation/interview", json={
            "agent_name": "Sarah Chen",
            "agent_role": "VP of Support",
            "agent_company": "Acme SaaS",
            "prompt": "What did you think about the messaging?",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "response" in data
        assert len(data["response"]) > 20

    def test_interview_default_fallback(self, demo_client):
        resp = demo_client.post("/api/simulation/interview", json={
            "agent_name": "Test Agent",
            "agent_role": "Manager",
            "prompt": "What is your favorite color?",
        })
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "response" in data

    def test_interview_batch(self, demo_client):
        resp = demo_client.post("/api/simulation/interview/batch")
        assert resp.status_code == 200

    def test_interview_all(self, demo_client):
        resp = demo_client.post("/api/simulation/interview/all")
        assert resp.status_code == 200

    def test_interview_history(self, demo_client):
        resp = demo_client.post("/api/simulation/interview/history")
        assert resp.status_code == 200


class TestSettings:
    def test_test_llm(self, demo_client):
        resp = demo_client.post("/api/settings/test-llm")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "model" in data

    def test_test_zep(self, demo_client):
        resp = demo_client.post("/api/settings/test-zep")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_auth_status(self, demo_client):
        resp = demo_client.get("/api/settings/auth-status")
        assert resp.status_code == 200
        assert resp.get_json()["authEnabled"] is False


class TestAuth:
    def test_logout(self, demo_client):
        resp = demo_client.get("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True


class TestDemoSpeed:
    def test_get_speed(self, demo_client):
        resp = demo_client.get("/api/demo/speed")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["speed"] == 1.0

    def test_set_speed(self, demo_client):
        resp = demo_client.post("/api/demo/speed", json={"speed": 5.0})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["speed"] == 5.0
        # Verify it persists
        get_resp = demo_client.get("/api/demo/speed")
        assert get_resp.get_json()["data"]["speed"] == 5.0

    def test_speed_minimum_clamped(self, demo_client):
        resp = demo_client.post("/api/demo/speed", json={"speed": 0.01})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["speed"] >= 0.1


class TestDemoSkip:
    def test_skip_graph(self, demo_client):
        demo_client.post("/api/graph/build")
        resp = demo_client.post("/api/demo/skip/graph")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["skipped"] == "graph"

    def test_skip_simulation(self, demo_client):
        demo_client.post("/api/simulation/create")
        resp = demo_client.post("/api/demo/skip/simulation")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["skipped"] == "simulation"

    def test_skip_report(self, demo_client):
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        resp = demo_client.post("/api/demo/skip/report")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["skipped"] == "report"

    def test_skip_unknown_phase(self, demo_client):
        resp = demo_client.post("/api/demo/skip/unknown")
        assert resp.status_code == 400


class TestDemoReset:
    def test_reset_clears_state(self, demo_client):
        # Create some state
        demo_client.post("/api/graph/build")
        demo_client.post("/api/simulation/create")
        demo_client.post("/api/report/generate", json={"simulation_id": "demo-sim-00001"})
        demo_client.post("/api/demo/speed", json={"speed": 10.0})

        # Reset
        resp = demo_client.post("/api/demo/reset")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["reset"] is True

        # Speed should be back to 1.0
        speed = demo_client.get("/api/demo/speed").get_json()["data"]["speed"]
        assert speed == 1.0

        # Report should not be found
        resp = demo_client.post("/api/report/generate/status", json={"report_id": "demo-report-00001"})
        assert resp.status_code == 404


class TestChatWithLLM:
    """Test that LLM integration path works when chat_completion returns a response."""

    @patch("demo_app.chat_completion", return_value="Mocked LLM response about the data.")
    def test_chat_uses_llm_when_available(self, mock_llm, demo_client):
        resp = demo_client.post("/api/report/chat", json={"message": "Tell me about the data"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["response"] == "Mocked LLM response about the data."
        mock_llm.assert_called_once()

    @patch("demo_app.chat_completion", return_value=None)
    def test_chat_falls_back_when_llm_unavailable(self, mock_llm, demo_client):
        resp = demo_client.post("/api/report/chat", json={"message": "subject line performance"})
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        # Should fall back to keyword matching
        assert "open rate" in data["response"].lower() or "subject line" in data["response"].lower()

    @patch("demo_app.chat_completion", return_value="I am Sarah Chen, VP of Support.")
    def test_interview_uses_llm_when_available(self, mock_llm, demo_client):
        resp = demo_client.post("/api/simulation/interview", json={
            "agent_name": "Sarah Chen",
            "agent_role": "VP of Support",
            "prompt": "Introduce yourself",
        })
        assert resp.status_code == 200
        assert resp.get_json()["data"]["response"] == "I am Sarah Chen, VP of Support."
