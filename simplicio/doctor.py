"""doctor.py — `simplicio doctor` subcommand.

Prints detected hardware tier + recommended local model + install status.
With --install, opt-in to pulling the recommended model via Ollama. Without
the flag, never touches the disk. With --json, machine-readable output.
"""
from __future__ import annotations

import argparse
import json
import sys

from .hardware import detect
from .local_models import (
    RECOMMENDATIONS,
    ensure_recommended,
    is_installed,
    ollama_list_installed,
    ollama_present,
)


def _render_human(result, profile) -> None:
    print("simplicio doctor", file=sys.stderr)
    print(f"  os            {profile.os_name}")
    if profile.apple_silicon:
        print(f"  chip          {profile.gpu_name} (Apple Silicon, unified memory)")
    print(f"  ram           {profile.ram_gb:.1f} GB"
          f"  ({profile.detected_via.get('ram', '?')})")
    print(f"  gpu / vram    {profile.gpu_name or '(none)':30s} "
          f"{profile.vram_gb:.1f} GB"
          f"  ({profile.detected_via.get('gpu', '?')})")
    print(f"  detected tier {profile.tier}")
    print()
    print("recommended doer model:")
    print(f"  label         {result.spec.label}")
    print(f"  ollama id     {result.spec.ollama_id}")
    print(f"  size (Q4)     ~{result.spec.size_gb_q4:.1f} GB")
    print(f"  notes         {result.spec.notes}")
    print()
    print(f"  ollama        {'installed' if ollama_present() else 'NOT FOUND on PATH'}")
    print(f"  can run       {'yes' if result.can_run else 'NO'}")
    print(f"  can pull      {'yes' if result.can_pull else 'NO'}")
    print(f"  installed     {'YES' if result.installed else 'no'}")
    if result.reason:
        print(f"  status        {result.reason}")
    print()
    if result.installed:
        print("→ set SIMPLICIO_MODEL to use it:")
        print(f"  export SIMPLICIO_MODEL={result.spec.ollama_id}")
        print(f"  export SIMPLICIO_BASE_URL=http://localhost:11434/v1")
        print(f"  export SIMPLICIO_API_KEY=ollama   # any non-empty string works")
    elif result.can_pull:
        print("→ to install:")
        print("  simplicio doctor --install")
        print(f"  (or manually: ollama pull {result.spec.ollama_id})")
    elif not ollama_present():
        print("→ install Ollama first: https://ollama.ai")
    else:
        print("→ hardware is too small for the recommended model; "
              "consider a smaller stack or move to cloud (SIMPLICIO_MODEL = "
              "OpenRouter/HF/etc.)")

    other_installed = [m for m in ollama_list_installed()
                       if m != result.spec.ollama_id]
    if other_installed:
        print()
        print("other Ollama models you have installed:")
        for m in other_installed[:10]:
            print(f"  - {m}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="simplicio doctor")
    p.add_argument("--install", action="store_true",
                   help="opt-in: pull the recommended model via Ollama if not present")
    p.add_argument("--json", action="store_true",
                   help="machine-readable output")
    p.add_argument("--list-tiers", action="store_true",
                   help="print the full hardware → model map and exit")
    args = p.parse_args(argv)

    if args.list_tiers:
        if args.json:
            print(json.dumps({
                tier: {"ollama_id": s.ollama_id, "label": s.label,
                       "size_gb_q4": s.size_gb_q4, "notes": s.notes}
                for tier, s in RECOMMENDATIONS.items()
            }, indent=2))
        else:
            print(f"{'tier':14s}  {'size':>7s}  ollama id")
            print("-" * 80)
            for tier, spec in RECOMMENDATIONS.items():
                print(f"{tier:14s}  {spec.size_gb_q4:5.1f}GB  {spec.ollama_id}")
                print(f"  ↳ {spec.label} — {spec.notes}")
        return 0

    profile = detect()
    result = ensure_recommended(profile, auto_pull=args.install)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    _render_human(result, profile)
    return 0
