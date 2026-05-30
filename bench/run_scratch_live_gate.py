"""Run the live scratch v0.5 gate matrix in resumable slices.

Unlike the preflight, this runner invokes the real `simplicio scratch` command.
It can run a bounded slice with `--max-runs` so the 15 x 5 matrix can be
collected incrementally without redefining partial evidence as release-ready.
"""

from __future__ import annotations

import argparse
import json
import platform
import shlex
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
from simplicio.scratch.stack_registry import StackRegistry  # noqa: E402


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
    post_verify: bool = False,
    timeout_seconds: int = 900,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    if max_runs is not None and max_runs < 1:
        raise ValueError("max_runs must be >= 1 when provided")
    work_dir.mkdir(parents=True, exist_ok=True)
    projects_dir = work_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    registry = StackRegistry()

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
                post_verify=post_verify,
                timeout_seconds=timeout_seconds,
                runner=runner,
                registry=registry,
            )
        )

    elapsed_s = round(time.perf_counter() - t0, 3)
    summary = _summarize(rows, elapsed_s, plan_only=plan_only, post_verify=post_verify)
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
            "post_verify": post_verify,
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
    post_verify: bool,
    timeout_seconds: int,
    runner: Runner,
    registry: StackRegistry,
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
            "task_all_passed": False,
            "e2e_green": None,
            "tasks_passed": 0,
            "tasks_total": 0,
            "post_verify": {
                "enabled": post_verify and not plan_only,
                "passed": False if post_verify and not plan_only else None,
                "error": "scratch command timed out",
            },
            "json_parse_error": "scratch command timed out before JSON output",
            "error": f"TIMEOUT after {timeout_seconds}s",
            "stdout_tail": _tail_text(exc.stdout),
            "stderr_tail": _tail_text(exc.stderr),
        }

    duration_s = round(time.perf_counter() - started, 3)
    stdout_text = _as_text(proc.stdout)
    stderr_text = _as_text(proc.stderr)
    payload, parse_error = _parse_json_stdout(stdout_text)
    verify = _post_verify(
        payload,
        stack_slug=stack,
        enabled=post_verify and not plan_only,
        timeout_seconds=timeout_seconds,
        runner=runner,
        registry=registry,
    )
    metrics = _row_metrics(
        payload,
        returncode=proc.returncode,
        plan_only=plan_only,
        post_verify=post_verify,
        verify=verify,
    )
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
        "post_verify": verify,
        "json_parse_error": parse_error,
        "stdout_tail": _tail_text(stdout_text),
        "stderr_tail": _tail_text(stderr_text),
    }


def _row_metrics(
    payload: dict[str, Any] | None,
    *,
    returncode: int,
    plan_only: bool,
    post_verify: bool,
    verify: dict[str, Any],
) -> dict[str, Any]:
    if not payload:
        return {
            "planner_valid": False,
            "scaffold_clean": None,
            "task_all_passed": False,
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
            "task_all_passed": False,
            "e2e_green": None,
            "tasks_passed": 0,
            "tasks_total": len(tasks) if isinstance(tasks, list) else 0,
        }

    tasks_total, total_error = _coerce_int(payload.get("tasks_total", 0), "tasks_total")
    tasks_passed, passed_error = _coerce_int(
        payload.get("tasks_passed", 0),
        "tasks_passed",
    )
    if total_error or passed_error:
        return {
            "planner_valid": False,
            "scaffold_clean": False,
            "task_all_passed": False,
            "e2e_green": False if post_verify else None,
            "tasks_passed": max(tasks_passed, 0),
            "tasks_total": max(tasks_total, 0),
            "error": "; ".join(error for error in (total_error, passed_error) if error),
        }
    files_written = payload.get("files_written", [])
    scaffold_clean = isinstance(files_written, list) and bool(files_written)
    task_all_passed = (
        returncode == 0 and tasks_total > 0 and tasks_passed == tasks_total
    )
    e2e_green = bool(verify.get("passed")) if post_verify else None
    return {
        "planner_valid": tasks_total > 0 or scaffold_clean,
        "scaffold_clean": scaffold_clean,
        "task_all_passed": task_all_passed,
        "e2e_green": e2e_green,
        "tasks_passed": tasks_passed,
        "tasks_total": tasks_total,
    }


