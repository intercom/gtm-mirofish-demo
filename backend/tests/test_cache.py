"""Tests for app.services.cache — CacheManager with TTL, eviction, and stats."""

import time

from app.services.cache import CacheManager, CacheEntry


class TestCacheEntry:
    def test_stores_value_and_computes_expiry(self):
        entry = CacheEntry("hello", ttl=10)
        assert entry.value == "hello"
        assert entry.expires_at > entry.created_at
        assert entry.expires_at - entry.created_at == 10


class TestCacheManagerGetSet:
    def test_set_and_get(self):
        cm = CacheManager()
        cm.set("k1", {"data": 1}, ttl=60)
        assert cm.get("k1") == {"data": 1}

    def test_get_missing_returns_none(self):
        cm = CacheManager()
        assert cm.get("nonexistent") is None

    def test_expired_entry_returns_none(self):
        cm = CacheManager()
        cm.set("k1", "value", ttl=0.01)
        time.sleep(0.02)
        assert cm.get("k1") is None

    def test_expired_entry_removed_on_get(self):
        cm = CacheManager()
        cm.set("k1", "value", ttl=0.01)
        time.sleep(0.02)
        cm.get("k1")
        assert "k1" not in cm._store


class TestCacheManagerClear:
    def test_clear_removes_all(self):
        cm = CacheManager()
        cm.set("a", 1, ttl=60)
        cm.set("b", 2, ttl=60)
        count = cm.clear()
        assert count == 2
        assert cm.get("a") is None
        assert cm.get("b") is None

    def test_clear_resets_counters(self):
        cm = CacheManager()
        cm.set("a", 1, ttl=60)
        cm.get("a")  # hit
        cm.get("b")  # miss
        cm.clear()
        stats = cm.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestCacheManagerEviction:
    def test_evict_expired_removes_old_entries(self):
        cm = CacheManager()
        cm.set("fresh", "ok", ttl=60)
        cm.set("stale", "old", ttl=0.01)
        time.sleep(0.02)
        evicted = cm.evict_expired()
        assert evicted == 1
        assert cm.get("fresh") == "ok"
        assert cm.get("stale") is None

    def test_evict_returns_zero_when_nothing_expired(self):
        cm = CacheManager()
        cm.set("a", 1, ttl=60)
        assert cm.evict_expired() == 0


class TestCacheManagerStats:
    def test_stats_tracks_hits_and_misses(self):
        cm = CacheManager()
        cm.set("k", "v", ttl=60)
        cm.get("k")  # hit
        cm.get("k")  # hit
        cm.get("missing")  # miss
        stats = cm.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == round(2 / 3, 3)

    def test_stats_counts_active_and_expired(self):
        cm = CacheManager()
        cm.set("active", "ok", ttl=60)
        cm.set("expired", "old", ttl=0.01)
        time.sleep(0.02)
        stats = cm.stats()
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1
        assert stats["total_entries"] == 2

    def test_stats_zero_division(self):
        cm = CacheManager()
        stats = cm.stats()
        assert stats["hit_rate"] == 0


class TestCacheManagerMakeKey:
    def test_key_is_deterministic(self):
        cm = CacheManager()
        k1 = cm._make_key("/api/test", "page=1")
        k2 = cm._make_key("/api/test", "page=1")
        assert k1 == k2

    def test_different_paths_produce_different_keys(self):
        cm = CacheManager()
        k1 = cm._make_key("/api/a")
        k2 = cm._make_key("/api/b")
        assert k1 != k2

    def test_query_string_affects_key(self):
        cm = CacheManager()
        k1 = cm._make_key("/api/test", "page=1")
        k2 = cm._make_key("/api/test", "page=2")
        assert k1 != k2
