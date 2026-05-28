# Execution benchmark — simplicio-cli on sistema-sindico (real PHPUnit)

Date: **2026-05-28**  
Target project: `wesleysimplicio/sistema-sindico` (PHP 8 + PHPUnit 11)  
Models: `meta-llama/Llama-3.2-1B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct`  
Tasks: **4** additive modifications to `src/Core/` classes.

Each task asks the model to add a new method to a real file in the sindico codebase. The generated file is written into a working copy, a **hidden PHPUnit test** (never shown to the model, asserting true AND false states) is added under `tests/unit/Core/Hidden/`, and the ENTIRE suite is run. **Pass = every existing test + the hidden test go green.** This means the new method works AND no existing test was broken. Both sides emit the complete file — the only variable is whether the goal is wrapped in the simplicio contract.

## Headline

- **Without simplicio:** 3/12 (25%)
- **With simplicio:** 4/12 (33%)
- **Delta:** **+8 points**

## Per-model (pass = full PHPUnit suite green)

| Model | Without | With | Delta (pts) |
|---|---|---|---|
| `meta-llama/Llama-3.2-1B-Instruct` | 0/4 (0%) | 0/4 (0%) | **+0** |
| `Qwen/Qwen2.5-7B-Instruct` | 0/4 (0%) | 0/4 (0%) | **+0** |
| `meta-llama/Llama-3.1-8B-Instruct` | 3/4 (75%) | 4/4 (100%) | **+25** |

## Per-task × model (P = pass, . = fail)

| Task (w/o, with) | Llama-3.2-1B-Instruct | Qwen2.5-7B-Instruct | Llama-3.1-8B-Instruct |
|---|---|---|---|
| password_strength | . / . | . / . | P / P |
| password_require_symbol | . / . | . / . | P / P |
| env_get_int | . / . | . / . | . / P |
| env_get_bool | . / . | . / . | P / P |

Raw counts above are real `vendor/bin/phpunit` exit codes against `sistema-sindico`. `results_exec_sindico.json` holds per-case pass/fail, tokens, latency and a phpunit tail.
