"""Tests for app.services.sentiment_analyzer — sentiment scoring and event detection."""

import math

from app.services.sentiment_analyzer import (
    _score_content,
    _score_action,
    _moving_average,
    _interpolate,
    _detect_events,
    _generate_story_arc,
    _empty_result,
    analyze_sentiment,
    generate_demo_sentiment,
    POSITIVE_WORDS,
    NEGATIVE_WORDS,
    AGENT_COLORS,
)


class TestScoreContent:
    def test_empty_returns_zero(self):
        assert _score_content("") == 0.0
        assert _score_content(None) == 0.0

    def test_purely_positive(self):
        score = _score_content("This is excellent and innovative")
        assert score > 0

    def test_purely_negative(self):
        score = _score_content("This is frustrating and problematic")
        assert score < 0

    def test_no_keywords_returns_zero(self):
        assert _score_content("The sky is blue") == 0.0

    def test_score_bounded(self):
        assert -1 <= _score_content(" ".join(POSITIVE_WORDS + NEGATIVE_WORDS)) <= 1


class TestScoreAction:
    def test_like_action_gets_positive_boost(self):
        action = {"action_type": "LIKE", "action_args": {"content": ""}}
        score = _score_action(action)
        assert score == pytest.approx(0.3, abs=0.01)

    def test_reply_with_positive_content(self):
        action = {"action_type": "REPLY", "action_args": {"content": "excellent work"}}
        score = _score_action(action)
        assert score > 0

    def test_post_with_negative_content(self):
        action = {"action_type": "POST", "action_args": {"content": "frustrated and poor"}}
        score = _score_action(action)
        assert score < 0

    def test_repost_gets_boost(self):
        action = {"action_type": "REPOST", "action_args": {"content": ""}}
        score = _score_action(action)
        assert score == pytest.approx(0.2, abs=0.01)

    def test_missing_action_type(self):
        action = {"action_args": {"content": "hello"}}
        score = _score_action(action)
        assert isinstance(score, float)


class TestMovingAverage:
    def test_window_1_returns_same(self):
        values = [1.0, 2.0, 3.0, 4.0]
        result = _moving_average(values, window=1)
        assert result == values

    def test_smooths_values(self):
        values = [0.0, 10.0, 0.0]
        result = _moving_average(values, window=3)
        # Middle value should be average of all three
        assert result[1] == pytest.approx(10.0 / 3, abs=0.01)

    def test_preserves_length(self):
        values = [1, 2, 3, 4, 5]
        assert len(_moving_average(values, window=3)) == 5

    def test_empty_list(self):
        assert _moving_average([], window=3) == []


