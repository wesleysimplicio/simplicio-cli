"""Tests for the fixture-backed unified run F5 bench report."""

from __future__ import annotations

import json

from bench.run_unified_run_bench import (
    main,
    run_benchmark,
    write_partial_results,
    write_reports,
)


def test_unified_run_bench_fixture_covers_required_modes() -> None:
    result = run_benchmark()

    mode_ids = {mode["mode_id"] for mode in result["modes"]}
    assert result["benchmark"] == "unified-run-f5-fixture"
    assert result["issue"] == "#41"
    assert result["phase"] == "F5"
    assert mode_ids == {
        "cli_ag",
        "unified_feature",
        "unified_sprint",
        "codex_goal",
    }
    assert result["summary"]["fixture_only"] is True
    assert result["summary"]["evidence_level"] == "fixture"
    assert result["summary"]["schema_fixture_complete"] is True
    assert result["summary"]["real_llm_runs_present"] is False
    assert result["summary"]["external_codex_goal_run_present"] is False
    assert result["summary"]["release_ready"] is False
    assert result["summary"]["release_blockers"]


def test_unified_run_bench_records_expected_tradeoffs() -> None:
    result = run_benchmark()
    by_mode = result["summary"]["by_mode"]

    assert by_mode["cli_ag"]["manual_decomposition_cases"] == 2
    assert by_mode["cli_ag"]["replan_supported_cases"] == 0
    assert by_mode["unified_feature"]["replan_supported_cases"] == 2
    assert by_mode["unified_sprint"]["resume_state_supported_cases"] == 1
    assert by_mode["unified_sprint"]["cost_cap_required_cases"] == 1
    assert by_mode["codex_goal"]["cost_observable_cases"] == 0
    assert any(
        "Codex /goal baseline" in item
        for item in result["summary"]["missing_live_evidence"]
    )


