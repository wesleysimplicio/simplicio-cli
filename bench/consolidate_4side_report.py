#!/usr/bin/env python3
"""
consolidate_4side_report.py — merge regex + functional benches into one
markdown showing all 4 sides (baseline / cli / cli+sp / cli+ag) for the
Qwen3 Coder MoE batch.

Reads:
  bench/results.json              (regex, from run_offline.py)
  bench/results_exec_sindico.json (functional, from run_exec_sindico.py)

Writes:
  bench/results_4side_qwen3.md
"""
from __future__ import annotations
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGEX_JSON = ROOT / "bench" / "results.json"
EXEC_JSON = ROOT / "bench" / "results_exec_sindico.json"
OUT_MD = ROOT / "bench" / "results_4side_qwen3.md"


def _row_attempts(rows: list, key: str) -> float:
    vals = [r[key].get("attempts", 1) for r in rows if key in r]
    return sum(vals) / max(len(vals), 1)


def _row_token_avg(rows: list, key: str, field: str = "tokens") -> float:
    vals = [r[key].get(field, 0) for r in rows if key in r]
    return sum(vals) / max(len(vals), 1)


def _row_ms_avg(rows: list, key: str) -> float:
    vals = [r[key].get("ms", 0) for r in rows if key in r]
    return sum(vals) / max(len(vals), 1)


def _exec_row(by_model: dict, model: str) -> dict:
    b = by_model[model]
    rows = b["rows"]
    return {
        "n": b["n"],
        "sem": b.get("sem_pct", 0),
        "com": b.get("com_pct", 0),
        "sp":  b.get("sp_pct", 0),
        "ag":  b.get("ag_pct", 0),
        "ag_attempts_avg": _row_attempts(rows, "ag"),
        "sem_tok": _row_token_avg(rows, "sem"),
        "com_tok": _row_token_avg(rows, "com"),
        "sp_tok":  _row_token_avg(rows, "sp"),
        "ag_tok":  _row_token_avg(rows, "ag"),
        "sem_ms": _row_ms_avg(rows, "sem"),
        "com_ms": _row_ms_avg(rows, "com"),
        "sp_ms":  _row_ms_avg(rows, "sp"),
        "ag_ms":  _row_ms_avg(rows, "ag"),
    }


def _regex_row(by_model: dict, model: str) -> dict:
    b = by_model[model]
    rows = b.get("rows", [])
    n = b["total"]
    ag_attempts = [r.get("ag_attempts", 1) for r in rows if "ag_attempts" in r]
    return {
        "n": n,
        "sem": b.get("sem_pct", 0),
        "com": b.get("com_pct", 0),
        "sp":  b.get("sp_pct", 0),
        "ag":  b.get("ag_pct", 0),
        "ag_attempts_avg": (sum(ag_attempts) / max(len(ag_attempts), 1)) if ag_attempts else 0,
        "sem_tok": b.get("usage_sem", {}).get("total_tokens", 0) / max(len(rows), 1),
        "com_tok": b.get("usage_com", {}).get("total_tokens", 0) / max(len(rows), 1),
        "sp_tok":  b.get("usage_sp",  {}).get("total_tokens", 0) / max(len(rows), 1),
        "ag_tok":  b.get("usage_ag",  {}).get("total_tokens", 0) / max(len(rows), 1),
    }


def fmt_pct(p: int) -> str:
    return f"{p}%"


def fmt_delta(a: int, b: int) -> str:
    d = a - b
    return f"**{d:+d}**"


