"""Fixture-backed F5 report for the unified ``simplicio run`` bench.

Issue #41 asks for a head-to-head bench comparing the existing cli+ag task loop,
the unified feature/sprint orchestrator, and Codex ``/goal`` on a controlled
sprint. This script records that comparison shape without invoking any LLM or
external agent. The output is intentionally marked as fixture evidence so a
future live run can replace the rows without changing the report schema.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

RESULTS_JSON = ROOT / "bench" / "results_unified_run_bench.json"
RESULTS_MD = ROOT / "bench" / "results_unified_run_bench.md"

DEFAULT_CASES: list[dict[str, Any]] = [
    {
        "case_id": "single-file-task",
        "scope": "task",
        "goal": "Fix email validation in src/forms/UserForm.tsx.",
        "expected_tasks": 1,
        "expected_files": 1,
        "dod_gates": 1,
    },
    {
        "case_id": "feature-auth-flow",
        "scope": "feature",
        "goal": "Implement JWT login with refresh tokens across API and UI.",
        "expected_tasks": 4,
        "expected_files": 4,
        "dod_gates": 2,
    },
    {
        "case_id": "sprint-checkout-hardening",
        "scope": "sprint",
        "goal": "Finish checkout sprint with billing, reports, and DoD green.",
        "expected_tasks": 7,
        "expected_files": 8,
        "dod_gates": 4,
    },
]

MODES: list[dict[str, Any]] = [
    {
        "mode_id": "cli_ag",
        "label": "cli+ag task loop",
        "entrypoint": "simplicio task",
        "decomposition_owner": "human",
        "replan_scope": "none",
        "cost_visibility": "per atomic task",
        "observable": True,
    },
    {
        "mode_id": "unified_feature",
        "label": "unified run feature",
        "entrypoint": "simplicio run --scope feature",
        "decomposition_owner": "planner",
        "replan_scope": "remaining feature tasks",
        "cost_visibility": "cost governor",
        "observable": True,
    },
    {
        "mode_id": "unified_sprint",
        "label": "unified run sprint",
        "entrypoint": "simplicio run --scope sprint --max-cost <usd>",
        "decomposition_owner": "sprint loader and planner",
        "replan_scope": "feature tasks inside sprint",
        "cost_visibility": "required cost governor",
        "observable": True,
    },
    {
        "mode_id": "codex_goal",
        "label": "Codex /goal",
        "entrypoint": "codex /goal",
        "decomposition_owner": "external agent",
        "replan_scope": "opaque",
        "cost_visibility": "opaque in this repo bench",
        "observable": False,
    },
]


def run_benchmark(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    fixtures = _normalize_cases(cases or DEFAULT_CASES)
    rows = [
        _fixture_row(case, mode)
        for case in fixtures
        for mode in MODES
    ]
    summary = _summarize(rows, fixtures)
    return {
        "benchmark": "unified-run-f5-fixture",
        "issue": "#41",
        "phase": "F5",
        "scope": (
            "planned fixture comparison for cli+ag, unified feature/sprint, "
            "and Codex /goal; no LLM or external agent was invoked"
        ),
        "fixture_only": True,
        "date": time.strftime("%Y-%m-%d"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "modes": MODES,
        "cases": fixtures,
        "rows": rows,
        "summary": summary,
    }


def _normalize_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for index, case in enumerate(cases, start=1):
        scope = str(case.get("scope", "")).strip()
        if scope not in {"task", "feature", "sprint"}:
            raise ValueError(f"case {index} has unsupported scope: {scope!r}")
        expected_tasks = int(case.get("expected_tasks", 0))
        if expected_tasks < 1:
            raise ValueError(f"case {index} expected_tasks must be >= 1")
        normalized.append(
            {
                "case_id": str(case.get("case_id") or f"case-{index:02d}"),
                "scope": scope,
                "goal": str(case.get("goal", "")).strip(),
                "expected_tasks": expected_tasks,
                "expected_files": int(case.get("expected_files", expected_tasks)),
                "dod_gates": int(case.get("dod_gates", 0)),
            }
        )
    return normalized


def _fixture_row(case: dict[str, Any], mode: dict[str, Any]) -> dict[str, Any]:
    scope = case["scope"]
    mode_id = mode["mode_id"]
    expected_tasks = case["expected_tasks"]

    row: dict[str, Any] = {
        "case_id": case["case_id"],
        "scope": scope,
        "mode_id": mode_id,
        "fixture": True,
        "llm_invoked": False,
        "external_agent_invoked": False,
        "expected_task_runs": expected_tasks,
        "planner_calls": 0,
        "manual_decomposition_required": False,
        "replan_supported": False,
        "resume_state_supported": False,
        "dod_gate_supported": False,
        "cost_cap_required": False,
        "cost_observable": bool(mode["observable"]),
        "outcome": "planned",
        "notes": [],
    }

    if mode_id == "cli_ag":
        if scope == "task":
            row["expected_task_runs"] = 1
            row["outcome"] = "covered_by_existing_atomic_loop"
        else:
            row["manual_decomposition_required"] = True
            row["outcome"] = "requires_human_decomposition"
            row["notes"].append("cli+ag has no native feature or sprint planner")
    elif mode_id == "unified_feature":
        if scope == "task":
            row["expected_task_runs"] = 1
            row["outcome"] = "dispatches_to_task"
        elif scope == "feature":
            row["planner_calls"] = 1
            row["replan_supported"] = True
            row["outcome"] = "covered_by_feature_orchestrator"
        else:
            row["planner_calls"] = max(1, expected_tasks // 3)
            row["manual_decomposition_required"] = True
            row["replan_supported"] = True
            row["outcome"] = "feature_loop_only_after_sprint_decomposition"
            row["notes"].append("needs sprint loader to provide feature-sized goals")
    elif mode_id == "unified_sprint":
        row["cost_cap_required"] = scope == "sprint"
        row["dod_gate_supported"] = scope in {"feature", "sprint"}
        row["resume_state_supported"] = scope == "sprint"
        if scope == "sprint":
            row["planner_calls"] = max(1, expected_tasks // 3)
            row["replan_supported"] = True
            row["outcome"] = "covered_by_sprint_orchestrator"
        else:
            row["outcome"] = "not_the_primary_scope"
            row["notes"].append("use task or feature mode for this scope")
    elif mode_id == "codex_goal":
        row["external_agent_invoked"] = False
        row["cost_observable"] = False
        row["replan_supported"] = True
        row["resume_state_supported"] = None
        row["dod_gate_supported"] = None
        row["outcome"] = "external_baseline_placeholder"
        row["notes"].append("live Codex /goal run is required for real comparison")
    return row


def _summarize(
    rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    by_mode: dict[str, dict[str, Any]] = {}
    for mode in MODES:
        mode_rows = [row for row in rows if row["mode_id"] == mode["mode_id"]]
        by_mode[mode["mode_id"]] = {
            "label": mode["label"],
            "rows": len(mode_rows),
            "manual_decomposition_cases": sum(
                1 for row in mode_rows if row["manual_decomposition_required"]
            ),
            "replan_supported_cases": sum(
                1 for row in mode_rows if row["replan_supported"] is True
            ),
            "resume_state_supported_cases": sum(
                1 for row in mode_rows if row["resume_state_supported"] is True
            ),
            "cost_observable_cases": sum(
                1 for row in mode_rows if row["cost_observable"] is True
            ),
            "cost_cap_required_cases": sum(
                1 for row in mode_rows if row["cost_cap_required"] is True
            ),
            "llm_invocations": sum(1 for row in mode_rows if row["llm_invoked"]),
            "external_agent_invocations": sum(
                1 for row in mode_rows if row["external_agent_invoked"]
            ),
        }

    expected_rows = len(cases) * len(MODES)
    release_blockers = [
        "real cli+ag runs on the controlled task, feature, and sprint cases",
        "real unified feature/sprint runs with cost governor telemetry",
        "real Codex /goal baseline runs with comparable success and cost data",
        "artifact collection for sprint DoD evidence",
    ]
    return {
        "fixture_only": True,
        "evidence_level": "fixture",
        "case_count": len(cases),
        "mode_count": len(MODES),
        "row_count": len(rows),
        "expected_row_count": expected_rows,
        "schema_fixture_complete": len(rows) == expected_rows,
        "real_llm_runs_present": any(row["llm_invoked"] for row in rows),
        "external_codex_goal_run_present": any(
            row["external_agent_invoked"] for row in rows
        ),
        "release_ready": False,
        "release_blockers": release_blockers,
        "head_to_head_ready_for_live_run": len(rows) == expected_rows,
        "by_mode": by_mode,
        "missing_live_evidence": release_blockers,
    }


def write_reports(result: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(result), encoding="utf-8")


def _to_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Unified Run F5 Bench Fixture",
        "",
        result["scope"],
        "",
        "## Summary",
        "",
        f"- issue: {result['issue']}",
        f"- phase: {result['phase']}",
        f"- fixture only: {summary['fixture_only']}",
        f"- evidence level: {summary['evidence_level']}",
        f"- cases: {summary['case_count']}",
        f"- modes: {summary['mode_count']}",
        f"- rows: {summary['row_count']}/{summary['expected_row_count']}",
        f"- release ready: {summary['release_ready']}",
        (
            "- ready for live run: "
            f"{summary['head_to_head_ready_for_live_run']}"
        ),
        "",
        "## Modes",
        "",
        "| mode | entrypoint | decomposition | replan | cost visibility |",
        "| --- | --- | --- | --- | --- |",
    ]
    for mode in result["modes"]:
        lines.append(
            f"| {mode['label']} | `{mode['entrypoint']}` | "
            f"{mode['decomposition_owner']} | {mode['replan_scope']} | "
            f"{mode['cost_visibility']} |"
        )

    lines.extend(
        [
            "",
            "## Fixture Matrix",
            "",
            (
                "| case | scope | mode | outcome | task runs | planner calls | "
                "manual split | replan | cost observable |"
            ),
            "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    mode_labels = {mode["mode_id"]: mode["label"] for mode in result["modes"]}
    for row in result["rows"]:
        lines.append(
            f"| {row['case_id']} | {row['scope']} | "
            f"{mode_labels[row['mode_id']]} | {row['outcome']} | "
            f"{row['expected_task_runs']} | {row['planner_calls']} | "
            f"{row['manual_decomposition_required']} | "
            f"{row['replan_supported']} | {row['cost_observable']} |"
        )

    lines.extend(["", "## Missing Live Evidence", ""])
    for item in summary["missing_live_evidence"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-json",
        type=Path,
        help="Optional case fixture JSON. Expected shape: {'cases': [...]} or [...].",
    )
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def _load_cases(path: Path | None) -> list[dict[str, Any]] | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cases", [])
    if not isinstance(data, list):
        raise ValueError("fixture JSON must be a list or an object with a cases list")
    return data


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_benchmark(_load_cases(args.fixture_json))
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
