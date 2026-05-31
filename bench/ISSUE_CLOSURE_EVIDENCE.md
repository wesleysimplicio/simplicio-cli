# GitHub Issue Closure Evidence

Date: 2026-05-31
Repo: `wesleysimplicio/simplicio-dev-cli`
Branch inspected: `codex/finish-github-issues`

This file is a local evidence index for the currently open GitHub issues:
`#32`, `#33`, `#41`, and `#46`.

Recently closed issue tracked here for historical closure evidence: `#37`.
Related implementation PR: `#47`
(`https://github.com/wesleysimplicio/simplicio-dev-cli/pull/47`), currently
open as a draft.

Scope of this artifact:

- No product or core code changes.
- No GitHub issues were closed by this file.
- The goal is to make each issue comment/closure posture explicit from
  repo-local evidence that already exists.

## Current Open Issues

| issue | title | local closure posture |
| --- | --- | --- |
| `#32` | from-scratch mode + planner + SkillOpt | keep open until SkillOpt human approval evidence is supplied |
| `#33` | reduce LLM dependency across simplicio flow | keep open until remaining release evidence is complete |
| `#41` | unified `simplicio run` orchestrator | keep open; F0/F1/F2/F3/F4 foundation plus F5 fixture schema are present, live bench still incomplete |
| `#46` | Qwen2.5-Coder-1.5B GGUF quant curve | keep open; required quant curve artifacts are not present |

## Recently Closed Issues

| issue | title | closure posture |
| --- | --- | --- |
| `#37` | mechanical task executors via libcst/ts-morph | closed on 2026-05-31 as implementation-complete; remaining full-corpus release baseline stays tracked by `#33` |

## Issue #32 Evidence

Status: mostly implemented, but not close-ready under the current release gate.

Repo-local evidence:

- `simplicio/templates/stacks/` contains 30 stack template directories.
- `bench/results_scratch_live_gate.md` records the full 75-run scratch matrix:
  75/75 selected runs, 75/75 e2e green, average cost `0.0`.
- The same live-gate report still records `release ready: False`.
- `bench/results_scratch_live_gate.md` lists the missing release evidence as
  `SkillOpt human approval evidence >=80%`.
- `bench/run_skillopt_review_packet.py` and
  `bench/results_skillopt_review_packet.{json,md}` now provide the pending
  review packet shape accepted by the live gate. It currently records zero
  review-gated generated skills, so it is not approval evidence.
- The same packet runner can now generate review-gated candidate skills from
  `--description` / `--descriptions-file`, then keep them pending with empty
  reviewer/approval fields.
- `bench/run_scratch_live_gate.py` now requires `reviewed_at` on review rows
  and verifies packet-style `path`/`sha256` artifacts before counting a
  SkillOpt approval row.

Suggested comment:

```text
Current local evidence shows the scratch v0.5 matrix is green: 75/75 selected
runs, 75/75 e2e green, average cost 0.0, and 30 stack templates present.
The issue should remain open until real SkillOpt human approval evidence is
attached and the gate reports skillopt_human_approval_ge_80=true.
```

## Issue #33 Evidence

Status: roadmap implementation is strong, but release evidence is still
incomplete.

Repo-local evidence:

- `bench/results_llm_reduction_summary.md` reports local synthetic gates pass.
- The same summary reports modeled local call reduction `19 -> 6`
  and release call proof `210 -> 0`.
- `bench/results_scratch_cache_gate.md` records the full 50-goal cold/warm
  planner cache evidence: 50/50 cold valid, 50/50 warm valid, 100% warm
  hit-rate.
- `bench/results_llm_reduction_summary.md` still lists missing release evidence:
  real scratch LLM baseline for B/codegen pass-rate and latency, plus SkillOpt
  human approval evidence >=80%.
- The SkillOpt review packet runner gives the human-review evidence a stable
  JSON shape, but the aggregate remains incomplete until a real filled packet is
  supplied and the codegen-disabled live baseline reaches the release corpus.
- `simplicio/scratch/executor.py` now records per-task line stats and aggregate
  generated/modified line metrics so future codegen-disabled live baseline
  slices can carry line-count evidence.

Suggested comment:

```text
The repo now has strong release-supporting evidence for the LLM-reduction
roadmap: cache gate 50/50 cold and warm valid with 100% warm hit-rate, scratch
live matrix 75/75 e2e green, and aggregate release call proof 210 -> 0.
I would keep this open until the remaining aggregate gaps are attached:
real scratch LLM baseline for B/codegen pass-rate and latency, and SkillOpt
human approval evidence >=80%.
```

## Issue #37 Evidence

Status: closed on GitHub as implementation-complete for mechanical executors.
The remaining empirical full-corpus baseline is not lost; it remains part of
the broader release-evidence tracking in `#33`.

Repo-local evidence:

- `simplicio/scratch/codegen/` contains executor modules for Python/LibCST,
  TypeScript/ts-morph-backed Next.js generation, Go Gin, PHP Laravel, and
  Rust Axum paths.
- `bench/results_scratch_codegen.md` reports 90/90 deterministic executor
  benchmark cases passed, 100% codegen share, 90 post-validated cases, and
  zero post-validation failures.
- The same report links live scratch-corpus evidence: 75/75 e2e green, 135/135
  codegen tasks, task-level LLM calls 0, and stacks
  `go-gin`, `php-laravel`, `py-fastapi`, `rust-axum`, `ts-nextjs`.
- The same report keeps the full-corpus comparison honest:
  `real_executor_pass_rate_ge_llm` and `real_latency_reduction_ge_50` are not
  proven by a real codegen-disabled live baseline.

