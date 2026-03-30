"""Tests for app.services.activity_feed — activity generation and filtering."""

from datetime import datetime, timezone, timedelta

from app.services.activity_feed import ActivityFeedService, ACTIVITY_TYPES


class TestGetRecent:
    def test_returns_list(self):
        result = ActivityFeedService.get_recent()
        assert isinstance(result, list)

    def test_respects_limit(self):
        result = ActivityFeedService.get_recent(limit=5)
        assert len(result) <= 5

    def test_default_limit_is_20(self):
        result = ActivityFeedService.get_recent()
        assert len(result) <= 20

    def test_filters_by_type(self):
        result = ActivityFeedService.get_recent(types=["deal_update"])
        assert all(a["type"] == "deal_update" for a in result)

    def test_filters_by_multiple_types(self):
        result = ActivityFeedService.get_recent(types=["deal_update", "churn_risk"])
        assert all(a["type"] in {"deal_update", "churn_risk"} for a in result)

    def test_ignores_invalid_types(self):
        result = ActivityFeedService.get_recent(types=["nonexistent_type"])
        # No valid types → returns unfiltered
        assert isinstance(result, list)

    def test_filters_by_since(self):
        # Use a since time far in the future → should return nothing
        future = (datetime.now(tz=timezone.utc) + timedelta(days=1)).isoformat()
        result = ActivityFeedService.get_recent(since=future)
        assert len(result) == 0

    def test_since_with_invalid_date_gracefully_ignored(self):
        result = ActivityFeedService.get_recent(since="not-a-date")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_internal_ts_field_in_output(self):
        result = ActivityFeedService.get_recent(limit=5)
        for a in result:
            assert "_ts" not in a


class TestActivityStructure:
    def test_activity_has_required_fields(self):
        result = ActivityFeedService.get_recent(limit=1)
        if result:
            activity = result[0]
            assert "id" in activity
            assert "type" in activity
            assert "title" in activity
            assert "description" in activity
            assert "timestamp" in activity
            assert "severity" in activity
            assert "related_entity" in activity

    def test_id_format(self):
        result = ActivityFeedService.get_recent(limit=5)
        for a in result:
            assert a["id"].startswith("act_")

    def test_severity_values(self):
        result = ActivityFeedService.get_recent(limit=50)
        valid_severities = {"info", "warning", "critical"}
        for a in result:
            assert a["severity"] in valid_severities

    def test_type_values(self):
        result = ActivityFeedService.get_recent(limit=50)
        for a in result:
            assert a["type"] in ACTIVITY_TYPES

    def test_related_entity_structure(self):
        result = ActivityFeedService.get_recent(limit=5)
        for a in result:
            entity = a["related_entity"]
            assert "type" in entity
            assert "name" in entity


class TestDeterminism:
    def test_same_hour_produces_same_results(self):
        """Activities use hour-based seed, so same-hour calls should match."""
        r1 = ActivityFeedService.get_recent(limit=10)
        r2 = ActivityFeedService.get_recent(limit=10)
        # IDs should match (same seed within same hour)
        ids1 = [a["id"] for a in r1]
        ids2 = [a["id"] for a in r2]
        assert ids1 == ids2

    def test_sorted_newest_first(self):
        result = ActivityFeedService.get_recent(limit=10)
        timestamps = [a["timestamp"] for a in result]
        assert timestamps == sorted(timestamps, reverse=True)
