# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.4] — 2026-05-30

### Added
- Commit `.simplicio/project-map.json` and `.simplicio/precedent-index.json`
  so downstream LLM executions can load the repository map directly.

## [0.4.3] — 2026-05-29

### Changed
- Align Simplicio ecosystem dependency floors with the latest published
  releases: `simplicio-mapper>=0.6.1` and `simplicio-prompt>=1.12.0`.
- Synchronize the package runtime `__version__` with the PyPI release version.

## [0.4.2] — 2026-05-29

### Added
- `simplicio task --dry-run-task --json` for SendSprint orchestration. It
  generates the would-be task output, returns the stable
  `{task_id, applied, files_changed, tokens_used, cost_usd, diff_summary,
  warnings}` JSON contract, and does not write `.simplicio/last_output.txt` or
  run the test/apply loop.
- `simplicio task --bound-paths <glob>` repeatable edit-surface guard. Generated
  diffs outside the allowed globs are refused before the test loop and reported
  as JSON warnings.

### Changed
- **`rust/simplicio-core`: PyO3 `0.22` → `0.28`** (manual major dependency bump,
  per `.specs/workflow/DEPENDENCY_POLICY.md`). The `build_6layer_prompt` / `hello`
  extension now builds against current PyO3. No source changes to `lib.rs` — the
  existing `Bound<'_, PyModule>` / `#[pyfunction]` API is forward-compatible.

### Fixed
- **Build blocker on Python 3.14.** PyO3 0.22 capped at CPython 3.13, so the crate
  failed to compile against the 3.14 default interpreter. Now builds natively on
  CPython 3.14.5 (cp314 wheel): parity suite 5/5, ~8.5x over the Python reference,
  and the Rust-assembled prompt drives `qwen2.5-coder:3b` to 5/6 on the real-pytest
  exec bench. See `bench/results_rust_qwen.md`.

## [0.4.1] — 2026-05-28

