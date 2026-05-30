"""Tests for deterministic FastAPI route scratch codegen."""

from __future__ import annotations

import ast
from pathlib import Path

from simplicio.scratch.codegen import PythonAddFastApiRouteExecutor
from simplicio.scratch.codegen import registry as codegen_registry
from simplicio.scratch.plan_schema import Task
from simplicio.scratch.stack_registry import Stack


def _stack(tmp_path: Path) -> Stack:
    return Stack(
        slug="py-fastapi",
        path=tmp_path,
        meta={"language": "Python", "framework": "FastAPI"},
    )


def _task(goal: str = "Add GET `/users/{id}` endpoint to the users route") -> Task:
    return Task(
        id="T02-api-route",
        goal=goal,
        target="src/api/users.py",
        criteria="- exposes @router.get with async handler and return type",
        constraints="- keep existing imports",
        verify="pytest tests/api/test_users.py -q",
    )


def _write_route(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "src/api/users.py"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_python_add_fastapi_route_appends_get_endpoint(tmp_path):
    route_path = _write_route(
        tmp_path,
        """from fastapi import APIRouter

router = APIRouter()
""",
    )

    result = PythonAddFastApiRouteExecutor().execute(
        _task(), tmp_path, _stack(tmp_path)
    )

    assert result.passed is True
    assert result.fallback_to_llm is False
    assert result.files_modified == [route_path]
    updated = route_path.read_text(encoding="utf-8")
    ast.parse(updated)
    assert '@router.get("/users/{id}")' in updated
    assert "async def get_user(id: str) -> dict[str, str]:" in updated
    assert 'return {"id": id}' in updated


def test_python_add_fastapi_route_adds_router_scaffold_when_missing(tmp_path):
    route_path = _write_route(tmp_path, "from fastapi import Depends\n")

    result = PythonAddFastApiRouteExecutor().execute(
        _task("Add POST `/users` route for user creation"),
        tmp_path,
        _stack(tmp_path),
    )

    assert result.passed is True
    updated = route_path.read_text(encoding="utf-8")
    ast.parse(updated)
    assert "from fastapi import Depends, APIRouter" in updated
    assert "router = APIRouter()" in updated
    assert '@router.post("/users")' in updated
    assert "async def create_user() -> dict[str, str]:" in updated


def test_python_add_fastapi_route_falls_back_for_ambiguous_route(tmp_path):
    route_path = _write_route(tmp_path, "router = object()\n")
    original = route_path.read_text(encoding="utf-8")

    result = PythonAddFastApiRouteExecutor().execute(
        _task("Add an endpoint for users"),
        tmp_path,
        _stack(tmp_path),
    )

    assert result.passed is False
    assert result.fallback_to_llm is True
    assert "unsupported FastAPI route task shape" in result.log
    assert route_path.read_text(encoding="utf-8") == original


def test_default_registry_includes_python_add_fastapi_route_executor():
    assert any(
        isinstance(executor, PythonAddFastApiRouteExecutor)
        for executor in codegen_registry.registered_executors()
    )
