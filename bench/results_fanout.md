# Fan-out benchmark — regex vs functional, 4 models × N ∈ {64, 200, 600}

Date: **2026-05-28**  
Engine: `kernel.subagent_runtime.SubagentRuntime` from simplicio-prompt v1.7.0 (PyPI) · `use_cache=False` (every subagent is an independent provider call) · `temperature=0.7` (induces real per-call variance).  
Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — real PHP 8 condominium system on GitHub.  
Models: `Qwen/Qwen2.5-Coder-3B-Instruct`  
N values: **64** *(sp default)*, **200**, **600**  
Tasks: **4** real engineering changes across `src/Core/`, `src/Middleware/`, `src/Repositories/`, and routing (includes one bug-fix task that scores against the existing `PasswordPolicyTest`, not a new hidden test).

## Methodology

For each (model, task, N), the simplicio-prompt **kernel** launches N real parallel LLM calls on the same prompt (simplicio-cli 6-layer wrap of the task). Every returned solution is scored TWO ways:

1. **Functional (real PHPUnit)** — write the solution to the target file in a working copy of sistema-sindico, install the hidden test for the case (or just keep the existing suite for the bug-fix task), run `vendor/bin/phpunit --configuration phpunit.xml.dist`. Pass = exit code 0.
2. **Regex (cheap structural proxy)** — match a small set of patterns against the solution text (method declared? right keywords? uses the expected APIs?). Per-task patterns in `sindico_cases.REGEX_CHECKS_BY_TASK`.

**The point of carrying both metrics**: where they AGREE, regex is a reasonable cheap proxy; where they DISAGREE (especially regex-PASS while phpunit-FAIL), regex is misleading and the criticism that 'regex doesn't mean the code works' is correct.

## Headline — per (model, N) aggregate across tasks

| Model | N | fn per-attempt | rx per-attempt | fn modal | rx modal | Tokens | Cost | Avg s |
|---|---|---|---|---|---|---|---|---|
| `Qwen/Qwen2.5-Coder-3B-Instruct` | **64** *(default)* | 83/256 (32%) | 218/256 (85%) | 2/4 | 4/4 | 255,684 | $0.0000 | 16.7s |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | **200** | 260/800 (32%) | 666/800 (83%) | 2/4 | 3/4 | 806,067 | $0.0000 | 40.2s |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | **600** | 923/1800 (51%) | 1538/1800 (85%) | 2/3 | 3/3 | 1,797,998 | $0.0000 | 84.7s |

## Per N (aggregate across all models)

| N | fn per-attempt | rx per-attempt | fn-vs-rx gap | fn modal | rx modal |
|---|---|---|---|---|---|
| **64** *(default)* | 83/256 (32%) | 218/256 (85%) | **+53** | 2/4 | 4/4 |
| **200** | 260/800 (32%) | 666/800 (83%) | **+51** | 2/4 | 3/4 |
| **600** | 923/1800 (51%) | 1538/1800 (85%) | **+34** | 2/3 | 3/3 |

## Regex-vs-functional disagreement (per task, averaged across models × N)

When the regex score is much higher than phpunit (positive gap), regex is a **false positive** — the code looks right but doesn't actually pass. When phpunit is higher, regex misses real wins.

| Task | fn per-attempt | rx per-attempt | gap (rx − fn) |
|---|---|---|---|
| `password_strength` | 74% | 99% | **+25** ⚠️ regex inflates |
| `password_require_symbol` | 0% | 61% | **+61** ⚠️ regex inflates |
| `env_get_int` | 55% | 96% | **+41** ⚠️ regex inflates |
| `env_get_bool` | 51% | 73% | **+22** ⚠️ regex inflates |

## Per-task × model × N detail

Format: `fn% / rx% / fn-modal-pass`. P = phpunit modal PASS, . = fail.

### `password_strength`

| Model \\ N | 64 | 200 | 600 |
|---|---|---|---|
| `Qwen2.5-Coder-3B-Instruct` |  79% / 100% / P |  76% /  99% / P |  73% /  99% / P |

### `password_require_symbol`

| Model \\ N | 64 | 200 | 600 |
|---|---|---|---|
| `Qwen2.5-Coder-3B-Instruct` |   3% /  67% / . |   1% /  64% / . |   0% /  59% / . |

### `env_get_int`

| Model \\ N | 64 | 200 | 600 |
|---|---|---|---|
| `Qwen2.5-Coder-3B-Instruct` |   0% /  96% / . |   0% /  97% / . |  79% /  97% / P |

### `env_get_bool`

| Model \\ N | 64 | 200 | 600 |
|---|---|---|---|
| `Qwen2.5-Coder-3B-Instruct` |  46% /  76% / P |  52% /  72% / P | — |
