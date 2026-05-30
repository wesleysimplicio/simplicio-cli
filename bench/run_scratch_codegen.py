"""Benchmark deterministic scratch codegen through the real executor path.

This is intentionally keyless: it removes SIMPLICIO_MODEL while running so
fallbacks are reported as skipped instead of calling an LLM. The report is a
local evidence slice for the mechanical executors, not the full 50-run LLM
reduction release gate.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simplicio.scratch.executor import execute_plan  # noqa: E402
from simplicio.scratch.plan_schema import Plan, Task  # noqa: E402
from simplicio.scratch.stack_registry import Stack  # noqa: E402


RESULTS_JSON = ROOT / "bench" / "results_scratch_codegen.json"
RESULTS_MD = ROOT / "bench" / "results_scratch_codegen.md"


@dataclass(frozen=True)
class BenchCase:
    name: str
    stack_slug: str
    language: str
    framework: str
    task: Task
    seed_files: dict[str, str]
    expected_executor: str


def build_cases(*, include_typescript: bool = True) -> list[BenchCase]:
    cases = [
        BenchCase(
            name="python-orm-field",
            stack_slug="py-fastapi",
            language="Python",
            framework="FastAPI",
            task=Task(
                id="T01-db-model",
                goal="Add email: Mapped[str] field to User model",
                target="src/db/models.py",
                criteria="- User has email: Mapped[str]",
                constraints="- use SQLAlchemy 2.0 declarative style",
                verify="pytest tests/db/test_models.py -q",
            ),
            seed_files={
                "src/db/models.py": """from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
"""
            },
            expected_executor="python-add-orm-field",
        ),
        BenchCase(
            name="python-pydantic-schema",
            stack_slug="py-fastapi",
            language="Python",
            framework="FastAPI",
            task=Task(
                id="T02-api-schemas",
                goal="Create Pydantic schemas for User create, update, and read flows.",
                target="src/api/schemas/user.py",
                criteria=(
                    "- UserCreate, UserUpdate, and UserRead schemas exist\n"
                    "- optional update fields are supported"
                ),
                constraints="- keep schemas framework-agnostic",
                verify="pytest tests/api/test_users.py -q",
            ),
            seed_files={
                "src/db/user.py": """from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
"""
            },
            expected_executor="python-add-pydantic-schema",
        ),
        BenchCase(
            name="python-fastapi-route",
            stack_slug="py-fastapi",
            language="Python",
            framework="FastAPI",
            task=Task(
                id="T03-api-route",
                goal="Add GET `/users/{id}` endpoint to the users route",
                target="src/api/users.py",
                criteria="- exposes @router.get with async handler and return type",
                constraints="- keep existing imports",
                verify="pytest tests/api/test_users.py -q",
            ),
            seed_files={
                "src/api/users.py": """from fastapi import APIRouter

router = APIRouter()
"""
            },
            expected_executor="python-add-fastapi-route",
        ),
        BenchCase(
            name="python-pytest-test",
            stack_slug="py-fastapi",
            language="Python",
            framework="FastAPI",
            task=Task(
                id="T04-pytest",
                goal="Generate a happy-path pytest for function double in src/utils/math_ops.py",
                target="tests/unit/test_math_ops.py",
                criteria="- imports the function under test\n- has a sane assert",
                constraints="- use pytest",
                verify="pytest tests/unit/test_math_ops.py -q",
            ),
            seed_files={
                "pyproject.toml": """[tool.pytest.ini_options]
pythonpath = ["src"]
""",
                "src/utils/math_ops.py": """def double(value: int) -> int:
    return value * 2
