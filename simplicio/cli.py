"""CLI entrypoint for simplicio."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def maybe_autoinstall(cmd: str | None) -> bool:
    """Install skill + hook on first run when Claude Code is detected."""
    if os.environ.get("SIMPLICIO_SKIP_AUTO_INIT"):
        return False
    if cmd in ("init", "detect"):
        return False
    home = Path(os.environ["HOME"]) if os.environ.get("HOME") else Path.home()
    claude_home = home / ".claude"
    if not claude_home.is_dir():
        return False
    hook_path = claude_home / "hooks" / "simplicio-userpromptsubmit.sh"
    if hook_path.exists():
        return False
    try:
        from .init import install

        report = install(claude_home=claude_home, dry_run=False)
    except Exception as e:
        print(f"simplicio: auto-activation skipped ({e})", file=sys.stderr)
        return False
    if (
        report.skill_installed
        or report.hook_script_installed
        or report.settings_updated
    ):
        print(
            "simplicio: auto-activation installed in Claude Code "
            "(skill + UserPromptSubmit hook). "
            "Disable next time with SIMPLICIO_SKIP_AUTO_INIT=1.",
            file=sys.stderr,
        )
        return True
    return False


def _dispatch_nested(argv: list[str]) -> int | None:
    if argv and argv[0] == "scratch":
        maybe_autoinstall("scratch")
        from .scratch.cli import main as scratch_main

        return scratch_main(argv[1:])
    if argv and argv[0] == "skill":
        maybe_autoinstall("skill")
        args = argv[1:]
        if not args or args[0] != "new":
            print(
                'usage: simplicio skill new "<description>" [--planner ...] [--dry-run]',
                file=sys.stderr,
            )
            return 2
        from .scratch.skill_opt import main as skill_main

        return skill_main(args[1:])
    return None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    nested = _dispatch_nested(argv)
    if nested is not None:
        return nested

    ap = argparse.ArgumentParser(prog="simplicio")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="index/cache the repo (once, or after changes)")
    pi.add_argument("--root", default=".")
    pi.add_argument("--stack", default="angular")

    pt = sub.add_parser("task", help="run a task")
    pt.add_argument("goal")
    pt.add_argument("--root", default=".")
    pt.add_argument("--stack", default="angular")
    pt.add_argument("--target", required=True)
    pt.add_argument("--criteria", default="- true state\n- false state")
    pt.add_argument("--constraints", default="- build passes")
    pt.add_argument(
        "--dry-run-task",
        action="store_true",
        help="generate the would-be task output without applying/testing",
    )
    pt.add_argument(
        "--json", action="store_true", help="emit stable structured task output"
    )
    pt.add_argument(
        "--bound-paths",
        action="append",
        default=[],
        help="glob limiting which paths the task may change; repeatable",
    )

    pb = sub.add_parser("bench", help="compare with vs without (real numbers)")
    pb.add_argument("--root", default=".")
    pb.add_argument("--stack", default="angular")
    pb.add_argument("--cases", default="bench/cases.json")

    pc = sub.add_parser("cache", help="inspect or clear completion cache")
    pc_sub = pc.add_subparsers(dest="cache_cmd", required=True)
    pc_stats = pc_sub.add_parser("stats", help="print completion cache statistics")
    pc_stats.add_argument("--json", action="store_true")
    pc_clear = pc_sub.add_parser("clear", help="clear completion cache")
    pc_clear.add_argument("--force", action="store_true", help="required to clear")

    sub.add_parser(
        "smoke", help="one proof call: connect+generate (needs SIMPLICIO_MODEL+KEY)"
    )

    p_init = sub.add_parser(
        "init", help="install skill + UserPromptSubmit hook into ~/.claude/"
    )
    p_init.add_argument("--claude-home", help="override ~/.claude (for tests)")
    p_init.add_argument("--dry-run", action="store_true")

    p_det = sub.add_parser("detect", help="heuristic: is a prompt a code-edit task")
    p_det.add_argument("--prompt", help="prompt text (default: read from stdin)")
    p_det.add_argument("--quiet", action="store_true")
    p_det.add_argument("--json", action="store_true")

    a = ap.parse_args(argv)
    maybe_autoinstall(a.cmd)
    if a.cmd == "index":
        from .precedent import index_repo

        index_repo(a.root, a.stack)
    elif a.cmd == "smoke":
        from .providers import generate, info

        print("provider:", info())
        out = generate("Reply exactly: OK simplicio connected.")
        print("model reply:", out.strip()[:200])
    elif a.cmd == "bench":
        from .bench import run_bench

        run_bench(a.root, a.stack, a.cases)
    elif a.cmd == "cache":
        from ._cache import cache

        c = cache()
        if a.cache_cmd == "stats":
            stats = c.stats()
            if a.json:
                print(json.dumps(stats, sort_keys=True))
            else:
                print(f"root: {stats['root']}")
                print(f"enabled: {stats['enabled']}  bust: {stats['bust']}")
                print(f"entries: {stats['entries']}  size: {stats['mb']} MB")
                print(f"ttl_days: {stats['ttl_days']}  max_mb: {stats['max_mb']}")
            return 0
        if a.cache_cmd == "clear":
            if not a.force:
                print("simplicio cache clear requires --force", file=sys.stderr)
                return 2
            removed = c.clear()
            print(f"cleared {removed} cached completion(s)")
            return 0
    elif a.cmd == "init":
        from .init import main as init_main

        init_argv = []
        if a.claude_home:
            init_argv += ["--claude-home", a.claude_home]
        if a.dry_run:
            init_argv += ["--dry-run"]
        return init_main(init_argv)
    elif a.cmd == "detect":
        from .detect import main as detect_main

        detect_argv = []
        if a.prompt is not None:
            detect_argv += ["--prompt", a.prompt]
        if a.quiet:
            detect_argv += ["--quiet"]
        if a.json:
            detect_argv += ["--json"]
        return detect_main(detect_argv)
    else:
        from .pipeline import run, run_task

        if a.json or a.dry_run_task:
            result = run_task(
                a.root,
                a.stack,
                a.goal,
                a.target,
                a.criteria,
                a.constraints,
                dry_run_task=a.dry_run_task,
                bound_paths=a.bound_paths,
                quiet=a.json,
            )
            if a.json:
                print(json.dumps(result, sort_keys=True))
            else:
                status = "DRY-RUN" if a.dry_run_task else "DONE"
                print(f"{status}: {result['diff_summary']}")
                for warning in result["warnings"]:
                    print(f"warning: {warning}", file=sys.stderr)
            return 0 if (a.dry_run_task or result["applied"]) else 1
        run(
            a.root,
            a.stack,
            a.goal,
            a.target,
            a.criteria,
            a.constraints,
            bound_paths=a.bound_paths,
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
