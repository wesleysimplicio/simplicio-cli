"""
Standalone bench runner — no heavy deps, only stdlib + an HTTP key.

Compares two prompts head-to-head on the *same* model:
  SEM:  raw one-line objetivo (baseline)
  COM:  same objetivo wrapped in simplicio's 6-layer contract (ALVO/CRITERIOS/
        RESTRICOES/SAIDA), without precedent/skill (offline mode — no repo,
        no embeddings, no API beyond the LLM call).

Scoring is deterministic: each case lists hard checks the model output must
pass (target-file mention, DIFF block, TEST block, key state words). No LLM
judging the LLM. The harness is the source of truth.

Usage:
  OPENROUTER_API_KEY=... BENCH_MODEL="qwen/qwen-2.5-7b-instruct" \
    python3 bench/run_offline.py
"""
from __future__ import annotations
import json, os, re, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "bench" / "cases_offline.json"
RESULTS_MD = ROOT / "bench" / "results.md"

MODEL = os.environ.get("BENCH_MODEL", "qwen/qwen-2.5-7b-instruct")
BASE_URL = os.environ.get("BENCH_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.environ.get("BENCH_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

SIX_LAYER_TEMPLATE = """You are a senior engineer working IN THIS project.
Stack: {stack}. Project conventions are LAW. Do not bring generic patterns.
Do not invent files or libraries the project does not use.

[OBJECTIVE]
{objetivo}

[TARGET]
Touch ONLY this file:
{alvo}

[CONTRACT]
Done WHEN, and only when, ALL of the states below are true:
{criterios}

Constraints (do not break):
{restricoes}

[OUTPUT]
Return EXACTLY in this shape, nothing else:
1. DIFF: unified diff, target file only.
2. TEST: test code asserting each contract state (true AND false case).
3. EVIDENCE: Playwright snippet capturing the UI states, or "N/A".
No prose, no preamble."""


def llm_call(prompt: str, timeout: int = 90) -> str:
    if not API_KEY:
        raise SystemExit("set OPENROUTER_API_KEY (or BENCH_API_KEY)")
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 900,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/wesleysimplicio/simplicio-cli",
            "X-Title": "simplicio-cli bench",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]


def score(output: str, checks: list[str]) -> tuple[int, int, list[tuple[str, bool]]]:
    """Each check is a regex (case-insensitive). Returns (hits, total, detail)."""
    detail = []
    out = output or ""
    for pat in checks:
        ok = re.search(pat, out, flags=re.IGNORECASE | re.MULTILINE) is not None
        detail.append((pat, ok))
    return sum(1 for _, ok in detail if ok), len(checks), detail


def run() -> int:
    cases = json.loads(CASES_PATH.read_text())
    rows, totals = [], {"sem_hits": 0, "com_hits": 0, "total_checks": 0}
    print(f"model: {MODEL}  base: {BASE_URL}  cases: {len(cases)}")
    for i, c in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {c['objetivo']}")
        sem_out = llm_call(c["objetivo"])
        com_prompt = SIX_LAYER_TEMPLATE.format(
            stack=c.get("stack", "angular"),
            objetivo=c["objetivo"],
            alvo=c["alvo"],
            criterios=c["criterios"],
            restricoes=c["restricoes"],
        )
        com_out = llm_call(com_prompt)

        sem_h, total, _ = score(sem_out, c["checks"])
        com_h, _, _ = score(com_out, c["checks"])
        totals["sem_hits"] += sem_h
        totals["com_hits"] += com_h
        totals["total_checks"] += total

        rows.append((c["objetivo"][:55], sem_h, com_h, total))
        print(f"  sem: {sem_h}/{total}   com: {com_h}/{total}")

        outdir = ROOT / ".simplicio" / "bench_runs" / f"case_{i:02d}"
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "sem.txt").write_text(sem_out)
        (outdir / "com.txt").write_text(com_out)

    sem_pct = 100 * totals["sem_hits"] // max(totals["total_checks"], 1)
    com_pct = 100 * totals["com_hits"] // max(totals["total_checks"], 1)

    md = [
        "# Benchmark — simplicio-cli (offline harness)",
        "",
        f"Model: `{MODEL}` · Base: `{BASE_URL}`  ",
        f"Date: {time.strftime('%Y-%m-%d')}  ",
        f"Cases: {len(cases)} · Total checks: {totals['total_checks']}",
        "",
        "Each check is a deterministic regex against the model output ",
        "(target-file mention, DIFF block, TEST block, contract state words). ",
        "Same model on both sides — only the prompt structure changes.",
        "",
        "| # | Task | Without (checks ✓) | With simplicio (checks ✓) |",
        "|---|---|---|---|",
    ]
    for i, (obj, s, c, t) in enumerate(rows, 1):
        md.append(f"| {i} | {obj} | {s}/{t} | {c}/{t} |")
    md += [
        "",
        f"**Overall** — without: **{totals['sem_hits']}/{totals['total_checks']} ({sem_pct}%)** "
        f"· with simplicio: **{totals['com_hits']}/{totals['total_checks']} ({com_pct}%)** "
        f"· delta: **{com_pct - sem_pct:+d} pts**",
        "",
        "Raw model outputs saved under `.simplicio/bench_runs/`. ",
        "Reproduce: `OPENROUTER_API_KEY=… python3 bench/run_offline.py`.",
        "",
    ]
    RESULTS_MD.write_text("\n".join(md))
    print(f"\n-> {RESULTS_MD}")
    print(f"without: {sem_pct}%  ·  with simplicio: {com_pct}%  ·  delta: {com_pct - sem_pct:+d} pts")
    return 0


if __name__ == "__main__":
    sys.exit(run())