def test_unified_run_bench_writes_reports(tmp_path) -> None:
    result = run_benchmark()
    json_path = tmp_path / "unified.json"
    md_path = tmp_path / "unified.md"

    write_reports(result, json_path, md_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    md = md_path.read_text(encoding="utf-8")
    assert payload["benchmark"] == "unified-run-f5-fixture"
    assert "# Unified Run F5 Bench Fixture" in md
    assert "cli+ag task loop" in md
    assert "Codex /goal" in md


def test_unified_run_bench_writes_partial_only_results(tmp_path) -> None:
    result = run_benchmark()
    partial_path = tmp_path / "partial.json"

    write_partial_results(result, partial_path)

    payload = json.loads(partial_path.read_text(encoding="utf-8"))
    assert payload["artifact"] == "partial-live-observations"
    assert payload["partial_only"] is True
    assert payload["release_evidence"] is False
    assert payload["release_ready"] is False
    assert payload["evidence_level"] == "partial-only"
    assert payload["source_evidence_level"] == "fixture"
    assert payload["observation_count"] == 9
    assert payload["observations"]
    assert all(
        observation["mode_id"] != "codex_goal"
        for observation in payload["observations"]
    )


def test_unified_run_bench_ingests_partial_live_results() -> None:
    result = run_benchmark(
        live_results=[
            {
                "case_id": "single-file-task",
                "mode_id": "cli_ag",
                "command": "simplicio task fix src/app.py",
                "exit_code": 0,
                "success": True,
                "duration_s": 1.2,
                "cost_usd": 0.0,
            }
        ]
    )

    live_row = next(row for row in result["rows"] if row["fixture"] is False)
    assert result["benchmark"] == "unified-run-f5-fixture"
    assert result["fixture_only"] is False
    assert result["summary"]["evidence_level"] == "partial-live"
    assert result["summary"]["live_row_count"] == 1
    assert result["summary"]["release_ready"] is False
    assert live_row["case_id"] == "single-file-task"
    assert live_row["success"] is True


def test_unified_run_bench_marks_complete_live_matrix_release_ready() -> None:
    live_results = []
    for case in run_benchmark()["cases"]:
        for mode in ("cli_ag", "unified_feature", "unified_sprint", "codex_goal"):
            live_results.append(
                {
                    "case_id": case["case_id"],
                    "mode_id": mode,
                    "command": f"run {case['case_id']} {mode}",
                    "exit_code": 0,
                    "success": True,
                    "duration_s": 1.0,
                    "llm_invoked": mode != "cli_ag",
                    "external_agent_invoked": mode == "codex_goal",
                    "transcript_sha256": "a" * 64 if mode == "codex_goal" else "",
                    "artifacts": ["dod.json"] if case["scope"] == "sprint" else [],
                }
            )

    result = run_benchmark(live_results=live_results)

    assert result["benchmark"] == "unified-run-f5-live"
    assert result["summary"]["evidence_level"] == "live"
    assert result["summary"]["live_row_count"] == result["summary"]["expected_row_count"]
    assert result["summary"]["external_codex_goal_run_present"] is True
    assert result["summary"]["release_ready"] is True
    assert result["summary"]["release_blockers"] == []


def test_unified_run_bench_requires_valid_codex_transcript_hash() -> None:
    live_results = []
    for case in run_benchmark()["cases"]:
        for mode in ("cli_ag", "unified_feature", "unified_sprint", "codex_goal"):
            live_results.append(
                {
                    "case_id": case["case_id"],
                    "mode_id": mode,
                    "command": f"run {case['case_id']} {mode}",
                    "exit_code": 0,
                    "success": True,
                    "duration_s": 1.0,
                    "llm_invoked": mode != "cli_ag",
                    "external_agent_invoked": mode == "codex_goal",
                    "transcript_sha256": "not-a-sha" if mode == "codex_goal" else "",
                    "artifacts": ["dod.json"] if case["scope"] == "sprint" else [],
                }
            )

    result = run_benchmark(live_results=live_results)

    assert result["summary"]["evidence_level"] == "partial-live"
    assert result["summary"]["external_codex_goal_run_present"] is False
    assert result["summary"]["release_ready"] is False
    assert "Codex /goal live row needs transcript hash" in result["summary"][
        "release_blockers"
    ]


def test_unified_run_bench_rejects_duplicate_live_rows() -> None:
    result = run_benchmark(
        live_results=[
            {
                "case_id": "single-file-task",
                "mode_id": "cli_ag",
                "command": "simplicio task fix src/app.py",
                "exit_code": 0,
                "success": True,
                "duration_s": 1.2,
            },
            {
                "case_id": "single-file-task",
                "mode_id": "cli_ag",
                "command": "simplicio task fix src/app.py",
                "exit_code": 0,
                "success": True,
                "duration_s": 1.3,
            },
        ]
    )

    assert result["summary"]["live_row_count"] == 1
    assert result["summary"]["release_ready"] is False
    assert result["summary"]["live_result_errors"] == [
        "live row 2 duplicates case/mode: single-file-task/cli_ag"
    ]


def test_unified_run_bench_rejects_inconsistent_live_success() -> None:
    result = run_benchmark(
        live_results=[
            {
                "case_id": "single-file-task",
                "mode_id": "cli_ag",
                "command": "simplicio task fix src/app.py",
                "exit_code": 1,
                "success": True,
                "duration_s": 1.2,
            }
        ]
    )

    assert result["summary"]["live_row_count"] == 0
    assert result["summary"]["live_result_errors"] == [
        "live row 1 success must match exit_code==0"
    ]


def test_unified_run_bench_rejects_invalid_live_timing_and_cost() -> None:
    result = run_benchmark(
        live_results=[
            {
                "case_id": "single-file-task",
                "mode_id": "cli_ag",
                "command": "simplicio task fix src/app.py",
                "exit_code": 0,
                "success": True,
                "duration_s": -1,
            },
            {
                "case_id": "feature-auth-flow",
                "mode_id": "unified_feature",
                "command": "simplicio run --scope feature",
                "exit_code": 0,
                "success": True,
                "duration_s": 1.0,
                "cost_usd": -0.01,
            },
        ]
    )

    assert result["summary"]["live_row_count"] == 0
    assert result["summary"]["live_result_errors"] == [
        "live row 1 duration_s must be finite and >= 0",
        "live row 2 cost_usd must be finite and >= 0",
    ]


def test_unified_run_bench_main_accepts_custom_fixture(tmp_path) -> None:
    fixture = tmp_path / "cases.json"
    fixture.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "custom-feature",
                        "scope": "feature",
                        "goal": "Implement audit exports.",
                        "expected_tasks": 3,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"

    rc = main(
        [
            "--fixture-json",
            str(fixture),
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--quiet",
        ]
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["summary"]["case_count"] == 1
    assert payload["summary"]["row_count"] == 4
    assert "custom-feature" in md_path.read_text(encoding="utf-8")


def test_unified_run_bench_main_writes_partial_results_json(tmp_path) -> None:
    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"
    partial_path = tmp_path / "partial.json"

    rc = main(
        [
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--partial-results-json",
            str(partial_path),
            "--quiet",
        ]
    )

    main_payload = json.loads(json_path.read_text(encoding="utf-8"))
    partial_payload = json.loads(partial_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert main_payload["summary"]["evidence_level"] == "fixture"
    assert main_payload["summary"]["release_ready"] is False
    assert partial_payload["partial_only"] is True
    assert partial_payload["release_evidence"] is False


def test_unified_run_bench_main_accepts_live_results(tmp_path) -> None:
    json_path = tmp_path / "out.json"
    md_path = tmp_path / "out.md"
    live_path = tmp_path / "live.json"
    live_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "case_id": "single-file-task",
                        "mode_id": "cli_ag",
                        "command": "simplicio task fix src/app.py",
                        "exit_code": 0,
                        "success": True,
                        "duration_s": 1.0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    rc = main(
        [
            "--live-results-json",
            str(live_path),
            "--json-output",
            str(json_path),
            "--md-output",
            str(md_path),
            "--quiet",
        ]
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["summary"]["evidence_level"] == "partial-live"
    assert payload["summary"]["live_row_count"] == 1
