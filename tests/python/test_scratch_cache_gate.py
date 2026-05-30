"""Tests for the scratch planner cache gate benchmark."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from bench.run_scratch_cache_gate import run_cache_gate, write_reports
from simplicio._cache import reset_for_tests
from simplicio.scratch.plan_schema import EXAMPLE_PLAN


def _planner_json() -> str:
    payload = dict(EXAMPLE_PLAN)
    payload["project_name"] = "cache-plan"
    return json.dumps(payload)


def test_scratch_cache_gate_measures_warm_hits(tmp_path, monkeypatch) -> None:
    calls: list[str] = []

    def fake_shell_out(prompt: str, model: str) -> str:
        calls.append(prompt)
        return _planner_json()

    monkeypatch.setenv("SIMPLICIO_PLANNER", "codex-cli/default")
    monkeypatch.setenv("SIMPLICIO_CACHE_DIR", str(tmp_path / "outer-cache"))
    monkeypatch.setattr("simplicio.providers._shell_out_codex", fake_shell_out)
    reset_for_tests()

    result = run_cache_gate(
        work_dir=tmp_path / "bench",
        goals=(
            "Build a FastAPI audit log service with export filters",
            "Build a FastAPI webhook ingestion service with replay controls",
        ),
    )

    summary = result["summary"]
    assert summary["cold_plans_valid"] == 2
    assert summary["warm_plans_valid"] == 2
    assert summary["warm_hit_rate"] == 1.0
    assert summary["release_gates"]["warm_hit_rate_ge_80"] is True
    assert summary["release_gates"]["cold_populated_cache"] is True
    assert len(calls) == 2


def test_scratch_cache_gate_writes_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIMPLICIO_PLANNER", "codex-cli/default")
    monkeypatch.setattr(
        "simplicio.providers._shell_out_codex",
        MagicMock(return_value=_planner_json()),
    )
    result = run_cache_gate(
        work_dir=tmp_path / "bench",
        goals=("Build a FastAPI cache fixture service",),
    )
    json_path = tmp_path / "cache.json"
    md_path = tmp_path / "cache.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "scratch-cache-gate"' in json_path.read_text(encoding="utf-8")
    assert "# Scratch Planner Cache Gate" in md_path.read_text(encoding="utf-8")
