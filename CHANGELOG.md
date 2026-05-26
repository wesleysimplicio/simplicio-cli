# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.4] — 2026-05-26

### Changed
- Re-ran the full offline bench against six **frontier 2026 models** —
  DeepSeek V4 Pro, Qwen 3.7 Max, Kimi K2.6, GPT-5.5, Claude Opus 4.7,
  and Gemini 3.5 Flash — replacing the previous trio of mid-tier 7B–12B
  open models in the headline numbers.
- Bench harness (`bench/run_offline.py`):
  - Raised `max_tokens` from 900 → 8192 to accommodate reasoning-heavy
    models (GPT-5.5, Kimi K2.6, Claude Opus 4.7) that need room to emit
    DIFF + TEST + EVIDENCE without hitting the length cap.
  - Added a `reasoning` field fallback when `message.content` is null
    (some providers return the answer under `reasoning` for thinking models).
- README and `bench/results.md` refreshed with the new headline numbers.

### Results (60 runs per side, 312 checks)
- Overall: **40% → 95%** (+55 pts, +139% relative).
- Per-model gains:
  - Kimi K2.6: **36% → 100%** (+64 pts).
  - GPT-5.5: **36% → 98%** (+62 pts).
  - Gemini 3.5 Flash: **40% → 100%** (+60 pts).
  - Claude Opus 4.7: **44% → 96%** (+52 pts).
  - Qwen 3.7 Max: **42% → 92%** (+50 pts).
  - DeepSeek V4 Pro: **40% → 88%** (+48 pts).
- DIFF block presence: **33% → 95%**.
- Target file mentioned: **0% → 98%**.
- TEST block presence: **85% → 95%**.

### Cost
- Tokens / run: 1,566 → 2,686 (+71%) — reasoning-class models spend more
  completion tokens when wrapped in the contract because they produce the
  full DIFF + TEST + EVIDENCE the contract demands.
- Wall-clock / run: 35.4s → 45.6s (+29%).
- Trade-off: ~2× tokens, +55 pass-rate points and a 95% DIFF-block rate.

## [0.2.3] — 2026-05-26

### Changed (BREAKING)
- Translated the entire codebase to English: docstrings, comments, variable
  names, function names, prompt template, and bench case data.
- **CLI flag renames** (breaking for any saved invocations):
  - `--alvo` → `--target`
  - `--criterios` → `--criteria`
  - `--restricoes` → `--constraints`
  - positional `objetivo` → `goal`
- **Internal function renames** (breaking for anyone importing `simplicio.*`):
  - `prompt.montar` → `prompt.build_prompt`
  - `providers.gerar` → `providers.generate`
  - `precedent.montar_bloco_precedente` → `precedent.build_precedent_block`
  - `precedent.grep_candidatos` → `precedent.grep_candidates`
  - `skill_router.montar_bloco_skill` → `skill_router.build_skill_block`
- **Bench JSON keys renamed** in `bench/cases.json` and
  `bench/cases_offline.json`: `objetivo/alvo/criterios/restricoes` →
  `goal/target/criteria/constraints`.
- Prompt template slot renames: `{{OBJETIVO}}/{{ALVO}}/{{PRECEDENTE}}/{{CRITERIOS}}/{{RESTRICOES}}`
  → `{{GOAL}}/{{TARGET}}/{{PRECEDENT}}/{{CRITERIA}}/{{CONSTRAINTS}}`.
- Prompt template now emits `[GOAL] / [TARGET] / [CONTRACT] / [OUTPUT]`
  blocks instead of the Portuguese `[OBJETIVO] / [ALVO] / [CONTRATO] / [SAIDA]`.

### Why
- Repo is intended for an international audience; mixed-language internals
  hurt onboarding and review.
- Aligns with the project's own English-first README, benchmark, and PyPI
  copy that were already in place since v0.2.0.

## [0.2.2] — 2026-05-26

### Added
- Benchmark harness (`bench/run_offline.py`) now captures per-call token
  usage (`usage.prompt_tokens` / `completion_tokens` / `total_tokens`) and
  wall-clock latency (`time.perf_counter()`) for every model call.
- `bench/results.md` gained a "Cost — tokens & wall-clock" section with a
  per-model table and aggregate totals over 30 runs per side.
- README now reports honest cost numbers alongside pass-rate.

### Changed
- Re-ran the full bench against OpenRouter; refreshed all numbers in
  `README.md` and `bench/results.md`:
  - Overall: **35% → 90%** (+55 pts, +156% relative) over 156 checks.
  - Gemma 3 12B: **34% → 92%** (+58 pts).
  - Llama 3.1 8B: **36% → 90%** (+54 pts).
  - Qwen 2.5 7B: **34% → 88%** (+54 pts).
- Wall-clock per run dropped from **12.4s → 9.9s (−21%)**; token cost per
  run shifted from 759 → 770 (+1%). simplicio is faster *and* better at
  ~same token bill.

### Results
- DIFF block presence: **0% → 100%**.
- Target file mentioned: **0% → 96%**.
- TEST block presence: **80% → 96%**.

## [0.2.1] — 2026-05-26

### Added
- README hero image generated with `gpt-image-2`, including a web-sized PNG and
  source PNG under `output/imagegen/`.

### Changed
- README top section now includes the visual pipeline summary from one-line task
  to verified code change.

## [0.2.0] — 2026-05-26

### Added
- Multi-model offline benchmark harness (`bench/run_offline.py`):
  3 models · 10 cases · 156 checks · SVG charts (stdlib only).
- Output-quality signals: DIFF block, TEST block, target-file mention,
  criteria-keyword coverage, output length.
- PyPI metadata: authors, license, classifiers, keywords, project URLs,
  package-data for `simplicio/templates/*.md`.
- PyPI badges and marketing hero in README with real numbers.
- `.gitignore` entry for `.env`.

### Changed
- Bumped version `0.1.0` → `0.2.0`.
- README: provider-agnostic install instructions (`pip install simplicio-cli`).
- Benchmark results re-generated against working OpenRouter models
  (qwen 2.5 7B, llama 3.1 8B, gemma 3 12B).

### Results
- Overall: **37% → 91%** (+54 pts, +145% relative) over 156 checks.
- Llama 3.1 8B: **34% → 98%** (+64 pts).
- Gemma 3 12B: **38% → 94%** (+56 pts).
- Qwen 2.5 7B: **38% → 80%** (+42 pts).
- DIFF block presence: **0% → 100%**.
- Target file mentioned: **3% → 96%**.

## [0.1.0] — 2026-05-25

### Added
- Initial release of `simplicio-cli`.
- Pipeline: mapper → precedent → skill-router → 6-layer prompt → verify loop.
- Content-hash embedding cache under `.simplicio/`.
- Provider-agnostic LLM client (any OpenAI-compatible endpoint + Anthropic native).
- CLI commands: `index`, `task`, `bench`, `smoke`.

[0.2.3]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.3
[0.2.2]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.2
[0.2.1]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.1
[0.2.0]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.0
[0.1.0]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.1.0
