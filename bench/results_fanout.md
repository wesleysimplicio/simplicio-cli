# Fan-out benchmark — does simplicio-prompt's subagent kernel help?

Date: **2026-05-28**  
Model: `meta-llama/llama-3.1-8b-instruct` · temperature **0.7** (induces real per-call variance)  
Task: `password_strength` (add PHP method to src/Core/PasswordPolicy.php)  
Engine: `kernel.subagent_runtime.SubagentRuntime` from simplicio-prompt v1.7.0 (PyPI), real parallel calls through `LaneWorkerPool`.

## Methodology

For each N, the simplicio-prompt **kernel** launches N real parallel LLM calls on the SAME prompt (simplicio-cli 6-layer wrap of the task) at `temperature=0.7`. Every returned solution.php is written into a working copy of `sistema-sindico` and scored by **real PHPUnit** (`vendor/bin/phpunit` exit code 0). The **majority-vote outcome** is computed by sha256-hashing the normalized code, picking the most frequent variant, and re-running phpunit on it.

**This is the real engagement of simplicio-prompt's value prop**: the kernel actually executes the fan-out, unlike the prompt-as-text benchmark in `results_exec_sindico.md`. The question answered here is: does sp's default 64 buy you anything over a single call? does 200 buy you more than 64?

## Headline

| N | Per-attempt pass | Unique outputs | Majority-vote pass | Tokens | Cost (USD) | Elapsed |
|---|---|---|---|---|---|---|
| **1** | 1/1 (100%) | 1 | PASS (1/1) | 991 | $0.0001 | 26.1s |
| **8** | 8/8 (100%) | 6 | PASS (3/8) | 8,008 | $0.0005 | 28.7s |
| **32** | 32/32 (100%) | 16 | PASS (14/32) | 32,165 | $0.0019 | 30.4s |
| **64** | 64/64 (100%) | 12 | PASS (51/64) | 65,205 | $0.0039 | 24.6s |
| **200** | 200/200 (100%) | 24 | PASS (156/200) | 203,529 | $0.0122 | 34.3s |

## Interpretation

- **Per-attempt pass** is the noise floor at `temperature=0.7`. A single call hits roughly this rate.
- **Unique outputs** measures real diversity at this temperature; if every subagent produces the same file, fan-out adds nothing.
- **Majority-vote** is the value test: does picking the most frequent answer recover correctness when single calls are noisy?
- **Cost** and **elapsed** scale linearly with N. The kernel runs calls in parallel (LaneWorkerPool), so wall-clock should grow much slower than total tokens.

Raw per-subagent data in `results_fanout.json`. Re-run with `BENCH_FANOUT_NS=...` to test other N values, or `BENCH_FANOUT_MODEL=...` to swap models.
