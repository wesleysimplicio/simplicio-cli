"""Run the live scratch v0.5 gate matrix in resumable slices.

Unlike the preflight, this runner invokes the real `simplicio scratch` command.
It can run a bounded slice with `--max-runs` so the 15 x 5 matrix can be
collected incrementally without redefining partial evidence as release-ready.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.run_scratch_release_gate import PILOT_STACKS, RELEASE_GOALS  # noqa: E402


RESULTS_JSON = ROOT / "bench" / "results_scratch_live_gate.json"
RESULTS_MD = ROOT / "bench" / "results_scratch_live_gate.md"

Runner = Callable[..., subprocess.CompletedProcess[str]]


def run_live_gate(
    *,
    work_dir: Path,
    stacks: tuple[str, ...] = PILOT_STACKS,
    goals: tuple[str, ...] = RELEASE_GOALS,
    max_runs: int | None = None,
    plan_only: bool = False,
    skip_install: bool = False,
    timeout_seconds: int = 900,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    if max_runs is not None and max_runs < 1:
        raise ValueError("max_runs must be >= 1 when provided")
    work_dir.mkdir(parents=True, exist_ok=True)
    projects_dir = work_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    matrix = [
        (goal_index, stack)
        for goal_index, _goal in enumerate(goals, start=1)
        for stack in stacks
    ]
    if max_runs is not None:
        matrix = matrix[:max_runs]

    rows = []
    t0 = time.perf_counter()
    for run_number, (goal_index, stack) in enumerate(matrix, start=1):
        goal = goals[goal_index - 1]
        rows.append(
            _run_one(
                run_number=run_number,
                goal_index=goal_index,
                goal=goal,
                stack=stack,
                projects_dir=projects_dir,
                plan_only=plan_only,
                skip_install=skip_install,
                timeout_seconds=timeout_seconds,
                runner=runner,
            )
        )

    elapsed_s = round(time.perf_counter() - t0, 3)
    summary = _summarize(rows, elapsed_s, plan_only=plan_only)
    return {
        "benchmark": "scratch-live-gate",
        "scope": (
            "live scratch v0.5 gate execution slice; partial runs are evidence "
            "only for the executed slice and do not replace the full 75-run gate"
        ),
        "date": time.strftime("%Y-%m-%d"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "matrix": {
            "goals": len(goals),
            "stacks": len(stacks),
            "planned_runs": len(goals) * len(stacks),
            "release_planned_runs": len(RELEASE_GOALS) * len(PILOT_STACKS),
            "selected_runs": len(matrix),
            "plan_only": plan_only,
            "skip_install": skip_install,
        },
        "work_dir": "$WORK_DIR",
        "summary": summary,
        "runs": rows,
    }


def _run_one(
    *,
    run_number: int,
    goal_index: int,
    goal: str,
    stack: str,
    projects_dir: Path,
    plan_only: bool,
    skip_install: bool,
    timeout_seconds: int,
    runner: Runner,
) -> dict[str, Any]:
    project_name = f"gate-g{goal_index:02d}-{stack}"
    cmd = [
        sys.executable,
        "-m",
        "simplicio.cli",
        "scratch",
        goal,
        "--stack",
        stack,
        "--name",
        project_name,
        "--dest",
        str(projects_dir),
        "--json",
    ]
    if plan_only:
        cmd.append("--plan-only")
    if skip_install:
        cmd.append("--skip-install")

    started = time.perf_counter()
    try:
        proc = runner(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        duration_s = round(time.perf_counter() - started, 3)
        return {
            "run_number": run_number,
            "goal_index": goal_index,
            "stack": stack,
            "goal": goal,
            "project_name": project_name,
            "command": _redact_command(cmd),
            "returncode": None,
            "timed_out": True,
            "duration_s": duration_s,
            "planner_valid": False,
            "scaffold_clean": None,
            "e2e_green": None,
            "error": f"TIMEOUT after {timeout_seconds}s",
            "stdout_tail": (exc.stdout or "")[-1500:],
            "stderr_tail": (exc.stderr or "")[-1500:],
        }

    duration_s = round(time.perf_counter() - started, 3)
    payload, parse_error = _parse_json_stdout(proc.stdout)
    metrics = _row_metrics(payload, returncode=proc.returncode, plan_only=plan_only)
    return {
        "run_number": run_number,
        "goal_index": goal_index,
        "stack": stack,
        "goal": goal,
        "project_name": project_name,
        "command": _redact_command(cmd),
        "returncode": proc.returncode,
        "timed_out": timed_out,
        "duration_s": duration_s,
        **metrics,
        "json_parse_error": parse_error,
        "stdout_tail": (proc.stdout or "")[-1500:],
        "stderr_tail": (proc.stderr or "")[-1500:],
    }


def _row_metrics(
    payload: dict[str, Any] | None,
    *,
    returncode: int,
    plan_only: bool,
) -> dict[str, Any]:
    if not payload:
        return {
            "planner_valid": False,
            "scaffold_clean": None,
            "e2e_green": None,
            "tasks_passed": 0,
            "tasks_total": 0,
        }

    if plan_only:
        tasks = payload.get("tasks", [])
        planner_valid = returncode == 0 and isinstance(tasks, list) and bool(tasks)
        return {
            "planner_valid": planner_valid,
            "scaffold_clean": None,
            "e2e_green": None,
            "tasks_passed": 0,
            "tasks_total": len(tasks) if isinstance(tasks, list) else 0,
        }

    tasks_total = int(payload.get("tasks_total", 0) or 0)
    tasks_passed = int(payload.get("tasks_passed", 0) or 0)
    files_written = payload.get("files_written", [])
    scaffold_clean = isinstance(files_written, list) and bool(files_written)
    e2e_green = returncode == 0 and tasks_total > 0 and tasks_passed == tasks_total
    return {
        "planner_valid": tasks_total > 0 or scaffold_clean,
        "scaffold_clean": scaffold_clean,
        "e2e_green": e2e_green,
        "tasks_passed": tasks_passed,
        "tasks_total": tasks_total,
    }


def _parse_json_stdout(stdout: str) -> tuple[dict[str, Any] | None, str]:
    text = (stdout or "").strip()
    if not text:
        return None, "stdout was empty"
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None, "stdout did not contain a JSON object"
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            return None, f"invalid JSON stdout: {exc}"
    if not isinstance(value, dict):
        return None, "stdout JSON was not an object"
    return value, ""


def _summarize(
    rows: list[dict[str, Any]],
    elapsed_s: float,
    *,
    plan_only: bool,
) -> dict[str, Any]:
    total = len(rows)
    planner_valid = sum(1 for row in rows if row.get("planner_valid"))
    scaffold_rows = [row for row in rows if row.get("scaffold_clean") is not None]
    e2e_rows = [row for row in rows if row.get("e2e_green") is not None]
    scaffold_clean = sum(1 for row in scaffold_rows if row.get("scaffold_clean"))
    e2e_green = sum(1 for row in e2e_rows if row.get("e2e_green"))
    durations = [float(row["duration_s"]) for row in rows if not row.get("timed_out")]
    median_wall_clock_s = round(statistics.median(durations), 3) if durations else None
    planner_valid_rate = _ratio(planner_valid, total)
    scaffold_clean_rate = _ratio(scaffold_clean, len(scaffold_rows))
    e2e_green_rate = _ratio(e2e_green, len(e2e_rows))
    release_gates = {
        "full_75_run_matrix": total >= len(RELEASE_GOALS) * len(PILOT_STACKS),
        "planner_valid_ge_90": planner_valid_rate >= 0.90 if total else False,
        "scaffold_clean_ge_95": None if plan_only else scaffold_clean_rate >= 0.95,
        "e2e_green_ge_80": None if plan_only else e2e_green_rate >= 0.80,
        "median_wall_clock_le_8m": (
            median_wall_clock_s <= 480 if median_wall_clock_s is not None else None
        ),
        "average_cost_le_1": None,
        "skillopt_human_approval_ge_80": False,
    }
    release_gates["release_ready"] = all(
        value is True for value in release_gates.values()
    )
    return {
        "total_runs": total,
        "planner_valid": planner_valid,
        "planner_valid_rate": planner_valid_rate,
        "scaffold_clean": scaffold_clean,
        "scaffold_clean_rate": scaffold_clean_rate,
        "e2e_green": e2e_green,
        "e2e_green_rate": e2e_green_rate,
        "timed_out": sum(1 for row in rows if row.get("timed_out")),
        "median_wall_clock_s": median_wall_clock_s,
        "average_cost_usd": None,
        "elapsed_s": elapsed_s,
        "release_gates": release_gates,
        "missing_release_evidence": _missing_release_evidence(release_gates, plan_only),
    }


def _missing_release_evidence(
    release_gates: dict[str, Any],
    plan_only: bool,
) -> list[str]:
    missing = []
    if not release_gates["full_75_run_matrix"]:
        missing.append("full 15 goals x 5 pilot stacks live matrix")
    if plan_only:
        missing.append("scaffold and end-to-end execution, not only plan validation")
    if release_gates["average_cost_le_1"] is None:
        missing.append("average cost measurement")
    if not release_gates["skillopt_human_approval_ge_80"]:
        missing.append("SkillOpt human approval evidence >=80%")
    return missing


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _redact_command(cmd: list[str]) -> list[str]:
    redacted = []
    for part in cmd:
        text = str(part)
        if str(ROOT) in text:
            text = text.replace(str(ROOT), "$ROOT")
        redacted.append(text)
    return redacted


def write_reports(result: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(result), encoding="utf-8")


def _to_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    matrix = result["matrix"]
    lines = [
        "# Scratch Live Gate",
        "",
        result["scope"],
        "",
        "## Matrix",
        "",
        f"- release planned runs: {matrix['release_planned_runs']}",
        f"- selected matrix runs: {matrix['planned_runs']}",
        f"- selected runs: {matrix['selected_runs']}",
        f"- plan only: {matrix['plan_only']}",
        f"- skip install: {matrix['skip_install']}",
        "",
        "## Summary",
        "",
        f"- planner valid: {summary['planner_valid']}/{summary['total_runs']} ({summary['planner_valid_rate']:.2%})",
        f"- scaffold clean: {summary['scaffold_clean']} ({summary['scaffold_clean_rate']:.2%})",
        f"- e2e green: {summary['e2e_green']} ({summary['e2e_green_rate']:.2%})",
        f"- median wall-clock: {summary['median_wall_clock_s']} s",
        f"- release ready: {summary['release_gates']['release_ready']}",
        "",
        "## Release Gate Status",
        "",
    ]
    for gate, value in summary["release_gates"].items():
        lines.append(f"- {gate}: {value}")
    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| # | stack | goal_index | rc | planner | scaffold | e2e | duration_s |",
            "| ---: | --- | ---: | ---: | --- | --- | --- | ---: |",
        ]
    )
    for row in result["runs"]:
        lines.append(
            "| {run} | {stack} | {goal_index} | {rc} | {planner} | {scaffold} | {e2e} | {duration} |".format(
                run=row["run_number"],
                stack=row["stack"],
                goal_index=row["goal_index"],
                rc=row["returncode"],
                planner=row["planner_valid"],
                scaffold=row["scaffold_clean"],
                e2e=row["e2e_green"],
                duration=row["duration_s"],
            )
        )
    lines.extend(["", "## Missing Release Evidence", ""])
    for item in summary["missing_release_evidence"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--max-runs", type=int)
    parser.add_argument("--goal-limit", type=int, default=len(RELEASE_GOALS))
    parser.add_argument("--stack", action="append", dest="stacks")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    goals = RELEASE_GOALS[: args.goal_limit]
    stacks = tuple(args.stacks) if args.stacks else PILOT_STACKS
    result = run_live_gate(
        work_dir=args.work_dir,
        stacks=stacks,
        goals=goals,
        max_runs=args.max_runs,
        plan_only=args.plan_only,
        skip_install=args.skip_install,
        timeout_seconds=args.timeout_seconds,
    )
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    return 0 if result["summary"]["planner_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
