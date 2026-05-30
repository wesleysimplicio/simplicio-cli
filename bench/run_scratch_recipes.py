"""Benchmark scratch plan recipes against a mixed synthetic goal corpus.

This measures lever A from the LLM-reduction roadmap: common scratch goals
should instantiate validated declarative plans without calling the planner LLM.
It is keyless and deterministic; it does not replace the real 50-scratch gate.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simplicio.scratch.recipes import RecipeRegistry  # noqa: E402
from simplicio.scratch.stack_registry import slugify_project  # noqa: E402


RESULTS_JSON = ROOT / "bench" / "results_scratch_recipes.json"
RESULTS_MD = ROOT / "bench" / "results_scratch_recipes.md"


@dataclass(frozen=True)
class RecipeCase:
    stack: str
    goal: str
    expected_match: bool
    expected_recipe: str | None = None


def build_cases() -> list[RecipeCase]:
    matched = [
        ("py-fastapi", "CRUD API for Unit", "crud-resource"),
        ("py-fastapi", "REST API for Invoice", "crud-resource"),
        ("py-fastapi", "CRUD API for Visitor", "crud-resource"),
        ("py-fastapi", "REST API for AmenityBooking", "crud-resource"),
        ("py-fastapi", "CRUD API for Vendor", "crud-resource"),
        ("py-fastapi", "admin panel for Booking", "admin-crud"),
        ("py-fastapi", "admin panel for Document", "admin-crud"),
        ("py-fastapi", "admin panel for Resident", "admin-crud"),
        ("py-fastapi", "add JWT auth", "auth-jwt"),
        ("py-fastapi", "login with JWT", "auth-jwt"),
        ("py-fastapi", "authentication with JWT", "auth-jwt"),
        ("py-fastapi", "REST API for ParkingSpace", "crud-resource"),
        ("py-fastapi", "CRUD API for PackageDelivery", "crud-resource"),
        ("py-fastapi", "admin panel for Announcement", "admin-crud"),
        ("py-fastapi", "CRUD API for Payment", "crud-resource"),
        ("ts-nextjs", "Manage Product with CRUD", "crud-resource"),
        ("ts-nextjs", "CRUD page for Unit", "crud-resource"),
        ("ts-nextjs", "Manage Invoice with CRUD", "crud-resource"),
        ("ts-nextjs", "CRUD page for Visitor", "crud-resource"),
        ("ts-nextjs", "Manage Vendor with CRUD", "crud-resource"),
        ("ts-nextjs", "admin CRUD for Tenant", "admin-crud"),
        ("ts-nextjs", "backoffice to manage Subscription", "admin-crud"),
        ("ts-nextjs", "admin CRUD for Booking", "admin-crud"),
        ("ts-nextjs", "authentication with JWT", "auth-jwt"),
        ("ts-nextjs", "login with JWT", "auth-jwt"),
        ("ts-nextjs", "add JWT auth", "auth-jwt"),
        ("ts-nextjs", "Manage Document with CRUD", "crud-resource"),
        ("ts-nextjs", "CRUD page for ParkingSpace", "crud-resource"),
        ("ts-nextjs", "backoffice to manage Payment", "admin-crud"),
        ("ts-nextjs", "Manage AccessDevice with CRUD", "crud-resource"),
    ]
    misses = [
        ("py-fastapi", "Build a recommendation engine for movies"),
        ("py-fastapi", "Analyze CSV exports overnight"),
        ("py-fastapi", "Create websocket chat rooms"),
        ("py-fastapi", "Generate a billing report"),
        ("py-fastapi", "Import legacy XML data"),
        ("py-fastapi", "Build a workflow scheduler"),
        ("py-fastapi", "Create an ML inference gateway"),
        ("py-fastapi", "Synchronize LDAP groups"),
        ("py-fastapi", "Build a search ranking service"),
        ("py-fastapi", "Create a geocoding proxy"),
        ("ts-nextjs", "Create a marketing landing page"),
        ("ts-nextjs", "Render a public docs site"),
        ("ts-nextjs", "Add image optimization pipeline"),
        ("ts-nextjs", "Design a pricing comparison table"),
        ("ts-nextjs", "Build a chart dashboard"),
        ("ts-nextjs", "Create a theme editor"),
        ("ts-nextjs", "Build a map explorer"),
        ("ts-nextjs", "Add offline-first sync"),
        ("ts-nextjs", "Create a video playlist page"),
        ("ts-nextjs", "Build an onboarding wizard"),
    ]
    return [
        RecipeCase(stack, goal, True, recipe) for stack, goal, recipe in matched
    ] + [RecipeCase(stack, goal, False) for stack, goal in misses]


def run_benchmark(cases: list[RecipeCase] | None = None) -> dict[str, Any]:
    registry = RecipeRegistry()
    rows = []
    t0 = time.perf_counter()
    for case in cases or build_cases():
        started = time.perf_counter()
        match = registry.match(case.goal, case.stack)
        plan_valid = False
        task_count = 0
        error = ""
        if match is not None:
            try:
                plan = registry.get(match.recipe_name, match.stack_slug).instantiate(
                    match,
                    slugify_project(case.goal),
                )
                plan_valid = True
                task_count = len(plan.tasks)
            except Exception as exc:  # pragma: no cover - defensive report detail
                error = f"{type(exc).__name__}: {exc}"

        actual_recipe = match.recipe_name if match is not None else None
        rows.append(
            {
                "stack": case.stack,
                "goal": case.goal,
                "expected_match": case.expected_match,
                "expected_recipe": case.expected_recipe,
                "matched": match is not None,
                "actual_recipe": actual_recipe,
                "expected_match_correct": (match is not None) == case.expected_match,
                "expected_recipe_correct": (
                    actual_recipe == case.expected_recipe
                    if case.expected_match
                    else actual_recipe is None
                ),
                "plan_valid": plan_valid,
                "task_count": task_count,
                "planner_calls_saved": 1 if match is not None else 0,
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "error": error,
            }
        )

    elapsed_s = round(time.perf_counter() - t0, 3)
    return {
        "benchmark": "scratch-recipes",
        "scope": (
            "synthetic declarative recipe benchmark; validates match-before-planner "
            "coverage and plan schema integrity but does not replace the real "
            "50-scratch release gate"
        ),
        "date": time.strftime("%Y-%m-%d"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "summary": _summarize(rows, elapsed_s),
        "cases": rows,
    }


def _summarize(rows: list[dict[str, Any]], elapsed_s: float) -> dict[str, Any]:
    total = len(rows)
    matched = sum(1 for row in rows if row["matched"])
    valid = sum(1 for row in rows if row["plan_valid"])
    match_correct = sum(1 for row in rows if row["expected_match_correct"])
    recipe_correct = sum(1 for row in rows if row["expected_recipe_correct"])
    planner_calls_saved = sum(int(row["planner_calls_saved"]) for row in rows)
    match_rate = round(matched / total, 4) if total else 0.0
    summary = {
        "total_cases": total,
        "matched_cases": matched,
        "missed_cases": total - matched,
        "match_rate": match_rate,
        "valid_recipe_plans": valid,
        "expected_match_accuracy": round(match_correct / total, 4) if total else 0.0,
        "expected_recipe_accuracy": round(recipe_correct / total, 4) if total else 0.0,
        "planner_calls_saved": planner_calls_saved,
        "elapsed_s": elapsed_s,
    }
    summary["release_gates"] = {
        "fifty_goal_corpus": total >= 50,
        "recipe_match_ge_40": match_rate >= 0.40,
        "matched_plans_valid": valid == matched,
        "expected_match_accuracy_100": match_correct == total,
        "real_scratch_corpus": False,
        "llm_pass_rate_baseline_present": False,
    }
    summary["missing_release_evidence"] = [
        "real 50-scratch corpus",
        "recipe path pass-rate compared with equivalent LLM planner/doer path",
        "aggregate call-reduction proof across cache, recipes, fixers, and executors",
    ]
    return summary


def write_reports(result: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(result), encoding="utf-8")


def _to_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Scratch Recipe Benchmark",
        "",
        result["scope"],
        "",
        "## Summary",
        "",
        f"- cases: {summary['total_cases']}",
        f"- matched: {summary['matched_cases']}",
        f"- match rate: {summary['match_rate']:.2%}",
        f"- valid recipe plans: {summary['valid_recipe_plans']}",
        f"- planner calls saved: {summary['planner_calls_saved']}",
        "",
        "## Release Gate Status",
        "",
    ]
    for gate, value in summary["release_gates"].items():
        lines.append(f"- {gate}: {value}")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| stack | goal | recipe | matched | plan_valid |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in result["cases"]:
        lines.append(
            "| {stack} | {goal} | {recipe} | {matched} | {valid} |".format(
                stack=row["stack"],
                goal=row["goal"],
                recipe=row["actual_recipe"] or "-",
                matched=row["matched"],
                valid=row["plan_valid"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_benchmark()
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    gates = result["summary"]["release_gates"]
    return 0 if gates["recipe_match_ge_40"] and gates["matched_plans_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
