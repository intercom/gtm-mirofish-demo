"""Tests for app.services.metrics_collector — metrics aggregation and computation."""

from datetime import datetime

from app.services.metrics_collector import MetricsCollector


class TestComputeActionDistribution:
    def test_empty_agent_stats(self):
        result = MetricsCollector._compute_action_distribution([])
        assert result == []

    def test_single_agent(self):
        agent_stats = [
            {"action_types": {"CREATE_POST": 5, "LIKE": 3, "REPLY": 2}}
        ]
        result = MetricsCollector._compute_action_distribution(agent_stats)
        assert len(result) == 3
        # Sorted by count descending
        assert result[0]["action_type"] == "CREATE_POST"
        assert result[0]["count"] == 5

    def test_aggregates_across_agents(self):
        agent_stats = [
            {"action_types": {"CREATE_POST": 5, "LIKE": 3}},
            {"action_types": {"CREATE_POST": 2, "REPLY": 4}},
        ]
        result = MetricsCollector._compute_action_distribution(agent_stats)
        types = {r["action_type"]: r["count"] for r in result}
        assert types["CREATE_POST"] == 7
        assert types["LIKE"] == 3
        assert types["REPLY"] == 4

    def test_percent_sums_to_100(self):
        agent_stats = [
            {"action_types": {"CREATE_POST": 50, "LIKE": 30, "REPLY": 20}}
        ]
        result = MetricsCollector._compute_action_distribution(agent_stats)
        total_pct = sum(r["percent"] for r in result)
        assert abs(total_pct - 100.0) < 0.5

    def test_categorizes_content_vs_engagement(self):
        agent_stats = [
            {"action_types": {"CREATE_POST": 10, "LIKE": 5, "UPVOTE": 3, "REPLY": 7}}
        ]
        result = MetricsCollector._compute_action_distribution(agent_stats)
        categories = {r["action_type"]: r["category"] for r in result}
        assert categories["CREATE_POST"] == "content"
        assert categories["REPLY"] == "content"
        assert categories["LIKE"] == "engagement"
        assert categories["UPVOTE"] == "engagement"


class TestBuildRoundSeries:
    def test_empty_timeline(self):
        assert MetricsCollector._build_round_series([]) == []

    def test_transforms_timeline(self):
        timeline = [
            {"round_num": 1, "twitter_actions": 10, "reddit_actions": 5,
             "total_actions": 15, "active_agents_count": 8},
            {"round_num": 2, "twitter_actions": 12, "reddit_actions": 7,
             "total_actions": 19, "active_agents_count": 10},
        ]
        result = MetricsCollector._build_round_series(timeline)
        assert len(result) == 2
        assert result[0] == {"round": 1, "twitter": 10, "reddit": 5, "total": 15, "active_agents": 8}
        assert result[1]["round"] == 2

    def test_handles_missing_fields(self):
        timeline = [{"round_num": 1}]
        result = MetricsCollector._build_round_series(timeline)
        assert result[0]["twitter"] == 0
        assert result[0]["reddit"] == 0


class TestBuildAgentLeaderboard:
    def test_empty_stats(self):
        assert MetricsCollector._build_agent_leaderboard([]) == []

    def test_builds_leaderboard(self):
        agent_stats = [
            {"agent_id": 0, "agent_name": "Alice", "total_actions": 20,
             "twitter_actions": 12, "reddit_actions": 8,
             "action_types": {"CREATE_POST": 10, "LIKE": 10}},
        ]
        result = MetricsCollector._build_agent_leaderboard(agent_stats)
        assert len(result) == 1
        assert result[0]["agent_name"] == "Alice"
        assert result[0]["total_actions"] == 20
        assert result[0]["top_action"] == "CREATE_POST"  # tied, but max returns first

    def test_limits_to_10(self):
        agent_stats = [
            {"agent_id": i, "agent_name": f"Agent_{i}", "total_actions": i,
             "action_types": {"POST": i}}
            for i in range(20)
        ]
        result = MetricsCollector._build_agent_leaderboard(agent_stats)
        assert len(result) == 10

    def test_handles_no_action_types(self):
        agent_stats = [
            {"agent_id": 0, "agent_name": "Bob", "total_actions": 5, "action_types": {}}
        ]
        result = MetricsCollector._build_agent_leaderboard(agent_stats)
        assert result[0]["top_action"] is None


class TestComputeRates:
    def test_basic_rates(self):
        timeline = [
            {"action_types": {"CREATE_POST": 5, "LIKE": 3, "REPLY": 2}},
            {"action_types": {"CREATE_POST": 3, "UPVOTE": 4, "SHARE": 1}},
        ]
        result = MetricsCollector._compute_rates(timeline, total_actions=18, current_round=2)
        assert result["content_actions"] == 10  # CREATE_POST + REPLY
        assert result["engagement_actions"] == 8  # LIKE + UPVOTE + SHARE
        assert result["actions_per_round"] == 9.0

    def test_zero_round_no_division_error(self):
        result = MetricsCollector._compute_rates([], total_actions=0, current_round=0)
        assert result["actions_per_round"] == 0


class TestEmptyMetrics:
    def test_structure(self):
        result = MetricsCollector._empty_metrics("test_sim")
        assert result["simulation_id"] == "test_sim"
        assert result["status"] == "idle"
        assert result["summary"]["total_actions"] == 0
        assert result["platform_breakdown"]["twitter"]["actions"] == 0
        assert result["action_distribution"] == []
        assert result["agent_leaderboard"] == []
        assert result["round_series"] == []


class TestGenerateDemoMetrics:
    def test_returns_complete_structure(self):
        result = MetricsCollector.generate_demo_metrics("demo_123")
        assert result["simulation_id"] == "demo_123"
        assert result["status"] == "completed"
        assert "summary" in result
        assert "platform_breakdown" in result
        assert "action_distribution" in result
        assert "agent_leaderboard" in result
        assert "round_series" in result

    def test_demo_totals_consistent(self):
        result = MetricsCollector.generate_demo_metrics()
        summary = result["summary"]
        platform = result["platform_breakdown"]
        # Total actions should equal twitter + reddit from round series
        twitter = platform["twitter"]["actions"]
        reddit = platform["reddit"]["actions"]
        assert summary["total_actions"] == twitter + reddit

    def test_demo_progress_is_100(self):
        result = MetricsCollector.generate_demo_metrics()
        assert result["summary"]["progress_percent"] == 100

    def test_demo_leaderboard_sorted(self):
        result = MetricsCollector.generate_demo_metrics()
        lb = result["agent_leaderboard"]
        for i in range(len(lb) - 1):
            assert lb[i]["total_actions"] >= lb[i + 1]["total_actions"]
