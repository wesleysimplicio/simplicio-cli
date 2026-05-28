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
INCLUDE_SP = os.environ.get("BENCH_INCLUDE_SP", "1").strip() not in ("0", "false", "False")


def _load_sp_runtime() -> str:
    """Load the simplicio-prompt runtime template (lazy: called only when sp is on).

    Order: explicit env, the simplicio-prompt clone at /tmp/prompt_check, a
    sibling npm install. The PyPI package ships only the kernel, not the .md.
    """
    candidates = [
        os.environ.get("BENCH_SIMPLICIO_PROMPT_PATH"),
        "/tmp/prompt_check/prompts/agent-runtime-execution-prompt.md",
        "node_modules/simplicio-prompt/prompts/agent-runtime-execution-prompt.md",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c).read_text(encoding="utf-8")
    raise SystemExit(
        "simplicio-prompt runtime template not found (needed when BENCH_INCLUDE_SP=1). "
        "Set BENCH_SIMPLICIO_PROMPT_PATH, or clone "
        "https://github.com/wesleysimplicio/simplicio-prompt to /tmp/prompt_check."
    )


SP_RUNTIME = _load_sp_runtime() if INCLUDE_SP else ""


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


SP_PROMPT = """{sp_runtime}

---

[USER INPUT - task X]
{goal}

Target file ({target}) current content:
```php
{file_content}
```

Output the COMPLETE updated contents of {target}. PHP only, no prose, no fences."""


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
        sem_pass = com_pass = sp_pass = 0
        for c in CASES:
            content = (SINDICO_SRC / c["target"]).read_text(encoding="utf-8")
            ctx = {**c, "file_content": content}
            s = one(model, c, RAW_PROMPT.format(**ctx), snaps)
            w = one(model, c, CONTRACT_PROMPT.format(**ctx), snaps)
            sem_pass += int(s["passed"]); com_pass += int(w["passed"])
            row = {"id": c["id"], "sem": s, "com": w}
            sp_msg = ""
            if INCLUDE_SP:
                p = one(model, c, SP_PROMPT.format(sp_runtime=SP_RUNTIME, **ctx), snaps)
                sp_pass += int(p["passed"]); row["sp"] = p
                sp_msg = f"  sp {'PASS' if p['passed'] else 'fail'}"
            rows.append(row)
            print(f"  {c['id']:25s} baseline {'PASS' if s['passed'] else 'fail'}  "
                  f"cli {'PASS' if w['passed'] else 'fail'}{sp_msg}")
        entry = {"rows": rows, "n": n,
            "sem_pass": sem_pass, "com_pass": com_pass,
            "sem_pct": 100*sem_pass//n, "com_pct": 100*com_pass//n}
        if INCLUDE_SP:
            entry["sp_pass"] = sp_pass; entry["sp_pct"] = 100*sp_pass//n
        by_model[model] = entry
        tail = f" | sp {sp_pass}/{n} ({100*sp_pass//n}%)" if INCLUDE_SP else ""
        print(f"  -> baseline {sem_pass}/{n} ({by_model[model]['sem_pct']}%) "
              f"| cli {com_pass}/{n} ({by_model[model]['com_pct']}%){tail}\n")
    RESULTS_JSON.write_text(json.dumps(by_model, indent=2))
    write_reports(by_model)
    g_sem = sum(b["sem_pass"] for b in by_model.values())
    g_com = sum(b["com_pass"] for b in by_model.values())
    g_tot = sum(b["n"] for b in by_model.values())
    sp_tail = ""
    if INCLUDE_SP:
        g_sp = sum(b.get("sp_pass", 0) for b in by_model.values())
        sp_tail = f" | sp {100*g_sp//g_tot}%"
    print(f"grand: baseline {100*g_sem//g_tot}% | cli {100*g_com//g_tot}%"
          f"{sp_tail} (real phpunit, {g_tot} runs/side)")
    return 0


def _has_sp(by_model: dict) -> bool:
    """True iff any model carries simplicio-prompt data in its rows."""
    return any("sp" in r for b in by_model.values() for r in b.get("rows", []))


def write_reports(by_model: dict) -> None:
    models = list(by_model.keys())
    # Drive the report off rows actually present in the data, not the static
    # CASES list, so regenerating from a partial run shows what was measured.
    sample_rows = next(iter(by_model.values())).get("rows", []) if by_model else []
    case_ids = [r["id"] for r in sample_rows]
    n_tasks = len(case_ids)
    with_sp = _has_sp(by_model)
    g_sem = sum(b.get("sem_pass", 0) for b in by_model.values())
    g_com = sum(b.get("com_pass", 0) for b in by_model.values())
    g_tot = sum(b["n"] for b in by_model.values())
    gsp = 100 * g_sem // max(g_tot, 1)
    gcp = 100 * g_com // max(g_tot, 1)
    sides_blurb = (
        "- **baseline**: raw goal + current file content\n"
        "- **simplicio-cli**: the 6-layer task contract (role/stack, goal, "
        "target, criteria as testable states, constraints, output shape)"
    )
    if with_sp:
        sides_blurb += ("\n- **simplicio-prompt**: the Tuple-Space + Yool "
                        "runtime template from the simplicio-prompt package, "
                        "with the task injected as user input X")
    md = [
        "# Execution benchmark — real project, real tasks, real test suite",
        "",
        f"Date: **{time.strftime('%Y-%m-%d')}**  ",
        f"Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico)"
        f" — a real condominium-management system in pure PHP 8 (public on GitHub, PHPUnit 11)  ",
        f"Models: " + ", ".join(f"`{m}`" for m in models) + "  ",
        f"Tasks: **{n_tasks}** additive real-engineering changes across "
        "`src/Core/`, `src/Middleware/`, `src/Repositories/`, and routing.",
        "",
        "## Methodology — what \"pass\" actually means",
        "",
        "**This is NOT regex pattern-matching on model output. This is NOT a "
        "synthetic toy unit-test harness in isolation.** The benchmark runs "
        "against an actual published PHP project using the project's real "
        "PHPUnit suite (`vendor/bin/phpunit --configuration phpunit.xml.dist`).",
        "",
        "For each task:",
        "",
        "1. The model is asked for a real engineering change — add a new method "
        "to an existing production class (permission helper, env parser, "
        "rate-limit key builder, repository SQL builder, route introspection, "
        "etc.).",
        "2. Its generated file replaces the original in a working copy of the "
        "real repo (with `composer install` deps already in place).",
        "3. A **hidden PHPUnit test** (never shown to the model, asserting "
        "BOTH true and false states of the required behaviour) is dropped into "
        "`tests/unit/Core/Hidden/`.",
        "4. The **ENTIRE production suite** runs — every pre-existing test of "
        "the real codebase plus the hidden one. The model's change must be "
        "**correct** (the new test passes) AND must **not break existing "
        "behaviour** (every prior test still passes).",
        "5. **Pass = `phpunit` exit code 0** — the same green/red signal the "
        "project's CI would use to merge a PR.",
        "",
        "All sides emit the complete file (identical output shape); the only "
        "variable is the wrapping prompt:",
        "",
        sides_blurb,
        "",
        "## Headline",
        "",
        f"- **Baseline:** {g_sem}/{g_tot} ({gsp}%)",
        f"- **simplicio-cli (6-layer):** {g_com}/{g_tot} ({gcp}%) — **{gcp - gsp:+d} pts vs baseline**",
    ]
    if with_sp:
        g_sp = sum(b.get("sp_pass", 0) for b in by_model.values())
        gpp = 100 * g_sp // max(g_tot, 1)
        md.append(f"- **simplicio-prompt (Yool runtime):** {g_sp}/{g_tot} ({gpp}%) "
                  f"— **{gpp - gsp:+d} pts vs baseline**")
    md += ["", "## Per-model (pass = full PHPUnit suite green)", ""]
    if with_sp:
        md += ["| Model | Baseline | simplicio-cli | simplicio-prompt | D cli | D sp |",
               "|---|---|---|---|---|---|"]
        for m in models:
            b = by_model[m]
            md.append(
                f"| `{m}` | {b['sem_pass']}/{b['n']} ({b['sem_pct']}%) | "
                f"{b['com_pass']}/{b['n']} ({b['com_pct']}%) | "
                f"{b.get('sp_pass', 0)}/{b['n']} ({b.get('sp_pct', 0)}%) | "
                f"**{b['com_pct'] - b['sem_pct']:+d}** | "
                f"**{b.get('sp_pct', 0) - b['sem_pct']:+d}** |"
            )
    else:
        md += ["| Model | Baseline | simplicio-cli | Delta (pts) |",
               "|---|---|---|---|"]
        for m in models:
            b = by_model[m]
            md.append(
                f"| `{m}` | {b['sem_pass']}/{b['n']} ({b['sem_pct']}%) | "
                f"{b['com_pass']}/{b['n']} ({b['com_pct']}%) | "
                f"**{b['com_pct'] - b['sem_pct']:+d}** |"
            )
    md += ["", f"## Per-task × model ({'baseline / cli / sp' if with_sp else 'baseline / cli'})", "",
           "| Task | " + " | ".join(m.split("/")[-1] for m in models) + " |",
           "|---|" + "|".join("---" for _ in models) + "|"]
    for i, cid in enumerate(case_ids):
        cells = []
        for m in models:
            r = by_model[m]["rows"][i]
            base = f"{'P' if r['sem']['passed'] else '.'}/{'P' if r['com']['passed'] else '.'}"
            if with_sp:
                sp = r.get("sp", {"passed": False})
                base += f"/{'P' if sp.get('passed') else '.'}"
            cells.append(base)
        md.append(f"| {cid} | " + " | ".join(cells) + " |")
    md += ["", "Raw counts above are real `vendor/bin/phpunit` exit codes against "
           "`sistema-sindico`. `results_exec_sindico.json` holds per-case "
           "pass/fail, tokens, latency and a phpunit tail for every side.", ""]
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
    with_sp = _has_sp(by_model)
    g_sem = sum(b.get("sem_pass", 0) for b in by_model.values())
    g_com = sum(b.get("com_pass", 0) for b in by_model.values())
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

    sample_rows = next(iter(by_model.values())).get("rows", []) if by_model else []
    n_tasks = len(sample_rows)
    pdf.add_page()
    h1("Execution benchmark - real project, real tasks, real test suite")
    p(f"Date: {time.strftime('%Y-%m-%d')}   "
      f"Target: wesleysimplicio/sistema-sindico (real PHP 8 condominium system, "
      f"public on GitHub)   Tasks: {n_tasks} additive engineering changes "
      f"across Core / Middleware / Repository / Router.")
    h2("Methodology - what 'pass' actually means")
    p("NOT regex on model output. NOT a toy harness in isolation. The model's "
      "generated file replaces the real source file in a working copy of the "
      "real repo; a hidden PHPUnit test (never shown to the model, asserting "
      "TRUE and FALSE states) is added to tests/unit/Core/Hidden/; the FULL "
      "production suite runs (existing tests + hidden). Pass = vendor/bin/phpunit "
      "exit code 0 - same green/red the project's CI would use to merge a PR. "
      "The model's change must be correct AND must not break any pre-existing "
      "test of the real codebase.")
    blurb = ("All sides emit the complete file (identical output shape). "
             "Variables: baseline = raw goal; cli = the simplicio-cli 6-layer "
             "task contract")
    if with_sp:
        blurb += "; sp = the simplicio-prompt Tuple-Space + Yool runtime template."
    else:
        blurb += "."
    p(blurb)
    pdf.ln(1)
    h2("Headline")
    th(["Side", "Passed", "Rate", "vs baseline"], [60, 30, 30, 40])
    tr(["Baseline", f"{g_sem}/{g_tot}", f"{100*g_sem//max(g_tot,1)}%", "-"], [60, 30, 30, 40])
    tr(["simplicio-cli (6-layer)", f"{g_com}/{g_tot}", f"{100*g_com//max(g_tot,1)}%",
        f"{100*g_com//max(g_tot,1) - 100*g_sem//max(g_tot,1):+d} pts"], [60, 30, 30, 40])
    if with_sp:
        g_sp = sum(b.get("sp_pass", 0) for b in by_model.values())
        tr(["simplicio-prompt (Yool)", f"{g_sp}/{g_tot}", f"{100*g_sp//max(g_tot,1)}%",
            f"{100*g_sp//max(g_tot,1) - 100*g_sem//max(g_tot,1):+d} pts"], [60, 30, 30, 40])
    pdf.ln(2)
    h2("Per-model (pass = full PHPUnit suite green)")
    if with_sp:
        th(["Model", "Baseline", "cli", "sp", "D cli", "D sp"], [70, 24, 24, 24, 18, 18])
        for m in models:
            b = by_model[m]
            tr([m, f"{b['sem_pass']}/{b['n']} ({b['sem_pct']}%)",
                f"{b['com_pass']}/{b['n']} ({b['com_pct']}%)",
                f"{b.get('sp_pass',0)}/{b['n']} ({b.get('sp_pct',0)}%)",
                f"{b['com_pct']-b['sem_pct']:+d}",
                f"{b.get('sp_pct',0)-b['sem_pct']:+d}"],
                [70, 24, 24, 24, 18, 18])
    else:
        th(["Model", "Baseline", "simplicio-cli", "Delta(pts)"], [86, 30, 30, 30])
        for m in models:
            b = by_model[m]
            tr([m, f"{b['sem_pass']}/{b['n']} ({b['sem_pct']}%)",
                f"{b['com_pass']}/{b['n']} ({b['com_pct']}%)",
                f"{b['com_pct']-b['sem_pct']:+d}"], [86, 30, 30, 30])
    pdf.ln(2)
    h2(f"Per-task x model ({'base / cli / sp' if with_sp else 'base / cli'})")
    case_ids = [r["id"] for r in sample_rows]
    th(["Task"] + [m.split("/")[-1] for m in models],
       [40] + [(140 // max(len(models), 1))] * len(models))
    for i, cid in enumerate(case_ids):
        row = [cid]
        for m in models:
            r = by_model[m]["rows"][i]
            cell = f"{'P' if r['sem']['passed'] else '.'}/{'P' if r['com']['passed'] else '.'}"
            if with_sp:
                sp = r.get("sp", {"passed": False})
                cell += f"/{'P' if sp.get('passed') else '.'}"
            row.append(cell)
        tr(row, [40] + [(140 // max(len(models), 1))] * len(models))
    pdf.output(str(RESULTS_PDF))
    print(f"-> {RESULTS_PDF}")


if __name__ == "__main__":
    raise SystemExit(run())
