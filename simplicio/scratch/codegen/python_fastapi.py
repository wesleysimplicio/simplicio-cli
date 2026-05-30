"""Deterministic FastAPI route edits for scratch tasks."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from ..plan_schema import Task
from ..stack_registry import Stack
from .python_cst import (
    LibCSTUnavailable,
    append_module_statements,
    ensure_from_import,
    insert_module_statement_after_imports,
)
from .types import CodegenResult, TaskExecutor


@dataclass(frozen=True)
class _RouteSpec:
    method: str
    path: str
    function_name: str
    parameters: list[str]


class PythonAddFastApiRouteExecutor(TaskExecutor):
    """Add one small FastAPI route handler to an existing API module."""

    name = "python-add-fastapi-route"

    def can_handle(self, task: Task, stack: Stack) -> bool:
        if not _is_fastapi_stack(stack):
            return False
        target = task.target.replace("\\", "/").lower()
        if not target.endswith(".py") or "/src/api/" not in f"/{target}":
            return False
        text = _task_text(task).lower()
        return "endpoint" in text or "route" in text or "router" in text

    def execute(self, task: Task, project_dir: Path, stack: Stack) -> CodegenResult:
        spec = _parse_route_spec(task)
        if spec is None:
            return _fallback("unsupported FastAPI route task shape")

        target = project_dir / task.target
        if not target.is_file():
            return _fallback(f"target file not found: {task.target}")

        original = target.read_text(encoding="utf-8")
        try:
            tree = ast.parse(original or "\n")
        except SyntaxError as exc:
            return _fallback(f"target is not valid Python: {exc.msg}")

        if _route_exists(tree, spec):
            return CodegenResult(
                passed=True,
                files_modified=[],
                log=f"{spec.method.upper()} {spec.path} already exists; no changes needed",
            )

        newline = _detect_newline(original)
        try:
            updated = ensure_from_import(original, "fastapi", "APIRouter")
            if not _has_router_assignment(ast.parse(updated or "\n")):
                updated = insert_module_statement_after_imports(
                    updated,
                    f"router = APIRouter(){newline}",
                )
            updated = append_module_statements(updated, _render_route(spec, newline))
        except LibCSTUnavailable as exc:
            return _fallback(str(exc))

        target.write_text(updated, encoding="utf-8")
        return CodegenResult(
            passed=True,
            files_modified=[target],
            log=f"added FastAPI {spec.method.upper()} {spec.path} route with libcst",
        )


def _is_fastapi_stack(stack: Stack) -> bool:
    text = f"{stack.slug} {stack.language} {stack.framework}".lower()
    return "fastapi" in text or stack.slug.startswith("py-")


def _task_text(task: Task) -> str:
    return "\n".join([task.goal, task.criteria, task.constraints])


def _parse_route_spec(task: Task) -> _RouteSpec | None:
    text = _task_text(task)
    method = _parse_method(text)
    path = _parse_path(text)
    if path is None:
        return None
    return _RouteSpec(
        method=method,
        path=path,
        function_name=_function_name(method, path, task.target),
        parameters=_path_parameters(path),
    )


def _parse_method(text: str) -> str:
    match = re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\b", text, re.IGNORECASE)
    return match.group(1).lower() if match else "get"


def _parse_path(text: str) -> str | None:
    for pattern in [
        r"`(/[^`]+)`",
        r"['\"](/[^'\"]+)['\"]",
        r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s`'\"]+)",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(match.lastindex or 1)
            if value.startswith("/"):
                return value.rstrip(".,")
    return None


def _path_parameters(path: str) -> list[str]:
    return re.findall(r"{([A-Za-z_][A-Za-z0-9_]*)}", path)


def _function_name(method: str, path: str, target: str) -> str:
    resource = next(
        (part for part in path.split("/") if part and not part.startswith("{")), ""
    )
    if not resource:
        resource = Path(target).stem
    name = re.sub(r"[^A-Za-z0-9_]+", "_", resource).strip("_").lower() or "resource"
    prefix = {
        "get": "get",
        "post": "create",
        "put": "update",
        "patch": "update",
        "delete": "delete",
    }.get(method, method)
    return f"{prefix}_{_singular(name)}"


def _singular(name: str) -> str:
    return name[:-1] if name.endswith("s") and len(name) > 1 else name


def _route_exists(tree: ast.AST, spec: _RouteSpec) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if _decorator_method(decorator.func) != spec.method:
                continue
            if decorator.args and _literal_string(decorator.args[0]) == spec.path:
                return True
    return False


def _decorator_method(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute) and _name(node.value) == "router":
        return node.attr.lower()
    return None


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _has_router_assignment(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(_name(target) == "router" for target in node.targets):
                return True
        if isinstance(node, ast.AnnAssign) and _name(node.target) == "router":
            return True
    return False


def _render_route(spec: _RouteSpec, newline: str) -> str:
    params = ", ".join(f"{param}: str" for param in spec.parameters)
    body = (
        [f'    return {{"{spec.parameters[0]}": {spec.parameters[0]}}}{newline}']
        if spec.parameters
        else [f'    return {{"status": "ok"}}{newline}']
    )
    return "".join(
        [
            f'{newline}@router.{spec.method}("{spec.path}"){newline}',
            f"async def {spec.function_name}({params}) -> dict[str, str]:{newline}",
            *body,
        ]
    )


def _detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _fallback(log: str) -> CodegenResult:
    return CodegenResult(passed=False, log=log, fallback_to_llm=True)
