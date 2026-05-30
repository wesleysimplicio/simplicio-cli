"""Tests for the scratch recipe benchmark harness."""

from __future__ import annotations

from bench.run_scratch_recipes import (
    RecipeCase,
    build_cases,
    capture_llm_baseline,
    load_llm_baseline,
    run_benchmark,
    write_llm_baseline,
    write_reports,
)


def test_scratch_recipe_bench_defines_fifty_goal_corpus() -> None:
    cases = build_cases()

    assert len(cases) == 50
    assert sum(1 for case in cases if case.expected_match) == 30
    assert {case.stack for case in cases} == {"py-fastapi", "ts-nextjs"}


def test_scratch_recipe_bench_measures_match_rate() -> None:
    result = run_benchmark(
        [
            RecipeCase("py-fastapi", "CRUD API for Unit", True, "crud-resource"),
            RecipeCase("py-fastapi", "Build a websocket gateway", False),
            RecipeCase("ts-nextjs", "authentication with JWT", True, "auth-jwt"),
        ]
    )

    summary = result["summary"]
    assert summary["total_cases"] == 3
    assert summary["matched_cases"] == 2
    assert summary["valid_recipe_plans"] == 2
    assert summary["planner_calls_saved"] == 2
    assert summary["recipe_plan_pass_rate"] == 1.0
    assert summary["release_gates"]["matched_plans_valid"] is True
    assert summary["release_gates"]["recipe_match_ge_40"] is True


def test_scratch_recipe_bench_writes_reports(tmp_path) -> None:
    result = run_benchmark(
        [RecipeCase("py-fastapi", "CRUD API for Unit", True, "crud-resource")]
    )
    json_path = tmp_path / "recipes.json"
    md_path = tmp_path / "recipes.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "scratch-recipes"' in json_path.read_text(encoding="utf-8")
    assert "# Scratch Recipe Benchmark" in md_path.read_text(encoding="utf-8")


def test_scratch_recipe_bench_compares_llm_baseline(tmp_path) -> None:
    result = run_benchmark(
        [RecipeCase("py-fastapi", "CRUD API for Unit", True, "crud-resource")],
        llm_baseline={
            "source": "fixture",
            "summary": {
                "total_cases": 1,
                "pass_rate": 1.0,
                "avg_llm_ms": 10000,
            },
        },
    )

    summary = result["summary"]
    assert summary["release_gates"]["llm_pass_rate_baseline_present"] is True
    assert summary["release_gates"]["llm_baseline_covers_matched_cases"] is True
    assert summary["release_gates"]["recipe_plan_pass_rate_ge_llm"] is True
    assert summary["llm_baseline"]["source"] == "fixture"
    assert "recipe path pass-rate compared" not in "\n".join(
        summary["missing_release_evidence"]
    )


def test_scratch_recipe_bench_captures_planner_llm_baseline(
    tmp_path,
    monkeypatch,
) -> None:
    import json

    from simplicio.scratch.plan_schema import EXAMPLE_PLAN

    calls: list[str] = []

    def fake_planner_complete(
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.1,
        template_version: str | None = None,
    ) -> str:
        calls.append(prompt)
        payload = dict(EXAMPLE_PLAN)
        payload["stack"] = "py-fastapi"
        payload["project_name"] = "crud-api-for-unit"
        return json.dumps(payload)

    monkeypatch.setenv("SIMPLICIO_PLANNER", "codex-cli/default")
    monkeypatch.setattr(
        "simplicio.scratch.planner.planner_complete",
        fake_planner_complete,
    )

    baseline = capture_llm_baseline(
        work_dir=tmp_path / "baseline",
        cases=[RecipeCase("py-fastapi", "CRUD API for Unit", True, "crud-resource")],
    )

    summary = baseline["summary"]
    assert summary["total_cases"] == 1
    assert summary["passed_cases"] == 1
    assert summary["pass_rate"] == 1.0
    assert summary["avg_llm_ms"] >= 0
    assert calls

    baseline_path = tmp_path / "recipes-baseline.json"
    write_llm_baseline(baseline, baseline_path)
    loaded = load_llm_baseline(baseline_path)
    assert loaded["total_cases"] == 1
    assert loaded["pass_rate"] == 1.0
