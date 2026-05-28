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

# ---- task + prompt (same simplicio-cli 6-layer wrap our other benches use) ---- #

TASK_ID = "password_strength"
TARGET = "src/Core/PasswordPolicy.php"

GOAL = (
    "Add a NEW public static method `strength(string $password): string` to "
    "App\\Core\\PasswordPolicy that classifies the password as 'weak', "
    "'medium' or 'strong'."
)
CRITERIA = (
    "- if violations(password) is not empty -> return 'weak'\n"
    "- otherwise, if strlen(password) >= 12 AND password contains at least "
    "one character from the set !@#$%^&* -> return 'strong'\n"
    "- otherwise -> return 'medium'\n"
    "- exact return values, lowercase: 'weak' | 'medium' | 'strong'"
)
CONSTRAINTS = (
    "- additive change: keep existing MIN_LENGTH, violations(), isValid(), "
    "describe() exactly as they are\n"
    "- pure function, no I/O\n"
    "- final class, namespace App\\Core, strict_types"
)

CLI_SYSTEM = (
    "You are a senior engineer working IN THIS project. Stack: PHP 8 + "
    "composer + PHPUnit. Project conventions are LAW. Do not invent files "
    "or libraries the project does not use."
)

# ---- helpers ---- #

def build_prompt(file_content: str) -> str:
    return (
        f"[GOAL]\n{GOAL}\n\n[TARGET]\nTouch ONLY this file: {TARGET}\n"
        f"Current content:\n```php\n{file_content}\n```\n\n"
        f"[CONTRACT]\nDone WHEN, and only when, ALL of the states below are true:\n"
        f"{CRITERIA}\n\nConstraints (do not break):\n{CONSTRAINTS}\n\n"
        f"[OUTPUT]\nReturn ONLY the complete updated contents of {TARGET}. "
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


def setup_workspace() -> str:
    """Fresh copy of sindico into WORK. Return original target file content."""
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(SINDICO_SRC, WORK)
    (WORK / "tests" / "unit" / "Core" / "Hidden").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        ROOT / "bench" / "sindico_hidden" / "PasswordStrengthTest.php",
        WORK / "tests" / "unit" / "Core" / "Hidden" / "PasswordStrengthTest.php",
    )
    return (SINDICO_SRC / TARGET).read_text(encoding="utf-8")


def run_phpunit(code: str) -> bool:
    """Write code to target, run the full phpunit suite. Pass = exit 0."""
    (WORK / TARGET).write_text(code, encoding="utf-8")
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

def fanout_at(n: int, runtime: SubagentRuntime, file_content: str) -> dict:
    user_prompt = build_prompt(file_content)
    prompts = [{"system": CLI_SYSTEM, "prompt": user_prompt} for _ in range(n)]
    print(f"\n=== N={n} subagents ===", flush=True)
    report = runtime.run(task=f"impl {TASK_ID}", subagents=n, prompts=prompts)
    codes = [extract_php(r.text) for r in report.results if r.ok]
    # score every subagent output (real phpunit)
    per_attempt = []
    for c in codes:
        per_attempt.append(run_phpunit(c))
    passes = sum(per_attempt)
    # majority-vote outcome
    maj_code, maj_count = majority(codes)
    maj_pass = run_phpunit(maj_code) if maj_code else False
    uniques = len({code_hash(c) for c in codes})
    out = {
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
        f"  completed {report.completed}/{n} | per-attempt {passes}/{report.completed} "
        f"({out['per_attempt_rate']}%) | unique outputs {uniques} | "
        f"modal {maj_count}/{report.completed} -> {'PASS' if maj_pass else 'fail'} | "
        f"{report.usage.total_tokens:,} tok | ${report.usage.cost_usd:.4f} | "
        f"{report.elapsed_s:.1f}s",
        flush=True,
    )
    return out


def run() -> int:
    if not SINDICO_SRC.exists():
        raise SystemExit(f"sindico source not found at {SINDICO_SRC}")
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("set OPENROUTER_API_KEY")

    file_content = setup_workspace()
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

    ns_str = os.environ.get("BENCH_FANOUT_NS", "1,8,32,64,200")
    ns = [int(x) for x in ns_str.split(",") if x.strip()]
    print(f"fanout benchmark: model={config.model} temp=0.7 N={ns}")

    rows = [fanout_at(n, runtime, file_content) for n in ns]
    RESULTS_JSON.write_text(json.dumps({"model": config.model, "rows": rows}, indent=2))

    write_reports(config.model, rows)
    return 0


