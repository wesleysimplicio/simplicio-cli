# Fan-out benchmark — does simplicio-prompt's subagent kernel help?

Date: **2026-05-28**  
Model: `meta-llama/llama-3.1-8b-instruct` · temperature **0.7** (induces real per-call variance)  
Engine: `kernel.subagent_runtime.SubagentRuntime` from simplicio-prompt v1.7.0 (PyPI), real parallel calls through `LaneWorkerPool`.  
Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — real PHP 8 condominium system.  
Tasks: **8** real engineering changes across `src/Core/`, `src/Middleware/`, `src/Repositories/`, and routing.  
N values tested: **64** *(sp default)*, **200**

## Methodology

For each (task, N), the simplicio-prompt **kernel** launches N real parallel LLM calls on the same prompt (simplicio-cli 6-layer wrap of the task) at `temperature=0.7`. Every returned solution.php is written into a working copy of `sistema-sindico` and scored by **real PHPUnit** (`vendor/bin/phpunit` exit code 0). The **majority-vote outcome** is computed by sha256-hashing the normalized code, picking the most frequent variant, and re-running phpunit on it.

**This is the real engagement of simplicio-prompt's value prop**: the kernel actually executes the fan-out (LaneWorkerPool, bounded concurrency, receipt cache, jittered backoff, circuit breaker), not just embeds the runtime as prompt text. The question is: **does sp's default N=64 buy more than a smaller N? does N=200 buy more than 64?**

## Headline — per N (aggregate across tasks)

| N | Tasks | Per-attempt pass (sum) | Modal-vote pass | Tokens (sum) | Cost (USD, sum) | Avg elapsed |
|---|---|---|---|---|---|---|
| **64** *(sp default)* | 8 | 356/512 (69%) | 5/8 | 675,616 | $0.0405 | 41.3s |
| **200** | 8 | 1343/1600 (83%) | 7/8 | 2,126,410 | $0.1276 | 39.2s |

## Per-task breakdown

| Task | N | Per-attempt | Uniq | Modal | Tokens | Cost | Elapsed |
|---|---|---|---|---|---|---|---|
| `password_strength` | **64** | 64/64 (100%) | 10 | PASS (33/64) | 65,398 | $0.0039 | 36.1s |
| `password_strength` | **200** | 200/200 (100%) | 24 | PASS (163/200) | 204,825 | $0.0123 | 35.6s |
| `password_require_symbol` | **64** | 12/64 (18%) | 17 | fail (37/64) | 61,215 | $0.0037 | 27.1s |
| `password_require_symbol` | **200** | 166/200 (83%) | 47 | PASS (137/200) | 190,731 | $0.0114 | 30.5s |
| `env_get_int` | **64** | 53/64 (82%) | 17 | PASS (34/64) | 61,346 | $0.0037 | 20.1s |
| `env_get_int` | **200** | 180/200 (90%) | 30 | PASS (137/200) | 192,874 | $0.0116 | 24.9s |
| `env_get_bool` | **64** | 13/64 (20%) | 28 | fail (33/64) | 61,039 | $0.0037 | 15.2s |
| `env_get_bool` | **200** | 155/200 (77%) | 50 | PASS (137/200) | 199,687 | $0.0120 | 24.0s |
| `admin_only_allowed_roles` | **64** | 64/64 (100%) | 2 | PASS (61/64) | 32,449 | $0.0019 | 7.0s |
| `admin_only_allowed_roles` | **200** | 200/200 (100%) | 2 | PASS (196/200) | 102,008 | $0.0061 | 12.4s |
| `rate_limit_bucket_key` | **64** | 64/64 (100%) | 13 | PASS (36/64) | 90,217 | $0.0054 | 45.5s |
| `rate_limit_bucket_key` | **200** | 199/200 (99%) | 17 | PASS (137/200) | 282,474 | $0.0169 | 25.1s |
| `base_repository_build_where_sql` | **64** | 23/64 (35%) | 15 | fail (33/64) | 157,915 | $0.0095 | 117.8s |
| `base_repository_build_where_sql` | **200** | 45/200 (22%) | 45 | fail (137/200) | 495,439 | $0.0297 | 96.7s |
| `router_has` | **64** | 63/64 (98%) | 20 | PASS (33/64) | 146,037 | $0.0088 | 61.9s |
| `router_has` | **200** | 198/200 (99%) | 41 | PASS (144/200) | 458,372 | $0.0275 | 64.4s |

## Interpretation

- **Per-attempt pass** is the noise floor at `temperature=0.7`. A single call lands roughly at this rate.
- **Unique outputs** measures real diversity per task at this temperature; if every subagent produces the same file, fan-out adds nothing.
- **Modal (majority-vote)** is the value test: does picking the most frequent answer recover correctness when single calls are noisy?
- **N=64 vs N=200**: the central comparison. If 200 doesn't beat 64 on modal pass rate, sp's default is at the sweet spot.
- **Cost** scales linearly with N (tokens are proportional). **Elapsed** grows much slower because `LaneWorkerPool` runs calls in parallel.

Raw per-subagent data in `results_fanout.json`. Re-run with `BENCH_FANOUT_NS=...` or `BENCH_FANOUT_TASKS=...` to focus.
