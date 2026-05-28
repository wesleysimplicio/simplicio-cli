# Execution benchmark — real project, real tasks, real test suite

Date: **2026-05-28**  
Target project: [`wesleysimplicio/sistema-sindico`](https://github.com/wesleysimplicio/sistema-sindico) — a real condominium-management system in pure PHP 8 (public on GitHub, PHPUnit 11)  
Models: `meta-llama/Llama-3.2-1B-Instruct`, `google/gemma-3n-E4B-it`, `google/gemma-3-4b-it`, `qwen/qwen-2.5-7b-instruct`, `meta-llama/Llama-3.1-8B-Instruct`, `google/gemma-3-12b-it`, `google/gemini-3.5-flash`, `anthropic/claude-opus-4.7`, `openai/gpt-5.5`  
Tasks: **4** additive real-engineering changes across `src/Core/`, `src/Middleware/`, `src/Repositories/`, and routing.

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

## Headline

- **Baseline:** 12/36 (33%)
- **simplicio-cli (6-layer):** 23/36 (63%) — **+30 pts vs baseline**

## Per-model (pass = full PHPUnit suite green)

| Model | Baseline | simplicio-cli | Delta (pts) |
|---|---|---|---|
| `meta-llama/Llama-3.2-1B-Instruct` | 0/4 (0%) | 0/4 (0%) | **+0** |
| `google/gemma-3n-E4B-it` | 0/4 (0%) | 0/4 (0%) | **+0** |
| `google/gemma-3-4b-it` | 0/4 (0%) | 3/4 (75%) | **+75** |
| `qwen/qwen-2.5-7b-instruct` | 0/4 (0%) | 1/4 (25%) | **+25** |
| `meta-llama/Llama-3.1-8B-Instruct` | 2/4 (50%) | 4/4 (100%) | **+50** |
| `google/gemma-3-12b-it` | 2/4 (50%) | 3/4 (75%) | **+25** |
| `google/gemini-3.5-flash` | 3/4 (75%) | 4/4 (100%) | **+25** |
| `anthropic/claude-opus-4.7` | 2/4 (50%) | 4/4 (100%) | **+50** |
| `openai/gpt-5.5` | 3/4 (75%) | 4/4 (100%) | **+25** |

## Per-task × model (baseline / cli)

| Task | Llama-3.2-1B-Instruct | gemma-3n-E4B-it | gemma-3-4b-it | qwen-2.5-7b-instruct | Llama-3.1-8B-Instruct | gemma-3-12b-it | gemini-3.5-flash | claude-opus-4.7 | gpt-5.5 |
|---|---|---|---|---|---|---|---|---|---|
| password_strength | ./. | ./. | ./P | ./P | P/P | ./P | P/P | ./P | P/P |
| password_require_symbol | ./. | ./. | ./. | ./. | P/P | P/. | P/P | ./P | P/P |
| env_get_int | ./. | ./. | ./P | ./. | ./P | ./P | ./P | P/P | ./P |
| env_get_bool | ./. | ./. | ./P | ./. | ./P | P/P | P/P | P/P | P/P |

Raw counts above are real `vendor/bin/phpunit` exit codes against `sistema-sindico`. `results_exec_sindico.json` holds per-case pass/fail, tokens, latency and a phpunit tail for every side.
