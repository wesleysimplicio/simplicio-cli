# 4-side comparison — Qwen3 Coder MoE

Date: **2026-05-29**  

**Sides** (same 6-layer task contract on cli / cli+sp / cli+ag):

- `baseline` — raw one-line goal + file content. No simplicio at all.
- `cli` — wrapped in the simplicio-cli 6-layer contract (role/stack, goal, target, criteria, constraints, output shape).
- `cli + sp` — same contract, embedded as user-input-X inside the simplicio-prompt v1.9 Tuple-Space + Yool runtime template (3,907 chars of runtime preamble).
- `cli + ag` — same contract, but on failure the harness classifies the failure (syntax/assertion/runtime/etc.), feeds the PHPUnit tail (or list of missed regex patterns) back as retry feedback, re-prompts. Up to 3 attempts. Mirrors `simplicio task --verify`.

**Metrics**:

- `functional` — real `vendor/bin/phpunit --configuration phpunit.xml.dist` on `wesleysimplicio/sistema-sindico` (PHP 8). Pass = full suite green.
- `regex` — structural pattern match against the generated output (cheap proxy used by `bench/run_offline.py`).

## Headline — pass rate per side, both metrics

| Model | metric | baseline | cli | cli+sp | cli+ag | Δ cli | Δ cli+sp | Δ cli+ag |
|---|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | functional | 33% | 91% | 91% | 91% | **+58** | **+58** | **+58** |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | regex | 36% | 90% | 98% | 90% | **+54** | **+62** | **+54** |
| `Qwen/Qwen3-Coder-Next` | functional | 50% | 83% | 83% | 91% | **+33** | **+33** | **+41** |
| `Qwen/Qwen3-Coder-Next` | regex | 44% | 100% | 94% | 100% | **+56** | **+50** | **+56** |

## Agents verify-loop convergence

Lower attempts = the model resolved the case earlier; 1 means it passed on the first try with no feedback. Max attempts capped per harness.

| Model | metric | avg attempts (cli+ag) |
|---|---|---|
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | functional | 1.17 |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | regex | 2.00 |
| `Qwen/Qwen3-Coder-Next` | functional | 1.17 |
| `Qwen/Qwen3-Coder-Next` | regex | 1.00 |

## Cost & latency per call (functional bench)

Tokens/call averaged across the 12 cases. cli+ag burns more tokens AND more wall-clock per case because it may run up to 3 attempts. If pass-rate gain doesn't justify the multiplier, single-shot cli wins for batch jobs; cli+ag wins for interactive workflows where a 1.5x cost is acceptable to avoid manual rerun.

| Model | side | tokens/call | ms/call |
|---|---|---|---|
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | baseline | 1259 | 5030 |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | cli      | 1449 | 4983 |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | cli+sp   | 2412 | 4879 |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | cli+ag   | 1579 | 5332 |
| `Qwen/Qwen3-Coder-Next` | baseline | 1280 | 3571 |
| `Qwen/Qwen3-Coder-Next` | cli      | 1449 | 3485 |
| `Qwen/Qwen3-Coder-Next` | cli+sp   | 2416 | 3398 |
| `Qwen/Qwen3-Coder-Next` | cli+ag   | 1858 | 4210 |

## Per-task × model (functional, base / cli / cli+sp / cli+ag)

| Task | Qwen3-Coder-30B-A3B-Instruct | Qwen3-Coder-Next |
|---|---|---|
| password_strength | ./P/P/P(1) | ./P/P/P(1) |
| password_require_symbol | ./././.(3) | ./P/./P(1) |
| env_get_int | ./P/P/P(1) | P/P/P/P(1) |
| env_get_bool | ./P/P/P(1) | ././P/P(1) |
| admin_only_allowed_roles | P/P/P/P(1) | P/P/P/P(1) |
| rate_limit_bucket_key | ./P/P/P(1) | ./P/P/P(1) |
| base_repository_build_where_sql | ./P/P/P(1) | ./P/P/P(1) |
| router_has | ./P/P/P(1) | P/P/P/P(1) |
| bugfix_password_policy_lowercase | P/P/P/P(1) | P/P/./P(1) |
| password_assess | P/P/P/P(1) | P/P/P/P(1) |
| base_repository_build_update_sql | ./P/P/P(1) | ././P/.(3) |
| router_extract_params | P/P/P/P(1) | P/P/P/P(1) |

Last digit on cli+ag is the attempt count consumed (1–3). 1 = no feedback loop needed. 3 with `.` = ran the full loop and still failed; this is a model-capability ceiling, not a feedback-loop problem.