def _post_verify(
    payload: dict[str, Any] | None,
    *,
    stack_slug: str,
    enabled: bool,
    timeout_seconds: int,
    runner: Runner,
    registry: StackRegistry,
) -> dict[str, Any]:
    if not enabled:
        return {"enabled": False, "passed": None}
    if not payload:
        return {"enabled": True, "passed": False, "error": "missing scratch payload"}
    project_dir_raw = str(payload.get("project_dir", "")).strip()
    if not project_dir_raw:
        return {"enabled": True, "passed": False, "error": "missing project_dir"}
    project_dir = Path(project_dir_raw)
    if not project_dir.is_dir():
        return {
            "enabled": True,
            "passed": False,
            "error": f"project_dir not found: {project_dir}",
        }
    stack = registry.get(stack_slug)
    if stack is None:
        return {
            "enabled": True,
            "passed": False,
            "error": f"unknown stack: {stack_slug}",
        }
    commands = [
        ("test", stack.test_command),
        ("lint", stack.lint_command),
    ]
    rows = []
    started = time.perf_counter()
    for name, command in commands:
        if not command:
            rows.append(
                {"name": name, "command": "", "returncode": None, "skipped": True}
            )
            continue
        command_start = time.perf_counter()
        rows.append(
            _run_verify_command(
                name=name,
                command=command,
                project_dir=project_dir,
                timeout_seconds=timeout_seconds,
                runner=runner,
                started=command_start,
            )
        )
    ran = [row for row in rows if not row.get("skipped")]
    return {
        "enabled": True,
        "passed": bool(ran) and all(row.get("passed") for row in ran),
        "duration_s": round(time.perf_counter() - started, 3),
        "commands": rows,
    }


def _run_verify_command(
    *,
    name: str,
    command: str,
    project_dir: Path,
    timeout_seconds: int,
    runner: Runner,
    started: float,
) -> dict[str, Any]:
    row = _invoke_verify_command(
        command,
        project_dir=project_dir,
        timeout_seconds=timeout_seconds,
        runner=runner,
        shell=True,
    )
    fallback = _python_module_fallback(command)
    if fallback and _verify_command_unavailable(row):
        row = _invoke_verify_command(
            fallback,
            project_dir=project_dir,
            timeout_seconds=timeout_seconds,
            runner=runner,
            shell=False,
        ) | {"fallback_for": command}

    row.update(
        {
            "name": name,
            "duration_s": round(time.perf_counter() - started, 3),
            "passed": row.get("returncode") == 0,
        }
    )
    return row


def _invoke_verify_command(
    command: str | list[str],
    *,
    project_dir: Path,
    timeout_seconds: int,
    runner: Runner,
    shell: bool,
) -> dict[str, Any]:
    try:
        proc = runner(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            shell=shell,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "timed_out": True,
            "stdout_tail": _tail_text(exc.stdout, limit=1000),
            "stderr_tail": _tail_text(exc.stderr, limit=1000),
        }
    return {
        "command": command,
        "returncode": proc.returncode,
        "timed_out": False,
        "stdout_tail": _tail_text(proc.stdout, limit=1000),
        "stderr_tail": _tail_text(proc.stderr, limit=1000),
    }


def _python_module_fallback(command: str) -> list[str] | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    module = parts[0].lower()
    if module not in {"pytest", "ruff"}:
        return None
    return [sys.executable, "-m", module, *parts[1:]]


def _verify_command_unavailable(row: dict[str, Any]) -> bool:
    if row.get("returncode") == 0 or row.get("timed_out"):
        return False
    if row.get("stdout_tail"):
        return False
    stderr = str(row.get("stderr_tail", "")).lower()
    return any(
        marker in stderr
        for marker in (
            "not recognized",
            "not found",
            "reconhecido",
            "no such file",
        )
    )


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


def _coerce_int(value: Any, field: str) -> tuple[int, str]:
    try:
        return int(value or 0), ""
    except (TypeError, ValueError):
        return 0, f"{field} must be an integer"


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _tail_text(value: Any, *, limit: int = 1500) -> str:
    return _as_text(value)[-limit:]


