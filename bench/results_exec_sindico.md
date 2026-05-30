# Execution benchmark — real project, real tasks, real test suite

Date: **2026-05-30**  
Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — a real condominium-management system in pure PHP 8 (public on GitHub, PHPUnit 11)  
Models: `meta-llama/llama-3.2-3b-instruct`, `google/gemma-3-4b-it`, `qwen/qwen-2.5-coder-32b-instruct`  
Tasks: **12** additive real-engineering changes across `src/Core/`, `src/Middleware/`, `src/Repositories/`, and routing.

## Methodology — what "pass" actually means

**This is NOT regex pattern-matching on model output. This is NOT a synthetic toy unit-test harness in isolation.** The benchmark runs against an actual published PHP project using the project's real PHPUnit suite (`vendor/bin/phpunit --configuration phpunit.xml.dist`).

For each task:

1. The model is asked for a real engineering change — add a new method to an existing production class (permission helper, env parser, rate-limit key builder, repository SQL builder, route introspection, etc.).
2. Its generated file replaces the original in a working copy of the real repo (with `composer install` deps already in place).
3. A **hidden PHPUnit test** (never shown to the model, asserting BOTH true and false states of the required behaviour) is dropped into `tests/unit/Core/Hidden/`.
4. The **ENTIRE production suite** runs — every pre-existing test of the real codebase plus the hidden one. The model's change must be **correct** (the new test passes) AND must **not break existing behaviour** (every prior test still passes).
5. **Pass = `phpunit` exit code 0** — the same green/red signal the project's CI would use to merge a PR.

All sides emit the complete file (identical output shape); the only variable is the wrapping prompt:

- **baseline**: raw goal + current file content
- **simplicio-cli**: the 6-layer task contract (role/stack, goal, target, criteria as testable states, constraints, output shape)
- **simplicio-cli + simplicio-prompt (composition)**: the Tuple-Space + Yool runtime template from simplicio-prompt wrapping the simplicio-cli 6-layer contract as user input X. Measures whether the runtime adds value ON TOP of an already-sharp 6-layer prompt — not whether sp alone beats raw goal.
- **simplicio-cli + agents (verify-loop)**: same 6-layer contract, but on failure the harness feeds the PHPUnit tail back as classified retry feedback (syntax/assertion/runtime/etc.) and re-prompts up to 3 attempts — the exact loop shipped in `simplicio task --verify` (`simplicio/pipeline.py`).

## Headline

- **Baseline:** 6/36 (16%)
- **simplicio-cli (6-layer):** 11/36 (30%) — **+14 pts vs baseline**
- **simplicio-cli + simplicio-prompt (composition):** 9/36 (25%) — **+9 pts vs baseline · -5 pts vs cli alone**
- **simplicio-cli + agents (verify-loop):** 11/36 (30%) — **+14 pts vs baseline · +0 pts vs cli alone**

## Per-model (pass = full PHPUnit suite green)

| Model | Baseline | cli alone | cli + sp | cli + ag | D cli | D (cli+sp) | D (cli+ag) |
|---|---|---|---|---|---|---|---|
| `meta-llama/llama-3.2-3b-instruct` | 1/12 (8%) | 1/12 (8%) | 1/12 (8%) | 1/12 (8%) | **+0** | **+0** | **+0** |
| `google/gemma-3-4b-it` | 4/12 (33%) | 8/12 (66%) | 6/12 (50%) | 8/12 (66%) | **+33** | **+17** | **+33** |
| `qwen/qwen-2.5-coder-32b-instruct` | 1/12 (8%) | 2/12 (16%) | 2/12 (16%) | 2/12 (16%) | **+8** | **+8** | **+8** |

## Per-task × model (baseline / cli / cli+sp / cli+ag)

| Task | llama-3.2-3b-instruct | gemma-3-4b-it | qwen-2.5-coder-32b-instruct |
|---|---|---|---|
| password_strength | ./././.(3) | ./P/P/P(1) | ./././.(3) |
| password_require_symbol | ./././.(3) | ./././.(3) | ./././.(3) |
| env_get_int | ./././.(3) | ./P/P/P(1) | ./P/P/P(1) |
| env_get_bool | ./././.(3) | ./P/./P(1) | P/P/P/P(1) |
| admin_only_allowed_roles | P/P/P/P(1) | P/P/P/P(1) | ./././.(3) |
| rate_limit_bucket_key | ./././.(3) | ./P/P/P(1) | ./././.(3) |
| base_repository_build_where_sql | ./././.(3) | ./././.(3) | ./././.(3) |
| router_has | ./././.(3) | P/P/P/P(1) | ./././.(3) |
| bugfix_password_policy_lowercase | ./././.(3) | P/P/P/P(1) | ./././.(3) |
| password_assess | ./././.(3) | P/P/./P(1) | ./././.(3) |
| base_repository_build_update_sql | ./././.(3) | ./././.(3) | ./././.(3) |
| router_extract_params | ./././.(3) | ./././.(3) | ./././.(3) |

Format suffix `(N)` on cli+ag is the number of verify-loop attempts consumed (1–3). Lower is better; 1 means it passed on the first try, no feedback needed.

Raw counts above are real `vendor/bin/phpunit` exit codes against `sistema-sindico`. `results_exec_sindico.json` holds per-case pass/fail, tokens, latency and a phpunit tail for every side.
