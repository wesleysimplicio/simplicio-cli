"""Tests for simplicio._cache — the 9 scenarios enumerated in issue #34.

  1. hit
  2. miss
  3. ttl expired
  4. version invalidation
  5. bust env var
  6. disabled
  7. lru evict
  8. concurrent write
  9. malformed cache file
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import pytest

from simplicio import _cache as cache_mod
from simplicio._cache import CacheEntry, CompletionCache, make_key, reset_for_tests


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every test gets a clean cache directory and resets the singleton.
    Defaults: cache enabled, no bust, 30 day TTL, 500 MB cap. Tests
    override what they need."""
    monkeypatch.setenv("SIMPLICIO_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("SIMPLICIO_CACHE", raising=False)
    monkeypatch.delenv("SIMPLICIO_BUST_CACHE", raising=False)
    monkeypatch.delenv("SIMPLICIO_CACHE_TTL_DAYS", raising=False)
    monkeypatch.delenv("SIMPLICIO_CACHE_MAX_MB", raising=False)
    reset_for_tests()
    yield tmp_path
    reset_for_tests()


def _entry(text: str = "hello world") -> CacheEntry:
    return CacheEntry(completion=text, usage={"total_tokens": 42},
                      model="test-model", timestamp=time.time())


# ---- 1. hit ---- #

def test_hit_returns_cached_completion() -> None:
    c = CompletionCache()
    key = make_key("planner", "test-model", "prompt 1", temperature=0.1)
    c.put(key, _entry("cached response"))
    got = c.get(key)
    assert got is not None
    assert got.completion == "cached response"


# ---- 2. miss ---- #

def test_miss_returns_none_when_key_absent() -> None:
    c = CompletionCache()
    key = make_key("planner", "test-model", "never seen this prompt")
    assert c.get(key) is None


def test_miss_returns_none_when_different_prompt() -> None:
    c = CompletionCache()
    k1 = make_key("planner", "test-model", "prompt A")
    k2 = make_key("planner", "test-model", "prompt B")
    c.put(k1, _entry("A response"))
    assert c.get(k2) is None


# ---- 3. ttl expired ---- #

def test_ttl_expired_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMPLICIO_CACHE_TTL_DAYS", "1")
    c = CompletionCache()
    key = make_key("planner", "test-model", "ttl test")
    c.put(key, _entry())
    # Backdate the file mtime by 2 days
    path = c._entry_path(key)
    two_days_ago = time.time() - (2 * 86400)
    os.utime(path, (two_days_ago, two_days_ago))
    assert c.get(key) is None
    # Expired file should have been cleaned up
    assert not path.exists()


# ---- 4. version invalidation ---- #

def test_template_version_change_invalidates() -> None:
    c = CompletionCache()
    k_v1 = make_key("planner", "test-model", "same prompt",
                    template_version="0.1.0")
    k_v2 = make_key("planner", "test-model", "same prompt",
                    template_version="0.2.0")
    assert k_v1 != k_v2
    c.put(k_v1, _entry("v1 response"))
    assert c.get(k_v1) is not None
    assert c.get(k_v2) is None  # version bump invalidates


# ---- 5. bust env var ---- #

def test_bust_env_var_forces_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    c = CompletionCache()
    key = make_key("planner", "test-model", "prompt")
    c.put(key, _entry("response"))
    assert c.get(key) is not None  # would normally hit
    monkeypatch.setenv("SIMPLICIO_BUST_CACHE", "1")
    assert c.get(key) is None
    # But put still goes through so the next non-busted run hits
    c.put(key, _entry("fresh response"))
    monkeypatch.delenv("SIMPLICIO_BUST_CACHE")
    got = c.get(key)
    assert got is not None
    assert got.completion == "fresh response"


# ---- 6. disabled ---- #

def test_cache_disabled_no_op(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMPLICIO_CACHE", "0")
    c = CompletionCache()
    key = make_key("planner", "test-model", "prompt")
    c.put(key, _entry())
    # Disabled means we don't even write
    assert c.get(key) is None
    # And the file should not have been created
    assert not c._entry_path(key).exists()


# ---- 7. lru evict ---- #

def test_lru_evict_when_over_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1 byte cap — every put past the first triggers eviction
    monkeypatch.setenv("SIMPLICIO_CACHE_MAX_MB", "0")
    c = CompletionCache()
    # Set the cap to something tiny via env override (0 means no cap, so we
    # use a small positive). Tests with very tiny caps require integer MB,
    # so we monkeypatch the helper directly.
    monkeypatch.setattr(cache_mod, "_max_mb", lambda: 1)
    # Each entry rounds to a few hundred bytes — write enough to exceed 1 MB
    for i in range(2000):
        k = make_key("planner", "test-model", f"prompt {i}")
        c.put(k, _entry(f"response {i}" * 50))  # ~600 bytes each
    stats = c.stats()
    # Verify we cap to ~1 MB (allow ~3x slack since eviction is opportunistic)
    assert stats.size_bytes <= 3 * 1024 * 1024
    # And that the oldest entries were evicted: very first key should be gone
    first_key = make_key("planner", "test-model", "prompt 0")
    assert c.get(first_key) is None
    # While a recent one should still be there
    last_key = make_key("planner", "test-model", "prompt 1999")
    assert c.get(last_key) is not None


# ---- 8. concurrent write ---- #

def test_concurrent_writes_are_race_safe() -> None:
    """Multiple threads writing the same key must never produce a partial
    file; readers should always see either nothing or a complete entry."""
    c = CompletionCache()
    key = make_key("planner", "test-model", "concurrent test")
    errors: list[Exception] = []

    def writer(i: int) -> None:
        try:
            c.put(key, _entry(f"writer-{i}"))
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert errors == []
    got = c.get(key)
    assert got is not None
    assert got.completion.startswith("writer-")  # any winner is fine
    # And the file is valid JSON, not half-written
    blob = c._entry_path(key).read_text()
    data = json.loads(blob)  # raises if half-written
    assert "completion" in data


# ---- 9. malformed cache file ---- #

def test_malformed_cache_file_treated_as_miss() -> None:
    c = CompletionCache()
    key = make_key("planner", "test-model", "malformed test")
    # Write something that put() never would have produced
    path = c._entry_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json", encoding="utf-8")
    assert c.get(key) is None
    # And the bad file should have been removed
    assert not path.exists()


# ---- bonus: stats sanity ---- #

def test_stats_reports_meaningful_numbers() -> None:
    c = CompletionCache()
    assert c.stats().entries == 0
    for i in range(5):
        c.put(make_key("planner", "m", f"p{i}"), _entry())
    s = c.stats()
    assert s.entries == 5
    assert s.size_bytes > 0
    assert s.enabled is True


def test_clear_removes_all_entries() -> None:
    c = CompletionCache()
    for i in range(3):
        c.put(make_key("planner", "m", f"p{i}"), _entry())
    assert c.stats().entries == 3
    removed = c.clear()
    assert removed == 3
    assert c.stats().entries == 0
