# Execution benchmark — sistema-sindico (real PHPUnit)

Date: **2026-05-28**  
Target project: `wesleysimplicio/sistema-sindico` (PHP 8 + PHPUnit 11)  
Models: `meta-llama/Llama-3.2-1B-Instruct`, `google/gemma-3n-E4B-it`, `google/gemma-3-4b-it`, `qwen/qwen-2.5-7b-instruct`, `meta-llama/Llama-3.1-8B-Instruct`, `google/gemma-3-12b-it`, `google/gemini-3.5-flash`, `anthropic/claude-opus-4.7`, `openai/gpt-5.5`  
Tasks: **4** additive modifications to `src/Core/` classes.

Each task asks the model to add a new method to a real file in the sindico codebase. The generated file is written into a working copy, a **hidden PHPUnit test** (never shown to the model, asserting true AND false states) is added under `tests/unit/Core/Hidden/`, and the ENTIRE suite is run. **Pass = every existing test + the hidden test go green.** All three sides emit the complete file; the only variable is the wrapping prompt:

- **baseline**: raw goal + current file content
- **simplicio-cli**: the 6-layer task contract (role/stack, goal, target, criteria as testable states, constraints, output shape)
- **simplicio-prompt**: the Tuple-Space + Yool runtime template from the simplicio-prompt package, with the task injected as user input X

## Headline

- **Baseline:** 12/36 (33%)
- **simplicio-cli (6-layer):** 23/36 (63%) — **+30 pts vs baseline**
- **simplicio-prompt (Yool runtime):** 8/36 (22%) — **-11 pts vs baseline**

## Per-model (pass = full PHPUnit suite green)

| Model | Baseline | simplicio-cli | simplicio-prompt | D cli | D sp |
|---|---|---|---|---|---|
| `meta-llama/Llama-3.2-1B-Instruct` | 0/4 (0%) | 0/4 (0%) | 0/4 (0%) | **+0** | **+0** |
| `google/gemma-3n-E4B-it` | 0/4 (0%) | 0/4 (0%) | 0/4 (0%) | **+0** | **+0** |
| `google/gemma-3-4b-it` | 0/4 (0%) | 3/4 (75%) | 0/4 (0%) | **+75** | **+0** |
| `qwen/qwen-2.5-7b-instruct` | 0/4 (0%) | 1/4 (25%) | 1/4 (25%) | **+25** | **+25** |
| `meta-llama/Llama-3.1-8B-Instruct` | 2/4 (50%) | 4/4 (100%) | 0/4 (0%) | **+50** | **-50** |
| `google/gemma-3-12b-it` | 2/4 (50%) | 3/4 (75%) | 1/4 (25%) | **+25** | **-25** |
| `google/gemini-3.5-flash` | 3/4 (75%) | 4/4 (100%) | 1/4 (25%) | **+25** | **-50** |
| `anthropic/claude-opus-4.7` | 2/4 (50%) | 4/4 (100%) | 2/4 (50%) | **+50** | **+0** |
| `openai/gpt-5.5` | 3/4 (75%) | 4/4 (100%) | 3/4 (75%) | **+25** | **+0** |

## Per-task × model (baseline / cli / sp)

| Task | Llama-3.2-1B-Instruct | gemma-3n-E4B-it | gemma-3-4b-it | qwen-2.5-7b-instruct | Llama-3.1-8B-Instruct | gemma-3-12b-it | gemini-3.5-flash | claude-opus-4.7 | gpt-5.5 |
|---|---|---|---|---|---|---|---|---|---|
| password_strength | ././. | ././. | ./P/. | ./P/. | P/P/. | ./P/. | P/P/. | ./P/. | P/P/P |
| password_require_symbol | ././. | ././. | ././. | ././P | P/P/. | P/./P | P/P/P | ./P/. | P/P/P |
| env_get_int | ././. | ././. | ./P/. | ././. | ./P/. | ./P/. | ./P/. | P/P/P | ./P/. |
| env_get_bool | ././. | ././. | ./P/. | ././. | ./P/. | P/P/. | P/P/. | P/P/P | P/P/P |

Raw counts above are real `vendor/bin/phpunit` exit codes against `sistema-sindico`. `results_exec_sindico.json` holds per-case pass/fail, tokens, latency and a phpunit tail for every side.
