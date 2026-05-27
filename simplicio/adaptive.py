"""Model-adaptive prompt helpers and lightweight task decomposition."""
from __future__ import annotations

import os
import re


WEAK_MODEL_HINTS = (
    "tiny",
    "small",
    "mini",
    "local",
    "3b",
    "7b",
    "8b",
    "qwen",
    "llama",
    "mistral",
)


def model_profile(model: str | None = None) -> dict[str, str]:
    name = (model or os.environ.get("SIMPLICIO_MODEL") or os.environ.get("MODEL") or "").lower()
    if any(hint in name for hint in WEAK_MODEL_HINTS):
        return {
            "name": name or "unknown",
            "tier": "scaffolded",
            "guidance": "Use extra scaffolding, explicit file/path checks, short steps, and concrete verification before producing the final diff.",
        }
    return {
        "name": name or "unknown",
        "tier": "efficient",
        "guidance": "Use concise reasoning, rely on the mapper and precedents, and avoid redundant explanation.",
    }


def split_task(goal: str, max_steps: int = 6) -> list[str]:
    parts = [
        part.strip(" .")
        for part in re.split(r"\s*(?:;|\band\b|,|\bthen\b)\s*", goal, flags=re.I)
        if part.strip(" .")
    ]
    if len(parts) <= 1:
        return []
    return parts[:max_steps]


def build_adaptation_block(goal: str, model: str | None = None) -> str:
    profile = model_profile(model)
    lines = [
        "[MODEL ADAPTATION]",
        f"Model profile: {profile['tier']} ({profile['name']}).",
        profile["guidance"],
    ]
    steps = split_task(goal)
    if steps:
        lines.extend(["", "[TASK DECOMPOSITION]"])
        lines.extend(f"{i}. {step}" for i, step in enumerate(steps, start=1))
        lines.append("Complete each step in order; verify the relevant files before moving on.")
    return "\n".join(lines)
