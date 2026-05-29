"""
providers.py — provider-agnostic. Does NOT list specific models.

Three modes, picked by SIMPLICIO_MODEL prefix:

1. Native Anthropic SDK
     SIMPLICIO_MODEL=claude-opus-4-7
     SIMPLICIO_API_KEY=<anthropic key>
     SIMPLICIO_BASE_URL=(unset)

2. Any OpenAI-compatible endpoint (OpenRouter, GLM, DeepSeek, Ollama, ...)
     SIMPLICIO_MODEL=anthropic/claude-opus-4
     SIMPLICIO_API_KEY=<provider key>
     SIMPLICIO_BASE_URL=https://openrouter.ai/api/v1

3. Shell-out to a logged-in CLI (zero API key — uses OAuth subscription)
     SIMPLICIO_MODEL=claude-cli/<model>      -> spawns `claude -p`
     SIMPLICIO_MODEL=codex-cli/<model>       -> spawns `codex exec`
     No SIMPLICIO_API_KEY needed. Requires the CLI to be on PATH and the user
     to be logged in (Claude Code session or `codex login`). Subprocess is
     given SIMPLICIO_HOOK_GUARD=1 so the inner CLI does not re-trigger the
     simplicio UserPromptSubmit hook (recursion guard).
"""
import os

from ._cache import CacheEntry, cache, make_key


def _cfg():
    return {
        "model": os.environ.get("SIMPLICIO_MODEL"),
        "base":  os.environ.get("SIMPLICIO_BASE_URL"),
        "key":   os.environ.get("SIMPLICIO_API_KEY")
                 or os.environ.get("OPENROUTER_API_KEY")
                 or os.environ.get("ANTHROPIC_API_KEY"),
    }


def _msgs(prompt, feedback):
    m = [{"role": "user", "content": prompt}]
    if feedback:
        m.append({"role": "user",
                  "content": f"The test FAILED:\n{feedback}\nFix it. Same output format."})
    return m


def _inline_feedback(prompt, feedback):
    if not feedback:
        return prompt
    return f"{prompt}\n\nThe test FAILED:\n{feedback}\nFix it. Same output format."


def _provider_id(model, base):
    if model.startswith("claude-cli/"):
        return "claude-cli"
    if model.startswith("codex-cli/"):
        return "codex-cli"
    if base:
        return f"openai-compatible:{base.rstrip('/')}"
    return "anthropic-native"


