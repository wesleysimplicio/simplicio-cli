"""
run_exec_sindico.py — EXECUTION benchmark against sistema-sindico (real PHPUnit).

For every case and every model, two prompts are sent:
  WITHOUT: raw goal + existing file content + "output the full updated file"
  WITH:    same goal + content, wrapped in the simplicio contract (role/stack,
           target, testable criteria, constraints, identical output shape)
Both sides emit the COMPLETE updated PHP file. The harness writes that file
into a working copy of sistema-sindico, drops a HIDDEN PHPUnit test (never
shown to the model) into tests/unit/Core/Hidden/, and runs `vendor/bin/phpunit`
on the WHOLE suite. Pass = every existing test plus the hidden one go green —
which means the new method works AND nothing else was broken.

Usage:
  BENCH_BASE_URL=https://router.huggingface.co/v1 BENCH_API_KEY=... \
    BENCH_MODELS="Qwen/Qwen2.5-7B-Instruct,..." \
    python3 bench/run_exec_sindico.py
"""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SINDICO_SRC = Path(os.environ.get("BENCH_SINDICO_SRC", "/tmp/sindico"))
WORK = Path(os.environ.get("BENCH_SINDICO_WORK", "/tmp/sindico_work_bench"))
HIDDEN_TPL = ROOT / "bench" / "sindico_hidden"
RESULTS_JSON = ROOT / "bench" / "results_exec_sindico.json"
RESULTS_MD = ROOT / "bench" / "results_exec_sindico.md"
RESULTS_PDF = ROOT / "bench" / "results_exec_sindico.pdf"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_offline as ro  # llm_call / local_call / _lat1
from sindico_cases import CASES

MODELS = [m.strip() for m in os.environ.get("BENCH_MODELS", "").split(",") if m.strip()]
PHPUNIT_TIMEOUT = int(os.environ.get("BENCH_PHPUNIT_TIMEOUT", "60"))

RAW_PROMPT = """{goal}

Here is the current content of {target}:
```php
{file_content}
```

Output the COMPLETE updated contents of {target}. PHP only, no prose."""

CONTRACT_PROMPT = """You are a senior engineer working IN THIS project.
Stack: PHP 8 + composer + PHPUnit. Project conventions are LAW. Do not invent files or libraries the project does not use.

[GOAL]
{goal}

[TARGET]
Touch ONLY this file: {target}
Current content:
```php
{file_content}
```

[CONTRACT]
Done WHEN, and only when, ALL of the states below are true:
{criteria}

Constraints (do not break):
{constraints}

[OUTPUT]
Return ONLY the complete updated contents of {target}. PHP only, no prose, no fences."""


def setup_workspace() -> dict:
    """Fresh copy of sindico into WORK; return {target -> original content} snapshot."""
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(SINDICO_SRC, WORK)
    (WORK / "tests" / "unit" / "Core" / "Hidden").mkdir(parents=True, exist_ok=True)
    snaps: dict[str, str] = {}
    for c in CASES:
        snaps[c["target"]] = (SINDICO_SRC / c["target"]).read_text(encoding="utf-8")
    return snaps


def reset_target(target: str, snaps: dict) -> None:
    (WORK / target).write_text(snaps[target], encoding="utf-8")


def extract_php(text: str) -> str:
    """Pull the PHP module out of a model reply (largest fenced block, else raw)."""
    text = text or ""
    blocks = re.findall(r"```(?:php)?\s*\n(.*?)```", text, re.DOTALL)
    code = max(blocks, key=len).strip() if blocks else text.strip()
    if not code.lstrip().startswith("<?php"):
        code = "<?php\n" + code
    return code


