"""cli.py — commands: index, task, bench, smoke, init, detect.

Heavy imports (numpy, sentence-transformers, openai/anthropic SDKs) are lazy so
that lightweight commands (`init`, `detect`, `--help`) don't pay for them.
"""
import argparse


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
