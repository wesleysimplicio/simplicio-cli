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
OUT_PDF = ROOT / "bench" / "results_4side_qwen3.pdf"


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
    _write_pdf(exec_data, regex_data, exec_models, all_models)
    return 0


def _write_pdf(exec_data: dict, regex_data: dict,
               exec_models: list, all_models: list) -> None:
    """Use reportlab (pure Python, no native crypto deps) to render a PDF
    mirroring the markdown headline + tables. Falls back silently if
    reportlab is missing."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)
    except ImportError:
        print("[warn] reportlab not installed; skipping PDF.")
        return

    doc = SimpleDocTemplate(
        str(OUT_PDF), pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=14*mm, bottomMargin=14*mm,
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]; body.fontSize = 9; body.leading = 12
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10)
    story = []

    story.append(Paragraph(
        "4-side comparison &mdash; Qwen3 Coder MoE", h1))
    story.append(Paragraph(
        f"Date: <b>{time.strftime('%Y-%m-%d')}</b>", body))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Sides", h2))
    story.append(Paragraph(
        "<b>baseline</b> &mdash; raw one-line goal + file content. No "
        "simplicio.<br/>"
        "<b>cli</b> &mdash; the simplicio-cli 6-layer task contract "
        "(role/stack, goal, target, criteria, constraints, output shape).<br/>"
        "<b>cli + sp</b> &mdash; same contract wrapped as user-input-X inside "
        "the simplicio-prompt v1.9 Tuple-Space + Yool runtime template.<br/>"
        "<b>cli + ag</b> &mdash; same contract, with classified failure feedback "
        "(PHPUnit tail or missed regex patterns) fed back over up to 3 attempts. "
        "Mirrors <font face='Courier'>simplicio task --verify</font>.",
        body))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("Metrics", h2))
    story.append(Paragraph(
        "<b>functional</b> &mdash; real <font face='Courier'>vendor/bin/phpunit "
        "--configuration phpunit.xml.dist</font> on "
        "<font face='Courier'>wesleysimplicio/sistema-sindico</font> (PHP 8). "
        "Pass = full suite green.<br/>"
        "<b>regex</b> &mdash; structural pattern match against the generated "
        "output (cheap proxy used by <font face='Courier'>bench/run_offline.py</font>).",
        body))
    story.append(Spacer(1, 5*mm))

    # Headline table
    story.append(Paragraph("Headline &mdash; pass rate per side, both metrics", h2))
    headline = [["Model", "Metric", "baseline", "cli", "cli+sp", "cli+ag",
                 "Δcli", "Δcli+sp", "Δcli+ag"]]
    for model in all_models:
        short = model.replace("Qwen/", "")
        if model in exec_data:
            e = _exec_row(exec_data, model)
            headline.append([short, "functional",
                             f"{e['sem']}%", f"{e['com']}%",
                             f"{e['sp']}%", f"{e['ag']}%",
                             f"{e['com']-e['sem']:+d}",
                             f"{e['sp']-e['sem']:+d}",
                             f"{e['ag']-e['sem']:+d}"])
        if model in regex_data:
            r = _regex_row(regex_data, model)
            headline.append([short, "regex",
                             f"{r['sem']}%", f"{r['com']}%",
                             f"{r['sp']}%", f"{r['ag']}%",
                             f"{r['com']-r['sem']:+d}",
                             f"{r['sp']-r['sem']:+d}",
                             f"{r['ag']-r['sem']:+d}"])
    t = Table(headline, colWidths=[55*mm, 18*mm, 17*mm, 13*mm, 17*mm, 17*mm,
                                   13*mm, 17*mm, 17*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eaf0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888")),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    # Agents convergence
    story.append(Paragraph("Agents verify-loop convergence", h2))
    story.append(Paragraph(
        "Lower attempts = the model resolved the case earlier; 1 means it "
        "passed on the first try. Max attempts capped per harness.", body))
    conv = [["Model", "Metric", "avg attempts (cli+ag)"]]
    for model in all_models:
        short = model.replace("Qwen/", "")
        if model in exec_data:
            e = _exec_row(exec_data, model)
            conv.append([short, "functional", f"{e['ag_attempts_avg']:.2f}"])
        if model in regex_data:
            r = _regex_row(regex_data, model)
            conv.append([short, "regex", f"{r['ag_attempts_avg']:.2f}"])
    t = Table(conv, colWidths=[80*mm, 25*mm, 40*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eaf0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888")),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    # Cost & latency (functional only)
    story.append(Paragraph("Cost & latency per call (functional bench)", h2))
    story.append(Paragraph(
        "Tokens/call averaged across the 12 cases. cli+ag burns more "
        "tokens AND wall-clock per case because it may run up to 3 attempts.", body))
    cost = [["Model", "Side", "tokens/call", "ms/call"]]
    for model in exec_models:
        short = model.replace("Qwen/", "")
        e = _exec_row(exec_data, model)
        cost.append([short, "baseline", f"{e['sem_tok']:.0f}", f"{e['sem_ms']:.0f}"])
        cost.append([short, "cli", f"{e['com_tok']:.0f}", f"{e['com_ms']:.0f}"])
        cost.append([short, "cli+sp", f"{e['sp_tok']:.0f}", f"{e['sp_ms']:.0f}"])
        cost.append([short, "cli+ag", f"{e['ag_tok']:.0f}", f"{e['ag_ms']:.0f}"])
    t = Table(cost, colWidths=[80*mm, 25*mm, 30*mm, 30*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eaf0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888")),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    # Per-task matrix (functional)
    if exec_models:
        story.append(PageBreak())
        story.append(Paragraph(
            "Per-task &times; model (functional, base / cli / cli+sp / cli+ag)", h2))
        story.append(Paragraph(
            "P = pass, . = fail. cli+ag suffix is the attempt count (1-3). "
            "1 means no feedback loop needed; 3 with . means the loop ran to "
            "exhaustion and still failed (model-capability ceiling).", small))
        sample = next(iter(exec_data.values()))["rows"]
        header = ["Task"] + [m.replace("Qwen/Qwen3-Coder-", "Qwen3-C-")
                             for m in exec_models]
        rows = [header]
        for i, r0 in enumerate(sample):
            cid = r0["id"]
            cells = [cid]
            for m in exec_models:
                r = exec_data[m]["rows"][i]
                cell = ("P" if r["sem"]["passed"] else ".") + "/" + \
                       ("P" if r["com"]["passed"] else ".") + "/" + \
                       ("P" if r.get("sp", {}).get("passed") else ".") + "/" + \
                       ("P" if r.get("ag", {}).get("passed") else ".") + \
                       f"({r.get('ag', {}).get('attempts', 0)})"
                cells.append(cell)
            rows.append(cells)
        t = Table(rows, colWidths=[55*mm] + [55*mm] * len(exec_models))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eaf0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (-1, -1), "Courier"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888")),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))
        story.append(t)

    doc.build(story)
    print(f"-> {OUT_PDF}")


if __name__ == "__main__":
    raise SystemExit(main())
