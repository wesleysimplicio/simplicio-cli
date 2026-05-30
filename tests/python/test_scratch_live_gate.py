"""Tests for the live scratch gate runner."""

from __future__ import annotations

import json
import subprocess

from bench.run_scratch_live_gate import (
    merge_results,
    _parse_json_stdout,
    _summarize,
    load_skillopt_review_evidence,
    run_live_gate,
    write_reports,
)
from bench.run_scratch_release_gate import PILOT_STACKS, RELEASE_GOALS


def _completed(cmd, stdout, returncode=0, stderr=""):
    return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)


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
    project_dir = tmp_path / "live" / "projects" / "gate-g01-py-fastapi"
    project_dir.mkdir(parents=True)

    def fake_runner(cmd, **_kwargs):
        if isinstance(cmd, list) and len(cmd) > 2 and cmd[2] in {"pytest", "ruff"}:
            return _completed(cmd, "ok\n")
        if isinstance(cmd, str):
            return _completed(cmd, "", returncode=1, stderr=f"{cmd} not recognized")
        assert "--plan-only" not in cmd
        return _completed(
            cmd,
            json.dumps(
                {
                    "project_dir": str(project_dir),
                    "files_written": ["src/main.py"],
                    "tasks_passed": 2,
                    "tasks_total": 2,
                    "metrics": {"tasks_llm": 0, "tasks_codegen": 2},
                }
            ),
        )

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        skip_install=True,
        post_verify=True,
        runner=fake_runner,
    )

    row = result["runs"][0]
    summary = result["summary"]
    assert row["planner_valid"] is True
    assert row["scaffold_clean"] is True
    assert row["task_all_passed"] is True
    assert row["e2e_green"] is True
    assert row["scratch_metrics"]["tasks_llm"] == 0
    assert row["cost_usd"] == 0.0
    assert row["post_verify"]["passed"] is True
    assert summary["scaffold_clean_rate"] == 1.0
    assert summary["e2e_green_rate"] == 1.0
    assert summary["average_cost_usd"] == 0.0
    assert summary["release_gates"]["average_cost_le_1"] is True
    assert summary["release_gates"]["full_75_run_matrix"] is False


def test_live_gate_can_disable_codegen_for_llm_baseline(tmp_path) -> None:
    def fake_runner(cmd, **kwargs):
        assert kwargs["env"]["SIMPLICIO_DISABLE_CODEGEN"] == "1"
        return _completed(
            cmd,
            json.dumps(
                {
                    "project_dir": str(tmp_path),
                    "files_written": ["src/main.py"],
                    "tasks_passed": 2,
                    "tasks_total": 2,
                    "metrics": {
                        "tasks_llm": 2,
                        "tasks_codegen": 0,
                        "avg_llm_ms": 1200,
                    },
                }
            ),
        )

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        disable_codegen=True,
        runner=fake_runner,
    )

    row = result["runs"][0]
    assert result["matrix"]["disable_codegen"] is True
    assert row["codegen_disabled"] is True
    assert row["scratch_metrics"]["tasks_llm"] == 2


def test_live_gate_requires_project_dir_for_post_verify(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
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
        post_verify=True,
        runner=fake_runner,
    )

    row = result["runs"][0]
    assert row["e2e_green"] is False
    assert row["post_verify"]["error"] == "missing project_dir"


def test_live_gate_requires_post_verify_for_e2e_metric(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
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
        runner=fake_runner,
    )

    row = result["runs"][0]
    summary = result["summary"]
    assert row["task_all_passed"] is True
    assert row["e2e_green"] is None
    assert summary["release_gates"]["e2e_green_ge_80"] is None
    assert (
        "post-scratch stack test/lint verification"
        in summary["missing_release_evidence"]
    )


def test_live_gate_handles_timeout_bytes_in_reports(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
        raise subprocess.TimeoutExpired(cmd, 1, output=b"partial", stderr=b"err")

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        post_verify=True,
        runner=fake_runner,
    )
    json_path = tmp_path / "timeout.json"
    md_path = tmp_path / "timeout.md"

    row = result["runs"][0]
    assert row["timed_out"] is True
    assert row["stdout_tail"] == "partial"
    assert row["stderr_tail"] == "err"
    assert row["post_verify"]["error"] == "scratch command timed out"
    write_reports(result, json_path, md_path)
    assert '"timed_out": true' in json_path.read_text(encoding="utf-8")


