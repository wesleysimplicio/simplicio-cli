"""Deterministic code-generation executors for scratch tasks."""

from .go_gin import GoGinCrudExecutor
from .php_laravel import PhpLaravelCrudRoutesExecutor
from .python_fastapi import PythonAddFastApiRouteExecutor
from .python_orm import PythonAddOrmFieldExecutor
from .python_pydantic import PythonAddPydanticSchemaExecutor
from .python_pytest import PythonAddPytestTestExecutor
from .registry import register_executor, registered_executors, try_execute
from .rust_axum import RustAxumCrudExecutor
from .typescript_next_page import TypeScriptAddNextPageExecutor
from .typescript_next_route import TypeScriptAddNextRouteExecutor
from .types import CodegenResult, TaskExecutor

__all__ = [
    "CodegenResult",
    "GoGinCrudExecutor",
    "PhpLaravelCrudRoutesExecutor",
    "PythonAddFastApiRouteExecutor",
    "PythonAddOrmFieldExecutor",
    "PythonAddPydanticSchemaExecutor",
    "PythonAddPytestTestExecutor",
    "RustAxumCrudExecutor",
    "TaskExecutor",
    "TypeScriptAddNextPageExecutor",
    "TypeScriptAddNextRouteExecutor",
    "register_executor",
    "registered_executors",
    "try_execute",
]
