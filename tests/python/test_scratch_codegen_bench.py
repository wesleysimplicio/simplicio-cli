"""Tests for the scratch codegen benchmark harness."""

from __future__ import annotations

from bench.run_scratch_codegen import build_cases, run_benchmark, write_reports


def test_scratch_codegen_bench_cases_cover_python_executors() -> None:
    cases = build_cases(include_typescript=False)

    assert {case.expected_executor for case in cases} == {
        "python-add-fastapi-route",
        "python-add-orm-field",
        "python-add-pydantic-schema",
        "python-add-pytest-test",
    }


def test_scratch_codegen_bench_runs_keyless_python_cases(tmp_path) -> None:
    result = run_benchmark(
        work_dir=tmp_path / "bench",
        repeat=1,
        include_typescript=False,
    )

    summary = result["summary"]
    assert summary["total_cases"] == 4
    assert summary["passed_cases"] == 4
    assert summary["tasks_codegen"] == 4
    assert summary["llm_calls"] == 0
    assert summary["planner_calls"] == 0
    assert summary["post_validated_cases"] == 0
    assert summary["post_validation_failed_cases"] == 0
    assert summary["release_gates"]["llm_baseline_present"] is False
    assert (
        summary["release_gates"]["typescript_next_route_compiles_and_responds_json"]
        is False
    )


def test_scratch_codegen_bench_writes_reports(tmp_path) -> None:
    result = run_benchmark(
        work_dir=tmp_path / "bench",
        repeat=1,
        include_typescript=False,
    )
    json_path = tmp_path / "results.json"
    md_path = tmp_path / "results.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "scratch-codegen"' in json_path.read_text(encoding="utf-8")
    assert "# Scratch Codegen Benchmark" in md_path.read_text(encoding="utf-8")
