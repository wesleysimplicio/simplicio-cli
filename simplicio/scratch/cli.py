"""cli.py — argparse handler for `simplicio scratch ...`.

Wired into simplicio.cli.main; this module never expects to be invoked
directly. Top-level surface:

    simplicio scratch "<goal>" [--stack <slug>] [--planner <provider>]
    simplicio scratch --list-stacks
    simplicio scratch --show-stack <slug>
    simplicio scratch --plan-only "<goal>" --stack <slug>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from ..providers import planner_info
from .planner import PlannerError, generate_plan
from .stack_registry import StackRegistry, slugify_project


def _add_scratch_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("goal", nargs="?", default=None,
                   help="one-line description of the project to create")
    p.add_argument("--stack", default=None,
                   help="explicit stack slug (e.g. py-fastapi); inferred if omitted")
    p.add_argument("--name", default=None,
                   help="project directory name (derived from goal if omitted)")
    p.add_argument("--dest", default=".",
                   help="parent directory where the project dir is created (default: cwd)")
    p.add_argument("--planner", default=None,
                   help="override SIMPLICIO_PLANNER for this run only")
    p.add_argument("--plan-only", action="store_true",
                   help="run planner and print the validated plan; skip execution")
    p.add_argument("--skip-install", action="store_true",
                   help="skip package-manager install after scaffolding")
    p.add_argument("--list-stacks", action="store_true",
                   help="print available stack templates")
    p.add_argument("--show-stack", default=None, metavar="SLUG",
                   help="print readme + metadata for one stack")
    p.add_argument("--json", action="store_true",
                   help="emit machine-readable JSON output where applicable")


def _cmd_list(reg: StackRegistry, as_json: bool) -> int:
    stacks = reg.list()
    if as_json:
        print(json.dumps([{
            "slug": s.slug, "language": s.language, "framework": s.framework,
            "version": s.version,
            "tags": s.meta.get("tags", []),
        } for s in stacks], indent=2))
        return 0
    if not stacks:
        print("(no stack templates installed)")
        return 0
    print(f"{'slug':24s}  {'language':14s}  {'framework':30s}  version")
    print("-" * 86)
    for s in stacks:
        print(f"{s.slug:24s}  {s.language:14s}  {s.framework:30s}  {s.version}")
    return 0


def _cmd_show(reg: StackRegistry, slug: str, as_json: bool) -> int:
    s = reg.get(slug)
    if s is None:
        print(f"unknown stack: {slug}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps({
            "slug": s.slug, "meta": s.meta, "verify": s.verify,
            "readme": s.readme, "practices": s.practices,
        }, indent=2))
        return 0
    print(f"# {s.slug}")
    print(f"language : {s.language}")
    print(f"framework: {s.framework}")
    print(f"version  : {s.version}")
    print(f"verify   : install={s.install_command!r} "
          f"test={s.test_command!r} lint={s.lint_command!r}")
    print()
    print("## README")
    print(s.readme or "(no README)")
    return 0


def _infer_stack(reg: StackRegistry, goal: str) -> str | None:
    """Very small rule-based heuristic. v1 leaves the heavy lift to the planner;
    here we only catch the obvious cases so the user does not have to type
    --stack for common requests."""
    g = goal.lower()
    if any(k in g for k in ("nextjs", "next.js", "next ", "vercel")):
        if reg.get("ts-nextjs"):
            return "ts-nextjs"
    if "fastapi" in g and reg.get("py-fastapi"):
        return "py-fastapi"
    if any(k in g for k in ("axum", "rust ")) and reg.get("rust-axum"):
        return "rust-axum"
    if "laravel" in g and reg.get("php-laravel"):
        return "php-laravel"
    if any(k in g for k in (" go ", "golang", "gin ")) and reg.get("go-gin"):
        return "go-gin"
    return None


def _cmd_scratch(args: argparse.Namespace, reg: StackRegistry) -> int:
    goal = args.goal
    if not goal:
        print("error: provide a goal, e.g. simplicio scratch \"CRUD for condo units\"",
              file=sys.stderr)
        return 2

    stack_slug = args.stack or _infer_stack(reg, goal)
    if not stack_slug:
        print("error: could not infer stack from goal; pass --stack <slug>. "
              "List available with `simplicio scratch --list-stacks`.",
              file=sys.stderr)
        return 2
    stack = reg.get(stack_slug)
    if stack is None:
        print(f"error: unknown stack '{stack_slug}'. Run "
              f"`simplicio scratch --list-stacks`.", file=sys.stderr)
        return 2

    project_name = args.name or slugify_project(goal)

    if args.planner:
        os.environ["SIMPLICIO_PLANNER"] = args.planner

    print(f"[scratch] stack:   {stack.slug} ({stack.language} / {stack.framework})",
          file=sys.stderr)
    print(f"[scratch] project: {project_name}", file=sys.stderr)
    print(f"[scratch] planner: {planner_info()}", file=sys.stderr)
    print(f"[scratch] generating plan...", file=sys.stderr)

    try:
        plan = generate_plan(stack, goal, project_name)
    except PlannerError as e:
        print(f"[scratch] planner failed: {e}", file=sys.stderr)
        return 3

    print(f"[scratch] plan ok: {len(plan.tasks)} tasks", file=sys.stderr)

    if args.plan_only:
        if args.json:
            print(json.dumps({
                "version": plan.version, "stack": plan.stack,
                "project_name": plan.project_name, "rationale": plan.rationale,
                "tasks": [{"id": t.id, "goal": t.goal, "target": t.target,
                           "criteria": t.criteria, "constraints": t.constraints,
                           "verify": t.verify, "depends_on": t.depends_on}
                          for t in plan.tasks],
                "deps_to_install": plan.deps_to_install,
                "deps_dev": plan.deps_dev,
                "test_command": plan.test_command,
                "lint_command": plan.lint_command,
            }, indent=2))
        else:
            print(f"# scratch plan — {plan.project_name}")
            print(f"rationale: {plan.rationale}")
            print(f"tasks: {len(plan.tasks)}")
            for t in plan.tasks:
                deps = f" (depends_on={','.join(t.depends_on) or 'none'})"
                print(f"  - {t.id}{deps}: {t.goal}")
                print(f"     target: {t.target}")
                print(f"     verify: {t.verify}")
        return 0

    from .executor import execute_plan
    try:
        report = execute_plan(plan, stack, Path(args.dest),
                              skip_install=args.skip_install)
    except FileExistsError as e:
        print(f"[scratch] {e}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"[scratch] done: {report.project_dir}", file=sys.stderr)
        print(f"          files written: {len(report.files_written)}", file=sys.stderr)
        print(f"          install: {'ok' if report.install_ok else 'fail/skipped'}",
              file=sys.stderr)
        print(f"          tasks  : {report.tasks_passed}/{report.tasks_total} passed",
              file=sys.stderr)
    return 0 if report.tasks_passed == report.tasks_total else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="simplicio scratch")
    _add_scratch_args(parser)
    args = parser.parse_args(argv)

    reg = StackRegistry()

    if args.list_stacks:
        return _cmd_list(reg, args.json)
    if args.show_stack:
        return _cmd_show(reg, args.show_stack, args.json)
    return _cmd_scratch(args, reg)
