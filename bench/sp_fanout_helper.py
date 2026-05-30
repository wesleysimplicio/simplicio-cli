"""sp_fanout_helper.py — execute the sp side via REAL N=200 subagents.

Before: bench harnesses prepended the sp .md template to the prompt and
sent ONE LLM call. The template was just text; the runtime fan-out kernel
was never touched. Empirical result: sp regressed or tied vs cli alone on
4 models.

After (mandate from user 2026-05-30): every sp invocation must run through
`kernel.subagent_runtime.SubagentRuntime` with N=200 parallel subagents
(diversify=True so prompts actually differ), then modal-vote pick the
winning output.

Public API:
  sp_fanout_complete(model_id, sp_wrapped_prompt) -> dict
    {"text": str, "tokens": int, "ms": int, "uniq": int,
     "modal_count": int, "subagents": int, "error": str|None}
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from collections import Counter
from typing import Optional


DEFAULT_SUBAGENTS = int(os.environ.get("BENCH_SP_SUBAGENTS", "200"))


# ---- model → endpoint table (mirrors bench/run_fanout.py) ---- #

_ROUTING: dict[str, dict] = {
    # HuggingFace router models
    "Qwen/Qwen2.5-Coder-3B-Instruct":   {"preset": None, "base_url": "https://router.huggingface.co/v1", "env_key": "HF_TOKEN"},
    "Qwen/Qwen2.5-Coder-7B-Instruct":   {"preset": None, "base_url": "https://router.huggingface.co/v1", "env_key": "HF_TOKEN"},
    "Qwen/Qwen3-Coder-30B-A3B-Instruct": {"preset": None, "base_url": "https://router.huggingface.co/v1", "env_key": "HF_TOKEN"},
    "Qwen/Qwen3-Coder-Next":             {"preset": None, "base_url": "https://router.huggingface.co/v1", "env_key": "HF_TOKEN"},
}


def _normalize(text: str) -> str:
    """Hash-friendly normalization: strip trailing whitespace + collapse blanks."""
    if not text:
        return ""
    lines = [line.rstrip() for line in text.split("\n")]
    out, blank = [], False
    for ln in lines:
        if ln == "":
            if blank:
                continue
            blank = True
        else:
            blank = False
        out.append(ln)
    return "\n".join(out).strip()


def _modal_vote(texts: list[str]) -> tuple[Optional[str], int, int]:
    """Return (winning_text, count_of_modal, unique_outputs)."""
    if not texts:
        return None, 0, 0
    normalized = [_normalize(t) for t in texts]
    by_hash: dict[str, str] = {}
    for raw, norm in zip(texts, normalized):
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]
        by_hash.setdefault(h, raw)
    hashes = [hashlib.sha256(n.encode("utf-8")).hexdigest()[:12] for n in normalized]
    counter = Counter(hashes)
    winning_hash, winning_count = counter.most_common(1)[0]
    return by_hash[winning_hash], winning_count, len(counter)


def _build_runtime(model_id: str):
    """Make a SubagentRuntime configured for model_id. Routes via the same
    table run_fanout.py uses; falls back to OpenRouter for unlisted models."""
    from kernel.providers import LLMProvider, resolve_provider_config
    from kernel.subagent_runtime import SubagentRuntime

    cfg = _ROUTING.get(model_id)
    if cfg is not None:
        api_key = os.environ.get(cfg["env_key"])
        if not api_key:
            raise SystemExit(
                f"sp_fanout_helper: missing {cfg['env_key']} for {model_id}")
        overrides = {
            "api_key": api_key, "model": model_id,
            "prompt_cost_per_mtok": 0.0, "completion_cost_per_mtok": 0.0,
        }
        if cfg.get("base_url"):
            overrides["base_url"] = cfg["base_url"]
        config = resolve_provider_config(cfg.get("preset"), **overrides)
    else:
        # default: OpenRouter
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise SystemExit(
                f"sp_fanout_helper: missing OPENROUTER_API_KEY for {model_id}")
        config = resolve_provider_config(
            "openrouter", api_key=api_key, model=model_id,
            prompt_cost_per_mtok=0.0, completion_cost_per_mtok=0.0,
        )

    return SubagentRuntime(
        LLMProvider(config),
        temperature=float(os.environ.get("BENCH_SP_TEMP", "0.7")),
        max_tokens=int(os.environ.get("BENCH_SP_MAX_TOKENS", "4096")),
    )


def sp_fanout_complete(model_id: str, sp_wrapped_prompt: str,
                        system: str = "You are a senior engineer.",
                        subagents: int = DEFAULT_SUBAGENTS) -> dict:
    """Fan out N=subagents parallel calls of the sp-wrapped prompt. Take
    modal vote. Returns the winning text + diagnostics."""
    t0 = time.perf_counter()
    try:
        runtime = _build_runtime(model_id)
    except SystemExit as e:
        return {"text": "", "tokens": 0, "ms": 0, "uniq": 0,
                "modal_count": 0, "subagents": 0, "error": str(e)}

    # Build N prompts. We use diversify=True via the kernel so each subagent
    # gets a different persona injected — same goal, varied framing → varied
    # outputs → meaningful modal vote.
    prompts = [{"system": system, "prompt": sp_wrapped_prompt}] * subagents
    try:
        report = runtime.run(
            task="sp-fanout",
            subagents=subagents,
            prompts=prompts,
            use_cache=False,
            diversify=True,
        )
    except TypeError:
        # Older kernel without diversify kwarg — fall back without it
        report = runtime.run(
            task="sp-fanout",
            subagents=subagents,
            prompts=prompts,
            use_cache=False,
        )
    except Exception as e:
        return {"text": "", "tokens": 0, "ms": int((time.perf_counter() - t0) * 1000),
                "uniq": 0, "modal_count": 0, "subagents": 0, "error": str(e)}

    texts = [r.text for r in report.results if getattr(r, "ok", False)]
    winning_text, modal_count, uniq = _modal_vote(texts)
    return {
        "text": winning_text or "",
        "tokens": getattr(report.usage, "total_tokens", 0) if hasattr(report, "usage") else 0,
        "ms": int((time.perf_counter() - t0) * 1000),
        "uniq": uniq,
        "modal_count": modal_count,
        "subagents": subagents,
        "completed": getattr(report, "completed", subagents),
        "failed": getattr(report, "failed", 0),
        "error": None,
    }
