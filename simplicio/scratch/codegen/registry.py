"""Registry for deterministic scratch task executors."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..plan_schema import Task
from ..stack_registry import Stack
from .types import CodegenResult, TaskExecutor

_DEFAULT_EXECUTORS: list[TaskExecutor] = []


def registered_executors() -> list[TaskExecutor]:
    return list(_DEFAULT_EXECUTORS)


def register_executor(executor: TaskExecutor) -> None:
    _DEFAULT_EXECUTORS.append(executor)


def try_execute(
    task: Task,
    project_dir: Path,
    stack: Stack,
    executors: Iterable[TaskExecutor] | None = None,
) -> CodegenResult | None:
    for executor in executors if executors is not None else _DEFAULT_EXECUTORS:
        if executor.can_handle(task, stack):
            return executor.execute(task, project_dir, stack)
    return None