""",
            },
            expected_executor="python-add-pytest-test",
        ),
    ]

    if include_typescript:
        cases.append(
            BenchCase(
                name="typescript-next-route",
                stack_slug="ts-nextjs",
                language="TypeScript 5",
                framework="Next.js app router",
                task=Task(
                    id="T05-next-route",
                    goal="Create Next.js route handlers for Unit CRUD",
                    target="src/app/api/units/route.ts",
                    criteria="- exports GET and POST handlers\n- returns JSON responses",
                    constraints="- no external dependencies",
                    verify="pnpm vitest run src/app/api/units/route.test.ts",
                ),
                seed_files={},
                expected_executor="typescript-add-next-route",
            )
        )

    return cases


def run_benchmark(
    *,
    work_dir: Path | None = None,
    repeat: int = 10,
    include_typescript: bool = True,
) -> dict[str, Any]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")

    owned_temp = False
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="simplicio-scratch-codegen-"))
        owned_temp = True
    work_dir.mkdir(parents=True, exist_ok=True)

    cases = build_cases(include_typescript=include_typescript)
    projects_parent = work_dir / "projects"
    templates_parent = work_dir / "templates"
    projects_parent.mkdir(parents=True, exist_ok=True)
    templates_parent.mkdir(parents=True, exist_ok=True)

    old_model = os.environ.pop("SIMPLICIO_MODEL", None)
    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    try:
        for run_index in range(1, repeat + 1):
            for case in cases:
                rows.append(
                    _run_case(
                        case,
                        run_index=run_index,
                        projects_parent=projects_parent,
                        templates_parent=templates_parent,
                    )
                )
    finally:
        if old_model is not None:
            os.environ["SIMPLICIO_MODEL"] = old_model

    elapsed_s = round(time.perf_counter() - t0, 3)
    return {
        "benchmark": "scratch-codegen",
        "scope": (
            "synthetic deterministic executor benchmark; no LLM calls; "
            "does not replace the full 50-scratch release gate"
        ),
        "work_dir": "$WORK_DIR",
        "work_dir_owned_by_runner": owned_temp,
        "repeat": repeat,
        "include_typescript": include_typescript,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "summary": _summarize(rows, elapsed_s),
        "cases": rows,
    }


def _run_case(
    case: BenchCase,
    *,
    run_index: int,
    projects_parent: Path,
    templates_parent: Path,
) -> dict[str, Any]:
    project_name = f"{case.name}-r{run_index:02d}"
    template_root = templates_parent / project_name
    _write_seed_tree(template_root / "tree", case.seed_files)
    stack = Stack(
        slug=case.stack_slug,
        path=template_root,
        meta={
            "language": case.language,
            "framework": case.framework,
            "template_version": "bench-scratch-codegen-v1",
        },
    )
    plan = _plan_for_case(case, project_name)

    try:
        report = execute_plan(plan, stack, projects_parent, skip_install=True)
    except Exception as exc:  # pragma: no cover - defensive bench reporting
        return {
            "name": case.name,
            "run_index": run_index,
            "stack": case.stack_slug,
            "expected_executor": case.expected_executor,
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    task = report.task_results[0] if report.task_results else None
    executor = task.codegen_executor if task is not None else None
    expected_match = executor == case.expected_executor
    task_passed = bool(task and task.passed)
    work_dir = projects_parent.parent
    return {
        "name": case.name,
        "run_index": run_index,
        "stack": case.stack_slug,
        "project_dir": _redact_path(report.project_dir, work_dir),
        "expected_executor": case.expected_executor,
        "actual_executor": executor,
        "expected_executor_match": expected_match,
        "passed": task_passed and expected_match,
        "task_passed": task_passed,
        "execution_mode": task.execution_mode if task is not None else "missing",
        "duration_ms": task.duration_ms if task is not None else 0,
        "metrics": report.metrics,
        "log_tail": _redact_text(task.log_tail[-300:], work_dir)
        if task is not None
        else "",
    }


def _write_seed_tree(tree: Path, seed_files: dict[str, str]) -> None:
    for rel_path, content in seed_files.items():
        path = tree / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _plan_for_case(case: BenchCase, project_name: str) -> Plan:
    return Plan(
        version="1.0",
        stack=case.stack_slug,
        project_name=project_name,
        rationale=f"Benchmark deterministic executor {case.expected_executor}.",
        files_to_create=[],
        tasks=[case.task],
        deps_to_install=[],
        deps_dev=[],
        test_command=case.task.verify,
        lint_command="",
        estimated_total_tasks=1,
    )


def _summarize(rows: list[dict[str, Any]], elapsed_s: float) -> dict[str, Any]:
    total_cases = len(rows)
    passed_cases = sum(1 for row in rows if row.get("passed"))
    codegen_tasks = sum(
        int(row.get("metrics", {}).get("tasks_codegen", 0)) for row in rows
    )
    llm_tasks = sum(int(row.get("metrics", {}).get("tasks_llm", 0)) for row in rows)
    skipped_tasks = sum(
        int(row.get("metrics", {}).get("tasks_skipped", 0)) for row in rows
    )
    failed_tasks = sum(
        int(row.get("metrics", {}).get("tasks_failed", 0)) for row in rows
    )
    total_tasks = codegen_tasks + llm_tasks + skipped_tasks + failed_tasks
    matched = sum(1 for row in rows if row.get("expected_executor_match"))
    codegen_durations = [
        int(row.get("duration_ms", 0))
        for row in rows
        if row.get("execution_mode") == "codegen"
    ]
    summary = {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": total_cases - passed_cases,
        "pass_rate": _ratio(passed_cases, total_cases),
        "expected_executor_match_rate": _ratio(matched, total_cases),
        "total_tasks": total_tasks,
        "tasks_codegen": codegen_tasks,
        "tasks_llm": llm_tasks,
        "tasks_skipped": skipped_tasks,
        "tasks_failed": failed_tasks,
        "codegen_share": _ratio(codegen_tasks, total_tasks),
        "avg_codegen_ms": _avg(codegen_durations),
        "elapsed_s": elapsed_s,
        "planner_calls": 0,
        "llm_calls": llm_tasks,
    }
    summary["release_gates"] = {
        "fifty_runs": total_cases >= 50,
        "mechanical_share_ge_30": summary["codegen_share"] >= 0.30,
        "executor_pass_rate_100": summary["pass_rate"] == 1.0,
        "llm_baseline_present": False,
        "latency_reduction_ge_50": None,
    }
    summary["missing_release_evidence"] = [
        "LLM baseline pass-rate and latency comparison",
        "50 real scratch goals across the release corpus",
        "planner cache hit-rate measured across cold/warm scratch runs",
    ]
    return summary


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _avg(values: list[int]) -> int:
    return round(sum(values) / len(values)) if values else 0


def _redact_path(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return _redact_text(str(path), root)
    return "$WORK_DIR/" + rel.as_posix()


def _redact_text(text: str, root: Path) -> str:
    root_text = str(root)
    return text.replace(root_text, "$WORK_DIR").replace(
        root_text.replace("\\", "/"),
        "$WORK_DIR",
    )


def write_reports(result: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(result), encoding="utf-8")


def _to_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Scratch Codegen Benchmark",
        "",
        result["scope"],
        "",
        "## Summary",
        "",
        f"- cases: {summary['passed_cases']}/{summary['total_cases']} passed",
        f"- codegen share: {summary['codegen_share']:.2%}",
        f"- expected executor match: {summary['expected_executor_match_rate']:.2%}",
        f"- avg codegen latency: {summary['avg_codegen_ms']} ms",
        f"- planner calls: {summary['planner_calls']}",
        f"- llm calls: {summary['llm_calls']}",
        "",
        "## Release Gate Status",
        "",
    ]
    for gate, value in summary["release_gates"].items():
        lines.append(f"- {gate}: {value}")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| case | stack | executor | mode | passed | duration_ms |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in result["cases"]:
        lines.append(
            "| {name} r{run_index:02d} | {stack} | {executor} | {mode} | {passed} | {duration} |".format(
                name=row["name"],
                run_index=row["run_index"],
                stack=row["stack"],
                executor=row.get("actual_executor") or "",
                mode=row.get("execution_mode") or "",
                passed=row.get("passed"),
                duration=row.get("duration_ms", 0),
            )
        )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=10)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument(
        "--no-typescript",
        action="store_true",
        help="Skip the Next.js ts-morph executor case.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_benchmark(
        work_dir=args.work_dir,
        repeat=args.repeat,
        include_typescript=not args.no_typescript,
    )
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    return 0 if result["summary"]["failed_cases"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
