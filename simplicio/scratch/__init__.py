"""simplicio.scratch — from-scratch project creation pipeline.

Two-phase flow (planner + executor) that complements simplicio.task
(single-file edit pipeline). See bench/SCRATCH_MODE_RFC.md.
"""
from .stack_registry import StackRegistry, Stack
from .plan_schema import Plan, validate_plan, PlanValidationError
from .planner import generate_plan, PlannerError
from .executor import execute_plan, ExecutorReport

__all__ = [
    "StackRegistry", "Stack",
    "Plan", "validate_plan", "PlanValidationError",
    "generate_plan", "PlannerError",
    "execute_plan", "ExecutorReport",
]
