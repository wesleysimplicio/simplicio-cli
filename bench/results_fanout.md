# Fan-out benchmark — regex vs functional, 4 models × N ∈ {64, 200, 600}

Date: **2026-05-28**  
Engine: `kernel.subagent_runtime.SubagentRuntime` from simplicio-prompt v1.7.0 (PyPI) · `use_cache=False` (every subagent is an independent provider call) · `temperature=0.7` (induces real per-call variance).  
Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — real PHP 8 condominium system on GitHub.  
Models: `Qwen/Qwen2.5-Coder-3B-Instruct`  
N values: **8**  
Tasks: **1** real engineering changes across `src/Core/`, `src/Middleware/`, `src/Repositories/`, and routing (includes one bug-fix task that scores against the existing `PasswordPolicyTest`, not a new hidden test).

## Methodology

For each (model, task, N), the simplicio-prompt **kernel** launches N real parallel LLM calls on the same prompt (simplicio-cli 6-layer wrap of the task). Every returned solution is scored TWO ways:

1. **Functional (real PHPUnit)** — write the solution to the target file in a working copy of sistema-sindico, install the hidden test for the case (or just keep the existing suite for the bug-fix task), run `vendor/bin/phpunit --configuration phpunit.xml.dist`. Pass = exit code 0.
2. **Regex (cheap structural proxy)** — match a small set of patterns against the solution text (method declared? right keywords? uses the expected APIs?). Per-task patterns in `sindico_cases.REGEX_CHECKS_BY_TASK`.

**The point of carrying both metrics**: where they AGREE, regex is a reasonable cheap proxy; where they DISAGREE (especially regex-PASS while phpunit-FAIL), regex is misleading and the criticism that 'regex doesn't mean the code works' is correct.

## Headline — per (model, N) aggregate across tasks

| Model | N | fn per-attempt | rx per-attempt | fn modal | rx modal | Tokens | Cost | Avg s |
|---|---|---|---|---|---|---|---|---|
| `Qwen/Qwen2.5-Coder-3B-Instruct` | **8** | 8/8 (100%) | 8/8 (100%) | 1/1 | 1/1 | 8,109 | $0.0000 | 9.5s |

## Per N (aggregate across all models)

| N | fn per-attempt | rx per-attempt | fn-vs-rx gap | fn modal | rx modal |
|---|---|---|---|---|---|
| **8** | 8/8 (100%) | 8/8 (100%) | **+0** | 1/1 | 1/1 |

## Regex-vs-functional disagreement (per task, averaged across models × N)

When the regex score is much higher than phpunit (positive gap), regex is a **false positive** — the code looks right but doesn't actually pass. When phpunit is higher, regex misses real wins.

| Task | fn per-attempt | rx per-attempt | gap (rx − fn) |
|---|---|---|---|
| `password_strength` | 100% | 100% | **+0** |

## Per-task × model × N detail

Format: `fn% / rx% / fn-modal-pass`. P = phpunit modal PASS, . = fail.

### `password_strength`

| Model \\ N | 8 |
|---|---|
| `Qwen2.5-Coder-3B-Instruct` | 100% / 100% / P |
