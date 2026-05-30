"""Tests for the live scratch gate runner."""

from __future__ import annotations

import json
import subprocess

from bench.run_scratch_live_gate import (
    _parse_json_stdout,
    run_live_gate,
    write_reports,
)


def _completed(cmd, stdout, returncode=0):
    return subprocess.CompletedProcess(cmd, returncode, stdout, "")


def test_live_gate_runs_plan_only_slice(tmp_path) -> None:
    calls = []

    def fake_runner(cmd, **_kwargs):
        calls.append(cmd)
        assert "--plan-only" in cmd
        return _completed(
            cmd,
            json.dumps(
                {
                    "project_name": "gate-g01-py-fastapi",
                    "tasks": [{"id": "T01", "goal": "add model"}],
                }
            ),
        )

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi", "ts-nextjs"),
        goals=("CRUD app for condo units",),
        max_runs=1,
        plan_only=True,
        runner=fake_runner,
    )

    summary = result["summary"]
    assert len(calls) == 1
    assert result["matrix"]["selected_runs"] == 1
    assert result["matrix"]["release_planned_runs"] == 75
    assert summary["planner_valid"] == 1
    assert summary["planner_valid_rate"] == 1.0
    assert summary["release_gates"]["scaffold_clean_ge_95"] is None
    assert summary["release_gates"]["release_ready"] is False


def test_live_gate_runs_execution_slice(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
        assert "--plan-only" not in cmd
        return _completed(
            cmd,
            json.dumps(
                {
                    "files_written": ["src/main.py"],
                    "tasks_passed": 2,
                    "tasks_total": 2,
                }
            ),
        )

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        skip_install=True,
        runner=fake_runner,
    )

    row = result["runs"][0]
    summary = result["summary"]
    assert row["planner_valid"] is True
    assert row["scaffold_clean"] is True
    assert row["e2e_green"] is True
    assert summary["scaffold_clean_rate"] == 1.0
    assert summary["e2e_green_rate"] == 1.0
    assert summary["release_gates"]["full_75_run_matrix"] is False


def test_live_gate_marks_bad_stdout_as_failed(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
        return _completed(cmd, "not json", returncode=3)

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        plan_only=True,
        runner=fake_runner,
    )

    row = result["runs"][0]
    assert row["planner_valid"] is False
    assert row["json_parse_error"]
    assert result["summary"]["planner_valid_rate"] == 0.0


def test_live_gate_extracts_json_from_noisy_stdout() -> None:
    payload, error = _parse_json_stdout('noise\n{"tasks": [{"id": "T01"}]}\n')

    assert error == ""
    assert payload == {"tasks": [{"id": "T01"}]}


def test_live_gate_writes_reports(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
        return _completed(cmd, '{"tasks": [{"id": "T01"}]}')

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        plan_only=True,
        runner=fake_runner,
    )
    json_path = tmp_path / "live.json"
    md_path = tmp_path / "live.md"

    write_reports(result, json_path, md_path)

    assert '"benchmark": "scratch-live-gate"' in json_path.read_text(encoding="utf-8")
    assert "# Scratch Live Gate" in md_path.read_text(encoding="utf-8")
