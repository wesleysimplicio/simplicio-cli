# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.10] — 2026-05-26

### Added
- Skill `simplicio-cli` (`.skills/simplicio-cli/SKILL.md` + global mirror at
  `~/.claude/skills/simplicio-cli/SKILL.md`) — auto-triggers when the user asks
  for a small/medium code edit on a known file. Maps the natural-language goal
  to `simplicio task --stack <s> --target <f> --criteria <…> --constraints <…>`,
  runs verify-loop, and reports diff + test result. Pushy trigger description
  covers explicit invocations (`$simplicio`, "use simplicio") plus implicit
  cues (small/local model, verify-loop / pass-rate / 6-layer keywords).
- Registered the skill in `.skills/README.md` table.

## [0.2.9] — 2026-05-26

### Added
- Wider 4-quadrant run: 3 models × 10 cases (qwen partial 5/10),
  max_iters=5 — `google/gemma-3-4b-it`, `meta-llama/llama-3.2-3b-instruct`,
  `qwen/qwen-2.5-7b-instruct`. Aggregate over 25 observed (model × case)
  tuples: Q1 = 0%, Q2 = 64%, Q3 = 44%, **Q4 = 76%**. All three falsifiable
  hypotheses (loop-alone closes the gap, simplicio-alone is enough, gains
  stack linearly) **rejected** at |Δ| ≥ 5 pts.
- New report `bench/results_4quadrant_wide.md` + raw artefact
  `bench/results_4quadrant_wide.json` reconstructed from the wide run log.
- README "Run 2 — wider multi-model" subsection with per-model breakdown,
  decomposition table and hypothesis verdicts.

### Changed
- `pyproject.toml` version bumped 0.2.8 → 0.2.9.
- README "First run on record" subsection renamed to "Run 1 — focused
  single-model" for symmetry with Run 2.

### Notes
- Wide run was killed mid-execution; `claude-3.5-haiku` not reached.
  Reproduce command for the full intended run is documented in
  `bench/results_4quadrant_wide.md`.

## [0.2.8] — 2026-05-26

### Added
- 4-quadrant benchmark harness `bench/run_4quadrant.py` — isolates two
  axes (prompt structure × execution model) on the same model, same cases,
  same checks. Q1 raw 1-shot (baseline), Q2 simplicio 1-shot (current bench),
  Q3 loop on raw goal, Q4 loop on simplicio goal (composition).
- Methodology doc `docs/benchmark-4quadrant.md` — explains the matrix,
  feedback shape, metrics, hypothesis decomposition (loop-alone /
  simplicio-alone / linear-stacking falsification tests), cost model and
  limitations.
- README section "### 4-quadrant bench — agent × simplicio matrix" with
  reproduce command and matrix decomposition formulas (Q2-Q1, Q3-Q1, Q4-Q3,
  Q4-Q2, Q4-max(Q2,Q3), Q4-linear).
- Optional dependency group `[project.optional-dependencies] bench`
  shipping `fpdf2>=2.7` for the PDF report. Install via `pip install -e ".[bench]"`.
- Outputs `bench/results_4quadrant.{md,pdf,json}`, charts under
  `bench/charts/4q_*.svg`, raw per-iteration outputs under
  `.simplicio/bench_4q/<model>/case_NN/q*_iter*.txt` for audit.

### Changed
- `pyproject.toml` version bumped 0.2.7 → 0.2.8.

## [0.2.7] — 2026-05-26

### Added
- Agent spec `.agents/simplicio-ralph.agent.md` — composição do padrão Ralph Loop
  com o `simplicio-cli` como gerador de código no passo `execute`. Lido por
  Claude Code, Codex CLI, GitHub Copilot, Cursor, Hermes, OpenClaw, Aider.
- ADR-002 `.specs/architecture/ADR-002-simplicio-ralph-composition.md` —
  registra a decisão arquitetural de **compor** com ralph-loop em vez de
  inchar o CLI com `simplicio review`, `simplicio refactor`, etc. Documenta
  alternativas avaliadas, trade-offs e critério de revisão (6 meses).