def run_phpunit() -> tuple[bool, str]:
    try:
        p = subprocess.run(
            ["vendor/bin/phpunit", "--configuration", "phpunit.xml.dist"],
            cwd=WORK, capture_output=True, text=True, timeout=PHPUNIT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    tail = (p.stdout + p.stderr).splitlines()[-3:]
    return p.returncode == 0, " | ".join(tail)


def one(model: str, case: dict, prompt: str, snaps: dict) -> dict:
    reset_target(case["target"], snaps)
    res = ro.llm_call(model, prompt)
    code = extract_php(res["text"])
    (WORK / case["target"]).write_text(code, encoding="utf-8")
    hidden_dst = WORK / "tests" / "unit" / "Core" / "Hidden" / case["hidden_test"]
    hidden_dst.write_text((HIDDEN_TPL / case["hidden_test"]).read_text(encoding="utf-8"),
                           encoding="utf-8")
    passed, tail = run_phpunit()
    hidden_dst.unlink(missing_ok=True)
    reset_target(case["target"], snaps)
    return {"passed": passed, "tokens": res.get("total_tokens", 0),
            "ms": res.get("elapsed_ms", 0), "tail": tail,
            "error": res.get("error")}


def run() -> int:
    if not MODELS:
        raise SystemExit("set BENCH_MODELS")
    if not SINDICO_SRC.exists():
        raise SystemExit(f"sindico source not found at {SINDICO_SRC}")
    snaps = setup_workspace()
    n = len(CASES)
    print(f"exec target: sistema-sindico ({WORK})\nmodels: {MODELS}\ncases: {n}\n")
    by_model = {}
    for model in MODELS:
        print(f"=== {model} ===")
        rows = []
        sem_pass = com_pass = 0
        for c in CASES:
            content = (SINDICO_SRC / c["target"]).read_text(encoding="utf-8")
            ctx = {**c, "file_content": content}
            s = one(model, c, RAW_PROMPT.format(**ctx), snaps)
            w = one(model, c, CONTRACT_PROMPT.format(**ctx), snaps)
            sem_pass += int(s["passed"]); com_pass += int(w["passed"])
            rows.append({"id": c["id"], "sem": s, "com": w})
            print(f"  {c['id']:25s} without {'PASS' if s['passed'] else 'fail'}  "
                  f"with {'PASS' if w['passed'] else 'fail'}")
        by_model[model] = {"rows": rows, "n": n,
            "sem_pass": sem_pass, "com_pass": com_pass,
            "sem_pct": 100*sem_pass//n, "com_pct": 100*com_pass//n}
        print(f"  -> without {sem_pass}/{n} ({by_model[model]['sem_pct']}%)  "
              f"with {com_pass}/{n} ({by_model[model]['com_pct']}%)\n")
    RESULTS_JSON.write_text(json.dumps(by_model, indent=2))
    write_reports(by_model)
    g_sem = sum(b["sem_pass"] for b in by_model.values())
    g_com = sum(b["com_pass"] for b in by_model.values())
    g_tot = sum(b["n"] for b in by_model.values())
    print(f"grand: without {100*g_sem//g_tot}% · with {100*g_com//g_tot}% "
          f"(real phpunit, {g_tot} runs/side)")
    return 0


def write_reports(by_model: dict) -> None:
    models = list(by_model.keys())
    case_ids = [c["id"] for c in CASES]
    g_sem = sum(b["sem_pass"] for b in by_model.values())
    g_com = sum(b["com_pass"] for b in by_model.values())
    g_tot = sum(b["n"] for b in by_model.values())
    gsp = 100 * g_sem // max(g_tot, 1)
    gcp = 100 * g_com // max(g_tot, 1)
    md = [
        "# Execution benchmark — simplicio-cli on sistema-sindico (real PHPUnit)",
        "",
        f"Date: **{time.strftime('%Y-%m-%d')}**  ",
        f"Target project: `wesleysimplicio/sistema-sindico` (PHP 8 + PHPUnit 11)  ",
        f"Models: " + ", ".join(f"`{m}`" for m in models) + "  ",
        f"Tasks: **{len(CASES)}** additive modifications to `src/Core/` classes.",
        "",
        "Each task asks the model to add a new method to a real file in the "
        "sindico codebase. The generated file is written into a working copy, "
        "a **hidden PHPUnit test** (never shown to the model, asserting true "
        "AND false states) is added under `tests/unit/Core/Hidden/`, and the "
        "ENTIRE suite is run. **Pass = every existing test + the hidden test "
        "go green.** This means the new method works AND no existing test was "
        "broken. Both sides emit the complete file — the only variable is "
        "whether the goal is wrapped in the simplicio contract.",
        "",
        "## Headline",
        "",
        f"- **Without simplicio:** {g_sem}/{g_tot} ({gsp}%)",
        f"- **With simplicio:** {g_com}/{g_tot} ({gcp}%)",
        f"- **Delta:** **{gcp - gsp:+d} points**",
        "",
        "## Per-model (pass = full PHPUnit suite green)",
        "",
        "| Model | Without | With | Delta (pts) |",
        "|---|---|---|---|",
    ]
    for m in models:
        b = by_model[m]
        md.append(f"| `{m}` | {b['sem_pass']}/{b['n']} ({b['sem_pct']}%) | "
                  f"{b['com_pass']}/{b['n']} ({b['com_pct']}%) | "
                  f"**{b['com_pct'] - b['sem_pct']:+d}** |")
    md += ["", "## Per-task × model (P = pass, . = fail)", "",
           "| Task (w/o, with) | " + " | ".join(m.split("/")[-1] for m in models) + " |",
           "|---|" + "|".join("---" for _ in models) + "|"]
    for i, cid in enumerate(case_ids):
        cells = []
        for m in models:
            r = by_model[m]["rows"][i]
            cells.append(f"{'P' if r['sem']['passed'] else '.'} / "
                         f"{'P' if r['com']['passed'] else '.'}")
        md.append(f"| {cid} | " + " | ".join(cells) + " |")
    md += ["", "Raw counts above are real `vendor/bin/phpunit` exit codes against "
           "`sistema-sindico`. `results_exec_sindico.json` holds per-case "
           "pass/fail, tokens, latency and a phpunit tail.", ""]
    RESULTS_MD.write_text("\n".join(md))
    print(f"-> {RESULTS_MD}")
    _pdf(by_model)


def _pdf(by_model: dict) -> None:
    try:
        from fpdf import FPDF
    except ImportError:
        print("[warn] fpdf2 not installed; skipping exec sindico PDF.")
        return
    models = list(by_model.keys())
    g_sem = sum(b["sem_pass"] for b in by_model.values())
    g_com = sum(b["com_pass"] for b in by_model.values())
    g_tot = sum(b["n"] for b in by_model.values())
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15); pdf.set_margins(15, 15, 15)
    L = ro._lat1

    def h1(t): pdf.set_font("Helvetica", "B", 16); pdf.multi_cell(0, 8, L(t)); pdf.ln(1)
    def h2(t): pdf.set_font("Helvetica", "B", 12); pdf.multi_cell(0, 7, L(t)); pdf.ln(1)
    def p(t): pdf.set_font("Helvetica", "", 9); pdf.multi_cell(0, 5, L(t)); pdf.ln(1)

    def th(cols, w):
        pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(230, 230, 230)
        for c, x in zip(cols, w):
            pdf.cell(x, 6, L(c), border=1, fill=True)
        pdf.ln()

    def tr(cells, w):
        pdf.set_font("Helvetica", "", 9)
        for c, x in zip(cells, w):
            pdf.cell(x, 6, L(c), border=1)
        pdf.ln()

    pdf.add_page()
    h1("Execution benchmark - sistema-sindico (real PHPUnit, not regex)")
    p(f"Date: {time.strftime('%Y-%m-%d')}   Tasks: {len(CASES)} additive PHP modifications")
    p("Each generated file is written into a real sindico working copy. A hidden "
      "PHPUnit test (true AND false states) is added; the full suite runs. "
      "Pass = every test (existing + hidden) goes green.")
    pdf.ln(1)
    h2("Headline")
    th(["Side", "Passed", "Rate"], [70, 50, 40])
    tr(["Without simplicio", f"{g_sem}/{g_tot}", f"{100*g_sem//max(g_tot,1)}%"], [70, 50, 40])
    tr(["With simplicio", f"{g_com}/{g_tot}", f"{100*g_com//max(g_tot,1)}%"], [70, 50, 40])
    pdf.ln(2)
    h2("Per-model (pass = full PHPUnit suite green)")
    th(["Model", "Without", "With", "Delta(pts)"], [86, 30, 30, 30])
    for m in models:
        b = by_model[m]
        tr([m, f"{b['sem_pass']}/{b['n']} ({b['sem_pct']}%)",
            f"{b['com_pass']}/{b['n']} ({b['com_pct']}%)",
            f"{b['com_pct']-b['sem_pct']:+d}"], [86, 30, 30, 30])
    pdf.ln(2)
    h2("Per-task x model (w/o / with)")
    case_ids = [c["id"] for c in CASES]
    th(["Task"] + [m.split("/")[-1] for m in models],
       [40] + [(140 // max(len(models), 1))] * len(models))
    for i, cid in enumerate(case_ids):
        row = [cid]
        for m in models:
            r = by_model[m]["rows"][i]
            row.append(f"{'P' if r['sem']['passed'] else '.'}/{'P' if r['com']['passed'] else '.'}")
        tr(row, [40] + [(140 // max(len(models), 1))] * len(models))
    pdf.output(str(RESULTS_PDF))
    print(f"-> {RESULTS_PDF}")


if __name__ == "__main__":
    raise SystemExit(run())
