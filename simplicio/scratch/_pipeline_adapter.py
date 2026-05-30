"""_pipeline_adapter.py — bridge between scratch.executor (which iterates
plan tasks) and simplicio.pipeline (which runs the cli verify-loop on one
task at a time).

The existing simplicio.pipeline.run() signature is
  run(root, stack, goal, target, criteria, constraints)
plus it reads SIMPLICIO_TEST_CMD from the environment. We adapt one Task
from the plan into one pipeline.run invocation, with SIMPLICIO_TEST_CMD
temporarily set to the per-task verify command.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from .plan_schema import Task
from .stack_registry import Stack


def run_task(task: Task, project_dir: Path, stack: Stack) -> tuple[bool, str]:
    """Run one plan task through simplicio.pipeline.run.
    Returns (passed, log_tail)."""
    from ..pipeline import run as pipeline_run

    # Per-task verify command supersedes any global SIMPLICIO_TEST_CMD
    prev_test_cmd = os.environ.get("SIMPLICIO_TEST_CMD")
    previous_cwd = Path.cwd()
    os.environ["SIMPLICIO_TEST_CMD"] = task.verify
    try:
        stack_label = stack.language
        if stack.framework:
            stack_label = f"{stack.language} + {stack.framework}"

        _ensure_git_repo(project_dir)
        os.chdir(project_dir)
        output = pipeline_run(
            root=str(project_dir),
            stack=stack_label,
            goal=task.goal,
            target=task.target,
            criteria=task.criteria,
            constraints=task.constraints,
        )
    finally:
        os.chdir(previous_cwd)
        if prev_test_cmd is None:
            os.environ.pop("SIMPLICIO_TEST_CMD", None)
        else:
            os.environ["SIMPLICIO_TEST_CMD"] = prev_test_cmd

    if output is None:
        return False, "(pipeline returned None — task did not converge)"
    if isinstance(output, str):
        log = output
    else:
        log = json.dumps(output, indent=2, sort_keys=True)
    return True, log[:1500]


def _ensure_git_repo(project_dir: Path) -> None:
    if (project_dir / ".git").exists():
        return
    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
