"""Tests for the scratch codegen benchmark harness."""

from __future__ import annotations

from bench.run_scratch_codegen import (
    build_cases,
    capture_llm_baseline,
    load_llm_baseline,
    run_benchmark,
    write_llm_baseline,
    write_reports,
)


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


def test_scratch_codegen_bench_compares_captured_llm_baseline(tmp_path) -> None:
    result = run_benchmark(
        work_dir=tmp_path / "bench",
        repeat=1,
        include_typescript=False,
        llm_baseline={
            "source": "fixture",
            "summary": {
                "total_cases": 4,
                "pass_rate": 0.75,
                "avg_llm_ms": 10000,
            },
        },
    )

    summary = result["summary"]
    assert summary["release_gates"]["llm_baseline_present"] is True
    assert summary["release_gates"]["executor_pass_rate_ge_llm"] is True
    assert summary["release_gates"]["latency_reduction_ge_50"] is True
    assert summary["llm_baseline"]["source"] == "fixture"
    assert "LLM baseline pass-rate" not in "\n".join(
        summary["missing_release_evidence"]
    )


def test_scratch_codegen_bench_loads_baseline_file(tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        '{"summary": {"total_cases": 10, "pass_rate": 0.8, "avg_llm_ms": 9000}}',
        encoding="utf-8",
    )

    baseline = load_llm_baseline(baseline_path)

    assert baseline["total_cases"] == 10
    assert baseline["pass_rate"] == 0.8
    assert baseline["avg_llm_ms"] == 9000


def test_scratch_codegen_bench_captures_llm_baseline_without_codegen(
    tmp_path,
    monkeypatch,
) -> None:
    from simplicio import pipeline

    generate_calls: list[str] = []

    def fake_generate(prompt: str, feedback: str | None = None) -> str:
        generate_calls.append(prompt)
        return "\n".join(
            [
                "diff --git a/src/app.py b/src/app.py",
                "--- a/src/app.py",
                "+++ b/src/app.py",
                "@@ -0,0 +1 @@",
                "+print('ok')",
                "",
                "TEST: pytest -q",
            ]
        )

    def fake_apply_and_test(output, root, bound_paths=None):
        return True, "baseline passed"

    monkeypatch.setenv("SIMPLICIO_MODEL", "fake-llm/baseline")
    monkeypatch.setattr(pipeline, "generate", fake_generate)
    monkeypatch.setattr(pipeline, "_apply_and_test", fake_apply_and_test)

    baseline = capture_llm_baseline(
        work_dir=tmp_path / "baseline",
        repeat=1,
        include_typescript=False,
    )

    summary = baseline["summary"]
    assert summary["total_cases"] == 4
    assert summary["passed_cases"] == 4
    assert summary["pass_rate"] == 1.0
    assert summary["avg_llm_ms"] >= 0
    assert summary["model"] == "fake-llm/baseline"
    assert len(generate_calls) == 4
    assert all(row["execution_mode"] == "llm" for row in baseline["cases"])

    baseline_path = tmp_path / "captured-baseline.json"
    write_llm_baseline(baseline, baseline_path)
    loaded = load_llm_baseline(baseline_path)
    assert loaded["pass_rate"] == 1.0
    assert loaded["avg_llm_ms"] > 0


def test_scratch_codegen_bench_requires_model_for_baseline(tmp_path, monkeypatch):
    monkeypatch.delenv("SIMPLICIO_MODEL", raising=False)

    try:
        capture_llm_baseline(
            work_dir=tmp_path / "baseline",
            repeat=1,
            include_typescript=False,
        )
    except RuntimeError as exc:
        assert "SIMPLICIO_MODEL" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected missing model to block baseline capture")


def test_scratch_codegen_bench_writes_captured_baseline(tmp_path, monkeypatch) -> None:
    baseline = {
        "benchmark": "scratch-codegen-llm-baseline",
        "summary": {
            "total_cases": 4,
            "pass_rate": 0.5,
            "avg_llm_ms": 12000,
        },
    }
    json_path = tmp_path / "baseline.json"

    write_llm_baseline(baseline, json_path)
    loaded = load_llm_baseline(json_path)

    assert loaded["total_cases"] == 4
    assert loaded["pass_rate"] == 0.5
    assert loaded["avg_llm_ms"] == 12000
