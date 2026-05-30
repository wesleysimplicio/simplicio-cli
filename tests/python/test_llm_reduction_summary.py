"""Tests for the aggregate LLM-reduction evidence report."""

from __future__ import annotations

import json

from bench.run_llm_reduction_summary import run_summary, write_reports


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fixtures(tmp_path):
    cache = tmp_path / "cache.json"
    fixers = tmp_path / "fixers.json"
    recipes = tmp_path / "recipes.json"
    codegen = tmp_path / "codegen.json"
    preflight = tmp_path / "preflight.json"
    _write_json(
        cache,
        {
            "benchmark": "scratch-cache-gate",
            "summary": {
                "warm_hit_rate": 1.0,
                "warm_hits": 2,
                "warm_misses": 0,
                "release_gates": {
                    "warm_hit_rate_ge_80": True,
                    "warm_plans_all_valid": True,
                    "real_50_scratch_corpus": False,
                },
                "missing_release_evidence": ["50 real scratch goals"],
            },
        },
    )
    _write_json(
        fixers,
        {
            "benchmark": "static-fixers",
            "summary": {
                "fixer_resolved_rate": 0.8,
                "retry_call_reduction": 0.4,
                "baseline_llm_calls": 100,
                "with_fixer_llm_calls": 60,
                "release_gates": {
                    "fixer_resolved_ge_80": True,
                    "retry_calls_down_ge_30": True,
                    "real_scratch_corpus": False,
                },
            },
        },
    )
    _write_json(
        recipes,
        {
            "benchmark": "scratch-recipes",
            "summary": {
                "match_rate": 0.6,
                "matched_cases": 30,
                "total_cases": 50,
                "planner_calls_saved": 30,
                "release_gates": {
                    "recipe_match_ge_40": True,
                    "matched_plans_valid": True,
                    "real_scratch_corpus": False,
                    "llm_pass_rate_baseline_present": False,
                },
            },
        },
    )
    _write_json(
        codegen,
        {
            "benchmark": "scratch-codegen",
            "summary": {
                "codegen_share": 1.0,
                "pass_rate": 1.0,
                "avg_codegen_ms": 71,
                "tasks_codegen": 50,
                "total_tasks": 50,
                "release_gates": {
                    "mechanical_share_ge_30": True,
                    "executor_pass_rate_100": True,
                    "typescript_next_route_compiles_and_responds_json": True,
                    "llm_baseline_present": False,
                    "executor_pass_rate_ge_llm": None,
                    "latency_reduction_ge_50": None,
                },
                "missing_release_evidence": ["LLM baseline pass-rate"],
            },
        },
    )
    _write_json(
        preflight,
        {
            "benchmark": "scratch-release-gate",
            "summary": {
                "ready_for_live_gate": True,
                "blocker_count": 0,
                "blockers": [],
            },
        },
    )
    return {
        "cache": cache,
        "static_fixers": fixers,
        "recipes": recipes,
        "codegen": codegen,
        "preflight": preflight,
    }


def test_llm_reduction_summary_keeps_release_gap_explicit(tmp_path) -> None:
    result = run_summary(_fixtures(tmp_path))

    summary = result["summary"]
    assert summary["local_synthetic_gates_pass"] is True
    assert summary["release_evidence_complete"] is False
    assert summary["target_reduction_met"] is False
    assert summary["modeled_baseline_calls"] == 19
    assert summary["modeled_final_calls"] == 6
    assert summary["modeled_reduction"] == 0.6842
    assert result["levers"]["B_codegen"]["llm_baseline_present"] is False
    assert any(
        "captured LLM baseline" in item for item in summary["missing_release_evidence"]
    )


def test_llm_reduction_summary_marks_missing_inputs(tmp_path) -> None:
    paths = _fixtures(tmp_path)
    paths["codegen"] = tmp_path / "missing-codegen.json"

    result = run_summary(paths)

    assert result["inputs"]["codegen"]["present"] is False
    assert result["summary"]["local_synthetic_gates_pass"] is False
    assert result["summary"]["modeled_final_calls"] == 16


def test_llm_reduction_summary_writes_reports(tmp_path) -> None:
    result = run_summary(_fixtures(tmp_path))
    json_path = tmp_path / "summary.json"
    md_path = tmp_path / "summary.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "llm-reduction-summary"' in json_path.read_text(
        encoding="utf-8"
    )
    assert "# LLM Reduction Summary" in md_path.read_text(encoding="utf-8")
