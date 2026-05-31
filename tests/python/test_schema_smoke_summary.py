from __future__ import annotations

import json

from bench.run_schema_smoke_summary import main, summarize_smokes, write_reports


def test_schema_smoke_summary_normalizes_supported_formats(tmp_path):
    schema_v1 = tmp_path / "results_v14_qwen15b_q8_0_smoke_schema_v1.json"
    schema_v1.write_text(
        json.dumps(
            {
                "benchmark": "schema-v1-smoke",
                "model": "Qwen2.5-Coder-1.5B-Instruct",
                "quant": "Q8_0",
                "calls": 4,
                "go_no_go": {"pass": True},
                "summary": {"parse_ok": 2, "parse_failed": 2},
            }
        ),
        encoding="utf-8",
    )
    legacy_flat = tmp_path / "results_sp_schema_smoke_qwen3b.json"
    legacy_flat.write_text(
        json.dumps(
            {
                "model": "Qwen/Qwen2.5-Coder-3B-Instruct",
                "N": 4,
                "parse_ok_count": 4,
                "parse_failed_count": 0,
            }
        ),
        encoding="utf-8",
    )
    legacy_escalation = tmp_path / "results_sp_schema_smoke_deepseek.json"
    legacy_escalation.write_text(
        json.dumps(
            {
                "model": "deepseek/deepseek-v4-flash",
                "result": {"parse_ok": 3, "parse_fail": 1},
            }
        ),
        encoding="utf-8",
    )

    summary = summarize_smokes([schema_v1, legacy_flat, legacy_escalation])

    assert summary["summary"]["input_files"] == 3
    assert summary["summary"]["go_no_go_passes"] == 3
    assert summary["summary"]["qwen15b_smokes"] == 1
    assert summary["summary"]["release_ready"] is False
    assert {row["format"] for row in summary["rows"]} == {
        "schema-v1-smoke",
        "legacy-flat",
        "legacy-escalation",
    }


def test_schema_smoke_summary_writes_reports(tmp_path):
    smoke = tmp_path / "smoke.json"
    smoke.write_text(
        json.dumps(
            {
                "model": "qwen",
                "N": 4,
                "parse_ok_count": 1,
                "parse_failed_count": 3,
            }
        ),
        encoding="utf-8",
    )
    summary = summarize_smokes([smoke])
    json_path = tmp_path / "summary.json"
    md_path = tmp_path / "summary.md"

    write_reports(summary, json_path, md_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["benchmark"] == (
        "schema-smoke-summary"
    )
    md = md_path.read_text(encoding="utf-8")
    assert "# Schema Smoke Summary" in md
    assert "release ready: False" in md


def test_schema_smoke_summary_main_accepts_inputs(tmp_path):
    smoke = tmp_path / "smoke.json"
    smoke.write_text(
        json.dumps(
            {
                "model": "qwen",
                "N": 4,
                "parse_ok_count": 4,
                "parse_failed_count": 0,
            }
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"

    rc = main(
        [
            "--inputs",
            str(smoke),
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--quiet",
        ]
    )

    assert rc == 0
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"][
        "go_no_go_passes"
    ] == 1