def test_live_gate_marks_malformed_task_counts_failed(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
        return _completed(
            cmd,
            json.dumps(
                {
                    "project_dir": str(tmp_path),
                    "files_written": ["src/main.py"],
                    "tasks_passed": "two",
                    "tasks_total": 2,
                }
            ),
        )

    result = run_live_gate(
        work_dir=tmp_path / "live",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        runner=fake_runner,
    )

    row = result["runs"][0]
    assert row["planner_valid"] is False
    assert row["task_all_passed"] is False
    assert row["error"] == "tasks_passed must be an integer"


def test_live_gate_full_matrix_requires_official_pairs() -> None:
    rows = [
        {
            "goal": "not an official goal",
            "stack": "py-fastapi",
            "planner_valid": True,
            "scaffold_clean": True,
            "task_all_passed": True,
            "e2e_green": True,
            "duration_s": 1,
            "timed_out": False,
        }
        for _ in range(75)
    ]

    summary = _summarize(rows, 1.0, plan_only=False, post_verify=True)

    assert summary["release_gates"]["full_75_run_matrix"] is False


def test_live_gate_keeps_cost_unknown_when_llm_cost_is_missing() -> None:
    rows = [
        {
            "goal": "CRUD app for condo units with owner contact search",
            "stack": "py-fastapi",
            "planner_valid": True,
            "scaffold_clean": True,
            "task_all_passed": True,
            "e2e_green": True,
            "duration_s": 1,
            "timed_out": False,
            "cost_usd": None,
            "scratch_metrics": {"tasks_llm": 1},
        }
    ]

    summary = _summarize(rows, 1.0, plan_only=False, post_verify=True)

    assert summary["average_cost_usd"] is None
    assert summary["release_gates"]["average_cost_le_1"] is None
    assert "average cost measurement" in summary["missing_release_evidence"]


def test_live_gate_accepts_skillopt_human_review_evidence(tmp_path) -> None:
    reviews = [
        {
            "skill": f"generated-skill-{index:02d}",
            "reviewer": "wesley",
            "approved": index <= 8,
            "reviewed_at": "2026-05-30",
        }
        for index in range(1, 11)
    ]
    review_path = tmp_path / "skillopt-review.json"
    review_path.write_text(json.dumps({"reviews": reviews}), encoding="utf-8")
    rows = [
        {
            "goal": goal,
            "stack": stack,
            "planner_valid": True,
            "scaffold_clean": True,
            "task_all_passed": True,
            "e2e_green": True,
            "duration_s": 1,
            "timed_out": False,
            "cost_usd": 0.0,
        }
        for goal in RELEASE_GOALS
        for stack in PILOT_STACKS
    ]

    summary = _summarize(
        rows,
        1.0,
        plan_only=False,
        post_verify=True,
        skillopt_review=load_skillopt_review_evidence(review_path),
    )

    assert summary["skillopt_review"]["total_reviews"] == 10
    assert summary["skillopt_review"]["approved"] == 8
    assert summary["release_gates"]["skillopt_human_approval_ge_80"] is True
    assert summary["release_gates"]["release_ready"] is True
    assert (
        "SkillOpt human approval evidence >=80%"
        not in summary["missing_release_evidence"]
    )


def test_live_gate_rejects_invalid_skillopt_review_rows() -> None:
    summary = _summarize(
        [
            {
                "goal": "CRUD app for condo units with owner contact search",
                "stack": "py-fastapi",
                "planner_valid": True,
                "scaffold_clean": True,
                "task_all_passed": True,
                "e2e_green": True,
                "duration_s": 1,
                "timed_out": False,
                "cost_usd": 0.0,
            }
        ],
        1.0,
        plan_only=False,
        post_verify=True,
        skillopt_review={
            "reviews": [
                {"skill": "missing-reviewer", "approved": True},
                {"skill": "string-approved", "reviewer": "wesley", "approved": "yes"},
            ]
        },
    )

    assert summary["skillopt_review"]["total_reviews"] == 0
    assert summary["skillopt_review"]["invalid_reviews"] == 2
    assert summary["release_gates"]["skillopt_human_approval_ge_80"] is False


def test_live_gate_merges_distinct_slices(tmp_path) -> None:
    def fake_runner(cmd, **_kwargs):
        stack = cmd[cmd.index("--stack") + 1]
        project = tmp_path / "live" / "projects" / f"gate-g01-{stack}"
        project.mkdir(parents=True, exist_ok=True)
        if isinstance(cmd, str):
            return _completed(cmd, "")
        return _completed(
            cmd,
            json.dumps(
                {
                    "project_dir": str(project),
                    "files_written": ["src/main.py"],
                    "tasks_passed": 1,
                    "tasks_total": 1,
                }
            ),
        )

    existing = run_live_gate(
        work_dir=tmp_path / "live-py",
        stacks=("py-fastapi",),
        goals=("CRUD app for condo units",),
        post_verify=False,
        runner=fake_runner,
    )
    current = run_live_gate(
        work_dir=tmp_path / "live-ts",
        stacks=("ts-nextjs",),
        goals=("CRUD app for condo units",),
        post_verify=False,
        runner=fake_runner,
    )

    merged = merge_results(existing, current)

    assert merged["matrix"]["selected_runs"] == 2
    assert merged["matrix"]["planned_runs"] == 2
    assert [row["run_number"] for row in merged["runs"]] == [1, 2]
    assert [row["stack"] for row in merged["runs"]] == ["py-fastapi", "ts-nextjs"]
    assert merged["summary"]["total_runs"] == 2
    assert merged["summary"]["task_all_passed"] == 2


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
