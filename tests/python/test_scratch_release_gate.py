"""Tests for the scratch release-gate preflight harness."""

from __future__ import annotations

from bench.run_scratch_release_gate import (
    PILOT_STACKS,
    RELEASE_GOALS,
    run_preflight,
    write_reports,
)


def test_release_gate_preflight_defines_full_matrix(monkeypatch) -> None:
    monkeypatch.delenv("SIMPLICIO_MODEL", raising=False)
    monkeypatch.delenv("SIMPLICIO_PLANNER", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)

    result = run_preflight()

    assert result["gate"]["goals"] == 15
    assert result["gate"]["pilot_stacks"] == 5
    assert result["gate"]["planned_runs"] == len(RELEASE_GOALS) * len(PILOT_STACKS)
    assert {row["stack"] for row in result["stacks"]} == set(PILOT_STACKS)
    assert result["summary"]["ready_for_live_gate"] is False
    assert result["summary"]["blocker_count"] >= 2


def test_release_gate_preflight_writes_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("SIMPLICIO_MODEL", raising=False)
    monkeypatch.delenv("SIMPLICIO_PLANNER", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    result = run_preflight()
    json_path = tmp_path / "release-gate.json"
    md_path = tmp_path / "release-gate.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "scratch-release-gate"' in json_path.read_text(
        encoding="utf-8"
    )
    assert "# Scratch Release Gate Preflight" in md_path.read_text(encoding="utf-8")
