"""Tests for the static fixer benchmark harness."""

from __future__ import annotations

import subprocess

from bench.run_static_fixers import (
    build_cases,
    run_benchmark,
    run_real_package_manager_probe,
    write_reports,
)


def test_static_fixer_bench_cases_have_expected_mix() -> None:
    cases = build_cases()

    assert len(cases) == 50
    assert sum(1 for case in cases if case.resolvable) == 40
    assert sum(1 for case in cases if not case.resolvable) == 10


def test_static_fixer_bench_measures_retry_reduction(tmp_path) -> None:
    result = run_benchmark(work_dir=tmp_path / "bench")
    summary = result["summary"]

    assert summary["total_cases"] == 50
    assert summary["passed_cases"] == 50
    assert summary["fixer_resolved_before_retry"] == 40
    assert summary["fixer_resolved_rate"] == 0.8
    assert summary["baseline_llm_calls"] == 100
    assert summary["with_fixer_llm_calls"] == 60
    assert summary["retry_call_reduction"] == 0.4
    assert summary["release_gates"]["real_package_manager_execution"] is False
    assert summary["release_gates"]["real_scratch_corpus"] is False


def test_static_fixer_bench_writes_reports(tmp_path) -> None:
    result = run_benchmark(work_dir=tmp_path / "bench")
    json_path = tmp_path / "results.json"
    md_path = tmp_path / "results.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "static-fixers"' in json_path.read_text(encoding="utf-8")
    assert "# Static Fixers Benchmark" in md_path.read_text(encoding="utf-8")


def test_static_fixer_bench_real_package_probe_uses_runner(tmp_path) -> None:
    calls: list[list[str]] = []

    def fake_runner(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "", "")

    rows = run_real_package_manager_probe(
        work_dir=tmp_path / "real-probe",
        repeat=1,
        runner=fake_runner,
    )

    assert len(rows) == 5
    assert all(row["passed"] for row in rows)
    assert any("pip" in " ".join(call) for call in calls)


def test_static_fixer_bench_records_real_probe_summary(tmp_path) -> None:
    result = run_benchmark(
        work_dir=tmp_path / "bench",
        real_package_manager_probe=True,
        real_probe_repeat=0,
    )

    summary = result["summary"]
    assert summary["real_package_manager_cases"] == 0
    assert summary["release_gates"]["real_package_manager_execution"] is False
