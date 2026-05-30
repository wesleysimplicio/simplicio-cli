"""Deterministic SQLAlchemy ORM model edits for scratch tasks."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from ..plan_schema import Task
from ..stack_registry import Stack
from .python_cst import LibCSTUnavailable, append_statement_to_class, ensure_from_import
from .types import CodegenResult, TaskExecutor


@dataclass(frozen=True)
class _FieldSpec:
    model_name: str
    field_name: str
    mapped_type: str


class PythonAddOrmFieldExecutor(TaskExecutor):
    """Add one SQLAlchemy 2.0 ``Mapped[...]`` field to an existing model."""

    name = "python-add-orm-field"

    def can_handle(self, task: Task, stack: Stack) -> bool:
        if not _is_python_stack(stack):
            return False
        target = task.target.replace("\\", "/").lower()
        if not target.endswith(".py"):
            return False
        if "/src/db/" not in f"/{target}" and "model" not in Path(target).stem:
            return False
        text = _task_text(task).lower()
        return ("field" in text or "column" in text) and (
            "model" in text or "orm" in text or "sqlalchemy" in text
        )

    def execute(self, task: Task, project_dir: Path, stack: Stack) -> CodegenResult:
        spec = _parse_field_spec(task)
        if spec is None:
            return _fallback("unsupported ORM field task shape")

        target = project_dir / task.target
        if not target.is_file():
            return _fallback(f"target file not found: {task.target}")

        original = target.read_text(encoding="utf-8")
        try:
            tree = ast.parse(original)
        except SyntaxError as exc:
            return _fallback(f"target is not valid Python: {exc.msg}")

        model = _find_model_class(tree, spec.model_name)
        if model is None:
            return _fallback(f"could not find SQLAlchemy model class {spec.model_name}")
        if not _looks_like_sqlalchemy_model(model):
            return _fallback(f"class {spec.model_name} is not a SQLAlchemy model")
        if _class_has_field(model, spec.field_name):
            return CodegenResult(
                passed=True,
                files_modified=[],
                log=(
                    f"{spec.model_name}.{spec.field_name} already exists; "
                    "no changes needed"
                ),
            )

        try:
            updated = ensure_from_import(original, "sqlalchemy.orm", "Mapped")
            updated = append_statement_to_class(
                updated,
                spec.model_name,
                f"{spec.field_name}: Mapped[{spec.mapped_type}]\n",
            )
        except LibCSTUnavailable as exc:
            return _fallback(str(exc))
        if updated is None:
            return _fallback(f"could not update class {spec.model_name} with LibCST")

        target.write_text(updated, encoding="utf-8")
        return CodegenResult(
            passed=True,
            files_modified=[target],
            log=(
                f"added {spec.model_name}.{spec.field_name}: Mapped[{spec.mapped_type}] with libcst"
            ),
        )


def _is_python_stack(stack: Stack) -> bool:
    text = f"{stack.slug} {stack.language}".lower()
    return "python" in text or stack.slug.startswith("py-")


def _task_text(task: Task) -> str:
    return "\n".join([task.goal, task.criteria, task.constraints])


def _parse_field_spec(task: Task) -> _FieldSpec | None:
    text = _task_text(task)
    model_name = _parse_model_name(text)
    field_name, mapped_type = _parse_field(text)
    if not model_name or not field_name or not mapped_type:
        return None
    return _FieldSpec(
        model_name=model_name,
        field_name=field_name,
        mapped_type=mapped_type,
    )


def _parse_model_name(text: str) -> str | None:
    patterns = [
        r"\bclass\s+([A-Z][A-Za-z0-9_]*)\b",
        r"`([A-Z][A-Za-z0-9_]*)`\s+(?:ORM\s+)?model\b",
        r"\b([A-Z][A-Za-z0-9_]*)\s+(?:ORM\s+)?model\b",
        r"\b(?:to|on|in)\s+(?:the\s+)?([A-Z][A-Za-z0-9_]*)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _parse_field(text: str) -> tuple[str | None, str | None]:
    explicit = re.search(
        r"\b([a-z_][A-Za-z0-9_]*)\s*:\s*Mapped\[([A-Za-z0-9_., \[\]\"']+)\]",
        text,
    )
    if explicit:
        return explicit.group(1), explicit.group(2).strip()

    name_patterns = [
        r"\badd\s+(?:the\s+)?`?([a-z_][A-Za-z0-9_]*)`?\s+(?:field|column)\b",
        r"\b(?:field|column)\s+`?([a-z_][A-Za-z0-9_]*)`?\b",
    ]
    field_name = None
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            field_name = match.group(1)
            break

    if field_name is None:
        return None, None

    lowered = text.lower()
    if "mapped[str]" in lowered or " string" in lowered or field_name == "email":
        return field_name, "str"
    if "mapped[int]" in lowered or " integer" in lowered:
        return field_name, "int"
    if "mapped[bool]" in lowered or " boolean" in lowered:
        return field_name, "bool"
    return None, None


def _find_model_class(tree: ast.AST, model_name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == model_name:
            return node
    return None


def _looks_like_sqlalchemy_model(node: ast.ClassDef) -> bool:
    if any(_base_name(base) in {"Base", "DeclarativeBase"} for base in node.bases):
        return True
    for item in node.body:
        if isinstance(item, ast.Assign):
            if any(_target_name(target) == "__tablename__" for target in item.targets):
                return True
        if isinstance(item, ast.AnnAssign):
            if _target_name(item.target) == "__tablename__":
                return True
    return False


def _base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _class_has_field(node: ast.ClassDef, field_name: str) -> bool:
    for item in node.body:
        if isinstance(item, ast.AnnAssign):
            if _target_name(item.target) == field_name:
                return True
        if isinstance(item, ast.Assign):
            if any(_target_name(target) == field_name for target in item.targets):
                return True
    return False


def _fallback(log: str) -> CodegenResult:
    return CodegenResult(passed=False, log=log, fallback_to_llm=True)
