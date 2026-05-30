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
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .codegen import CodegenResult, try_execute
from .plan_schema import Plan, Task
from .stack_registry import Stack


@dataclass
class TaskResult:
    id: str
    target: str
    passed: bool
    execution_mode: str = "unknown"
    codegen_executor: Optional[str] = None
    files_modified: list[str] = field(default_factory=list)
    skipped_reason: Optional[str] = None
    duration_ms: int = 0
    log_tail: str = ""
    generated_skill: Optional[str] = None


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

    @property
    def metrics(self) -> dict:
        by_mode = {
            mode: [task for task in self.task_results if task.execution_mode == mode]
            for mode in ("codegen", "llm", "skipped", "failed")
        }
        total = self.tasks_total
        codegen = len(by_mode["codegen"])
        return {
            "tasks_total": total,
            "tasks_codegen": codegen,
            "tasks_llm": len(by_mode["llm"]),
            "tasks_skipped": len(by_mode["skipped"]),
            "tasks_failed": len(by_mode["failed"]),
            "codegen_share": round(codegen / total, 4) if total else 0.0,
            "avg_codegen_ms": _avg_ms(by_mode["codegen"]),
            "avg_llm_ms": _avg_ms(by_mode["llm"]),
            "avg_task_ms": _avg_ms(self.task_results),
        }

    def to_dict(self) -> dict:
        return {
            "project_dir": str(self.project_dir),
            "stack_slug": self.stack_slug,
            "files_written": [str(p) for p in self.files_written],
            "install_ok": self.install_ok,
            "install_log_tail": self.install_log[-1500:],
            "tasks": [
                {
                    "id": t.id,
                    "target": t.target,
                    "passed": t.passed,
                    "execution_mode": t.execution_mode,
                    "codegen_executor": t.codegen_executor,
                    "files_modified": t.files_modified,
                    "skipped": t.skipped_reason,
                    "duration_ms": t.duration_ms,
                    "log_tail": t.log_tail[-400:],
                    "generated_skill": t.generated_skill,
                }
                for t in self.task_results
            ],
            "tasks_passed": self.tasks_passed,
            "tasks_total": self.tasks_total,
            "metrics": self.metrics,
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


def _safe_run(cmd: list[str] | str, cwd: Path, timeout: int = 300) -> tuple[bool, str]:
    """Run a shell command, never raising. Returns (ok, log_tail)."""
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
        )
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s"
    except FileNotFoundError as e:
        return False, f"command not found: {e}"
    log = (p.stdout or "") + (p.stderr or "")
    return p.returncode == 0, log


def _execute_one_task(task: Task, project_dir: Path, stack: Stack) -> TaskResult:
    """Execute a single task. For Phase 0/1, this stubs out the actual code
    generation if no SIMPLICIO_MODEL is set so the scaffold + verify pipeline
    can still be smoke-tested. When SIMPLICIO_MODEL IS set, defers to
    simplicio.pipeline via the adapter."""
    t0 = time.perf_counter()
    codegen_log = ""
    skill_log, generated_skill = _ensure_required_skill(task, project_dir)
    if skill_log.startswith("skill-opt failed:"):
        ms = int((time.perf_counter() - t0) * 1000)
        return TaskResult(
            id=task.id,
            target=task.target,
            passed=False,
            duration_ms=ms,
            execution_mode="failed",
            skipped_reason="required skill generation failed",
            log_tail=skill_log,
        )

    if _codegen_disabled():
        codegen_result = None
        codegen_log = "codegen disabled by SIMPLICIO_DISABLE_CODEGEN"
    else:
        codegen_result = try_execute(task, project_dir, stack)
    if codegen_result is not None:
        codegen_log = codegen_result.log
        if codegen_result.passed or not codegen_result.fallback_to_llm:
            return _task_result_from_codegen(
                task,
                t0,
                codegen_result,
                skill_log=skill_log,
                generated_skill=generated_skill,
            )

    if not os.environ.get("SIMPLICIO_MODEL"):
        # smoke-test mode: log the task but mark as skipped (no LLM call made)
        ms = int((time.perf_counter() - t0) * 1000)
        fallback_note = (
            f"codegen fallback: {codegen_log[:200]}\n" if codegen_log else ""
        )
        return TaskResult(
            id=task.id,
            target=task.target,
            passed=False,
            duration_ms=ms,
            execution_mode="skipped",
            skipped_reason="no SIMPLICIO_MODEL set; task generation skipped",
            log_tail=f"{skill_log}{fallback_note}goal={task.goal[:200]}",
            generated_skill=generated_skill,
        )

    try:
        from ._pipeline_adapter import run_task
    except ImportError as e:
        ms = int((time.perf_counter() - t0) * 1000)
        return TaskResult(
            id=task.id,
            target=task.target,
            passed=False,
            duration_ms=ms,
            execution_mode="failed",
            skipped_reason=f"adapter import failed: {e}",
            log_tail=skill_log,
            generated_skill=generated_skill,
        )

    passed, log = run_task(task, project_dir, stack)
    if codegen_log:
        log = f"codegen fallback: {codegen_log}\n\n{log}"
    if skill_log:
        log = f"{skill_log}{log}"
    ms = int((time.perf_counter() - t0) * 1000)
    return TaskResult(
        id=task.id,
        target=task.target,
        passed=passed,
        execution_mode="llm" if passed else "failed",
        duration_ms=ms,
        log_tail=log,
        generated_skill=generated_skill,
    )