def write_reports(model: str, rows: list[dict]) -> None:
    md = [
        "# Fan-out benchmark — does simplicio-prompt's subagent kernel help?",
        "",
        f"Date: **{time.strftime('%Y-%m-%d')}**  ",
        f"Model: `{model}` · temperature **0.7** (induces real per-call variance)  ",
        f"Task: `{TASK_ID}` (add PHP method to {TARGET})  ",
        "Engine: `kernel.subagent_runtime.SubagentRuntime` from simplicio-prompt "
        "v1.7.0 (PyPI), real parallel calls through `LaneWorkerPool`.",
        "",
        "## Methodology",
        "",
        "For each N, the simplicio-prompt **kernel** launches N real parallel "
        "LLM calls on the SAME prompt (simplicio-cli 6-layer wrap of the task) "
        "at `temperature=0.7`. Every returned solution.php is written into a "
        "working copy of `sistema-sindico` and scored by **real PHPUnit** "
        "(`vendor/bin/phpunit` exit code 0). The **majority-vote outcome** is "
        "computed by sha256-hashing the normalized code, picking the most "
        "frequent variant, and re-running phpunit on it.",
        "",
        "**This is the real engagement of simplicio-prompt's value prop**: the "
        "kernel actually executes the fan-out, unlike the prompt-as-text "
        "benchmark in `results_exec_sindico.md`. The question answered here is: "
        "does sp's default 64 buy you anything over a single call? does 200 "
        "buy you more than 64?",
        "",
        "## Headline",
        "",
        "| N | Per-attempt pass | Unique outputs | Majority-vote pass | Tokens | Cost (USD) | Elapsed |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| **{r['n']}** | {r['per_attempt_pass']}/{r['completed']} "
            f"({r['per_attempt_rate']}%) | {r['unique_outputs']} | "
            f"{'PASS' if r['majority_pass'] else 'fail'} "
            f"({r['majority_count']}/{r['completed']}) | "
            f"{r['tokens']:,} | ${r['cost_usd']:.4f} | {r['elapsed_s']:.1f}s |"
        )
    md += ["", "## Interpretation", "",
           "- **Per-attempt pass** is the noise floor at `temperature=0.7`. A "
           "single call hits roughly this rate.",
           "- **Unique outputs** measures real diversity at this temperature; if "
           "every subagent produces the same file, fan-out adds nothing.",
           "- **Majority-vote** is the value test: does picking the most "
           "frequent answer recover correctness when single calls are noisy?",
           "- **Cost** and **elapsed** scale linearly with N. The kernel runs "
           "calls in parallel (LaneWorkerPool), so wall-clock should grow much "
           "slower than total tokens.",
           "",
           "Raw per-subagent data in `results_fanout.json`. Re-run with "
           "`BENCH_FANOUT_NS=...` to test other N values, or "
           "`BENCH_FANOUT_MODEL=...` to swap models.",
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

    pdf.add_page()
    h1("Fan-out benchmark - real simplicio-prompt kernel on sistema-sindico")
    p(f"Date: {time.strftime('%Y-%m-%d')}   Model: {model}   temperature: 0.7   "
      f"Task: {TASK_ID}")
    p("Engine: kernel.subagent_runtime.SubagentRuntime (PyPI simplicio-prompt 1.7.0). "
      "For each N, the kernel launches N real parallel LLM calls through "
      "LaneWorkerPool on the same prompt; each output is scored by real PHPUnit; "
      "the majority-vote outcome (sha256-mode of normalized code) is re-scored. "
      "Question: does the sp-default 64 help vs single? does 200 help vs 64?")
    pdf.ln(1)
    h2("Headline")
    th(["N", "Per-attempt", "Uniq", "Majority", "Tokens", "Cost", "Elapsed"],
       [15, 35, 18, 35, 25, 22, 25])
    for r in rows:
        tr([str(r["n"]),
            f"{r['per_attempt_pass']}/{r['completed']} ({r['per_attempt_rate']}%)",
            str(r["unique_outputs"]),
            f"{'PASS' if r['majority_pass'] else 'fail'} ({r['majority_count']}/{r['completed']})",
            f"{r['tokens']:,}",
            f"${r['cost_usd']:.4f}",
            f"{r['elapsed_s']:.1f}s"], [15, 35, 18, 35, 25, 22, 25])
    pdf.ln(2)
    h2("Interpretation")
    p("Per-attempt pass = noise floor at temp=0.7 (single-call equivalent). "
      "Unique outputs = real diversity at this temperature (if all equal, "
      "fan-out adds nothing). Majority-vote = does picking the most frequent "
      "answer recover correctness? Cost / elapsed scale linearly with N for "
      "tokens; wall-clock grows slower because calls run in parallel.")
    pdf.output(str(RESULTS_PDF))
    print(f"-> {RESULTS_PDF}")


if __name__ == "__main__":
    raise SystemExit(run())
