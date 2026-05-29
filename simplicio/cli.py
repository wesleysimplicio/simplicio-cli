"""cli.py — commands: index, task, bench, smoke, init, detect.

Heavy imports (numpy, sentence-transformers, openai/anthropic SDKs) are lazy so
that lightweight commands (`init`, `detect`, `--help`) don't pay for them.

First-run auto-bootstrap: if Claude Code (`~/.claude/`) is present and the
UserPromptSubmit hook is missing, the first `simplicio` invocation installs
the skill + hook automatically. Opt-out via `SIMPLICIO_SKIP_AUTO_INIT=1`.
PEP 517 wheels can't run code on `pip install`, so the bootstrap happens on
first CLI use instead — the closest equivalent that works on every machine.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def maybe_autoinstall(cmd: str | None) -> bool:
    """Install skill + hook on first run when Claude Code is detected.

    Returns True iff install actually wrote files. Silent no-op on every
    short-circuit so the CLI never breaks because of auto-activation.
    """
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
    if report.skill_installed or report.hook_script_installed or report.settings_updated:
        print(
            "simplicio: auto-activation installed in Claude Code "
            "(skill + UserPromptSubmit hook). "
            "Disable next time with SIMPLICIO_SKIP_AUTO_INIT=1.",
            file=sys.stderr,
        )
        return True
    return False


def main():
    ap = argparse.ArgumentParser(prog="simplicio")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="index/cache the repo (once, or after changes)")
    pi.add_argument("--root", default="."); pi.add_argument("--stack", default="angular")

    pt = sub.add_parser("task", help="run a task")
    pt.add_argument("goal")
    pt.add_argument("--root", default="."); pt.add_argument("--stack", default="angular")
    pt.add_argument("--target", required=True)
    pt.add_argument("--criteria", default="- true state\n- false state")
    pt.add_argument("--constraints", default="- build passes")


    pb = sub.add_parser("bench", help="compare with vs without (real numbers)")
    pb.add_argument("--root", default="."); pb.add_argument("--stack", default="angular")
    pb.add_argument("--cases", default="bench/cases.json")


    sub.add_parser("smoke", help="one proof call: connect+generate (needs SIMPLICIO_MODEL+KEY)")

    p_init = sub.add_parser("init", help="install skill + UserPromptSubmit hook into ~/.claude/")
    p_init.add_argument("--claude-home", help="override ~/.claude (for tests)")
    p_init.add_argument("--dry-run", action="store_true")

    p_det = sub.add_parser("detect", help="heuristic: is a prompt a code-edit task? (used by hook)")
    p_det.add_argument("--prompt", help="prompt text (default: read from stdin)")
    p_det.add_argument("--quiet", action="store_true")
    p_det.add_argument("--json", action="store_true")

    a = ap.parse_args()
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
    elif a.cmd == "init":
        from .init import main as init_main
        argv = []
        if a.claude_home:
            argv += ["--claude-home", a.claude_home]
        if a.dry_run:
            argv += ["--dry-run"]
        return init_main(argv)
    elif a.cmd == "detect":
        from .detect import main as detect_main
        argv = []
        if a.prompt is not None:
            argv += ["--prompt", a.prompt]
        if a.quiet:
            argv += ["--quiet"]
        if a.json:
            argv += ["--json"]
        return detect_main(argv)
    else:
        from .pipeline import run
        run(a.root, a.stack, a.goal, a.target, a.criteria, a.constraints)

if __name__ == "__main__":
    main()
