"""Tests for the scratch recipe benchmark harness."""

from __future__ import annotations

from bench.run_scratch_recipes import (
    RecipeCase,
    build_cases,
    run_benchmark,
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