### Added
- **Dependency-update policy and enforcement** (closes #21):
  - `.specs/workflow/DEPENDENCY_POLICY.md` — ecosystem version policy:
    semver, floor-pinning (`>=`), 15-day floor-bump rule after upstream
    release, no cyclic deps, release-sync checklist.
  - `.github/workflows/check-deps.yml` — daily CI (and on every PR
    touching `pyproject.toml`) that compares pinned floors against the
    latest published version of every ecosystem dependency on PyPI and
    fails the build with `::error::` annotations when one is at least
    a minor behind.
  - `.github/dependabot.yml` — weekly grouped updates for `pip`
    (ecosystem packages grouped), `cargo` (`rust/simplicio-core`), and
    `github-actions`. Patches auto-merge, minor/major wait for review.

### Changed
- `simplicio-mapper>=0.5.0` → `>=0.6.0` (catch up with upstream 0.6.0).
- `simplicio-prompt>=1.7.0` → `>=1.9.0` (catch up with upstream 1.9.0).

Both bumps validated locally: `pytest tests/python` stays 38/38 green
with the new versions installed.

## [0.4.0] — 2026-05-28

### Added
- **Real-execution benchmark on a real project (`wesleysimplicio/sistema-sindico`).**
  New `bench/run_exec_sindico.py` harness writes each model's PHP output
  into a working copy and scores by `vendor/bin/phpunit` exit code over the
  full production suite. 12 cases cover `src/Core/`, `src/Middleware/`,
  `src/Repositories/`, routing, and one bug-fix scenario that scores
  against the existing `PasswordPolicyTest`. Headline on 9 models × 4
  tasks: baseline 33% → simplicio-cli **64%** (+31 pts).
  Reports: `bench/results_exec_sindico.{md,pdf,json}`.
- **17-model regex re-run + old→new comparison.** `bench/run_offline.py`
  gained a local `transformers` backend for HF-only small models, HTTP
  retry with exponential backoff (`BENCH_HTTP_RETRIES`), and `--pdf-only` /
  `--report-only` modes for regenerating reports without re-calling models.
  New `bench/compare_versions.py` joins the published per-model numbers
  with the fresh re-run side by side; 14 of 17 returned clean data
  (with simplicio averaged 86% → **88%**, within noise of the prior
  publication). Three frontier models hit account-level provider failures
  and are flagged `n/a` with the reason in the report.
  Reports: `bench/results_comparison.{md,pdf}`, merged data in
  `bench/results_all.json`.
- **Fan-out benchmark using the real `simplicio-prompt` kernel.** New
  `bench/run_fanout.py` instantiates `kernel.subagent_runtime.SubagentRuntime`
  from the PyPI package and launches real parallel LLM calls through
  `LaneWorkerPool`. Every subagent output gets scored two ways: real
  PHPUnit (functional) and a structural regex check. Default N=200 (the
  level where harder tasks recover from per-call noise).
- **Three-side comparison report (`bench/compare_sp.py`).** Generates a
  focused "with vs without simplicio-prompt" report from any sp-enabled
  exec validation JSON, with a data-quality guard that flags models whose
  calls returned no model output (HTTP 402 / empty bodies / etc.) so the
  numbers never silently average in noise.
- **`simplicio/utils/` package (Performance Phase 1, closes #14):**
  - `http_client.py` — lazy singleton `httpx.Client` with connection
    pooling and env-driven timeouts; `post_json()` helper.
  - `serialization.py` — orjson-backed `dumps` / `dumps_str` / `loads`,
    with stdlib `json` fallback so the import never breaks.
  - `cache.py` — `diskcache` namespaces under `.simplicio/cache/` plus a
    `memoize_disk(namespace=, ttl=)` decorator.
- **`simplicio-core` Rust crate (closes #15, #17, #18):**
  - New `rust/simplicio-core/` with PyO3 0.22 + bumpalo. Build with
    `cd rust/simplicio-core && maturin develop --release`.
  - `simplicio_core.build_6layer_prompt(...)` runs the substitution +
    comment-strip step of `build_prompt` in Rust. **4.9x faster
    (12.4 µs → 2.5 µs)** on the real template, byte-equal to the Python
    reference. UTF-8-safe walker handles multibyte content (em-dashes,
    etc.) without corruption.
  - `simplicio/prompt.py` picks the Rust path when the extension is
    installed and falls back to the extracted `_assemble_python`
    reference implementation otherwise. The CLI's runtime deps do not
    include `simplicio-core`, so a pip-only install (no Rust toolchain)
    keeps working.
- **`simplicio-prompt>=1.7.0` and `simplicio-mapper>=0.5.0` as runtime
  dependencies.** README install section documents the three Simplicio
  packages and their per-scope roles.
- **README rewrite to "real project, real tasks, real test suite".**
  Section 1 leads with the real-PHPUnit benchmark on sistema-sindico;
  Section 2 explicitly labels the regex tables as a complementary
  *contract-adherence* metric (not a runtime proof). The HF Qwen2.5-Coder
  re-run is documented honestly with the n/a callouts for the
  paywall-blocked frontier models.

### Changed
- `simplicio/mapper.py`, `simplicio/observability.py`, `simplicio/init.py`
  switched from stdlib `json` to the new orjson-backed helpers (13x
  faster on the bench payloads).
- `simplicio/prompt.py` caches the 6-layer template through an
  `lru_cache(maxsize=4)` so it is read once per process instead of every
  call.
- `bench/run_offline.py` extracts report generation into
  `build_reports(by_model, cases)` so md/pdf/charts can be regenerated
  from results.json without re-calling any model (`--report-only`).
- README fanout claim rewritten against actually measured data (the
  earlier "N=64 is the sweet spot" came from a single-task run with
  `use_cache=True` that triggered ReceiptCache dedup; cache-off partial
  data shows N depends on task difficulty).
- `BENCH_FANOUT_NS` defaults to a single value (`"200"`) for our chosen
  production operating point; sweep across multiple Ns by setting the
  env var explicitly.

### Fixed
- 7B-only re-run in the Qwen2.5-Coder benchmark recovered one case
  that hit a transient SSL `CERTIFICATE_VERIFY_FAILED` on the HF router
  (single-call empty result was inflating the gap by ~2 points). Merged
  cleanly with the 1.5B/3B data through the new `--report-only` path.

## [0.3.0] — 2026-05-27

### Added
- Real mapper consumption for `.simplicio/project-map.json` and
  `.simplicio/precedent-index.json`, including relevant files, architecture
  signals, modules, recent changes, and fallback target inspection.
- Structured precedent retrieval from the mapper `precedent-index.json` before
  falling back to embedding-based grep candidates.
- Model-adaptive prompt scaffolding plus lightweight task decomposition for
  smaller/local models.
- Pre-apply output validation, failure classification, and targeted retry
  feedback for syntax, assertion, dependency, timeout, runtime, and unknown
  failures.
- Opt-in run observability at `.simplicio/runs.jsonl`, recording prompt
  variant, model/provider, estimated tokens, modes, targets, attempts, and
  failure class.

### Changed
- Benchmarks now log baseline/pipeline runs and report hallucinated-target
  flags alongside pass rate.
- Prompt template now injects a model adaptation/decomposition layer while
  preserving the DIFF + TEST + EVIDENCE output contract.

## [0.2.12] — 2026-05-26

### Added
- **Zero-step bootstrap**: the first time `simplicio` is invoked after
  `pip install`, if `~/.claude/` exists and the hook is missing, the skill +
  UserPromptSubmit hook are installed automatically. PEP 517 wheels can't run
  code on `pip install`, so the bootstrap happens on first CLI use — the
  closest equivalent that works on every machine. Idempotent. Subcommands
  `init` and `detect` are excluded (no loops). All failure modes silently
  no-op so the CLI never breaks because of auto-activation. Opt-out:
  `export SIMPLICIO_SKIP_AUTO_INIT=1` before the first call.
- README sections:
  - "How it works at runtime" — explains the two layers (skill = semantic,
    hook = deterministic) and what flows on every prompt.
  - "Why UserPromptSubmit and not PreToolUse" — UserPromptSubmit fires once,
    before tool decision, with the raw prompt; PreToolUse fires after the
    decision and per tool call without access to the prompt.
  - "Disable / re-enable" matrix — env var, manual removal, dry-run, repair,
    skill-only path.
  - "How you use it — pick your path" — upfront 2-path matrix (Claude Code
    zero-key vs standalone CLI with API key), with end-to-end examples for
    each path so the user can decide which one applies in 30 seconds.
  - "The pipeline (both paths)" — clarifies that whichever entry point is
    used, the underlying engine (precedent → skill → 6-layer → LLM → apply
    → test → retry) is the same.
  - "Common questions" FAQ — covers the four most asked questions: does it
    work with a Claude Pro subscription alone, how to run it in CI without
    Claude Code, the ChatGPT Plus / Codex CLI situation (not auto-wired),
    when the skill actually fires, and how to turn it off.
  - Tagline updated to lead with "Zero API key inside Claude Code" so the
    PyPI / GitHub landing page makes the no-key-needed path obvious.
- `tests/python/test_cli_autoinstall.py` — 5 tests covering the env opt-out,
  missing `~/.claude/`, `init`/`detect` subcommand exclusion, fresh install,
  and already-installed short-circuit.

### Changed
- `simplicio/cli.py`: new `maybe_autoinstall(cmd)` helper called once after
  argparse, before dispatch. Errors are caught and logged to stderr without
  raising. `from __future__ import annotations` added for Python 3.9
  compatibility on the new type hints.

## [0.2.11] — 2026-05-26

### Added
- `simplicio init` — one-shot installer that drops the `simplicio-cli` skill
  into `~/.claude/skills/simplicio-cli/SKILL.md` and merges a
  `UserPromptSubmit` hook entry into `~/.claude/settings.json` (with a
  `.bak` backup of the previous settings). Idempotent. `--dry-run` shows the
  plan without writing.
- `simplicio detect` — pure-Python heuristic (no LLM) that scores a prompt for
  code-edit intent (verbs + file extension + code nouns + explicit invocation
  cues, with a negative-cue list for read-only questions). Prints a
  `[SIMPLICIO_PROMPT_HINT]` block to stderr when the score crosses the
  threshold. `--json` for machine-readable output, `--quiet` to suppress the
  hint.
- Shipped templates: `simplicio/templates/SKILL.md` (skill body) and
  `simplicio/templates/userpromptsubmit-hook.sh` (hook wrapper). Both packaged
  in the wheel via `tool.setuptools.package-data`.
- README section "Auto-activation in Claude Code" explaining the
  two-mechanism (skill + hook) design and the single-command install flow.

### Changed
- `simplicio/cli.py` — heavy imports (numpy via `precedent`, providers SDKs)
  are now lazy: `simplicio init`, `simplicio detect`, and `--help` start
  instantly without paying for them.
- `tool.setuptools.package-data` now includes `templates/*.sh`.

### Notes
- Skill-only path: when `simplicio` is not on PATH or the user never runs
  `simplicio init`, behavior degrades gracefully — the hook script no-ops, and
  the skill still triggers on description match when the project ships a copy
  in `.skills/simplicio-cli/`. End-users without `simplicio init` get the
  description-matching tier (~80% coverage); with `simplicio init` they get
  the deterministic-fallback tier (~98%).

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

[0.2.12]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.12
[0.2.11]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.11
[0.2.10]: https://github.com/wesleysimplicio/simplicio-cli/releases/tag/v0.2.10
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