def _task_result_from_codegen(
    task: Task,
    started_at: float,
    result: CodegenResult,
    *,
    skill_log: str = "",
    generated_skill: Optional[str] = None,
) -> TaskResult:
    ms = int((time.perf_counter() - started_at) * 1000)
    files = ", ".join(str(path) for path in result.files_modified)
    suffix = f"\nfiles_modified={files}" if files else ""
    return TaskResult(
        id=task.id,
        target=task.target,
        passed=result.passed,
        execution_mode="codegen" if result.passed else "failed",
        codegen_executor=result.executor_name,
        files_modified=[str(path) for path in result.files_modified],
        duration_ms=ms,
        log_tail=f"{skill_log}{result.log}{suffix}".strip(),
        generated_skill=generated_skill,
    )


def _codegen_disabled() -> bool:
    value = os.environ.get("SIMPLICIO_DISABLE_CODEGEN", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _ensure_required_skill(
    task: Task,
    project_dir: Path,
) -> tuple[str, Optional[str]]:
    required = (task.required_skill or "").strip()
    if not required:
        return "", None

    from . import skill_opt

    skills_root = project_dir / ".skills"
    try:
        slug, markdown = skill_opt.generate_skill_doc(
            required,
            skills_root=skills_root,
        )
        path = skill_opt.install_skill(slug, markdown, skills_root=skills_root)
    except skill_opt.SkillOptError as exc:
        return f"skill-opt failed: {exc}", None
    except SystemExit as exc:
        return f"skill-opt failed: {exc}", None

    rel = path.relative_to(project_dir).as_posix()
    return f"skill-opt generated {rel} with review_required=true\n", rel


def _avg_ms(tasks: list[TaskResult]) -> int:
    if not tasks:
        return 0
    return round(sum(task.duration_ms for task in tasks) / len(tasks))


def execute_plan(
    plan: Plan, stack: Stack, parent_dir: Path, skip_install: bool = False
) -> ExecutorReport:
    """Materialize the plan into parent_dir/<project_name>/."""
    t_start = time.perf_counter()

    project_dir = parent_dir / plan.project_name
    if project_dir.exists():
        raise FileExistsError(
            f"project directory already exists: {project_dir}. "
            "Choose a different project_name or remove the existing dir."
        )
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
    plan_path.write_text(
        json.dumps(
            {
                "version": plan.version,
                "stack": plan.stack,
                "project_name": plan.project_name,
                "rationale": plan.rationale,
                "files_to_create": [
                    {"path": f.path, "purpose": f.purpose} for f in plan.files_to_create
                ],
                "tasks": [
                    {
                        "id": t.id,
                        "goal": t.goal,
                        "target": t.target,
                        "criteria": t.criteria,
                        "constraints": t.constraints,
                        "verify": t.verify,
                        "depends_on": t.depends_on,
                        **(
                            {"required_skill": t.required_skill}
                            if t.required_skill
                            else {}
                        ),
                    }
                    for t in plan.tasks
                ],
                "deps_to_install": plan.deps_to_install,
                "deps_dev": plan.deps_dev,
                "test_command": plan.test_command,
                "lint_command": plan.lint_command,
                "estimated_total_tasks": plan.estimated_total_tasks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # 3. Run install (best-effort)
    if not skip_install and stack.install_command:
        report.install_ok, report.install_log = _safe_run(
            stack.install_command, project_dir, timeout=600
        )

    # 4. Execute tasks in dependency order
    for task in _topo_sort(plan.tasks):
        report.task_results.append(_execute_one_task(task, project_dir, stack))

    report.elapsed_s = time.perf_counter() - t_start

    # 5. Write final report next to the plan
    (sim_dir / "scratch_report.json").write_text(
        json.dumps(report.to_dict(), indent=2), encoding="utf-8"
    )

    return report