- Doc `docs/agent-architecture.md` — visão única da arquitetura agentic
  (4 camadas: orquestrador → roteamento → simplicio-cli → provedores LLM),
  matriz de roteamento por tipo de task, fluxo end-to-end, invocação por
  ferramenta, limitações conhecidas e como o orquestrador compensa.

### Changed
- `AGENTS.md` e `CLAUDE.md` (mirror) — entry novo na lista de "Custom agents
  disponíveis" apontando para `simplicio-ralph.agent.md`.
- `.agents/README.md` — diagrama de arquivos listados inclui o agent novo.

### Notes
- **Aditivo only.** Zero linha de código mexida em `simplicio/*.py`, `bench/`,
  `README.md` ou `README.pt-BR.md`. Benchmarks publicados permanecem
  reproduzíveis com a mesma versão do código.

## [0.2.6] — 2026-05-26

### Added
- Third bench run on record — **tiny sub-4B models** via OpenRouter. Five
  models, 10 cases, 50 runs/side, 260 checks:
  - `google/gemma-3-4b-it`: **38% → 96%** (+58 pts)
  - `meta-llama/llama-3.2-3b-instruct`: **28% → 73%** (+45 pts)
  - `google/gemma-3n-e4b-it`: **44% → 88%** (+44 pts)
  - `microsoft/phi-4-mini-instruct`: **36% → 73%** (+37 pts)
  - `meta-llama/llama-3.2-1b-instruct`: **26% → 40%** (+14 pts)
  - **Tiny avg: 35% → 74% (+39 pts, +112% relative)**
- `bench/results.md` now has three sections (tiny → frontier → mid-tier
  archival), 14 models total across three runs.

### Changed
- README headline updated: **"Fourteen models tested across three runs"**
  with the tiny table positioned **above** the frontier table per request.

### Notes
- 8 of the 11 originally requested sub-4B models are **not hosted on
  OpenRouter** (Gemma 3 270M, Gemma 3 1B, Gemma 2 2B, Qwen3 0.6B, Qwen3 1.7B,
  Qwen2.5 0.5B, Qwen2.5 1.5B, Qwen 3B, Nemotron Nano 4B — OR's smallest
  Nemotron is 9B). Closest available substitutes were used.
- Output-quality on tiny rerun: DIFF block **0% → 74%**, target file
  mentioned **0% → 84%**, TEST block **82% → 80%**.
- Cost on tiny rerun: tokens 1,006 → 1,289 per run (+28%); wall-clock
  **15.6s → 9.1s per run (−42% — faster *with* simplicio)** because the
  raw side often emits long chatty answers while the contract clamps output
  shape.

## [0.2.5] — 2026-05-26

### Changed
- README and `bench/results.md` now list **all nine models** tested across both
  bench runs — six frontier 2026 models (current headline) plus the three
  mid-tier 7B–12B open models from the earlier v0.2.2 run (archival). The full
  set is explicit so readers can see every model the harness has hit.
- Re-ran the frontier bench (same 6 models, same 10 cases, `max_tokens=8192`).
  Headline moved **40% → 95%** (prior 0.2.4 numbers) to **41% → 99%** (+58 pts,
  +136% relative). Five of six frontier models hit **100% pass-rate**; smallest
  per-model gain is **+52 pts** (DeepSeek V4 Pro), largest **+62 pts** (GPT-5.5).
- Output-quality signals on the rerun: DIFF block **36% → 98%**, target file
  mentioned **1% → 100%**, TEST block **88% → 98%**.
- Cost on the rerun: tokens 1,967 → 3,168 per run (+61%); wall-clock 46.1s →
  57.6s per run (+24%); 118,040 → 190,119 total tokens across 60 runs/side.

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

[0.2.9]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.9
[0.2.8]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.8
[0.2.7]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.7
[0.2.6]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.6
[0.2.5]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.5
[0.2.4]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.4
[0.2.3]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.3
[0.2.2]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.2
[0.2.1]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.1
[0.2.0]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.0
[0.1.0]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.1.0
