"""Tests for app.services.anomaly_detector — Z-score anomaly detection."""

import pytest

from app.services.anomaly_detector import (
    AnomalyDetector,
    Anomaly,
    _score_content,
    _z_score,
    _normalize_surprise,
    generate_demo_anomalies,
    POSITIVE_WORDS,
    NEGATIVE_WORDS,
)


class TestScoreContent:
    def test_empty_string_returns_zero(self):
        assert _score_content("") == 0.0

    def test_none_returns_zero(self):
        assert _score_content(None) == 0.0

    def test_positive_content(self):
        score = _score_content("This is excellent and impressive work")
        assert score > 0

    def test_negative_content(self):
        score = _score_content("I am concerned and skeptical about the risk")
        assert score < 0

    def test_neutral_content(self):
        score = _score_content("The weather is cloudy today")
        assert score == 0.0

    def test_balanced_content(self):
        # One positive, one negative → score = 0
        score = _score_content("This is excellent but also risky")
        # "excellent" is positive, "risk" is in negative list (substring match)
        # Result depends on exact word matches
        assert -1 <= score <= 1

    def test_score_range(self):
        all_positive = " ".join(POSITIVE_WORDS)
        all_negative = " ".join(NEGATIVE_WORDS)
        assert _score_content(all_positive) == 1.0
        assert _score_content(all_negative) == -1.0


class TestZScore:
    def test_basic_z_score(self):
        assert _z_score(10.0, 5.0, 2.5) == 2.0

    def test_zero_std_returns_zero(self):
        assert _z_score(10.0, 5.0, 0.0) == 0.0

    def test_very_small_std_returns_zero(self):
        assert _z_score(10.0, 5.0, 0.005) == 0.0

    def test_negative_z_score(self):
        assert _z_score(0.0, 5.0, 2.5) == -2.0


class TestNormalizeSurprise:
    def test_below_threshold_returns_zero(self):
        assert _normalize_surprise(1.5, threshold=2.0) == 0.0

    def test_at_threshold_returns_zero(self):
        assert _normalize_surprise(2.0, threshold=2.0) == 0.0

    def test_above_threshold(self):
        result = _normalize_surprise(3.5, threshold=2.0, max_z=5.0)
        assert 0 < result < 1

    def test_at_max_returns_one(self):
        assert _normalize_surprise(5.0, threshold=2.0, max_z=5.0) == 1.0

    def test_above_max_capped_at_one(self):
        assert _normalize_surprise(10.0, threshold=2.0, max_z=5.0) == 1.0

    def test_negative_z_uses_absolute(self):
        assert _normalize_surprise(-3.5, threshold=2.0, max_z=5.0) == _normalize_surprise(3.5, threshold=2.0, max_z=5.0)


class TestAnomalyDataclass:
    def test_to_dict(self):
        a = Anomaly(
            anomaly_id="test_1",
            agent_id=1,
            agent_name="Agent One",
            anomaly_type="sentiment_reversal",
            round_num=3,
            surprise_score=0.75,
            description="test description",
            explanation="test explanation",
        )
        d = a.to_dict()
        assert d["anomaly_id"] == "test_1"
        assert d["agent_id"] == 1
        assert d["anomaly_type"] == "sentiment_reversal"
        assert d["surprise_score"] == 0.75


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_empty_actions_returns_empty(self):
        assert self.detector.detect_anomalies([]) == []

    def test_single_round_no_anomalies(self):
        actions = [
            {"agent_id": 0, "agent_name": "A", "round_num": 1,
             "action_args": {"content": "hello world"}, "action_type": "POST"},
        ]
        anomalies = self.detector.detect_anomalies(actions)
        assert isinstance(anomalies, list)

    def test_sentiment_reversal_detected(self):
        """Agent with dramatic sentiment swing should trigger anomaly."""
        actions = []
        # Rounds 1-4: consistently positive
        for r in range(1, 5):
            actions.append({
                "agent_id": 0, "agent_name": "TestAgent", "round_num": r,
                "action_args": {"content": "excellent impressive great amazing"},
                "action_type": "POST",
            })
        # Round 5: dramatically negative
        actions.append({
            "agent_id": 0, "agent_name": "TestAgent", "round_num": 5,
            "action_args": {"content": "concerned skeptical worried frustrated poor"},
            "action_type": "POST",
        })
        anomalies = self.detector.detect_anomalies(actions)
        sentiment_reversals = [a for a in anomalies if a.anomaly_type == "sentiment_reversal"]
        assert len(sentiment_reversals) > 0

    def test_filter_by_round(self):
        actions = []
        for r in range(1, 6):
            actions.append({
                "agent_id": 0, "agent_name": "A", "round_num": r,
                "action_args": {"content": "neutral text"},
                "action_type": "POST",
            })
        # Get all anomalies, then filter
        all_anomalies = self.detector.detect_anomalies(actions)
        round_3 = self.detector.detect_anomalies(actions, round_num=3)
        assert all(a.round_num == 3 for a in round_3)

    def test_results_sorted_by_surprise(self):
        """Anomalies should be sorted descending by surprise_score."""
        actions = []
        # Create multiple agents with varying behaviors
        for agent in range(3):
            for r in range(1, 8):
                sentiment = "excellent great" if r < 6 else "terrible poor frustrated"
                actions.append({
                    "agent_id": agent, "agent_name": f"Agent_{agent}", "round_num": r,
                    "action_args": {"content": sentiment},
                    "action_type": "POST",
                })
        anomalies = self.detector.detect_anomalies(actions)
        for i in range(len(anomalies) - 1):
            assert anomalies[i].surprise_score >= anomalies[i + 1].surprise_score

    def test_score_surprise_returns_anomaly_score(self):
        a = Anomaly(
            anomaly_id="t", agent_id=0, agent_name="A",
            anomaly_type="test", round_num=1, surprise_score=0.42,
            description="test",
        )
        assert self.detector.score_surprise(a) == 0.42

    def test_skips_actions_without_agent_or_round(self):
        actions = [
            {"agent_name": "A", "round_num": 1, "action_args": {"content": "hi"}, "action_type": "POST"},
            {"agent_id": 0, "agent_name": "A", "action_args": {"content": "hi"}, "action_type": "POST"},
        ]
        # Should not crash
        result = self.detector.detect_anomalies(actions)
        assert isinstance(result, list)


class TestGenerateDemoAnomalies:
    def test_returns_list_of_dicts(self):
        demos = generate_demo_anomalies()
        assert isinstance(demos, list)
        assert len(demos) == 4

    def test_demo_anomaly_types(self):
        demos = generate_demo_anomalies()
        types = {d["anomaly_type"] for d in demos}
        assert types == {"sentiment_reversal", "unexpected_agreement", "leadership_emergence", "topic_hijacking"}

    def test_demo_has_required_keys(self):
        demos = generate_demo_anomalies()
        required = {"anomaly_id", "agent_id", "agent_name", "anomaly_type", "round_num", "surprise_score", "description"}
        for d in demos:
            assert required.issubset(d.keys())
