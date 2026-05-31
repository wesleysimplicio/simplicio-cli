"""Feature-scope orchestration for ``simplicio run``.

This is the first Ralph-style layer above the atomic task primitive: the
planner decomposes a goal into ordered tasks, each task runs through the
existing verify-loop, and a failing task can trigger one bounded replan.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..scratch._pipeline_adapter import run_task as run_plan_task
from ..scratch.planner import generate_plan
from ..scratch.stack_registry import StackRegistry, slugify_project
from .cost_governor import CostGovernor


TaskRunner = Callable[[object, Path, object], tuple[bool, str]]


def run_feature(
    *,
    root: str,
    stack_slug: str,
    goal: str,
    max_iter: int = 3,
    max_cost: str | float | int | None = None,
    planner: Callable[..., object] = generate_plan,
    task_runner: TaskRunner = run_plan_task,
) -> dict:
    """Run a multi-task feature plan against an existing repository."""

    if max_iter < 0:
        raise ValueError("max_iter must be >= 0")

    reg = StackRegistry()
    stack = reg.get(stack_slug)
    if stack is None:
        raise ValueError(
            f"unknown stack '{stack_slug}'. Run `simplicio scratch --list-stacks`."
        )

    governor = CostGovernor.from_value(max_cost)
    project_name = slugify_project(goal)
    feature_goal = goal
    replans = 0
    task_results: list[dict] = []
    last_plan = None

    while True:
        last_plan = planner(stack, feature_goal, project_name)
        governor.charge_usd("0")
        failed = None

        for task in last_plan.tasks:
            passed, log = task_runner(task, Path(root), stack)
            row = {
                "id": task.id,
                "goal": task.goal,
                "target": task.target,
                "passed": bool(passed),
                "log": log[:1500],
                "replan": replans,
            }
            task_results.append(row)
            if not passed:
                failed = row
                break

        if failed is None:
            return {
                "scope": "feature",
                "goal": goal,
                "stack": stack.slug,
                "applied": True,
                "plan_tasks": len(last_plan.tasks),
                "tasks": task_results,
                "replans": replans,
                "warnings": [],
                "cost": governor.report(),
            }

        if replans >= max_iter:
            return {
                "scope": "feature",
                "goal": goal,
                "stack": stack.slug,
                "applied": False,
                "plan_tasks": len(last_plan.tasks),
                "tasks": task_results,
                "replans": replans,
                "warnings": [
                    f"feature task {failed['id']} failed after {replans} replans"
                ],
                "cost": governor.report(),
            }

        replans += 1
        feature_goal = (
            f"{goal}\n\n[REPLAN CONTEXT]\n"
            f"Previous plan failed at {failed['id']} targeting {failed['target']}.\n"
            f"Failure log:\n{failed['log']}\n\n"
            "Return a revised plan for the remaining feature work."
        )
