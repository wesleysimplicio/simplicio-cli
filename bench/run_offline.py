"""
Standalone bench runner — no heavy deps, only stdlib + an HTTP key.

Compares two prompts head-to-head on the *same* model(s):
  WITHOUT: raw one-line goal (baseline)
  WITH:    same goal wrapped in simplicio's 6-layer contract (target,
           criteria, constraints, output shape).

Scoring is deterministic: each case lists hard regex checks the model
output must satisfy. No LLM judging the LLM. Same model on both sides —
only the prompt structure changes. Runs across multiple models so the
result is a property of the *method*, not of one model.

Usage:
  OPENROUTER_API_KEY=... \\
    BENCH_MODELS="qwen/qwen-2.5-7b-instruct,meta-llama/llama-3.1-8b-instruct,mistralai/mistral-7b-instruct" \\
    python3 bench/run_offline.py
"""
from __future__ import annotations
import json, os, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "bench" / "cases_offline.json"
RESULTS_MD = ROOT / "bench" / "results.md"
RESULTS_JSON = ROOT / "bench" / "results.json"
CHART_DIR = ROOT / "bench" / "charts"

MODELS = [m.strip() for m in os.environ.get(
    "BENCH_MODELS",
    "qwen/qwen-2.5-7b-instruct"
).split(",") if m.strip()]
BASE_URL = os.environ.get("BENCH_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.environ.get("BENCH_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

SIX_LAYER_TEMPLATE = """You are a senior engineer working IN THIS project.
Stack: {stack}. Project conventions are LAW. Do not bring generic patterns.
Do not invent files or libraries the project does not use.

[GOAL]
{goal}

[TARGET]
Touch ONLY this file:
{target}

[CONTRACT]
Done WHEN, and only when, ALL of the states below are true:
{criteria}

Constraints (do not break):
{constraints}

[OUTPUT]
Return EXACTLY in this shape, nothing else:
1. DIFF: unified diff, target file only.
2. TEST: test code asserting each contract state (true AND false case).
3. EVIDENCE: Playwright snippet capturing the UI states, or "N/A".
No prose, no preamble."""


def llm_call(model: str, prompt: str, timeout: int = 120) -> dict:
    if not API_KEY:
        raise SystemExit("set OPENROUTER_API_KEY (or BENCH_API_KEY)")
    body = json.dumps({
        "model": model,
        "max_tokens": 8192,
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
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        usage = data.get("usage") or {}
        msg = data["choices"][0].get("message") or {}
        text = msg.get("content") or msg.get("reasoning") or ""
        return {
            "text": text,
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
            "elapsed_ms": elapsed_ms,
            "error": None,
        }
    except Exception as e:
        return {
            "text": f"[BENCH_ERROR] {e}",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            "error": str(e),
        }


def score(output: str, checks: list[str]) -> list[bool]:
    out = output or ""
    return [
        re.search(p, out, flags=re.IGNORECASE | re.MULTILINE) is not None
        for p in checks
    ]


def quality_metrics(output: str, case: dict) -> dict:
    out = output or ""
    return {
        "len": len(out),
        "has_diff_block": bool(re.search(r"```diff|^---\s|^\+\+\+\s|@@", out, re.M)),
        "has_test_block": bool(re.search(r"```(ts|js|tsx|jsx|csharp|cs|python|typescript|javascript)\b|describe\(|it\(|test\(|\[Test\]|\[Fact\]", out, re.I | re.M)),
        "target_mentioned": case["target"].split("/")[-1].lower() in out.lower(),
        "criteria_keywords_hit": sum(
            1 for kw in re.findall(r"[A-Za-z]{4,}", case["criteria"].lower())
            if kw in out.lower()
        ),
    }


# ---------- SVG charts (no matplotlib) ---------- #

def _svg_bar_compare(title: str, labels: list[str], sem: list[float], com: list[float],
                     ymax: float = 100.0, unit: str = "%") -> str:
    """Grouped bar chart: sem (gray) vs com (blue) per label."""
    n = len(labels)
    bar_w = 28
    group_w = bar_w * 2 + 14
    chart_w = max(560, 90 + group_w * n + 20)
    chart_h = 360
    pad_l, pad_b, pad_t = 60, 90, 50
    plot_h = chart_h - pad_t - pad_b
    ax_y = pad_t + plot_h
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {chart_w} {chart_h}" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="12">',
        '<style>.bar-sem{fill:#aaa}.bar-com{fill:#2962ff}.lbl{fill:#222}.ax{stroke:#888;stroke-width:1}.grid{stroke:#eee;stroke-width:1}</style>',
        f'<text x="{chart_w/2}" y="22" text-anchor="middle" font-weight="600" font-size="14">{title}</text>',
    ]
    # gridlines
    for i in range(5):
        y = pad_t + plot_h * i / 4
        v = ymax * (1 - i / 4)
        parts.append(f'<line x1="{pad_l}" y1="{y}" x2="{chart_w-10}" y2="{y}" class="grid"/>')
        parts.append(f'<text x="{pad_l-6}" y="{y+4}" text-anchor="end" fill="#666">{v:.0f}{unit}</text>')
    # axes
    parts.append(f'<line x1="{pad_l}" y1="{ax_y}" x2="{chart_w-10}" y2="{ax_y}" class="ax"/>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{ax_y}" class="ax"/>')
    # bars
    for i, lbl in enumerate(labels):
        gx = pad_l + 30 + i * group_w
        hs = plot_h * (sem[i] / ymax)
        hc = plot_h * (com[i] / ymax)
        parts.append(f'<rect x="{gx}" y="{ax_y - hs}" width="{bar_w}" height="{hs}" class="bar-sem"/>')
        parts.append(f'<rect x="{gx + bar_w + 6}" y="{ax_y - hc}" width="{bar_w}" height="{hc}" class="bar-com"/>')
        parts.append(f'<text x="{gx + bar_w/2}" y="{ax_y - hs - 4}" text-anchor="middle" fill="#444" font-size="10">{sem[i]:.0f}</text>')
        parts.append(f'<text x="{gx + bar_w + 6 + bar_w/2}" y="{ax_y - hc - 4}" text-anchor="middle" fill="#2962ff" font-size="10">{com[i]:.0f}</text>')
        # rotated label
        cx = gx + bar_w + 3
        parts.append(f'<text x="{cx}" y="{ax_y + 14}" transform="rotate(-25 {cx} {ax_y + 14})" text-anchor="end" class="lbl">{lbl}</text>')
    # legend
    lx = chart_w - 220
    parts.append(f'<rect x="{lx}" y="32" width="14" height="10" class="bar-sem"/>')
    parts.append(f'<text x="{lx+20}" y="42">without simplicio</text>')
    parts.append(f'<rect x="{lx+120}" y="32" width="14" height="10" class="bar-com"/>')
    parts.append(f'<text x="{lx+140}" y="42">with simplicio</text>')
    parts.append("</svg>")
    return "".join(parts)


def _svg_delta(title: str, labels: list[str], deltas: list[float]) -> str:
    n = len(labels)
    bar_w = 36
    chart_w = max(560, 90 + (bar_w + 18) * n + 20)
    chart_h = 320
    pad_l, pad_b, pad_t = 60, 80, 50
    plot_h = chart_h - pad_t - pad_b
    ax_y = pad_t + plot_h / 2  # zero line in the middle
    ymax = max(50, max(abs(d) for d in deltas) + 10) if deltas else 50
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {chart_w} {chart_h}" font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="12">',
        '<style>.bar-pos{fill:#2e7d32}.bar-neg{fill:#c62828}.ax{stroke:#444;stroke-width:1.2}.grid{stroke:#eee;stroke-width:1}</style>',
        f'<text x="{chart_w/2}" y="22" text-anchor="middle" font-weight="600" font-size="14">{title}</text>',
    ]
    for i in range(5):
        y = pad_t + plot_h * i / 4
        v = ymax - 2 * ymax * i / 4
        parts.append(f'<line x1="{pad_l}" y1="{y}" x2="{chart_w-10}" y2="{y}" class="grid"/>')
        parts.append(f'<text x="{pad_l-6}" y="{y+4}" text-anchor="end" fill="#666">{v:+.0f} pts</text>')
    parts.append(f'<line x1="{pad_l}" y1="{ax_y}" x2="{chart_w-10}" y2="{ax_y}" class="ax"/>')
    for i, (lbl, d) in enumerate(zip(labels, deltas)):
        bx = pad_l + 30 + i * (bar_w + 18)
        h = abs(d) / ymax * (plot_h / 2)
        cls = "bar-pos" if d >= 0 else "bar-neg"
        y = ax_y - h if d >= 0 else ax_y
        parts.append(f'<rect x="{bx}" y="{y}" width="{bar_w}" height="{h}" class="{cls}"/>')
        ty = (ax_y - h - 6) if d >= 0 else (ax_y + h + 14)
        parts.append(f'<text x="{bx + bar_w/2}" y="{ty}" text-anchor="middle" fill="#222">{d:+.0f}</text>')
        cx = bx + bar_w / 2
        parts.append(f'<text x="{cx}" y="{pad_t + plot_h + 16}" transform="rotate(-25 {cx} {pad_t + plot_h + 16})" text-anchor="end" fill="#222">{lbl}</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------- main runner ---------- #

def run() -> int:
    cases = json.loads(CASES_PATH.read_text())
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    print(f"models: {MODELS}")
    print(f"cases:  {len(cases)} · base: {BASE_URL}")
    by_model = {}
    for model in MODELS:
        print(f"\n=== model: {model} ===")
        rows = []
        sem_hits = com_hits = total = 0
        qsum_sem = {"len": 0, "has_diff_block": 0, "has_test_block": 0, "target_mentioned": 0, "criteria_keywords_hit": 0}
        qsum_com = dict(qsum_sem)
        usage_sem = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "elapsed_ms": 0}
        usage_com = dict(usage_sem)
        for i, c in enumerate(cases, 1):
            sem_res = llm_call(model, c["goal"])
            com_prompt = SIX_LAYER_TEMPLATE.format(
                stack=c.get("stack", "angular"),
                goal=c["goal"],
                target=c["target"],
                criteria=c["criteria"],
                constraints=c["constraints"],
            )
            com_res = llm_call(model, com_prompt)
            sem_out = sem_res["text"]
            com_out = com_res["text"]

            s_flags = score(sem_out, c["checks"])
            c_flags = score(com_out, c["checks"])
            s_h, c_h, t = sum(s_flags), sum(c_flags), len(c["checks"])
            sem_hits += s_h; com_hits += c_h; total += t

            qs = quality_metrics(sem_out, c)
            qc = quality_metrics(com_out, c)
            for k in qsum_sem:
                qsum_sem[k] += int(qs[k]) if isinstance(qs[k], bool) else qs[k]
                qsum_com[k] += int(qc[k]) if isinstance(qc[k], bool) else qc[k]
            for k in usage_sem:
                usage_sem[k] += sem_res[k]
                usage_com[k] += com_res[k]

            rows.append({
                "goal": c["goal"], "stack": c["stack"],
                "sem_hits": s_h, "com_hits": c_h, "total": t,
                "sem_flags": s_flags, "com_flags": c_flags,
                "sem_quality": qs, "com_quality": qc,
                "sem_usage": {k: sem_res[k] for k in usage_sem},
                "com_usage": {k: com_res[k] for k in usage_com},
            })
            print(
                f"  [{i:02d}/{len(cases)}] {c['stack']:7s} "
                f"sem {s_h}/{t} ({sem_res['total_tokens']}tok {sem_res['elapsed_ms']}ms)  "
                f"com {c_h}/{t} ({com_res['total_tokens']}tok {com_res['elapsed_ms']}ms)  "
                f"Δ{c_h-s_h:+d}"
            )

            slug = model.replace("/", "_").replace(":", "_")
            outdir = ROOT / ".simplicio" / "bench_runs" / slug / f"case_{i:02d}"
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / "sem.txt").write_text(sem_out)
            (outdir / "com.txt").write_text(com_out)

        by_model[model] = {
            "rows": rows,
            "sem_hits": sem_hits, "com_hits": com_hits, "total": total,
            "sem_pct": 100 * sem_hits // max(total, 1),
            "com_pct": 100 * com_hits // max(total, 1),
            "quality_sem": qsum_sem, "quality_com": qsum_com,
            "usage_sem": usage_sem, "usage_com": usage_com,
        }

    # ---- write artifacts ---- #
    RESULTS_JSON.write_text(json.dumps(by_model, indent=2))

    # per-model overall chart
    overall_labels = [m.split("/")[-1] for m in MODELS]
    overall_sem = [by_model[m]["sem_pct"] for m in MODELS]
    overall_com = [by_model[m]["com_pct"] for m in MODELS]
    overall_delta = [c - s for c, s in zip(overall_com, overall_sem)]
    (CHART_DIR / "overall.svg").write_text(_svg_bar_compare(
        "Pass rate by model — without vs with simplicio", overall_labels,
        overall_sem, overall_com,
    ))
    (CHART_DIR / "delta.svg").write_text(_svg_delta(
        "Gain from simplicio (points) — by model", overall_labels, overall_delta,
    ))

    # per-case chart (average across models)
    case_labels = [f"#{i+1} {cases[i]['stack']}" for i in range(len(cases))]
    case_sem_avg = []
    case_com_avg = []
    for i in range(len(cases)):
        s_pcts = [100 * by_model[m]["rows"][i]["sem_hits"] / by_model[m]["rows"][i]["total"] for m in MODELS]
        c_pcts = [100 * by_model[m]["rows"][i]["com_hits"] / by_model[m]["rows"][i]["total"] for m in MODELS]
        case_sem_avg.append(sum(s_pcts) / len(s_pcts))
        case_com_avg.append(sum(c_pcts) / len(c_pcts))
    (CHART_DIR / "by_case.svg").write_text(_svg_bar_compare(
        "Per-case pass rate (avg across models)", case_labels,
        case_sem_avg, case_com_avg,
    ))

    # per-stack aggregation
    stacks = sorted({c["stack"] for c in cases})
    stack_sem = []
    stack_com = []
    for stk in stacks:
        idxs = [i for i, c in enumerate(cases) if c["stack"] == stk]
        s = sum(by_model[m]["rows"][i]["sem_hits"] for m in MODELS for i in idxs)
        cc = sum(by_model[m]["rows"][i]["com_hits"] for m in MODELS for i in idxs)
        t = sum(by_model[m]["rows"][i]["total"] for m in MODELS for i in idxs)
        stack_sem.append(100 * s / max(t, 1))
        stack_com.append(100 * cc / max(t, 1))
    (CHART_DIR / "by_stack.svg").write_text(_svg_bar_compare(
        "Per-stack pass rate (all models, all cases)", stacks, stack_sem, stack_com,
    ))

    # ---- markdown report ---- #
    n_cases = len(cases)
    grand_sem = sum(by_model[m]["sem_hits"] for m in MODELS)
    grand_com = sum(by_model[m]["com_hits"] for m in MODELS)
    grand_total = sum(by_model[m]["total"] for m in MODELS)
    grand_sem_pct = 100 * grand_sem // max(grand_total, 1)
    grand_com_pct = 100 * grand_com // max(grand_total, 1)

    md = [
        "# Benchmark — simplicio-cli (offline harness)",
        "",
        f"Date: **{time.strftime('%Y-%m-%d')}**  ",
        f"Models: " + ", ".join(f"`{m}`" for m in MODELS) + "  ",
        f"Cases: **{n_cases}** across stacks: " + ", ".join(f"`{s}`" for s in stacks) + "  ",
        f"Base: `{BASE_URL}`",
        "",
        "Each check is a deterministic regex against the model output ",
        "(target-file mention, DIFF block, TEST block, contract-state words). ",
        "Same model on both sides — only the prompt structure changes. The ",
        "*without* run is the raw one-line goal; the *with* run wraps the ",
        "same goal in simplicio's 6-layer contract.",
        "",
        "## Headline",
        "",
        f"- **Without simplicio:** {grand_sem}/{grand_total} ({grand_sem_pct}%)",
        f"- **With simplicio:** {grand_com}/{grand_total} ({grand_com_pct}%)",
        f"- **Delta:** **{grand_com_pct - grand_sem_pct:+d} points** "
        f"({100 * (grand_com - grand_sem) / max(grand_sem, 1):+.0f}% relative)",
        "",
        "![pass rate by model](charts/overall.svg)",
        "",
        "![gain in points](charts/delta.svg)",
        "",
        "## Per-model breakdown",
        "",
        "| Model | Cases | Without | With | Delta (pts) | Relative gain |",
        "|---|---|---|---|---|---|",
    ]
    for m in MODELS:
        b = by_model[m]
        rel = 100 * (b["com_hits"] - b["sem_hits"]) / max(b["sem_hits"], 1)
        md.append(
            f"| `{m}` | {n_cases} | {b['sem_hits']}/{b['total']} ({b['sem_pct']}%) | "
            f"{b['com_hits']}/{b['total']} ({b['com_pct']}%) | "
            f"**{b['com_pct'] - b['sem_pct']:+d}** | {rel:+.0f}% |"
        )

    md += [
        "",
        "## Per-case (averaged across models)",
        "",
        "![per case](charts/by_case.svg)",
        "",
        "| # | Stack | Task | Without | With | Δ |",
        "|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(cases, 1):
        s_avg = case_sem_avg[i-1]
        c_avg = case_com_avg[i-1]
        md.append(
            f"| {i} | `{c['stack']}` | {c['goal'][:60]} | "
            f"{s_avg:.0f}% | {c_avg:.0f}% | **{c_avg - s_avg:+.0f}** |"
        )

    md += [
        "",
        "## Per-stack",
        "",
        "![per stack](charts/by_stack.svg)",
        "",
        "| Stack | Without | With | Δ |",
        "|---|---|---|---|",
    ]
    for stk, sp, cp in zip(stacks, stack_sem, stack_com):
        md.append(f"| `{stk}` | {sp:.0f}% | {cp:.0f}% | **{cp - sp:+.0f}** |")

    md += [
        "",
        "## Output-quality signals (rate across all runs)",
        "",
        "Beyond pass-rate, the same outputs are scored on structural quality. ",
        "Each row = % of runs (cases × models) where the signal is present.",
        "",
        "| Signal | Without simplicio | With simplicio |",
        "|---|---|---|",
    ]
    total_runs = n_cases * len(MODELS)
    signals = [
        ("has_diff_block", "DIFF block present"),
        ("has_test_block", "TEST block present"),
        ("target_mentioned", "target file mentioned"),
    ]
    for key, label in signals:
        s_count = sum(by_model[m]["quality_sem"][key] for m in MODELS)
        c_count = sum(by_model[m]["quality_com"][key] for m in MODELS)
        md.append(
            f"| {label} | {100*s_count//total_runs}% ({s_count}/{total_runs}) | "
            f"{100*c_count//total_runs}% ({c_count}/{total_runs}) |"
        )
    # avg criteria keyword hits
    s_kw = sum(by_model[m]["quality_sem"]["criteria_keywords_hit"] for m in MODELS)
    c_kw = sum(by_model[m]["quality_com"]["criteria_keywords_hit"] for m in MODELS)
    md.append(f"| avg criteria-keywords hit / run | {s_kw/total_runs:.1f} | {c_kw/total_runs:.1f} |")
    # avg output length
    s_len = sum(by_model[m]["quality_sem"]["len"] for m in MODELS)
    c_len = sum(by_model[m]["quality_com"]["len"] for m in MODELS)
    md.append(f"| avg output length (chars) | {s_len//total_runs} | {c_len//total_runs} |")

    # ---- token & latency cost ---- #
    md += [
        "",
        "## Cost — tokens & wall-clock (measured, per run)",
        "",
        "Reported straight from the provider's `usage` field and `time.perf_counter()`. ",
        "*Per-run* = one model call (one case, one side). With simplicio uses more input ",
        "tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).",
        "",
        "| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |",
        "|---|---|---|---|---|---|",
    ]
    for m in MODELS:
        b = by_model[m]
        us = b["usage_sem"]; uc = b["usage_com"]
        md.append(
            f"| `{m}` | without | {us['prompt_tokens']//n_cases} | {us['completion_tokens']//n_cases} | "
            f"{us['total_tokens']//n_cases} | {us['elapsed_ms']//n_cases} ms |"
        )
        md.append(
            f"| `{m}` | with    | {uc['prompt_tokens']//n_cases} | {uc['completion_tokens']//n_cases} | "
            f"{uc['total_tokens']//n_cases} | {uc['elapsed_ms']//n_cases} ms |"
        )

    # aggregate totals
    agg_sem_p = sum(by_model[m]["usage_sem"]["prompt_tokens"] for m in MODELS)
    agg_sem_c = sum(by_model[m]["usage_sem"]["completion_tokens"] for m in MODELS)
    agg_sem_t = sum(by_model[m]["usage_sem"]["total_tokens"] for m in MODELS)
    agg_sem_ms = sum(by_model[m]["usage_sem"]["elapsed_ms"] for m in MODELS)
    agg_com_p = sum(by_model[m]["usage_com"]["prompt_tokens"] for m in MODELS)
    agg_com_c = sum(by_model[m]["usage_com"]["completion_tokens"] for m in MODELS)
    agg_com_t = sum(by_model[m]["usage_com"]["total_tokens"] for m in MODELS)
    agg_com_ms = sum(by_model[m]["usage_com"]["elapsed_ms"] for m in MODELS)
    md += [
        "",
        f"**Aggregate over the full bench** ({total_runs} runs per side):",
        "",
        f"- without simplicio: {agg_sem_t:,} tokens total · {agg_sem_ms/1000:.1f}s wall-clock · "
        f"{agg_sem_t // total_runs} tok/run · {agg_sem_ms // total_runs} ms/run",
        f"- with simplicio:    {agg_com_t:,} tokens total · {agg_com_ms/1000:.1f}s wall-clock · "
        f"{agg_com_t // total_runs} tok/run · {agg_com_ms // total_runs} ms/run",
        f"- token delta:       {agg_com_t - agg_sem_t:+,} ({(agg_com_t - agg_sem_t)*100//max(agg_sem_t,1):+d}%)",
        f"- time delta:        {(agg_com_ms - agg_sem_ms)/1000:+.1f}s ({(agg_com_ms - agg_sem_ms)*100//max(agg_sem_ms,1):+d}%)",
        "",
        "## How to reproduce",
        "",
        "```bash",
        "OPENROUTER_API_KEY=… \\",
        f'  BENCH_MODELS="{",".join(MODELS)}" \\',
        "  python3 bench/run_offline.py",
        "```",
        "",
        "Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` ",
        "so you can audit what the LLM actually produced on each side. Charts are ",
        "SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.",
        "",
    ]
    RESULTS_MD.write_text("\n".join(md))
    print(f"\n-> {RESULTS_MD}")
    print(f"grand: without {grand_sem_pct}% · with {grand_com_pct}% · delta {grand_com_pct - grand_sem_pct:+d} pts "
          f"(over {grand_total} checks, {n_cases} cases × {len(MODELS)} models)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