def _summarize(
    rows: list[dict[str, Any]],
    elapsed_s: float,
    *,
    plan_only: bool,
    post_verify: bool,
) -> dict[str, Any]:
    total = len(rows)
    planner_valid = sum(1 for row in rows if row.get("planner_valid"))
    scaffold_rows = [row for row in rows if row.get("scaffold_clean") is not None]
    e2e_rows = [row for row in rows if row.get("e2e_green") is not None]
    scaffold_clean = sum(1 for row in scaffold_rows if row.get("scaffold_clean"))
    e2e_green = sum(1 for row in e2e_rows if row.get("e2e_green"))
    task_all_passed = sum(1 for row in rows if row.get("task_all_passed"))
    durations = [float(row["duration_s"]) for row in rows if not row.get("timed_out")]
    median_wall_clock_s = round(statistics.median(durations), 3) if durations else None
    planner_valid_rate = _ratio(planner_valid, total)
    scaffold_clean_rate = _ratio(scaffold_clean, len(scaffold_rows))
    e2e_green_rate = _ratio(e2e_green, len(e2e_rows))
    release_gates = {
        "full_75_run_matrix": _has_full_release_matrix(rows),
        "planner_valid_ge_90": planner_valid_rate >= 0.90 if total else False,
        "scaffold_clean_ge_95": None if plan_only else scaffold_clean_rate >= 0.95,
        "e2e_green_ge_80": (
            e2e_green_rate >= 0.80 if post_verify and e2e_rows else None
        ),
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
        "task_all_passed": task_all_passed,
        "task_all_passed_rate": _ratio(task_all_passed, total),
        "e2e_green": e2e_green,
        "e2e_green_rate": e2e_green_rate,
        "timed_out": sum(1 for row in rows if row.get("timed_out")),
        "median_wall_clock_s": median_wall_clock_s,
        "average_cost_usd": None,
        "elapsed_s": elapsed_s,
        "release_gates": release_gates,
        "missing_release_evidence": _missing_release_evidence(
            release_gates,
            plan_only,
            post_verify,
        ),
    }


def _missing_release_evidence(
    release_gates: dict[str, Any],
    plan_only: bool,
    post_verify: bool,
) -> list[str]:
    missing = []
    if not release_gates["full_75_run_matrix"]:
        missing.append("full 15 goals x 5 pilot stacks live matrix")
    if plan_only:
        missing.append("scaffold and end-to-end execution, not only plan validation")
    elif not post_verify:
        missing.append("post-scratch stack test/lint verification")
    if release_gates["average_cost_le_1"] is None:
        missing.append("average cost measurement")
    if not release_gates["skillopt_human_approval_ge_80"]:
        missing.append("SkillOpt human approval evidence >=80%")
    return missing


def _has_full_release_matrix(rows: list[dict[str, Any]]) -> bool:
    required = {(goal, stack) for goal in RELEASE_GOALS for stack in PILOT_STACKS}
    observed = {
        (str(row.get("goal")), str(row.get("stack")))
        for row in rows
        if row.get("goal") and row.get("stack")
    }
    return required.issubset(observed)


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
        f"- post verify: {matrix['post_verify']}",
        "",
        "## Summary",
        "",
        f"- planner valid: {summary['planner_valid']}/{summary['total_runs']} ({summary['planner_valid_rate']:.2%})",
        f"- scaffold clean: {summary['scaffold_clean']} ({summary['scaffold_clean_rate']:.2%})",
        f"- task all passed: {summary['task_all_passed']} ({summary['task_all_passed_rate']:.2%})",
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
            "| # | stack | goal_index | rc | planner | scaffold | tasks | e2e | duration_s |",
            "| ---: | --- | ---: | ---: | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in result["runs"]:
        lines.append(
            "| {run} | {stack} | {goal_index} | {rc} | {planner} | {scaffold} | {tasks} | {e2e} | {duration} |".format(
                run=row["run_number"],
                stack=row["stack"],
                goal_index=row["goal_index"],
                rc=row["returncode"],
                planner=row["planner_valid"],
                scaffold=row["scaffold_clean"],
                tasks=row.get("task_all_passed"),
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
    parser.add_argument(
        "--post-verify",
        action="store_true",
        help="after scratch execution, run the selected stack test and lint commands",
    )
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
        post_verify=args.post_verify,
        timeout_seconds=args.timeout_seconds,
    )
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    summary = result["summary"]
    return (
        0
        if summary["total_runs"] > 0
        and summary["planner_valid"] == summary["total_runs"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
