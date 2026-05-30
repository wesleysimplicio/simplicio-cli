"""Benchmark static verify-loop fixers with a synthetic retry corpus.

The runner exercises the real pipeline retry loop and real static fixer
dispatch while replacing external package installs and LLM generation with
deterministic fakes. It proves the measurement path for lever C, not the full
50-real-scratch release gate.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simplicio import pipeline  # noqa: E402
from simplicio.pipeline_fixers import FixerResult  # noqa: E402
from simplicio.pipeline_fixers import try_static_fixers as real_try_static_fixers  # noqa: E402


RESULTS_JSON = ROOT / "bench" / "results_static_fixers.json"
RESULTS_MD = ROOT / "bench" / "results_static_fixers.md"


@dataclass(frozen=True)
class FixerCase:
    name: str
    failure_log: str
    resolvable: bool


@dataclass(frozen=True)
class RealPackageCase:
    name: str
    module: str
    package: str


def build_cases() -> list[FixerCase]:
    cases: list[FixerCase] = []
    for idx in range(1, 41):
        cases.append(
            FixerCase(
                name=f"missing-pip-{idx:02d}",
                failure_log="ModuleNotFoundError: No module named 'fastapi'",
                resolvable=True,
            )
        )
    for idx in range(1, 11):
        cases.append(
            FixerCase(
                name=f"assertion-{idx:02d}",
                failure_log="AssertionError: expected 200 got 500",
                resolvable=False,
            )
        )
    return cases


def build_real_package_cases(repeat: int = 2) -> list[RealPackageCase]:
    packages = [
        RealPackageCase("packaging", "packaging", "packaging"),
        RealPackageCase("colorama", "colorama", "colorama"),
        RealPackageCase("idna", "idna", "idna"),
        RealPackageCase("certifi", "certifi", "certifi"),
        RealPackageCase(
            "charset-normalizer",
            "charset_normalizer",
            "charset-normalizer",
        ),
    ]
    return [
        RealPackageCase(f"{case.name}-{idx:02d}", case.module, case.package)
        for idx in range(1, repeat + 1)
        for case in packages
    ]


def run_benchmark(
    *,
    work_dir: Path | None = None,
    real_package_manager_probe: bool = False,
    real_probe_repeat: int = 2,
) -> dict[str, Any]:
    owned_temp = False
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="simplicio-static-fixers-"))
        owned_temp = True
    work_dir.mkdir(parents=True, exist_ok=True)

    old_generate = pipeline.generate
    old_build_prompt = pipeline.build_prompt
    old_apply_and_test = pipeline._apply_and_test
    old_try_static_fixers = pipeline.try_static_fixers

    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    try:
        for case in build_cases():
            baseline = _run_case(case, work_dir / "baseline" / case.name, False)
            with_fixer = _run_case(case, work_dir / "with-fixer" / case.name, True)
            rows.append(_row(case, baseline, with_fixer))
    finally:
        pipeline.generate = old_generate
        pipeline.build_prompt = old_build_prompt
        pipeline._apply_and_test = old_apply_and_test
        pipeline.try_static_fixers = old_try_static_fixers

    real_probe_rows = (
        run_real_package_manager_probe(
            work_dir=work_dir / "real-package-manager",
            repeat=real_probe_repeat,
        )
        if real_package_manager_probe
        else []
    )
    elapsed_s = round(time.perf_counter() - t0, 3)
    return {
        "benchmark": "static-fixers",
        "scope": (
            "synthetic verify-loop fixer benchmark with optional real package-manager "
            "probe; does not replace the full 50-scratch gate"
        ),
        "work_dir": "$WORK_DIR",
        "work_dir_owned_by_runner": owned_temp,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "summary": _summarize(rows, elapsed_s, real_probe_rows),
        "cases": rows,
        "real_package_manager_cases": real_probe_rows,
    }


def _run_case(case: FixerCase, root: Path, fixer_enabled: bool) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = []\n',
        encoding="utf-8",
    )

    generate_calls: list[str | None] = []
    fixer_calls: list[FixerResult] = []

    def fake_generate(prompt: str, feedback: str | None = None) -> str:
        generate_calls.append(feedback)
        attempt = "SECOND_ATTEMPT" if len(generate_calls) > 1 else "FIRST_ATTEMPT"
        return _valid_pipeline_diff(attempt)

    def fake_apply_and_test(
        output: str,
        run_root: str,
        bound_paths: list[str] | None = None,
    ) -> tuple[bool, str]:
        text = output or ""
        pyproject = Path(run_root) / "pyproject.toml"
        if "SECOND_ATTEMPT" in text:
            return True, "1 passed after LLM retry"
        if case.resolvable and '"fastapi"' in pyproject.read_text(encoding="utf-8"):
            return True, "1 passed after static fixer"
        return False, case.failure_log

    def fake_runner(
        argv: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "", "")

    def patched_fixers(log: str, run_root: str | Path) -> FixerResult:
        if not fixer_enabled:
            result = FixerResult("none", False, "disabled synthetic baseline")
        else:
            result = real_try_static_fixers(log, run_root, runner=fake_runner)
        fixer_calls.append(result)
        return result

    pipeline.generate = fake_generate
    pipeline.build_prompt = lambda *args, **kwargs: "prompt"
    pipeline._apply_and_test = fake_apply_and_test
    pipeline.try_static_fixers = patched_fixers

    result = pipeline.run_task(
        str(root),
        "python",
        "add api",
        "src/app.py",
        "- passes",
        "- small",
        quiet=True,
    )

    return {
        "applied": result["applied"],
        "llm_calls": len(generate_calls),
        "fixer_calls": len(fixer_calls),
        "fixer_applied": any(item.applied for item in fixer_calls),
        "fixers": [item.fixer for item in fixer_calls],
    }


def _row(
    case: FixerCase,
    baseline: dict[str, Any],
    with_fixer: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": case.name,
        "resolvable": case.resolvable,
        "baseline_llm_calls": baseline["llm_calls"],
        "with_fixer_llm_calls": with_fixer["llm_calls"],
        "retry_calls_saved": baseline["llm_calls"] - with_fixer["llm_calls"],
        "fixed_before_llm_retry": bool(
            with_fixer["fixer_applied"] and with_fixer["llm_calls"] == 1
        ),
        "fixers": with_fixer["fixers"],
        "passed": baseline["applied"] and with_fixer["applied"],
    }


def run_real_package_manager_probe(
    *,
    work_dir: Path,
    repeat: int = 2,
    runner=None,
) -> list[dict[str, Any]]:
    work_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in build_real_package_cases(repeat):
        root = work_dir / case.name
        root.mkdir(parents=True, exist_ok=True)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "probe"\ndependencies = []\n',
            encoding="utf-8",
        )
        started = time.perf_counter()
        result = real_try_static_fixers(
            f"ModuleNotFoundError: No module named '{case.module}'",
            root,
            runner=runner,
        )
        pyproject = root / "pyproject.toml"
        declared = case.package in pyproject.read_text(encoding="utf-8")
        import_ok = (
            _check_import(case.module)
            if result.applied and runner is None
            else result.applied
        )
        rows.append(
            {
                "name": case.name,
                "module": case.module,
                "package": case.package,
                "fixer": result.fixer,
                "applied": result.applied,
                "details": result.details,
                "dependency_declared": declared,
                "import_ok": import_ok,
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "passed": result.applied and declared and import_ok,
            }
        )
    return rows


def _check_import(module: str) -> bool:
    proc = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0


def _summarize(
    rows: list[dict[str, Any]],
    elapsed_s: float,
    real_probe_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    real_probe_rows = real_probe_rows or []
    total = len(rows)
    passed = sum(1 for row in rows if row["passed"])
    fixed = sum(1 for row in rows if row["fixed_before_llm_retry"])
    baseline_calls = sum(int(row["baseline_llm_calls"]) for row in rows)
    with_fixer_calls = sum(int(row["with_fixer_llm_calls"]) for row in rows)
    reduction = (
        (baseline_calls - with_fixer_calls) / baseline_calls if baseline_calls else 0.0
    )
    real_total = len(real_probe_rows)
    real_passed = sum(1 for row in real_probe_rows if row.get("passed"))
    summary = {
        "total_cases": total,
        "passed_cases": passed,
        "fixer_resolved_before_retry": fixed,
        "fixer_resolved_rate": round(fixed / total, 4) if total else 0.0,
        "baseline_llm_calls": baseline_calls,
        "with_fixer_llm_calls": with_fixer_calls,
        "retry_call_reduction": round(reduction, 4),
        "real_package_manager_cases": real_total,
        "real_package_manager_passed": real_passed,
        "elapsed_s": elapsed_s,
        "release_gates": {
            "fifty_cases": total >= 50,
            "fixer_resolved_ge_80": fixed / total >= 0.80 if total else False,
            "retry_calls_down_ge_30": reduction >= 0.30,
            "real_package_manager_execution": real_total > 0
            and real_passed == real_total,
            "real_scratch_corpus": False,
        },
        "missing_release_evidence": [
            "real install/import/lint failures from 50 scratch runs",
            "comparison across actual scratch reports",
        ],
    }
    if not summary["release_gates"]["real_package_manager_execution"]:
        summary["missing_release_evidence"].insert(
            1,
            "non-faked package manager execution",
        )
    return summary


def _valid_pipeline_diff(marker: str) -> str:
    return "\n".join(
        [
            "diff --git a/src/app.py b/src/app.py",
            "--- a/src/app.py",
            "+++ b/src/app.py",
            "@@ -0,0 +1 @@",
            f"+print('{marker}')",
            "",
            "TEST: pytest -q",
        ]
    )


def write_reports(result: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_to_markdown(result), encoding="utf-8")


def _to_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Static Fixers Benchmark",
        "",
        result["scope"],
        "",
        "## Summary",
        "",
        f"- cases: {summary['passed_cases']}/{summary['total_cases']} passed",
        f"- fixed before LLM retry: {summary['fixer_resolved_rate']:.2%}",
        f"- baseline LLM calls: {summary['baseline_llm_calls']}",
        f"- with-fixer LLM calls: {summary['with_fixer_llm_calls']}",
        f"- retry-call reduction: {summary['retry_call_reduction']:.2%}",
        f"- real package-manager probe: {summary['real_package_manager_passed']}/{summary['real_package_manager_cases']}",
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
            "| case | fixed_before_retry | baseline_calls | with_fixer_calls | passed |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["cases"]:
        lines.append(
            "| {name} | {fixed} | {baseline} | {with_fixer} | {passed} |".format(
                name=row["name"],
                fixed=row["fixed_before_llm_retry"],
                baseline=row["baseline_llm_calls"],
                with_fixer=row["with_fixer_llm_calls"],
                passed=row["passed"],
            )
        )
    real_rows = result.get("real_package_manager_cases") or []
    if real_rows:
        lines.extend(
            [
                "",
                "## Real Package-Manager Probe",
                "",
                "| case | package | applied | dependency_declared | import_ok | passed | duration_ms |",
                "| --- | --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for row in real_rows:
            lines.append(
                "| {name} | {package} | {applied} | {declared} | {import_ok} | {passed} | {duration} |".format(
                    name=row["name"],
                    package=row["package"],
                    applied=row["applied"],
                    declared=row["dependency_declared"],
                    import_ok=row["import_ok"],
                    passed=row["passed"],
                    duration=row["duration_ms"],
                )
            )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--real-package-manager-probe", action="store_true")
    parser.add_argument("--real-probe-repeat", type=int, default=2)
    parser.add_argument("--json-output", type=Path, default=RESULTS_JSON)
    parser.add_argument("--md-output", type=Path, default=RESULTS_MD)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_benchmark(
        work_dir=args.work_dir,
        real_package_manager_probe=args.real_package_manager_probe,
        real_probe_repeat=args.real_probe_repeat,
    )
    write_reports(result, args.json_output, args.md_output)
    if not args.quiet:
        print(json.dumps(result["summary"], indent=2, sort_keys=True))
        print(f"wrote {args.json_output}")
        print(f"wrote {args.md_output}")
    return (
        0
        if result["summary"]["passed_cases"] == result["summary"]["total_cases"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
