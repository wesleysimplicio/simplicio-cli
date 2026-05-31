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