def main() -> int:
    if not EXEC_JSON.exists():
        raise SystemExit(f"missing {EXEC_JSON}")
    exec_data = json.loads(EXEC_JSON.read_text())
    regex_data = json.loads(REGEX_JSON.read_text()) if REGEX_JSON.exists() else {}

    # collect models present in either bench, in stable order
    exec_models = list(exec_data.keys())
    regex_models = [m for m in regex_data.keys() if m not in exec_models]
    all_models = exec_models + regex_models

    md = [
        "# 4-side comparison — Qwen3 Coder MoE",
        "",
        f"Date: **{time.strftime('%Y-%m-%d')}**  ",
        "",
        "**Sides** (same 6-layer task contract on cli / cli+sp / cli+ag):",
        "",
        "- `baseline` — raw one-line goal + file content. No simplicio at all.",
        "- `cli` — wrapped in the simplicio-cli 6-layer contract "
        "(role/stack, goal, target, criteria, constraints, output shape).",
        "- `cli + sp` — same contract, embedded as user-input-X inside the "
        "simplicio-prompt v1.9 Tuple-Space + Yool runtime template (3,907 "
        "chars of runtime preamble).",
        "- `cli + ag` — same contract, but on failure the harness classifies "
        "the failure (syntax/assertion/runtime/etc.), feeds the PHPUnit tail "
        "(or list of missed regex patterns) back as retry feedback, re-prompts. "
        "Up to 3 attempts. Mirrors `simplicio task --verify`.",
        "",
        "**Metrics**:",
        "",
        "- `functional` — real `vendor/bin/phpunit --configuration phpunit.xml.dist` "
        "on `wesleysimplicio/sistema-sindico` (PHP 8). Pass = full suite green.",
        "- `regex` — structural pattern match against the generated output "
        "(cheap proxy used by `bench/run_offline.py`).",
        "",
    ]

    # ---- HEADLINE TABLE ---- #
    md += ["## Headline — pass rate per side, both metrics", "",
           "| Model | metric | baseline | cli | cli+sp | cli+ag | "
           "Δ cli | Δ cli+sp | Δ cli+ag |",
           "|---|---|---|---|---|---|---|---|---|"]

    for model in all_models:
        if model in exec_data:
            e = _exec_row(exec_data, model)
            md.append(
                f"| `{model}` | functional | {fmt_pct(e['sem'])} | {fmt_pct(e['com'])} | "
                f"{fmt_pct(e['sp'])} | {fmt_pct(e['ag'])} | "
                f"{fmt_delta(e['com'], e['sem'])} | {fmt_delta(e['sp'], e['sem'])} | "
                f"{fmt_delta(e['ag'], e['sem'])} |"
            )
        if model in regex_data:
            r = _regex_row(regex_data, model)
            md.append(
                f"| `{model}` | regex | {fmt_pct(r['sem'])} | {fmt_pct(r['com'])} | "
                f"{fmt_pct(r['sp'])} | {fmt_pct(r['ag'])} | "
                f"{fmt_delta(r['com'], r['sem'])} | {fmt_delta(r['sp'], r['sem'])} | "
                f"{fmt_delta(r['ag'], r['sem'])} |"
            )

    # ---- AGENTS LOOP CONVERGENCE ---- #
    md += ["", "## Agents verify-loop convergence", "",
           "Lower attempts = the model resolved the case earlier; 1 means it "
           "passed on the first try with no feedback. Max attempts capped per "
           "harness.",
           "",
           "| Model | metric | avg attempts (cli+ag) |",
           "|---|---|---|"]
    for model in all_models:
        if model in exec_data:
            e = _exec_row(exec_data, model)
            md.append(f"| `{model}` | functional | {e['ag_attempts_avg']:.2f} |")
        if model in regex_data:
            r = _regex_row(regex_data, model)
            md.append(f"| `{model}` | regex | {r['ag_attempts_avg']:.2f} |")

    # ---- COST/LATENCY (functional only — exec captures both) ---- #
    md += ["", "## Cost & latency per call (functional bench)", "",
           "Tokens/call averaged across the 12 cases. cli+ag burns more tokens "
           "AND more wall-clock per case because it may run up to 3 attempts. "
           "If pass-rate gain doesn't justify the multiplier, single-shot cli "
           "wins for batch jobs; cli+ag wins for interactive workflows where "
           "a 1.5x cost is acceptable to avoid manual rerun.",
           "",
           "| Model | side | tokens/call | ms/call |",
           "|---|---|---|---|"]
    for model in exec_models:
        e = _exec_row(exec_data, model)
        md.append(f"| `{model}` | baseline | {e['sem_tok']:.0f} | {e['sem_ms']:.0f} |")
        md.append(f"| `{model}` | cli      | {e['com_tok']:.0f} | {e['com_ms']:.0f} |")
        md.append(f"| `{model}` | cli+sp   | {e['sp_tok']:.0f} | {e['sp_ms']:.0f} |")
        md.append(f"| `{model}` | cli+ag   | {e['ag_tok']:.0f} | {e['ag_ms']:.0f} |")

    # ---- PER-TASK MATRIX (functional) ---- #
    md += ["", "## Per-task × model (functional, base / cli / cli+sp / cli+ag)", ""]
    if exec_models:
        sample = next(iter(exec_data.values()))["rows"]
        md.append("| Task | " + " | ".join(m.split("/")[-1] for m in exec_models) + " |")
        md.append("|---|" + "|".join("---" for _ in exec_models) + "|")
        for i, r0 in enumerate(sample):
            cid = r0["id"]
            cells = []
            for m in exec_models:
                r = exec_data[m]["rows"][i]
                cell = ("P" if r["sem"]["passed"] else ".") + "/" + \
                       ("P" if r["com"]["passed"] else ".") + "/" + \
                       ("P" if r.get("sp", {}).get("passed") else ".") + "/" + \
                       ("P" if r.get("ag", {}).get("passed") else ".") + \
                       f"({r.get('ag', {}).get('attempts', 0)})"
                cells.append(cell)
            md.append(f"| {cid} | " + " | ".join(cells) + " |")
        md += ["",
               "Last digit on cli+ag is the attempt count consumed (1–3). 1 = "
               "no feedback loop needed. 3 with `.` = ran the full loop and "
               "still failed; this is a model-capability ceiling, not a "
               "feedback-loop problem."]

    OUT_MD.write_text("\n".join(md) + "\n")
    print(f"-> {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
