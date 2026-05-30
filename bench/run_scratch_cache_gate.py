"""Measure cold/warm planner cache behavior for scratch planning.

The LLM-reduction roadmap gate for lever D is about warm dev/CI reruns:
after a scratch plan has been produced once, an identical second pass should
hit the content-addressed completion cache instead of calling the planner.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simplicio._cache import cache, reset_for_tests  # noqa: E402
from simplicio.scratch.planner import PlannerError, generate_plan  # noqa: E402
from simplicio.scratch.stack_registry import StackRegistry, slugify_project  # noqa: E402


RESULTS_JSON = ROOT / "bench" / "results_scratch_cache_gate.json"
RESULTS_MD = ROOT / "bench" / "results_scratch_cache_gate.md"
LIVE_GATE_JSON = ROOT / "bench" / "results_scratch_live_gate.json"

CACHE_GOALS = (
    "Build a FastAPI audit log service with export filters and retention policy",
    "Build a FastAPI feature flag service with rollout rules and audit trail",
    "Build a FastAPI webhook ingestion service with replay controls",
    "Build a FastAPI data export service with signed download links",
    "Build a FastAPI notification preference service with channel rules",
    "Build a FastAPI incident escalation service with severity routing",
    "Build a FastAPI maintenance scheduling service with recurring windows",
    "Build a FastAPI resident profile merge service with conflict reports",
    "Build a FastAPI document indexing service with access policy checks",
    "Build a FastAPI visitor preapproval service with expiry reminders",
    "Build a FastAPI package pickup workflow with identity verification",
    "Build a FastAPI payment reconciliation service with exception queues",
    "Build a FastAPI amenity capacity service with blackout dates",
    "Build a FastAPI parking allocation service with waitlist promotion",
    "Build a FastAPI vendor insurance tracker with renewal alerts",
    "Build a FastAPI board vote recording service with quorum rules",
    "Build a FastAPI announcement targeting service with audience segments",
    "Build a FastAPI key fob lifecycle service with revocation audits",
    "Build a FastAPI work order triage service with SLA timers",
    "Build a FastAPI occupancy analytics service with monthly summaries",
    "Build a FastAPI service request intake flow with duplicate detection",
    "Build a FastAPI lease compliance service with document reminders",
    "Build a FastAPI inspection checklist service with photo evidence slots",
    "Build a FastAPI utility meter ingestion service with anomaly flags",
    "Build a FastAPI budget variance service with approval thresholds",
    "Build a FastAPI invoice dispute workflow with reviewer assignment",
    "Build a FastAPI procurement quote comparison service with scoring",
    "Build a FastAPI security patrol log service with geofence events",
    "Build a FastAPI elevator outage notification service with ETA updates",
    "Build a FastAPI pool access rule service with seasonal schedules",
    "Build a FastAPI guest parking permit service with plate validation",
    "Build a FastAPI storage locker assignment service with waitlist rules",
    "Build a FastAPI pet registration service with vaccine reminders",
    "Build a FastAPI move-in coordination service with deposit tracking",
    "Build a FastAPI architectural request review service with attachments",
    "Build a FastAPI violation notice workflow with appeal deadlines",
    "Build a FastAPI insurance claim tracker with status milestones",
    "Build a FastAPI emergency contact broadcast service with opt-out rules",
    "Build a FastAPI reserve study task service with funding categories",
    "Build a FastAPI janitorial route tracker with completion evidence",
    "Build a FastAPI landscaping issue queue with seasonal priorities",
    "Build a FastAPI snow removal dispatch service with weather holds",
    "Build a FastAPI energy usage report service with building comparisons",
    "Build a FastAPI noise complaint workflow with quiet-hour policies",
    "Build a FastAPI access camera incident log with retention controls",
    "Build a FastAPI owner portal preference service with language settings",
    "Build a FastAPI meeting agenda builder with attachment ordering",
    "Build a FastAPI contractor onboarding service with credential checks",
    "Build a FastAPI warranty inventory service with expiration alerts",
    "Build a FastAPI recurring assessment calculator with proration rules",
)


def run_cache_gate(
    *,
    work_dir: Path,
    stack_slug: str = "py-fastapi",
    goals: tuple[str, ...] = CACHE_GOALS,
    clear_cache: bool = True,
    live_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not goals:
        raise ValueError("at least one goal is required")

    work_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = work_dir / "cache"
    if clear_cache and cache_dir.exists():
        shutil.rmtree(cache_dir)

    previous_cache_dir = os.environ.get("SIMPLICIO_CACHE_DIR")
    previous_bust = os.environ.get("SIMPLICIO_BUST_CACHE")
    os.environ["SIMPLICIO_CACHE_DIR"] = str(cache_dir)
    os.environ["SIMPLICIO_BUST_CACHE"] = "0"

    registry = StackRegistry()
    stack = registry.get(stack_slug)
    if stack is None:
        raise ValueError(f"unknown stack: {stack_slug}")

    try:
        cold_rows, cold_stats, cold_elapsed = _run_pass(
            pass_name="cold",
            stack=stack,
            goals=goals,
        )
        reset_for_tests()
        warm_rows, warm_stats, warm_elapsed = _run_pass(
            pass_name="warm",
            stack=stack,
            goals=goals,
        )
    finally:
        reset_for_tests()
        if previous_cache_dir is None:
            os.environ.pop("SIMPLICIO_CACHE_DIR", None)
        else:
            os.environ["SIMPLICIO_CACHE_DIR"] = previous_cache_dir
        if previous_bust is None:
            os.environ.pop("SIMPLICIO_BUST_CACHE", None)
        else:
            os.environ["SIMPLICIO_BUST_CACHE"] = previous_bust

    live_corpus = _normalize_live_corpus(live_gate) if live_gate else None
    summary = _summarize(
        cold_rows,
        warm_rows,
        cold_stats,
        warm_stats,
        live_corpus=live_corpus,
    )
    return {
        "benchmark": "scratch-cache-gate",
        "scope": (
            "cold/warm scratch planner cache measurement; this proves planner "
            "cache replay for identical prompts. Optional live-gate input links "
            "the cache evidence to the shared real scratch release corpus without "
            "overstating the cold/warm sample size."
        ),
        "date": time.strftime("%Y-%m-%d"),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "planner": os.environ.get("SIMPLICIO_PLANNER", "<default>"),
        },
        "stack": stack_slug,
        "cache_dir": "$WORK_DIR/cache",
        "cold_elapsed_s": cold_elapsed,
        "warm_elapsed_s": warm_elapsed,
        "cold_stats": cold_stats,
        "warm_stats": warm_stats,
        "live_corpus": live_corpus,
        "summary": summary,
        "cold_cases": cold_rows,
        "warm_cases": warm_rows,
    }


def _run_pass(
    *, pass_name: str, stack: Any, goals: tuple[str, ...]
) -> tuple[list[dict[str, Any]], dict[str, Any], float]:
    reset_for_tests()
    rows = []
    t0 = time.perf_counter()
    for goal in goals:
        started = time.perf_counter()
        project_name = slugify_project(goal)[:60].rstrip("-") or "scratch-cache"
        try:
            plan = generate_plan(stack, goal, project_name)
            rows.append(
                {
                    "pass": pass_name,
                    "goal": goal,
                    "project_name": project_name,
                    "passed": True,
                    "tasks": len(plan.tasks),
                    "duration_ms": int((time.perf_counter() - started) * 1000),
                }
            )
        except PlannerError as exc:
            rows.append(
                {
                    "pass": pass_name,
                    "goal": goal,
                    "project_name": project_name,
                    "passed": False,
                    "tasks": 0,
                    "duration_ms": int((time.perf_counter() - started) * 1000),
                    "error": str(exc)[:1000],
                }
            )
    return rows, cache().stats(), round(time.perf_counter() - t0, 3)


def _summarize(
    cold_rows: list[dict[str, Any]],
    warm_rows: list[dict[str, Any]],
    cold_stats: dict[str, Any],
    warm_stats: dict[str, Any],
    live_corpus: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cold_passed = sum(1 for row in cold_rows if row.get("passed"))
    warm_passed = sum(1 for row in warm_rows if row.get("passed"))
    total = len(warm_rows)
    warm_hit_rate = float(warm_stats.get("hit_rate", 0.0))
    live_total = int((live_corpus or {}).get("total_runs", 0))
    live_e2e_green = int((live_corpus or {}).get("e2e_green", 0))
    measured_real_corpus = total >= 50
    linked_real_corpus = live_total >= 50 and live_e2e_green >= 50
    missing = []
    if not linked_real_corpus:
        missing.append("50 real scratch goals across the release corpus")
    if not measured_real_corpus:
        missing.append(
            "planner cache hit-rate measured across cold/warm real scratch runs"
        )
    return {
        "total_goals": total,
        "cold_plans_valid": cold_passed,
        "warm_plans_valid": warm_passed,
        "warm_hit_rate": warm_hit_rate,
        "warm_hits": int(warm_stats.get("hits", 0)),
        "warm_misses": int(warm_stats.get("misses", 0)),
        "cold_puts": int(cold_stats.get("puts", 0)),
        "release_gates": {
            "warm_hit_rate_ge_80": warm_hit_rate >= 0.80,
            "warm_plans_all_valid": warm_passed == total,
            "cold_populated_cache": int(cold_stats.get("puts", 0)) >= cold_passed,
            "real_50_scratch_corpus": linked_real_corpus,
            "cold_warm_measured_on_50_real_scratches": measured_real_corpus,
        },
        "live_corpus": live_corpus,
        "missing_release_evidence": missing,
    }


def load_live_gate(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _normalize_live_corpus(raw, source=_source_label(path))


def _normalize_live_corpus(
    live_gate: dict[str, Any],
    *,
    source: str | None = None,
) -> dict[str, Any]:
    if "runs" not in live_gate:
        return {
            "source": live_gate.get("source") or source or "inline",
            "total_runs": int(live_gate.get("total_runs", 0)),
            "e2e_green": int(live_gate.get("e2e_green", 0)),
            "e2e_green_rate": float(live_gate.get("e2e_green_rate", 0.0)),
            "stacks": sorted(live_gate.get("stacks", [])),
        }

    runs = live_gate.get("runs")
    rows = []
    for run in runs if isinstance(runs, list) else []:
        stack = str(run.get("stack") or "")
        goal = str(run.get("goal") or "")
        if not stack or not goal:
            continue
        rows.append(
            {
                "stack": stack,
                "goal": goal,
                "e2e_green": bool(run.get("e2e_green")),
            }
        )

    total = len(rows)
    e2e_green = sum(1 for row in rows if row["e2e_green"])
    return {
        "source": live_gate.get("source") or source or "inline",
        "total_runs": total,
        "e2e_green": e2e_green,
        "e2e_green_rate": round(e2e_green / total, 4) if total else 0.0,
        "stacks": sorted({row["stack"] for row in rows}),
        "cases": rows,
    }


def _source_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_reports(result: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(result), encoding="utf-8")


def _to_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Scratch Planner Cache Gate",
        "",
        result["scope"],
        "",
        "## Summary",
        "",
        f"- goals: {summary['total_goals']}",
        f"- cold valid plans: {summary['cold_plans_valid']}",
        f"- warm valid plans: {summary['warm_plans_valid']}",
        f"- warm cache hit-rate: {summary['warm_hit_rate']:.2%}",
        f"- warm hits/misses: {summary['warm_hits']}/{summary['warm_misses']}",
        f"- cold cache puts: {summary['cold_puts']}",
        "",
    ]
    live = summary.get("live_corpus")
    if live:
        lines.extend(
            [
                "## Live Corpus Link",
                "",
                f"- source: {live.get('source', 'inline')}",
                f"- runs: {live.get('total_runs', 0)}",
                f"- e2e green: {live.get('e2e_green', 0)}",
                f"- e2e green rate: {float(live.get('e2e_green_rate', 0.0)):.2%}",
                f"- stacks: {', '.join(live.get('stacks', [])) or '-'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Release Gate Status",
            "",
        ]
    )
    for gate, value in summary["release_gates"].items():
        lines.append(f"- {gate}: {value}")
    if summary["missing_release_evidence"]:
        lines.extend(["", "## Missing Release Evidence", ""])
        for item in summary["missing_release_evidence"]:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Warm Cases",
            "",
            "| goal | passed | tasks | duration_ms |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in result["warm_cases"]:
        lines.append(
            f"| {row['goal']} | {row['passed']} | {row['tasks']} | {row['duration_ms']} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--stack", default="py-fastapi")
    parser.add_argument("--goal-limit", type=int, default=len(CACHE_GOALS))
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument(
        "--live-gate-json",
        type=Path,
        default=None,
        help="Path to scratch live-gate JSON used to link cache evidence to the real corpus.",
    )
    parser.add_argument("--keep-cache", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    goals = CACHE_GOALS[: max(0, args.goal_limit)]
    result = run_cache_gate(
        work_dir=args.work_dir,
        stack_slug=args.stack,
        goals=goals,
        clear_cache=not args.keep_cache,
        live_gate=load_live_gate(args.live_gate_json) if args.live_gate_json else None,
    )
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    gates = result["summary"]["release_gates"]
    return 0 if gates["warm_hit_rate_ge_80"] and gates["warm_plans_all_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
