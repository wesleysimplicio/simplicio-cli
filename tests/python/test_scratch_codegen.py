"""Tests for deterministic scratch codegen executor plumbing."""

from __future__ import annotations

from pathlib import Path

from simplicio.scratch.codegen import CodegenResult, TaskExecutor
from simplicio.scratch.codegen import registry as codegen_registry
from simplicio.scratch.executor import _execute_one_task
from simplicio.scratch.plan_schema import Task
from simplicio.scratch.stack_registry import Stack


def _task() -> Task:
    return Task(
        id="T01-codegen",
        goal="add deterministic file",
        target="src/app.py",
        criteria="file exists",
        constraints="no llm",
        verify="pytest -q",
    )


def _stack(tmp_path: Path) -> Stack:
    return Stack(
        slug="py-fastapi",
        path=tmp_path,
        meta={"language": "Python", "framework": "FastAPI"},
    )


class _Executor(TaskExecutor):
    name = "fake"

    def __init__(
        self, *, can_handle: bool = True, result: CodegenResult | None = None
    ) -> None:
        self._can_handle = can_handle
        self._result = result or CodegenResult(passed=True, log="mechanical ok")
        self.calls = 0

    def can_handle(self, task: Task, stack: Stack) -> bool:
        return self._can_handle

    def execute(self, task: Task, project_dir: Path, stack: Stack) -> CodegenResult:
        self.calls += 1
        return self._result


def test_empty_registry_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(codegen_registry, "_DEFAULT_EXECUTORS", [])
    assert codegen_registry.try_execute(_task(), tmp_path, _stack(tmp_path)) is None


def test_registry_executes_first_matching_executor(tmp_path):
    skipped = _Executor(can_handle=False)
    matched = _Executor(result=CodegenResult(passed=True, log="matched"))
    result = codegen_registry.try_execute(
        _task(), tmp_path, _stack(tmp_path), [skipped, matched]
    )
    assert result is not None
    assert result.log == "matched"
    assert skipped.calls == 0
    assert matched.calls == 1


def test_successful_codegen_runs_without_model(tmp_path, monkeypatch):
    executor = _Executor(
        result=CodegenResult(
            passed=True, files_modified=[tmp_path / "src/app.py"], log="done"
        )
    )
    monkeypatch.setattr(codegen_registry, "_DEFAULT_EXECUTORS", [executor])
    monkeypatch.delenv("SIMPLICIO_MODEL", raising=False)
    result = _execute_one_task(_task(), tmp_path, _stack(tmp_path))
    assert result.passed is True
    assert result.skipped_reason is None
    assert "done" in result.log_tail
    assert "files_modified" in result.log_tail


def test_codegen_failure_without_fallback_does_not_call_llm(tmp_path, monkeypatch):
    executor = _Executor(result=CodegenResult(passed=False, log="missing class"))
    monkeypatch.setattr(codegen_registry, "_DEFAULT_EXECUTORS", [executor])
    monkeypatch.setenv("SIMPLICIO_MODEL", "fake-model")
    result = _execute_one_task(_task(), tmp_path, _stack(tmp_path))
    assert result.passed is False
    assert result.skipped_reason is None
    assert result.log_tail == "missing class"


def test_codegen_fallback_preserves_existing_stub_mode(tmp_path, monkeypatch):
    executor = _Executor(
        result=CodegenResult(
            passed=False, log="shape unsupported", fallback_to_llm=True
        )
    )
    monkeypatch.setattr(codegen_registry, "_DEFAULT_EXECUTORS", [executor])
    monkeypatch.delenv("SIMPLICIO_MODEL", raising=False)
    result = _execute_one_task(_task(), tmp_path, _stack(tmp_path))
    assert result.passed is False
    assert result.skipped_reason == "no SIMPLICIO_MODEL set; task generation skipped"
    assert "codegen fallback: shape unsupported" in result.log_tail
