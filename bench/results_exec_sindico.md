# Execution benchmark — real project, real tasks, real test suite

Date: **2026-05-28**  
Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — a real condominium-management system in pure PHP 8 (public on GitHub, PHPUnit 11)  
Models: `Qwen/Qwen2.5-Coder-3B-Instruct`, `Qwen/Qwen2.5-Coder-7B-Instruct`, `meta-llama/llama-3.1-8b-instruct`, `qwen/qwen3.7-max`  
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

## Headline

- **Baseline:** 21/48 (43%)
- **simplicio-cli (6-layer):** 37/48 (77%) — **+34 pts vs baseline**
- **simplicio-cli + simplicio-prompt (composition):** 34/48 (70%) — **+27 pts vs baseline · -7 pts vs cli alone**

## Per-model (pass = full PHPUnit suite green)

| Model | Baseline | cli alone | cli + sp | D cli | D (cli+sp) |
|---|---|---|---|---|---|
| `Qwen/Qwen2.5-Coder-3B-Instruct` | 5/12 (41%) | 9/12 (75%) | 9/12 (75%) | **+34** | **+34** |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | 4/12 (33%) | 8/12 (66%) | 6/12 (50%) | **+33** | **+17** |
| `meta-llama/llama-3.1-8b-instruct` | 4/12 (33%) | 8/12 (66%) | 7/12 (58%) | **+33** | **+25** |
| `qwen/qwen3.7-max` | 8/12 (66%) | 12/12 (100%) | 12/12 (100%) | **+34** | **+34** |

## Per-task × model (baseline / cli / cli+sp)

| Task | Qwen2.5-Coder-3B-Instruct | Qwen2.5-Coder-7B-Instruct | llama-3.1-8b-instruct | qwen3.7-max |
|---|---|---|---|---|
| password_strength | ./P/P | ./P/P | ./P/P | P/P/P |
| password_require_symbol | ././P | ././. | ./P/. | P/P/P |
| env_get_int | ./P/P | ./P/. | ././P | ./P/P |
| env_get_bool | P/P/P | ././. | ././. | P/P/P |
| admin_only_allowed_roles | P/P/P | P/P/P | P/P/P | P/P/P |
| rate_limit_bucket_key | ./P/P | ./P/P | ./P/P | ./P/P |
| base_repository_build_where_sql | ./P/. | ./P/P | ./P/. | ./P/P |
| router_has | P/P/P | P/P/. | P/P/P | P/P/P |
| bugfix_password_policy_lowercase | P/P/P | P/P/P | P/P/P | P/P/P |
| password_assess | P/P/P | P/P/P | P/P/P | P/P/P |
| base_repository_build_update_sql | ././. | ././. | ././. | ./P/P |
| router_extract_params | ././. | ././. | ././. | P/P/P |

Raw counts above are real `vendor/bin/phpunit` exit codes against `sistema-sindico`. `results_exec_sindico.json` holds per-case pass/fail, tokens, latency and a phpunit tail for every side.