class TestInterpolate:
    def test_no_nones(self):
        assert _interpolate([1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0]

    def test_fills_middle_none(self):
        result = _interpolate([1.0, None, 3.0])
        assert result[1] == 2.0

    def test_fills_leading_none(self):
        result = _interpolate([None, 2.0, 3.0])
        # Leading None: prev defaults to 0, next is 2.0 → average = 1.0
        assert result[0] == 1.0

    def test_fills_trailing_none(self):
        result = _interpolate([1.0, 2.0, None])
        # Trailing None: prev is 2.0, no next → uses prev as next_val → 2.0
        assert result[2] == 2.0


class TestDetectEvents:
    def test_consensus_detected(self):
        # All agents with similar scores → low spread
        agent_rounds = {
            0: {1: [0.5], 2: [0.5]},
            1: {1: [0.52], 2: [0.48]},
        }
        rounds = [1, 2]
        group_raw = [0.51, 0.49]
        events = _detect_events(group_raw, rounds, agent_rounds, rounds)
        consensus = [e for e in events if e["type"] == "consensus"]
        assert len(consensus) > 0

    def test_conflict_detected(self):
        # Agents with very different scores → high spread
        agent_rounds = {
            0: {1: [0.8]},
            1: {1: [-0.5]},
        }
        rounds = [1]
        group_raw = [0.15]
        events = _detect_events(group_raw, rounds, agent_rounds, rounds)
        conflicts = [e for e in events if e["type"] == "conflict"]
        assert len(conflicts) > 0

    def test_mood_swing_detected(self):
        # Need at least 2 agents per round for event detection
        agent_rounds = {
            0: {1: [0.1], 2: [0.5]},
            1: {1: [0.1], 2: [0.5]},
        }
        rounds = [1, 2]
        group_raw = [0.1, 0.5]
        events = _detect_events(group_raw, rounds, agent_rounds, rounds)
        swings = [e for e in events if e["type"] == "swing"]
        assert len(swings) > 0


class TestGenerateStoryArc:
    def test_returns_correct_length(self):
        rounds = [1, 2, 3, 4, 5]
        arc = _generate_story_arc(rounds)
        assert len(arc) == 5
        assert all("round" in p and "value" in p for p in arc)

    def test_single_round(self):
        arc = _generate_story_arc([1])
        assert len(arc) == 1
        assert arc[0]["value"] == 0

    def test_empty_rounds(self):
        assert _generate_story_arc([]) == []


class TestAnalyzeSentiment:
    def test_empty_actions(self):
        result = analyze_sentiment([])
        assert result == _empty_result()

    def test_basic_analysis(self):
        actions = [
            {"agent_id": 0, "agent_name": "Alice", "round_num": 1,
             "action_type": "POST", "action_args": {"content": "excellent work"}},
            {"agent_id": 1, "agent_name": "Bob", "round_num": 1,
             "action_type": "POST", "action_args": {"content": "poor results"}},
            {"agent_id": 0, "agent_name": "Alice", "round_num": 2,
             "action_type": "POST", "action_args": {"content": "good progress"}},
            {"agent_id": 1, "agent_name": "Bob", "round_num": 2,
             "action_type": "POST", "action_args": {"content": "still concerned"}},
        ]
        result = analyze_sentiment(actions)

        assert len(result["agents"]) == 2
        assert result["rounds"] == [1, 2]
        assert len(result["group_average"]) == 2
        assert isinstance(result["events"], list)
        assert isinstance(result["story_arc"], list)

    def test_agent_colors_assigned(self):
        actions = [
            {"agent_id": i, "agent_name": f"Agent_{i}", "round_num": 1,
             "action_type": "POST", "action_args": {"content": "test"}}
            for i in range(3)
        ]
        result = analyze_sentiment(actions)
        colors = [a["color"] for a in result["agents"]]
        assert len(set(colors)) == 3  # All unique

    def test_actions_without_round_skipped(self):
        actions = [
            {"agent_id": 0, "agent_name": "A", "action_type": "POST",
             "action_args": {"content": "hello"}},
        ]
        result = analyze_sentiment(actions)
        assert result == _empty_result()

    def test_scores_have_raw_and_smoothed(self):
        actions = [
            {"agent_id": 0, "agent_name": "A", "round_num": r,
             "action_type": "POST", "action_args": {"content": "great"}}
            for r in range(1, 4)
        ]
        result = analyze_sentiment(actions)
        scores = result["agents"][0]["scores"]
        for s in scores:
            assert "round" in s
            assert "raw" in s
            assert "smoothed" in s


class TestGenerateDemoSentiment:
    def test_returns_complete_structure(self):
        result = generate_demo_sentiment(num_rounds=5, num_agents=3)
        assert "agents" in result
        assert "group_average" in result
        assert "events" in result
        assert "story_arc" in result
        assert "rounds" in result

    def test_correct_agent_count(self):
        result = generate_demo_sentiment(num_rounds=5, num_agents=3)
        assert len(result["agents"]) == 3

    def test_correct_round_count(self):
        result = generate_demo_sentiment(num_rounds=8, num_agents=2)
        assert len(result["rounds"]) == 8

    def test_deterministic_with_seed(self):
        r1 = generate_demo_sentiment(num_rounds=5, num_agents=3)
        r2 = generate_demo_sentiment(num_rounds=5, num_agents=3)
        assert r1["agents"][0]["scores"] == r2["agents"][0]["scores"]


import pytest  # noqa: E402 (for approx)
