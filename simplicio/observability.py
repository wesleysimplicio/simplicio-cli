"""Lightweight opt-in run logging for benchmarks and retry loops."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from .utils.serialization import dumps_str


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    return max(1, len(text.split()) * 4 // 3)


def log_run(root: str, event: dict[str, Any]) -> Path | None:
    if os.environ.get("SIMPLICIO_DISABLE_RUN_LOG"):
        return None
    out = Path(root) / ".simplicio" / "runs.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": os.environ.get("SIMPLICIO_MODEL") or os.environ.get("MODEL") or "",
        "provider": os.environ.get("SIMPLICIO_PROVIDER", "claude"),
        "prompt_variant": os.environ.get("SIMPLICIO_PROMPT_VARIANT", "default"),
        **event,
    }
    with out.open("a", encoding="utf-8") as f:
        f.write(dumps_str(payload) + "\n")
    return out
