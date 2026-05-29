"""executor.py — apply a validated Plan to a destination directory.

Phase 1 (this file):
  1. Slug + create destination directory
  2. Render stack tree into destination
  3. Run package-manager install (best-effort, recoverable failure)
  4. Iterate tasks in dependency order; each task is logged but execution
     is delegated to simplicio.pipeline (or stubbed when no SIMPLICIO_MODEL
     is set, so the rest of the pipeline can be smoke-tested without a key)

This file deliberately does NOT call simplicio.pipeline.run directly yet —
the pipeline today expects a single goal/target/contract and we need a small
adapter shim. Adapter lives in simplicio/scratch/_pipeline_adapter.py.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .plan_schema import Plan, Task
from .stack_registry import Stack


@dataclass
class TaskResult:
    id: str
    target: str
    passed: bool
    skipped_reason: Optional[str] = None
    duration_ms: int = 0
    log_tail: str = ""


@dataclass
class ExecutorReport:
    project_dir: Path
    stack_slug: str
    files_written: list[Path] = field(default_factory=list)
    install_ok: bool = False
    install_log: str = ""
    task_results: list[TaskResult] = field(default_factory=list)
    elapsed_s: float = 0.0

    @property
    def tasks_passed(self) -> int:
        return sum(1 for t in self.task_results if t.passed)

    @property
    def tasks_total(self) -> int:
        return len(self.task_results)

    def to_dict(self) -> dict:
        return {
            "project_dir": str(self.project_dir),
            "stack_slug": self.stack_slug,
            "files_written": [str(p) for p in self.files_written],
            "install_ok": self.install_ok,
            "install_log_tail": self.install_log[-1500:],
            "tasks": [
                {"id": t.id, "target": t.target, "passed": t.passed,
                 "skipped": t.skipped_reason, "duration_ms": t.duration_ms,
                 "log_tail": t.log_tail[-400:]}
                for t in self.task_results
            ],
            "tasks_passed": self.tasks_passed,
            "tasks_total": self.tasks_total,
            "elapsed_s": round(self.elapsed_s, 2),
        }


def _topo_sort(tasks: list[Task]) -> list[Task]:
    """Order tasks so each depends_on entry runs before its dependents.
    Plan validation guarantees no missing refs; here we only break cycles
    (shouldn't happen) by falling back to declared order."""
    by_id = {t.id: t for t in tasks}
    ordered: list[Task] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(t: Task) -> None:
        if t.id in visited:
            return
        if t.id in visiting:
            # cycle — bail out and preserve declared order
            return
        visiting.add(t.id)
        for dep in t.depends_on:
            if dep in by_id:
                visit(by_id[dep])
        visiting.discard(t.id)
        visited.add(t.id)
        ordered.append(t)

    for t in tasks:
        visit(t)
    return ordered


def _safe_run(cmd: list[str] | str, cwd: Path,
              timeout: int = 300) -> tuple[bool, str]:
    """Run a shell command, never raising. Returns (ok, log_tail)."""
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            timeout=timeout, shell=isinstance(cmd, str),
        )
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s"
    except FileNotFoundError as e:
        return False, f"command not found: {e}"
    log = (p.stdout or "") + (p.stderr or "")
    return p.returncode == 0, log


def _execute_one_task(task: Task, project_dir: Path,
                      stack: Stack) -> TaskResult:
    """Execute a single task. For Phase 0/1, this stubs out the actual code
    generation if no SIMPLICIO_MODEL is set so the scaffold + verify pipeline
    can still be smoke-tested. When SIMPLICIO_MODEL IS set, defers to
    simplicio.pipeline via the adapter."""
    t0 = time.perf_counter()

    if not os.environ.get("SIMPLICIO_MODEL"):
        # smoke-test mode: log the task but mark as skipped (no LLM call made)
        ms = int((time.perf_counter() - t0) * 1000)
        return TaskResult(
            id=task.id, target=task.target, passed=False, duration_ms=ms,
            skipped_reason="no SIMPLICIO_MODEL set; task generation skipped",
            log_tail=f"goal={task.goal[:200]}",
        )

    try:
        from ._pipeline_adapter import run_task
    except ImportError as e:
        ms = int((time.perf_counter() - t0) * 1000)
        return TaskResult(
            id=task.id, target=task.target, passed=False, duration_ms=ms,
            skipped_reason=f"adapter import failed: {e}",
        )

    passed, log = run_task(task, project_dir, stack)
    ms = int((time.perf_counter() - t0) * 1000)
    return TaskResult(id=task.id, target=task.target, passed=passed,
                      duration_ms=ms, log_tail=log)


def execute_plan(plan: Plan, stack: Stack, parent_dir: Path,
                 skip_install: bool = False) -> ExecutorReport:
    """Materialize the plan into parent_dir/<project_name>/."""
    t_start = time.perf_counter()

    project_dir = parent_dir / plan.project_name
    if project_dir.exists():
        raise FileExistsError(
            f"project directory already exists: {project_dir}. "
            "Choose a different project_name or remove the existing dir.")
    project_dir.mkdir(parents=True)

    report = ExecutorReport(project_dir=project_dir, stack_slug=stack.slug)

    # 1. Render tree
    render_vars = {
        "project_name": plan.project_name,
        "goal": plan.rationale,
        "stack_slug": stack.slug,
    }
    report.files_written = stack.render_tree(project_dir, render_vars)

    # 2. Write the plan itself into .simplicio/plan.json for traceability
    sim_dir = project_dir / ".simplicio"
    sim_dir.mkdir(exist_ok=True)
    plan_path = sim_dir / "plan.json"
    plan_path.write_text(json.dumps({
        "version": plan.version,
        "stack": plan.stack,
        "project_name": plan.project_name,
        "rationale": plan.rationale,
        "files_to_create": [{"path": f.path, "purpose": f.purpose}
                            for f in plan.files_to_create],
        "tasks": [{"id": t.id, "goal": t.goal, "target": t.target,
                   "criteria": t.criteria, "constraints": t.constraints,
                   "verify": t.verify, "depends_on": t.depends_on}
                  for t in plan.tasks],
        "deps_to_install": plan.deps_to_install,
        "deps_dev": plan.deps_dev,
        "test_command": plan.test_command,
        "lint_command": plan.lint_command,
        "estimated_total_tasks": plan.estimated_total_tasks,
    }, indent=2), encoding="utf-8")

    # 3. Run install (best-effort)
    if not skip_install and stack.install_command:
        report.install_ok, report.install_log = _safe_run(
            stack.install_command, project_dir, timeout=600)

    # 4. Execute tasks in dependency order
    for task in _topo_sort(plan.tasks):
        report.task_results.append(_execute_one_task(task, project_dir, stack))

    report.elapsed_s = time.perf_counter() - t_start

    # 5. Write final report next to the plan
    (sim_dir / "scratch_report.json").write_text(
        json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    return report