def _shell_out(cmd, label):
    """Run a subprocess that uses an OAuth session instead of an API key.

    SIMPLICIO_HOOK_GUARD=1 + SIMPLICIO_SKIP_AUTO_INIT=1 are injected so the
    inner CLI does not recursively fire simplicio's UserPromptSubmit hook nor
    re-run the first-run bootstrap.
    """
    import subprocess
    env = {**os.environ, "SIMPLICIO_HOOK_GUARD": "1", "SIMPLICIO_SKIP_AUTO_INIT": "1"}
    try:
        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True,
            timeout=600, check=False,
        )
    except FileNotFoundError:
        raise SystemExit(
            f"simplicio: `{cmd[0]}` CLI not on PATH. "
            f"Install {label} first, then re-run."
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(f"simplicio: {label} timed out (>600s)")
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise SystemExit(
            f"simplicio: {label} failed (exit {result.returncode}): "
            f"{stderr[:500]}"
        )
    return result.stdout


def _shell_out_claude(prompt, model):
    cmd = ["claude", "-p", prompt]
    if model and model not in ("default", "auto"):
        cmd += ["--model", model]
    return _shell_out(cmd, "Claude Code CLI (`claude -p`)")


def _shell_out_codex(prompt, model):
    cmd = ["codex", "exec"]
    if model and model not in ("default", "auto"):
        cmd += ["--model", model]
    cmd.append(prompt)
    return _shell_out(cmd, "Codex CLI (`codex exec`)")


def generate(prompt, feedback=None, max_tokens=4000):
    c = _cfg()
    model = c["model"]
    if not model:
        raise SystemExit(
            "set SIMPLICIO_MODEL (e.g. anthropic/claude-opus-4, claude-cli/sonnet, "
            "codex-cli/gpt-5, glm-4.6, llama3, claude-opus-4-7)"
        )
    provider_id = _provider_id(model, c["base"])
    key = make_key(
        provider_id,
        model,
        prompt,
        feedback=feedback,
        max_tokens=max_tokens,
    )
    cached = cache().get(key)
    if cached is not None:
        return cached.completion

    # Path 3: shell out to a logged-in CLI. No API key needed.
    if model.startswith("claude-cli/"):
        out = _shell_out_claude(_inline_feedback(prompt, feedback), model.split("/", 1)[1])
        cache().put(key, CacheEntry(out, provider_id=provider_id, model=model))
        return out
    if model.startswith("codex-cli/"):
        out = _shell_out_codex(_inline_feedback(prompt, feedback), model.split("/", 1)[1])
        cache().put(key, CacheEntry(out, provider_id=provider_id, model=model))
        return out

    if not c["key"]:
        raise SystemExit(
            "set SIMPLICIO_API_KEY (or OPENROUTER_/ANTHROPIC_API_KEY). "
            "No key? Use SIMPLICIO_MODEL=claude-cli/<model> or codex-cli/<model> "
            "to shell out to your logged-in CLI instead (zero key)."
        )

    # Native Anthropic path: no base_url
    if not c["base"]:
        import anthropic
        cli = anthropic.Anthropic(api_key=c["key"])
        r = cli.messages.create(model=model, max_tokens=max_tokens,
                                messages=_msgs(prompt, feedback))
        out = next((b.text for b in r.content if b.type == "text"), "")
        cache().put(key, CacheEntry(out, provider_id=provider_id, model=model))
        return out

    # Any OpenAI-compatible endpoint (OpenRouter, GLM, DeepSeek, local...)
    from openai import OpenAI
    cli = OpenAI(base_url=c["base"], api_key=c["key"])
    r = cli.chat.completions.create(model=model, max_tokens=max_tokens,
                                    messages=_msgs(prompt, feedback))
    out = r.choices[0].message.content
    cache().put(key, CacheEntry(out, provider_id=provider_id, model=model))
    return out


def info():
    c = _cfg()
    model = c["model"] or "(unset)"
    if model.startswith("claude-cli/"):
        return f"model={model} provider=claude-cli (shell-out, uses Claude Code OAuth) key=not-needed"
    if model.startswith("codex-cli/"):
        return f"model={model} provider=codex-cli (shell-out, uses Codex/ChatGPT login) key=not-needed"
    return (f"model={model} base={c['base'] or 'anthropic-native'} "
            f"key={'set' if c['key'] else 'MISSING'}")


# --------------------------------------------------------------------------- #
# Planner-grade provider (used by `simplicio scratch`).
#
# Kept SEPARATE from generate() so:
#   - users keep their cheap doer (SIMPLICIO_MODEL = Coder-Next, etc.)
#   - the planner runs on a frontier model (DeepSeek-V4-Pro default)
#   - swap of one does not touch the other
#
# Selected via SIMPLICIO_PLANNER:
#   deepseek/<model>      -> https://api.deepseek.com/v1, DEEPSEEK_API_KEY
#   anthropic/<model>     -> ANTHROPIC_API_KEY, native SDK
#   openai/<model>        -> https://api.openai.com/v1, OPENAI_API_KEY
#   openrouter/<model>    -> https://openrouter.ai/api/v1, OPENROUTER_API_KEY
#   claude-cli/<model>    -> shell-out, no key needed
#   codex-cli/<model>     -> shell-out, no key needed
#   <bare>                -> falls through to SIMPLICIO_MODEL/_API_KEY path
# --------------------------------------------------------------------------- #

_PLANNER_ROUTES = {
    # Default planner route: DeepSeek family served via HuggingFace Inference
    # Router. Uses HF_TOKEN; the model id after the prefix is whatever HF
    # exposes (e.g. `deepseek-ai/DeepSeek-V3.1`). Cheapest path to a frontier
    # planner when the user already has an HF account.
    "deepseek-hf": ("https://router.huggingface.co/v1", "HF_TOKEN"),
    # DeepSeek's own API (paid, no HF middleman). Pin via `deepseek/<model>`.
    "deepseek":    ("https://api.deepseek.com/v1",      "DEEPSEEK_API_KEY"),
    "openai":      ("https://api.openai.com/v1",        "OPENAI_API_KEY"),
    "openrouter":  ("https://openrouter.ai/api/v1",     "OPENROUTER_API_KEY"),
    # Generic HF route for any non-DeepSeek model on the HF router (Qwen, Llama, ...).
    "hf":          ("https://router.huggingface.co/v1", "HF_TOKEN"),
}

# Default planner. DeepSeek-V3.1 on HF is the current "frontier model with a
# token most users already have"; users on the DeepSeek Pro plan can swap to
# `deepseek/deepseek-v4-pro` (direct API) when they prefer. Override via
# SIMPLICIO_PLANNER.
_DEFAULT_PLANNER = "deepseek-hf/deepseek-ai/DeepSeek-V3.1"


def planner_cfg():
    """Resolve the planner provider config without touching the doer config.

    Returns a dict with keys: model, base, key, native_anthropic, shell_out.
    Raises SystemExit if planner is selected but its credentials are missing.
    """
    raw = os.environ.get("SIMPLICIO_PLANNER", _DEFAULT_PLANNER).strip()
    if not raw:
        raw = _DEFAULT_PLANNER

    if raw.startswith("claude-cli/") or raw.startswith("codex-cli/"):
        return {"model": raw, "base": None, "key": None,
                "native_anthropic": False, "shell_out": True}

    if "/" in raw:
        prefix, name = raw.split("/", 1)
    else:
        prefix, name = "", raw

    if prefix == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise SystemExit(
                "SIMPLICIO_PLANNER=anthropic/* requires ANTHROPIC_API_KEY")
        return {"model": name, "base": None, "key": key,
                "native_anthropic": True, "shell_out": False}

    if prefix in _PLANNER_ROUTES:
        base, env_key = _PLANNER_ROUTES[prefix]
        key = os.environ.get(env_key)
        if not key:
            raise SystemExit(
                f"SIMPLICIO_PLANNER={raw} requires {env_key}")
        return {"model": name, "base": base, "key": key,
                "native_anthropic": False, "shell_out": False}

    # Bare model name — fall back to the same provider config the doer uses.
    # Lets the user run planner against whatever they already configured.
    c = _cfg()
    return {"model": raw, "base": c["base"], "key": c["key"],
            "native_anthropic": not c["base"], "shell_out": False}


def planner_complete(prompt, max_tokens=8192, temperature=0.1):
    """Call the planner provider. Used by simplicio.scratch.planner.

    temperature defaults to 0.1 because plans must be reproducible and
    schema-stable, not creative.
    """
    p = planner_cfg()

    if p["shell_out"]:
        if p["model"].startswith("claude-cli/"):
            return _shell_out_claude(prompt, p["model"].split("/", 1)[1])
        if p["model"].startswith("codex-cli/"):
            return _shell_out_codex(prompt, p["model"].split("/", 1)[1])

    if p["native_anthropic"]:
        import anthropic
        cli = anthropic.Anthropic(api_key=p["key"])
        r = cli.messages.create(
            model=p["model"], max_tokens=max_tokens, temperature=temperature,
            messages=[{"role": "user", "content": prompt}])
        return next((b.text for b in r.content if b.type == "text"), "")

    if not p["key"]:
        raise SystemExit(
            "no planner credentials: set SIMPLICIO_PLANNER + matching API key "
            "(default planner is deepseek/deepseek-v4-pro -> DEEPSEEK_API_KEY)")

    from openai import OpenAI
    cli = OpenAI(base_url=p["base"], api_key=p["key"])
    r = cli.chat.completions.create(
        model=p["model"], max_tokens=max_tokens, temperature=temperature,
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content


def planner_info():
    p = planner_cfg()
    if p["shell_out"]:
        return f"planner={p['model']} (shell-out)"
    if p["native_anthropic"]:
        return f"planner={p['model']} provider=anthropic-native key={'set' if p['key'] else 'MISSING'}"
    return (f"planner={p['model']} base={p['base']} "
            f"key={'set' if p['key'] else 'MISSING'}")
