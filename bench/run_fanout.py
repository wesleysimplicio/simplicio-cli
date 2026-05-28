"""
run_fanout.py — REAL fan-out benchmark using simplicio-prompt's SubagentRuntime.

For each N in (1, 8, 32, 64-default, 200), launches N parallel LLM calls
through `kernel.subagent_runtime.SubagentRuntime` (the simplicio-prompt kernel)
on the SAME sistema-sindico PHP-modification task, with `temperature=0.7` to
induce real per-call variance. Every subagent output is scored by REAL PHPUnit
on a working copy of the real repo. The "majority-vote" outcome is computed by
hashing each generated solution.php and running phpunit on the most frequent
one. Reports per-attempt noise floor vs majority-vote stability across N
values, plus tokens, cost, and elapsed wall-clock.

This is the only honest test of simplicio-prompt's fan-out value prop on this
codebase: the kernel actually executes N real subagent calls (not just embeds
the runtime as prompt text), and the question we're answering is "does
sp-default 64 buy you anything over single? does 200 buy you more than 64?".

Usage:
  OPENROUTER_API_KEY=sk-or-... python3 bench/run_fanout.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

# simplicio-prompt kernel (PyPI: simplicio-prompt>=1.7.0)
from kernel.providers import LLMProvider, resolve_provider_config
from kernel.subagent_runtime import SubagentRuntime

ROOT = Path(__file__).resolve().parent.parent
SINDICO_SRC = Path("/tmp/sindico")
WORK = Path("/tmp/sindico_work_fanout")
RESULTS_JSON = ROOT / "bench" / "results_fanout.json"
RESULTS_MD = ROOT / "bench" / "results_fanout.md"
RESULTS_PDF = ROOT / "bench" / "results_fanout.pdf"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_offline as ro  # _lat1
from sindico_cases import CASES

# ---- prompt builder uses the same simplicio-cli 6-layer wrap as our other benches ---- #

CLI_SYSTEM = (
    "You are a senior engineer working IN THIS project. Stack: PHP 8 + "
    "composer + PHPUnit. Project conventions are LAW. Do not invent files "
    "or libraries the project does not use."
)


def build_prompt(case: dict, file_content: str) -> str:
    return (
        f"[GOAL]\n{case['goal']}\n\n[TARGET]\nTouch ONLY this file: {case['target']}\n"
        f"Current content:\n```php\n{file_content}\n```\n\n"
        f"[CONTRACT]\nDone WHEN, and only when, ALL of the states below are true:\n"
        f"{case['criteria']}\n\nConstraints (do not break):\n{case['constraints']}\n\n"
        f"[OUTPUT]\nReturn ONLY the complete updated contents of {case['target']}. "
        f"PHP only, no prose, no fences."
    )


def extract_php(text: str) -> str:
    text = text or ""
    blocks = re.findall(r"```(?:php)?\s*\n(.*?)```", text, re.DOTALL)
    code = max(blocks, key=len).strip() if blocks else text.strip()
    if not code.lstrip().startswith("<?php"):
        code = "<?php\n" + code
    return code


def normalize(code: str) -> str:
    """Hash-friendly normalization: strip trailing ws, collapse blank lines."""
    lines = [line.rstrip() for line in code.split("\n")]
    out, blank = [], False
    for ln in lines:
        if ln == "":
            if blank: continue
            blank = True
        else:
            blank = False
        out.append(ln)
    return "\n".join(out).strip()


def code_hash(code: str) -> str:
    return hashlib.sha256(normalize(code).encode()).hexdigest()[:12]


def setup_workspace_base() -> None:
    """Fresh copy of sindico into WORK; create the Hidden test dir."""
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(SINDICO_SRC, WORK)
    (WORK / "tests" / "unit" / "Core" / "Hidden").mkdir(parents=True, exist_ok=True)


def install_case(case: dict) -> str:
    """Reset target file + install ONLY this case's hidden test. Return target content."""
    target_path = WORK / case["target"]
    original = (SINDICO_SRC / case["target"]).read_text(encoding="utf-8")
    target_path.write_text(original, encoding="utf-8")
    hidden_dir = WORK / "tests" / "unit" / "Core" / "Hidden"
    for old in hidden_dir.glob("*Test.php"):
        old.unlink()
    src_test = ROOT / "bench" / "sindico_hidden" / case["hidden_test"]
    (hidden_dir / case["hidden_test"]).write_text(
        src_test.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return original


def run_phpunit(target_rel: str, code: str) -> bool:
    """Write code to target, run the full phpunit suite. Pass = exit 0."""
    (WORK / target_rel).write_text(code, encoding="utf-8")
    try:
        p = subprocess.run(
            ["vendor/bin/phpunit", "--configuration", "phpunit.xml.dist"],
            cwd=WORK, capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False
    return p.returncode == 0


def majority(codes: list[str]) -> tuple[str | None, int]:
    """Return (most-common normalized code, its count) over the list."""
    if not codes:
        return None, 0
    norm = [normalize(c) for c in codes]
    counter = Counter(norm)
    code, count = counter.most_common(1)[0]
    return code, count


# ---- main runner ---- #

def fanout_at(n: int, case: dict, runtime: SubagentRuntime, file_content: str) -> dict:
    user_prompt = build_prompt(case, file_content)
    prompts = [{"system": CLI_SYSTEM, "prompt": user_prompt} for _ in range(n)]
    report = runtime.run(task=f"impl {case['id']}", subagents=n, prompts=prompts)
    codes = [extract_php(r.text) for r in report.results if r.ok]
    passes = sum(run_phpunit(case["target"], c) for c in codes)
    maj_code, maj_count = majority(codes)
    maj_pass = run_phpunit(case["target"], maj_code) if maj_code else False
    uniques = len({code_hash(c) for c in codes})
    out = {
        "task": case["id"],
        "n": n,
        "completed": report.completed,
        "failed": report.failed,
        "per_attempt_pass": passes,
        "per_attempt_rate": (100 * passes // max(report.completed, 1)),
        "unique_outputs": uniques,
        "majority_count": maj_count,
        "majority_pass": maj_pass,
        "tokens": report.usage.total_tokens,
        "cost_usd": float(report.usage.cost_usd),
        "elapsed_s": report.elapsed_s,
    }
    print(
        f"  N={n:<4d} {case['id']:<33s} per-attempt {passes}/{report.completed} "
        f"({out['per_attempt_rate']:>3d}%) | uniq {uniques:>2d} | modal "
        f"{maj_count:>3d}/{report.completed} -> {'PASS' if maj_pass else 'fail'} | "
        f"{report.usage.total_tokens:>7,} tok | ${report.usage.cost_usd:.4f} | "
        f"{report.elapsed_s:>5.1f}s",
        flush=True,
    )
    return out


def run() -> int:
    if not SINDICO_SRC.exists():
        raise SystemExit(f"sindico source not found at {SINDICO_SRC}")
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("set OPENROUTER_API_KEY")

    setup_workspace_base()
    config = resolve_provider_config(
        "openrouter",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ.get("BENCH_FANOUT_MODEL",
                             "meta-llama/llama-3.1-8b-instruct"),
        prompt_cost_per_mtok=0.06,
        completion_cost_per_mtok=0.06,
    )
    provider = LLMProvider(config)
    runtime = SubagentRuntime(provider, temperature=0.7, max_tokens=4096)

    ns_str = os.environ.get("BENCH_FANOUT_NS", "64,200")
    ns = [int(x) for x in ns_str.split(",") if x.strip()]
    task_filter = os.environ.get("BENCH_FANOUT_TASKS", "").strip()
    tasks = CASES if not task_filter else [c for c in CASES if c["id"] in task_filter.split(",")]
    print(f"fanout benchmark: model={config.model} temp=0.7 N={ns} tasks={[c['id'] for c in tasks]}")

    rows = []
    for case in tasks:
        print(f"\n=== task: {case['id']} ===", flush=True)
        file_content = install_case(case)
        for n in ns:
            rows.append(fanout_at(n, case, runtime, file_content))

    RESULTS_JSON.write_text(json.dumps({"model": config.model, "rows": rows}, indent=2))
    write_reports(config.model, rows)
    return 0


def _group_by_task(rows: list[dict]) -> dict:
    out: dict = {}
    for r in rows:
        out.setdefault(r["task"], []).append(r)
    return out


def write_reports(model: str, rows: list[dict]) -> None:
    by_task = _group_by_task(rows)
    ns = sorted({r["n"] for r in rows})
    n_tasks = len(by_task)

    md = [
        "# Fan-out benchmark — does simplicio-prompt's subagent kernel help?",
        "",
        f"Date: **{time.strftime('%Y-%m-%d')}**  ",
        f"Model: `{model}` · temperature **0.7** (induces real per-call variance)  ",
        f"Engine: `kernel.subagent_runtime.SubagentRuntime` from simplicio-prompt "
        "v1.7.0 (PyPI), real parallel calls through `LaneWorkerPool`.  ",
        f"Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — real PHP 8 condominium system.  ",
        f"Tasks: **{n_tasks}** real engineering changes across `src/Core/`, "
        "`src/Middleware/`, `src/Repositories/`, and routing.  ",
        f"N values tested: " + ", ".join(f"**{n}**" + (" *(sp default)*" if n == 64 else "") for n in ns),
        "",
        "## Methodology",
        "",
        "For each (task, N), the simplicio-prompt **kernel** launches N real "
        "parallel LLM calls on the same prompt (simplicio-cli 6-layer wrap of "
        "the task) at `temperature=0.7`. Every returned solution.php is written "
        "into a working copy of `sistema-sindico` and scored by **real PHPUnit** "
        "(`vendor/bin/phpunit` exit code 0). The **majority-vote outcome** is "
        "computed by sha256-hashing the normalized code, picking the most "
        "frequent variant, and re-running phpunit on it.",
        "",
        "**This is the real engagement of simplicio-prompt's value prop**: the "
        "kernel actually executes the fan-out (LaneWorkerPool, bounded "
        "concurrency, receipt cache, jittered backoff, circuit breaker), not "
        "just embeds the runtime as prompt text. The question is: **does sp's "
        "default N=64 buy more than a smaller N? does N=200 buy more than 64?**",
        "",
        "## Headline — per N (aggregate across tasks)",
        "",
        "| N | Tasks | Per-attempt pass (sum) | Modal-vote pass | Tokens (sum) | Cost (USD, sum) | Avg elapsed |",
        "|---|---|---|---|---|---|---|",
    ]
    for n in ns:
        ngroup = [r for r in rows if r["n"] == n]
        tot_attempts = sum(r["completed"] for r in ngroup)
        tot_passes = sum(r["per_attempt_pass"] for r in ngroup)
        tot_modal = sum(1 for r in ngroup if r["majority_pass"])
        tot_tokens = sum(r["tokens"] for r in ngroup)
        tot_cost = sum(r["cost_usd"] for r in ngroup)
        avg_elapsed = sum(r["elapsed_s"] for r in ngroup) / max(len(ngroup), 1)
        md.append(
            f"| **{n}**{' *(sp default)*' if n == 64 else ''} | {len(ngroup)} | "
            f"{tot_passes}/{tot_attempts} ({100*tot_passes//max(tot_attempts,1)}%) | "
            f"{tot_modal}/{len(ngroup)} | "
            f"{tot_tokens:,} | ${tot_cost:.4f} | {avg_elapsed:.1f}s |"
        )

    md += ["", "## Per-task breakdown", "",
           "| Task | N | Per-attempt | Uniq | Modal | Tokens | Cost | Elapsed |",
           "|---|---|---|---|---|---|---|---|"]
    for task, trows in by_task.items():
        for r in trows:
            md.append(
                f"| `{task}` | **{r['n']}** | "
                f"{r['per_attempt_pass']}/{r['completed']} ({r['per_attempt_rate']}%) | "
                f"{r['unique_outputs']} | "
                f"{'PASS' if r['majority_pass'] else 'fail'} ({r['majority_count']}/{r['completed']}) | "
                f"{r['tokens']:,} | ${r['cost_usd']:.4f} | {r['elapsed_s']:.1f}s |"
            )

    md += ["", "## Interpretation", "",
           "- **Per-attempt pass** is the noise floor at `temperature=0.7`. "
           "A single call lands roughly at this rate.",
           "- **Unique outputs** measures real diversity per task at this "
           "temperature; if every subagent produces the same file, fan-out "
           "adds nothing.",
           "- **Modal (majority-vote)** is the value test: does picking the "
           "most frequent answer recover correctness when single calls are "
           "noisy?",
           "- **N=64 vs N=200**: the central comparison. If 200 doesn't beat "
           "64 on modal pass rate, sp's default is at the sweet spot.",
           "- **Cost** scales linearly with N (tokens are proportional). "
           "**Elapsed** grows much slower because `LaneWorkerPool` runs calls "
           "in parallel.",
           "",
           "Raw per-subagent data in `results_fanout.json`. Re-run with "
           "`BENCH_FANOUT_NS=...` or `BENCH_FANOUT_TASKS=...` to focus.",
           ""]
    RESULTS_MD.write_text("\n".join(md))
    print(f"\n-> {RESULTS_MD}")
    _pdf(model, rows)


def _pdf(model: str, rows: list[dict]) -> None:
    try:
        from fpdf import FPDF
    except ImportError:
        print("[warn] fpdf2 not installed; skipping PDF")
        return
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15); pdf.set_margins(15, 15, 15)
    L = ro._lat1

    def h1(t): pdf.set_font("Helvetica", "B", 15); pdf.multi_cell(0, 8, L(t)); pdf.ln(1)
    def h2(t): pdf.set_font("Helvetica", "B", 12); pdf.multi_cell(0, 7, L(t)); pdf.ln(1)
    def p(t): pdf.set_font("Helvetica", "", 9); pdf.multi_cell(0, 5, L(t)); pdf.ln(1)
    def th(cols, w):
        pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(230, 230, 230)
        for c, x in zip(cols, w): pdf.cell(x, 6, L(c), border=1, fill=True)
        pdf.ln()
    def tr(cells, w):
        pdf.set_font("Helvetica", "", 9)
        for c, x in zip(cells, w): pdf.cell(x, 6, L(c), border=1)
        pdf.ln()

    by_task = _group_by_task(rows)
    ns = sorted({r["n"] for r in rows})

    pdf.add_page()
    h1("Fan-out benchmark - simplicio-prompt kernel on sistema-sindico")
    p(f"Date: {time.strftime('%Y-%m-%d')}   Model: {model}   temperature: 0.7   "
      f"Tasks: {len(by_task)}   N values: {', '.join(str(n) for n in ns)}")
    p("Engine: kernel.subagent_runtime.SubagentRuntime (PyPI simplicio-prompt 1.7.0). "
      "For each (task, N) the kernel launches N real parallel LLM calls through "
      "LaneWorkerPool on the same prompt; each output is scored by real PHPUnit; "
      "the majority-vote outcome (sha256-mode of normalized code) is re-scored. "
      "Central question: does N=64 (sp default) help vs lower N? does N=200 help vs 64?")
    pdf.ln(1)
    h2("Headline - per N (aggregate across tasks)")
    th(["N", "Tasks", "Per-attempt", "Modal pass", "Tokens", "Cost (USD)", "Avg elapsed"],
       [18, 16, 36, 28, 28, 22, 28])
    for n in ns:
        ngroup = [r for r in rows if r["n"] == n]
        tot_a = sum(r["completed"] for r in ngroup)
        tot_p = sum(r["per_attempt_pass"] for r in ngroup)
        tot_m = sum(1 for r in ngroup if r["majority_pass"])
        tot_t = sum(r["tokens"] for r in ngroup)
        tot_c = sum(r["cost_usd"] for r in ngroup)
        avg_e = sum(r["elapsed_s"] for r in ngroup) / max(len(ngroup), 1)
        label = f"{n}{' (default)' if n == 64 else ''}"
        tr([label, str(len(ngroup)),
            f"{tot_p}/{tot_a} ({100*tot_p//max(tot_a,1)}%)",
            f"{tot_m}/{len(ngroup)}",
            f"{tot_t:,}", f"${tot_c:.4f}", f"{avg_e:.1f}s"],
           [18, 16, 36, 28, 28, 22, 28])
    pdf.ln(2)
    h2("Per-task")
    th(["Task", "N", "Per-attempt", "Uniq", "Modal", "Tokens", "Cost"],
       [40, 14, 32, 14, 28, 24, 24])
    for task, trows in by_task.items():
        for r in trows:
            tr([task, str(r["n"]),
                f"{r['per_attempt_pass']}/{r['completed']} ({r['per_attempt_rate']}%)",
                str(r["unique_outputs"]),
                f"{'P' if r['majority_pass'] else '.'} {r['majority_count']}/{r['completed']}",
                f"{r['tokens']:,}", f"${r['cost_usd']:.4f}"],
               [40, 14, 32, 14, 28, 24, 24])
    pdf.ln(2)
    h2("Interpretation")
    p("Per-attempt pass = noise floor at temp=0.7 (single-call equivalent). "
      "Modal-vote = does picking the most frequent answer recover correctness? "
      "If N=200 doesn't beat N=64 on modal pass-rate, the sp default is the "
      "sweet spot. Cost scales linearly with N for tokens; wall-clock grows "
      "sub-linearly because calls run in parallel through LaneWorkerPool.")
    pdf.output(str(RESULTS_PDF))
    print(f"-> {RESULTS_PDF}")


if __name__ == "__main__":
    raise SystemExit(run())