Closure note:

```text
Implementation evidence is complete for the mechanical executor slice:
LibCST/ts-morph-backed executor paths are present, the deterministic executor
bench is 90/90 green, and the live scratch corpus shows 75/75 e2e green with
135/135 task executions handled by codegen and 0 task-level LLM calls.

Issue #37 is now closed as implementation-complete. The still-missing
codegen-disabled live baseline for pass-rate and latency remains tracked under
the aggregate release gate in #33.
```

## Issue #41 Evidence

Status: not close-ready, but the first executable slice is now present in this
worktree.

Repo-local evidence:

- `python -m simplicio.cli run --help` now exposes
  `--scope auto|task|feature|sprint|scratch`, `--max-cost`, `--max-iter`, and
  scratch forwarding flags.
- `simplicio/intent.py` now implements a regex-only classifier with explicit
  scope override and confidence threshold.
- `simplicio run --scope task` reuses the existing task primitive and preserves
  the stable JSON payload from `simplicio task`.
- `simplicio/orchestrator/feature.py` now runs feature plans through existing
  task execution and performs bounded replan on failed tasks.
- `simplicio/orchestrator/cost_governor.py` now provides a budget guard;
  `simplicio/providers.py` charges estimated non-cached provider calls when
  `SIMPLICIO_MAX_COST` is configured; and `simplicio run --max-cost` now
  exposes that budget to nested provider calls instead of requiring a manually
  pre-set environment variable.
- `simplicio/sprint_loader.py` and `simplicio/dod.py` provide the first sprint
  task loader and DoD command-gate primitives, while `simplicio status` reads
  the sprint state file written during sprint runs.
- Sprint execution now rejects empty sprints and invalid stacks, resumes from
  previously green feature rows, preserves full task specs when `## Goal` is
  absent, reads sprint-local checklist gates, and blocks unchecked manual DoD
  items.
- Feature execution now orders planned tasks by `depends_on` and reports blocked
  dependency cycles before running tasks.
- Sprint `--max-cost` now rejects negative budgets as usage errors instead of a
  traceback, and feature replan skips previously green task IDs when a revised
  plan repeats them.
- Non-decimal/non-finite `--max-cost` values are rejected as usage errors;
  feature plans with duplicate task IDs fail before executing; and sprint
  resume avoids ambiguous old state when task titles are duplicated.
- `simplicio status --json` now has regression coverage for invalid state files
  returning code `2` with a clear stderr diagnostic and no stdout.
- `bench/run_unified_run_bench.py` plus
  `bench/results_unified_run_bench.{json,md}` provide a fixture-backed F5
  comparison schema for cli+ag, unified feature/sprint, and Codex `/goal`.
  This is explicitly marked fixture-only and not release-ready.
- Validation in this worktree: `python -m pytest tests/python -q` -> `447
  passed, 3 skipped`.

Suggested comment:

```text
The first `simplicio run` slice is now implemented locally: argparse wire-up,
regex-only intent classification, task/scratch dispatch, a feature-scope
planner/runner with bounded replan, `--max-cost` propagation into provider
calls, sprint loading/state/status, sprint resume for already-green features,
stricter DoD gates, and dependency ordering. A fixture-backed F5 bench schema is
also present, but it is intentionally not release evidence: live cli+ag,
unified feature/sprint, and Codex `/goal` runs still need to be captured before
#41 can close.
```

## Issue #46 Evidence

Status: not close-ready.

Repo-local evidence:

- `bench/results_v14_qwen15b_gguf_partial.md` records a partial Q5_K_M run:
  2/12 cases, schema parse 0/8, and approximately 55 minutes per case.
- `bench/smoke_schema_v1.py` is present and provides the cheap 4-call
  schema-v1 go/no-go smoke required before the full expensive quant bench.
- `bench/run_schema_smoke_summary.py` plus
  `bench/results_v14_schema_smoke_summary.{json,md}` now summarize existing and
  future smoke JSON artifacts without claiming the GGUF quant curve is complete.
  The current summary has two legacy smoke inputs and zero Qwen 1.5B GGUF
  schema-v1 smokes; it explicitly reports missing required quants
  `Q8_0`, `Q6_K`, and `Q4_K_M`.
- `bench/run_schema_smoke_summary.py --fail-missing-required-quants` can now
  turn those missing quant smokes into an explicit non-zero gate while keeping
  the default summary command non-failing.
- `bench/RESULTS_LOCAL_GGUF.md` contains older local Q5_K_M vs Q8_0 evidence
  from `bench/run_exec.py`, but it is not the requested v14 schema-v1 quant
  curve.
- No matching required quant-curve result artifacts were found for:
  `bench/results_v14_qwen15b_quant_curve.md`,
  `bench/results_v14_qwen15b_quant_curve.json`,
  or `bench/results_v14_qwen15b_quant_curve.pdf`.

Suggested comment:

```text
Current repo-local evidence is still partial for #46. The Q5_K_M v14 partial
run exists and reports 2/12 cases with schema parse 0/8, `bench/smoke_schema_v1.py`
now exists for the cheap go/no-go smoke, and there is older Q5_K_M vs Q8_0
evidence from `bench/run_exec.py`. The requested schema-v1 quant curve is still
missing: `bench/results_v14_qwen15b_quant_curve.{md,json,pdf}` is not present.
```

## Recommended Next Actions

1. Keep `#32` and `#33` open until SkillOpt human approval evidence is real and
   attached to the release reports.
2. Continue `#41` with sprint UX hardening and the F5 unified-run bench.
3. For `#46`, create the smoke harness and quant-curve reports before running
   the long GGUF matrix.
