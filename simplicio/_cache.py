"""_cache.py — content-addressed cache for LLM completions.

Key = SHA256 of canonical JSON of (provider_id, model, prompt, kwargs).
Value = {timestamp, model, prompt_hash, completion, usage}.

Invariants:
- Reads are race-safe (we use os.replace for atomic writes; partial files
  are never observed).
- TTL is checked at READ time via file mtime; expired files yield miss
  and are unlinked.
- Bust via SIMPLICIO_BUST_CACHE=1 forces miss in the current process for
  all keys (no on-disk delete; downstream put still happens).
- Disable via SIMPLICIO_CACHE=0 makes every operation a no-op.
- Size cap via SIMPLICIO_CACHE_MAX_MB (default 500 MB); eviction is LRU
  by mtime when a put would push us over the cap.
- Hash includes template_version when supplied so changing the stack
  template invalidates all of its derived prompts.

Layout on disk:

  ~/.simplicio/cache/
    completions/
      ab/abcdef0123456789...json    # the cache entry
      ...
    index.jsonl                      # append-only audit log
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


# ----- config ----- #


def _enabled() -> bool:
    return os.environ.get("SIMPLICIO_CACHE", "1").strip() not in (
        "0", "false", "False", "no", "off",
    )


def _bust() -> bool:
    return os.environ.get("SIMPLICIO_BUST_CACHE", "0").strip() in (
        "1", "true", "True", "yes", "on",
    )


def _ttl_days() -> int:
    try:
        return int(os.environ.get("SIMPLICIO_CACHE_TTL_DAYS", "30"))
    except ValueError:
        return 30


def _max_mb() -> int:
    try:
        return int(os.environ.get("SIMPLICIO_CACHE_MAX_MB", "500"))
    except ValueError:
        return 500


def _root() -> Path:
    override = os.environ.get("SIMPLICIO_CACHE_DIR")
    if override:
        return Path(override)
    home = Path(os.environ.get("HOME", str(Path.home())))
    return home / ".simplicio" / "cache"


# ----- key construction ----- #


def make_key(provider_id: str, model: str, prompt: str,
             **kwargs: Any) -> str:
    """Stable SHA256 hex digest of the canonical inputs.

    Extra kwargs (temperature, max_tokens, template_version, ...) are
    folded into the hash; passing template_version="0.2.0" produces a
    different key than template_version="0.1.0" for an otherwise identical
    prompt — the mechanism we use to invalidate when a stack template
    bumps.
    """
    payload = {
        "provider_id": provider_id,
        "model": model,
        "prompt": prompt,
        **{k: v for k, v in sorted(kwargs.items()) if v is not None},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ----- result ADT ----- #


@dataclass
class CacheEntry:
    completion: str
    usage: dict
    model: str
    timestamp: float

    @classmethod
    def from_json(cls, data: dict) -> "CacheEntry":
        return cls(
            completion=data["completion"],
            usage=data.get("usage", {}),
            model=data.get("model", "?"),
            timestamp=data.get("timestamp", time.time()),
        )

    def to_json(self) -> dict:
        return {
            "completion": self.completion,
            "usage": self.usage,
            "model": self.model,
            "timestamp": self.timestamp,
        }


@dataclass
class CacheStats:
    entries: int
    size_bytes: int
    oldest_age_days: float
    enabled: bool
    bust_active: bool
    root: str


# ----- the cache itself ----- #


class CompletionCache:
    """Disk-backed cache for LLM completions. Thread-safety: each entry
    is written atomically via tempfile + os.replace. Multiple workers
    writing the same key are race-tolerant — last writer wins, no half
    files."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = root or _root()
        # Directory creation is lazy — we only mkdir on first put so that
        # a read-only environment can still call cache.get() without
        # surprises.

    @property
    def completions_dir(self) -> Path:
        return self.root / "completions"

    @property
    def index_path(self) -> Path:
        return self.root / "index.jsonl"

    def _entry_path(self, key: str) -> Path:
        return self.completions_dir / key[:2] / f"{key}.json"

    # ---- main API ---- #

    def get(self, key: str) -> Optional[CacheEntry]:
        """Return the cached completion if present, fresh, and bust is off."""
        if not _enabled() or _bust():
            return None
        path = self._entry_path(key)
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            return None
        # TTL check
        ttl_seconds = _ttl_days() * 86400
        if (time.time() - mtime) > ttl_seconds:
            # Best-effort cleanup; do not raise if it fails (race with
            # another process is fine).
            try: path.unlink()
            except OSError: pass
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Malformed cache file — treat as miss; try to remove so it
            # does not haunt future reads.
            try: path.unlink()
            except OSError: pass
            return None
        # touch mtime so this entry counts as recently-used for LRU
        os.utime(path, None)
        self._log("hit", key)
        return CacheEntry.from_json(data)

    def put(self, key: str, entry: CacheEntry) -> None:
        """Atomically write the cache entry. No-op when cache is disabled."""
        if not _enabled():
            return
        path = self._entry_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp file in the same directory and then os.replace
        # so concurrent readers never see a partial file.
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(entry.to_json(), fh, ensure_ascii=False)
            os.replace(tmp_path, path)
        except Exception:
            # On any failure clean up the tempfile and swallow — caching
            # is a side concern; never break the caller.
            try: os.unlink(tmp_path)
            except OSError: pass
            return
        self._log("put", key)
        # Best-effort size enforcement
        self._evict_if_needed()

    def clear(self) -> int:
        """Delete the entire cache directory. Returns the count of entries
        removed."""
        if not self.completions_dir.is_dir():
            return 0
        count = sum(1 for _ in self.completions_dir.rglob("*.json"))
        shutil.rmtree(self.completions_dir, ignore_errors=True)
        # We DO NOT remove the index.jsonl — audit log persists across
        # cache clears so we can reason about historical hit rate.
        return count

    def stats(self) -> CacheStats:
        entries = 0
        size_bytes = 0
        oldest_mtime = time.time()
        if self.completions_dir.is_dir():
            for p in self.completions_dir.rglob("*.json"):
                try:
                    st = p.stat()
                except FileNotFoundError:
                    continue
                entries += 1
                size_bytes += st.st_size
                if st.st_mtime < oldest_mtime:
                    oldest_mtime = st.st_mtime
        age_days = (time.time() - oldest_mtime) / 86400 if entries else 0.0
        return CacheStats(
            entries=entries,
            size_bytes=size_bytes,
            oldest_age_days=round(age_days, 1),
            enabled=_enabled(),
            bust_active=_bust(),
            root=str(self.root),
        )

    # ---- internals ---- #

    def _log(self, action: str, key: str) -> None:
        """Append a single JSONL line to the audit log. Never raises."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with self.index_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "ts": time.time(),
                    "action": action,
                    "key": key[:16],  # truncate to save space
                }) + "\n")
        except OSError:
            pass

    def _evict_if_needed(self) -> int:
        """LRU eviction when over the size cap. Returns the count removed."""
        cap_bytes = _max_mb() * 1024 * 1024
        if cap_bytes <= 0:
            return 0
        if not self.completions_dir.is_dir():
            return 0
        # Gather files with mtime so we can sort by LRU
        files: list[tuple[float, int, Path]] = []
        total = 0
        for p in self.completions_dir.rglob("*.json"):
            try:
                st = p.stat()
            except FileNotFoundError:
                continue
            files.append((st.st_mtime, st.st_size, p))
            total += st.st_size
        if total <= cap_bytes:
            return 0
        files.sort()  # oldest first
        removed = 0
        for mtime, size, path in files:
            if total <= cap_bytes:
                break
            try:
                path.unlink()
                total -= size
                removed += 1
            except OSError:
                continue
        return removed


# Module-level singleton so providers.py can call cache.get/put without
# rebuilding the cache instance per call.
_singleton: Optional[CompletionCache] = None


def cache() -> CompletionCache:
    global _singleton
    if _singleton is None:
        _singleton = CompletionCache()
    return _singleton


def reset_for_tests() -> None:
    """Test hook: drop the singleton so monkeypatched envvars take effect
    on the next cache() call."""
    global _singleton
    _singleton = None
