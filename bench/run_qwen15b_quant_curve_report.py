"""Build the Qwen2.5-Coder-1.5B GGUF quant-curve report for issue #46.

This script only writes final release artifacts after every required smoke JSON
from the manifest is present and passing. Missing smokes are reported as
blockers instead of producing placeholder quant-curve outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "bench" / "qwen15b_quant_curve_manifest.json"
RESULTS_JSON = ROOT / "bench" / "results_v14_qwen15b_quant_curve.json"
RESULTS_MD = ROOT / "bench" / "results_v14_qwen15b_quant_curve.md"
RESULTS_PDF = ROOT / "bench" / "results_v14_qwen15b_quant_curve.pdf"


def build_report(manifest_path: Path = MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [_smoke_row(item) for item in manifest["required_quants"]]
    required_present = {row["quant"]: row["present"] for row in rows}
    required_passed = {row["quant"]: row["go_no_go_pass"] is True for row in rows}
    missing = [row["quant"] for row in rows if not row["present"]]
    failed = [
        row["quant"]
        for row in rows
        if row["present"] and row["go_no_go_pass"] is not True
    ]
    release_ready = not missing and not failed
    return {
        "benchmark": "qwen15b-quant-curve",
        "issue": 46,
        "scope": (
            "final Qwen2.5-Coder-1.5B GGUF quant curve assembled from "
            "manifest-declared schema-v1 smoke artifacts"
        ),
        "date": time.strftime("%Y-%m-%d"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "manifest": {
            "path": _relative(manifest_path),
            "source_repo": manifest.get("source_repo"),
            "model_family": manifest.get("model_family"),
            "required_quants": [item["quant"] for item in manifest["required_quants"]],
            "final_artifacts": manifest.get("final_artifacts", []),
        },
        "rows": rows,
        "summary": {
            "required_quant_smokes_present": required_present,
            "required_quant_smokes_passed": required_passed,
            "missing_quant_smokes": missing,
            "failed_required_quant_smokes": failed,
            "qwen15b_quant_curve_complete": release_ready,
            "release_ready": release_ready,
            "missing_release_evidence": _missing_release_evidence(missing, failed),
        },
    }


def _smoke_row(item: dict[str, Any]) -> dict[str, Any]:
    smoke_path = ROOT / item["smoke_json"]
    base = {
        "quant": item["quant"],
        "filename": item["filename"],
        "smoke_json": item["smoke_json"],
        "smoke_command": item["smoke_command"],
        "present": smoke_path.is_file(),
        "sha256": "",
        "benchmark": "",
        "model": "",
        "calls": 0,
        "parse_ok": 0,
        "parse_failed": 0,
        "parse_ok_rate": 0.0,
        "go_no_go_pass": False,
        "error": "",
    }
    if not smoke_path.is_file():
        return base | {"error": "missing smoke JSON"}

    raw = smoke_path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        return base | {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "error": f"invalid JSON: {exc}",
        }

    calls = _int(payload.get("calls") or payload.get("N"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    parse_ok = _int(summary.get("parse_ok") or payload.get("parse_ok_count"))
    parse_failed = _int(
        summary.get("parse_failed")
        or payload.get("parse_failed_count")
        or max(0, calls - parse_ok)
    )
    go_no_go = payload.get("go_no_go")
    if isinstance(go_no_go, dict) and "pass" in go_no_go:
        passed = go_no_go.get("pass") is True
    else:
        passed = parse_ok >= max(1, math.ceil(calls / 2)) if calls else False
    quant = str(payload.get("quant") or "")
    if quant and quant != item["quant"]:
        return base | {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "benchmark": str(payload.get("benchmark") or ""),
            "model": str(payload.get("model") or payload.get("model_spec") or ""),
            "calls": calls,
            "parse_ok": parse_ok,
            "parse_failed": parse_failed,
            "parse_ok_rate": _rate(parse_ok, calls),
            "go_no_go_pass": False,
            "error": f"smoke quant {quant!r} does not match manifest quant {item['quant']!r}",
        }

    return base | {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "benchmark": str(payload.get("benchmark") or ""),
        "model": str(payload.get("model") or payload.get("model_spec") or ""),
        "calls": calls,
        "parse_ok": parse_ok,
        "parse_failed": parse_failed,
        "parse_ok_rate": _rate(parse_ok, calls),
        "go_no_go_pass": passed,
    }


def _missing_release_evidence(missing: list[str], failed: list[str]) -> list[str]:
    blockers = []
    if missing:
        blockers.append("missing schema-v1 smoke JSONs: " + ", ".join(missing))
    if failed:
        blockers.append("failing schema-v1 smoke JSONs: " + ", ".join(failed))
    if blockers:
        blockers.append(
            "bench/results_v14_qwen15b_quant_curve.{json,md,pdf} not written"
        )
    return blockers


def write_reports(report: dict[str, Any], json_path: Path, md_path: Path, pdf_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(report), encoding="utf-8")
    _write_minimal_pdf(pdf_path, _pdf_lines(report))


def _to_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Qwen 1.5B Quant Curve",
        "",
        report["scope"],
        "",
        "## Summary",
        "",
        f"- release ready: {summary['release_ready']}",
        f"- quant curve complete: {summary['qwen15b_quant_curve_complete']}",
        "- required quant smokes present: "
        + ", ".join(
            f"{quant}={present}"
            for quant, present in summary["required_quant_smokes_present"].items()
        ),
        "- required quant smokes passed: "
        + ", ".join(
            f"{quant}={passed}"
            for quant, passed in summary["required_quant_smokes_passed"].items()
        ),
        f"- missing quant smokes: {', '.join(summary['missing_quant_smokes']) or 'none'}",
        "- failed required quant smokes: "
        + (", ".join(summary["failed_required_quant_smokes"]) or "none"),
        "",
        "## Rows",
        "",
        "| quant | smoke JSON | calls | parse ok | parse failed | pass | sha256 |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report["rows"]:
        sha = row["sha256"][:12] if row["sha256"] else ""
        lines.append(
            f"| {row['quant']} | `{row['smoke_json']}` | {row['calls']} | "
            f"{row['parse_ok']} | {row['parse_failed']} | "
            f"{row['go_no_go_pass']} | `{sha}` |"
        )
    if summary["missing_release_evidence"]:
        lines.extend(["", "## Missing Release Evidence", ""])
        lines.extend(f"- {item}" for item in summary["missing_release_evidence"])
    lines.append("")
    return "\n".join(lines)


def _pdf_lines(report: dict[str, Any]) -> list[str]:
    summary = report["summary"]
    lines = [
        "Qwen 1.5B Quant Curve",
        f"release ready: {summary['release_ready']}",
        f"missing: {', '.join(summary['missing_quant_smokes']) or 'none'}",
        f"failed: {', '.join(summary['failed_required_quant_smokes']) or 'none'}",
    ]
    for row in report["rows"]:
        lines.append(
            f"{row['quant']}: pass={row['go_no_go_pass']} "
            f"parse_ok={row['parse_ok']}/{row['calls']}"
        )
    return lines


def _write_minimal_pdf(path: Path, lines: list[str]) -> None:
    text = ["BT", "/F1 12 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        if index:
            text.append("0 -18 Td")
        text.append(f"({_pdf_escape(line)}) Tj")
    text.append("ET")
    stream = "\n".join(text).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{number} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(content)


def _pdf_escape(value: str) -> str:
    return (
        value.encode("ascii", errors="replace")
        .decode("ascii")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _rate(parse_ok: int, calls: int) -> float:
    return round(parse_ok / max(calls, 1), 4)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument("--pdf-output", type=Path, default=RESULTS_PDF)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check readiness without writing final quant-curve artifacts.",
    )
    parser.add_argument(
        "--write-incomplete",
        action="store_true",
        help="Write diagnostic outputs even when required smokes are missing or failing.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.manifest)
    release_ready = report["summary"]["release_ready"] is True
    if not args.quiet:
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if args.check:
        return 0 if release_ready else 1
    if release_ready or args.write_incomplete:
        write_reports(report, args.json_output, args.md_output, args.pdf_output)
        if not args.quiet:
            print(f"wrote {args.json_output}")
            print(f"wrote {args.md_output}")
            print(f"wrote {args.pdf_output}")
    return 0 if release_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
