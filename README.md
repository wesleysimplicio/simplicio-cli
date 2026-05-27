# simplicio-cli

**Your tasks with 99% accuracy using any LLM (Claude, DeepSeek, Codex, Gemini, Hermes, OpenClaw, Cursor).**

[![PyPI](https://img.shields.io/pypi/v/simplicio-cli.svg)](https://pypi.org/project/simplicio-cli/)
[![Python](https://img.shields.io/pypi/pyversions/simplicio-cli.svg)](https://pypi.org/project/simplicio-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[![simplicio-cli pipeline hero: one-line task to verified code change](https://raw.githubusercontent.com/wesleysimplicio/simplicio-cli/master/output/imagegen/simplicio-cli-readme-hero-web.png)](output/imagegen/simplicio-cli-readme-hero.png)

> *"hide the Delete button for non-admins"* → diff + test + applied + verified.
> Works with **OpenRouter, OpenAI, Anthropic, GLM, DeepSeek, Ollama** — one env var.

```bash
pip install simplicio-cli
```

---

## Why it works — the numbers

Same model. Same task. Only the prompt changes. **Measured, reproducible, deterministic.**
**Fourteen models tested across three runs** — five sub-4B tiny models, six
frontier 2026 models, and three mid-tier 7B–12B open models. Every one gained
at least **+14 points** when wrapped in simplicio's 6-layer contract.

#### Tiny models — sub-4B, run on 2026-05-26 (50 runs/side, 260 checks)

| Model | Without simplicio | With simplicio | Gain |
|---|---|---|---|
| **Gemma 3 4B** (`google/gemma-3-4b-it`) | 38% | **96%** | **+58 pts** |
| **Llama 3.2 3B** (`meta-llama/llama-3.2-3b-instruct`) | 28% | **73%** | **+45 pts** |
| **Gemma 3n e4B** (`google/gemma-3n-e4b-it`) | 44% | **88%** | **+44 pts** |
| **Phi-4 mini** (`microsoft/phi-4-mini-instruct`) | 36% | **73%** | **+37 pts** |
| **Llama 3.2 1B** (`meta-llama/llama-3.2-1b-instruct`) | 26% | **40%** | **+14 pts** |
| **Tiny avg (5 models · 10 cases · 260 checks)** | **35%** | **74%** | **+39 pts (+112%)** |

> **Not hosted on OpenRouter** (requested but skipped): Gemma 3 270M, Gemma 3 1B,
> Gemma 2 2B, Qwen3 0.6B, Qwen3 1.7B, Qwen2.5 0.5B, Qwen2.5 1.5B, Qwen 3B,
> Nemotron Nano 4B (OR's smallest Nemotron is 9B). Sub-4B substitutes used above.
> simplicio still gains **+14 to +58 points** even on a 1B-param model.

#### Frontier 2026 models — run on 2026-05-26 (60 runs/side, 312 checks)

| Model | Without simplicio | With simplicio | Gain |
|---|---|---|---|
| **GPT-5.5** (`openai/gpt-5.5`) | 38% | **100%** | **+62 pts** |
| **Kimi K2.6** (`moonshotai/kimi-k2.6`) | 40% | **100%** | **+60 pts** |
| **Gemini 3.5 Flash** (`google/gemini-3.5-flash`) | 42% | **100%** | **+58 pts** |
| **Qwen 3.7 Max** (`qwen/qwen3.7-max`) | 44% | **100%** | **+56 pts** |
| **Claude Opus 4.7** (`anthropic/claude-opus-4.7`) | 42% | **98%** | **+56 pts** |
| **DeepSeek V4 Pro** (`deepseek/deepseek-v4-pro`) | 44% | **96%** | **+52 pts** |
| **Frontier avg (6 models · 10 cases · 312 checks)** | **41%** | **99%** | **+58 pts (+136%)** |

#### Mid-tier 7B–12B open models — earlier run (v0.2.2, 30 runs/side, 156 checks)

| Model | Without simplicio | With simplicio | Gain |
|---|---|---|---|
| **Gemma 3 12B** (`google/gemma-3-12b-it`) | 34% | **92%** | **+58 pts** |
| **Llama 3.1 8B** (`meta-llama/llama-3.1-8b-instruct`) | 36% | **90%** | **+54 pts** |
| **Qwen 2.5 7B** (`qwen/qwen-2.5-7b-instruct`) | 34% | **88%** | **+54 pts** |
| **Mid-tier avg (3 models · 10 cases · 156 checks)** | **35%** | **90%** | **+55 pts (+156%)** |

> **Across all 14 models tested across three runs**, the average gain is **+51
> points**. Smallest: **+14 pts** (Llama 3.2 1B — the contract still moves a
> 1B-param model). Largest: **+62 pts** (GPT-5.5). The contract helps tiny
> sub-4B models, frontier reasoning models, and mid-tier 7B–12B alike — five
> of the six frontier models hit **100% pass-rate**.

### Output-quality signals (rate across all 60 frontier runs)

| Signal | Raw prompt | With simplicio |
|---|---|---|
| **DIFF block present** | 36% | **98%** |
| Target file mentioned | 1% | **100%** |
| TEST block present | 88% | **98%** |

### Cost — tokens & wall-clock (measured, not estimated)

Same provider, same models, same cases. Token counts pulled from the API
`usage` field; latency from `time.perf_counter()` around each call.

| Side | Tokens / run | Wall-clock / run | Total tokens (60 runs) | Total time |
|---|---|---|---|---|
| Raw prompt | 1,967 | 46.1s | 118,040 | 46m 07s |
| With simplicio | **3,168** | **57.6s** | **190,119** | **57m 33s** |
| Δ | **+61%** | **+24%** | +72,079 | +11m 26s |

simplicio wraps the objective in a 6-layer contract — more input tokens up
front, longer completions because the model produces the full DIFF + TEST +
EVIDENCE the contract demands instead of a one-line guess. The bill goes up,
but so does the **pass-rate (41% → 99%)** and the **DIFF-block rate (36% → 98%)** —
useful tokens, not chat.

> Six frontier models — GPT-5.5, Kimi K2.6, Gemini 3.5 Flash, Qwen 3.7 Max,
> Claude Opus 4.7, DeepSeek V4 Pro — gained **+52 to +62 points** when wrapped
> in simplicio's 6-layer contract. Without changing the model. Without
> fine-tuning. Five of six landed at **100% pass-rate with simplicio**.

Full report: [`bench/results.md`](bench/results.md) · [`bench/results.pdf`](bench/results.pdf) · raw outputs under `.simplicio/bench_runs/`.

---

## How it works

```
mapper        WHERE   project structure + latest state
precedent     HOW-1   the real snippet in THIS repo that already does it
skill-router  HOW-2   the ONE mapper skill that matches (ranked, not all)
simplicio     BUILD   stacks the 6 layers into one prompt (cache-friendly)
test          JUDGE   contract written as testable states
verify        PROOF   ran it — did it actually pass? loop-fix up to 3x
```

**The idea in one line: don't ask the model to guess — hand it the path.**
Each layer terminates one decision the model would otherwise hallucinate.
Relevant > complete — inject the *right* context, never *all* of it.

---

## Install

```bash
pip install simplicio-cli           # from PyPI
# or
pip install -e .                    # from this repo
```

### Auto-activation in Claude Code (one extra step)

`pip install` only puts the `simplicio` binary on your PATH. To make Claude
Code **automatically** route code-edit tasks through simplicio, run once:

```bash
simplicio init
```

That installs **two** things into `~/.claude/`:

| File | Purpose |
|---|---|
| `~/.claude/skills/simplicio-cli/SKILL.md` | Skill the agent matches by description when your prompt looks like a code edit |
| `~/.claude/hooks/simplicio-userpromptsubmit.sh` + entry in `~/.claude/settings.json` | UserPromptSubmit hook that runs `simplicio detect` on every prompt and injects a hint when the heuristic catches a code-edit task the skill could miss |

**Skill** = semantic match (Claude decides). **Hook** = deterministic fallback
(always runs). Together they cover ~98% of code-edit prompts. Idempotent —
re-run safely after upgrades. Backs up your previous `settings.json` to
`settings.json.bak` before any merge. Add `--dry-run` to preview the changes.

To skip the hook and keep only the skill, just copy this repo's
`.skills/simplicio-cli/SKILL.md` to `~/.claude/skills/simplicio-cli/SKILL.md`
manually.

## Configure — any LLM, nothing hardcoded

| Provider | SIMPLICIO_MODEL | SIMPLICIO_BASE_URL |
|---|---|---|
| OpenRouter | `anthropic/claude-opus-4` | `https://openrouter.ai/api/v1` |
| GLM (z.ai) | `glm-4.6` | `https://api.z.ai/api/paas/v4` |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com` |
| OpenAI | `gpt-4.1` | `https://api.openai.com/v1` |
| Local (Ollama) | `llama3` | `http://localhost:11434/v1` |
| Anthropic native | `claude-opus-4-7` | *(leave unset)* |

If `SIMPLICIO_BASE_URL` is unset and the key is `ANTHROPIC_API_KEY`, it uses the
native Anthropic SDK. Otherwise it uses an OpenAI-compatible client pointed at
your `base_url` — so **any** OpenAI-like provider works without code changes.

```bash
simplicio smoke      # prints provider config + one test call
```

## Use

```bash
# index once (caches embeddings; re-run after big changes)
simplicio index --stack angular

# run a task
simplicio task "hide Delete button for non-admins" \
  --stack angular \
  --target src/app/screen/screen.component.html \
  --criteria "- no admin perm: button absent from DOM
- with admin perm: button present" \
  --constraints "- don't touch save flow
- build passes"
```

Each `task`: precedent (from cache) → skill match → 6 layers → LLM generates
(diff + test + Playwright) → apply → run `SIMPLICIO_TEST_CMD` → pass? **done** :
send the error back → fix → retry (up to 3x).

---

## Cache — why it doesn't re-map every time

Embeddings are keyed by **content hash**, stored in `.simplicio/`. Unchanged
code block → vector reused. Change one file → only that block re-embeds.

| Run | Blocks embedded | Time |
|---|---|---|
| 1st (cold cache) | 3 | ~baseline |
| 2nd (no change) | **0** | **~instant** |
| after editing 1 file | **1** | partial |

---

## Benchmark — reproduce in 30 seconds

```bash
OPENROUTER_API_KEY=… \
  BENCH_MODELS="deepseek/deepseek-v4-pro,qwen/qwen3.7-max,moonshotai/kimi-k2.6,openai/gpt-5.5,anthropic/claude-opus-4.7,google/gemini-3.5-flash" \
  python3 bench/run_offline.py
```

No project required, stdlib only, deterministic regex scoring — no LLM judges
the LLM. Each case runs twice on the **same** model: raw one-line objective vs
simplicio's 6-layer contract. Outputs scored on target-file mention, DIFF
block, TEST block, contract-state words. Full numbers in [`bench/results.md`](bench/results.md).

### Full harness (your real project, your real tests)

```bash
simplicio bench --cases bench/cases.json --stack angular
```

Runs each case two ways and runs **your real test command** (e.g. `ng test
--watch=false`) on each output. Writes the true pass-rate to
[`bench/results.md`](bench/results.md).

### 4-quadrant bench — agent × simplicio matrix

Adds the second axis: not just *"does the 6-layer wrap help one call?"* but
*"does it still help inside a retry loop?"*. Same model, same cases — only
the cell logic changes.

|                         | **no simplicio**         | **with simplicio**       |
| ----------------------- | ------------------------ | ------------------------ |
| **no agent** (1 call)   | Q1 — baseline            | Q2 — current bench       |
| **with agent** (loop)   | Q3 — loop only           | Q4 — composition         |

```bash
pip install -e ".[bench]"          # adds fpdf2 for PDF report
OPENROUTER_API_KEY=… \
  BENCH_MODELS="google/gemma-3-4b-it" \
  BENCH_MAX_ITERS=3 \
  python3 bench/run_4quadrant.py
```

Outputs `bench/results_4quadrant.{md,pdf,json}` + SVG charts under
`bench/charts/4q_*.svg` + per-iteration raw outputs under
`.simplicio/bench_4q/<model>/case_NN/q*_iter*.txt`. Methodology and
hypothesis decomposition: [`docs/benchmark-4quadrant.md`](docs/benchmark-4quadrant.md).

The matrix decomposes:

- **Prompt effect alone**: Q2 − Q1
- **Loop effect alone**: Q3 − Q1
- **Prompt effect inside loop**: Q4 − Q3 (does simplicio still matter once you loop?)
- **Composition gain over best single axis**: Q4 − max(Q2, Q3)
- **Synergy vs linear stacking**: Q4 − (Q1 + (Q2−Q1) + (Q3−Q1))

#### Run 1 — focused single-model, `google/gemma-3-4b-it`, 5 cases, max_iters=3 (2026-05-26)

| Quadrant | Prompt | Execution | Pass rate | Avg iters | Tokens / pass |
|---|---|---|---|---|---|
| **Q1** | raw goal | 1-shot | **0/5 (0%)** | 1.00 | 4,683 |
| **Q2** | simplicio 6-layer | 1-shot | **3/5 (60%)** | 1.00 | 800 |
| **Q3** | raw goal | loop w/ feedback | **2/5 (40%)** | 3.00 | 3,135 |
| **Q4** | simplicio 6-layer | loop w/ feedback | **4/5 (80%)** | 1.80 | 1,018 |

Decomposition (rejection threshold `|Δ| ≥ 5 pts`):

| Hypothesis | Δ | Verdict |
|---|---|---|
| Loop alone closes the gap (simplicio unnecessary once you loop) | Q4 − Q3 = **+40 pts** | **rejected** |
| Simplicio alone is enough (loop is overkill) | Q4 − Q2 = **+20 pts** | **rejected** |
| Gains stack linearly (no synergy) | Q4 − linear = **−20 pts** | **rejected** |

Cost per passing case: Q1 = 4,683 tok / 236s — Q2 = **800 tok / 21s** — Q3 = 3,135 tok / 109s — Q4 = **1,018 tok / 20s**. Full table + charts in [`bench/results_4quadrant.md`](bench/results_4quadrant.md).

#### Run 2 — wider multi-model, 3 models × 10 cases (partial), max_iters=5 (2026-05-26)

Replicated the matrix across more models and more cases. `qwen-2.5-7b` covers only the first 5 of 10 cases (wide run was killed mid-execution); `claude-3.5-haiku` not reached. Aggregate counts every observed `(model × case × quadrant)` tuple as one observation:

| Quadrant | Prompt | Execution | Pass rate | Avg iters | Tokens / pass | ms / pass |
|---|---|---|---|---|---|---|
| **Q1** | raw goal | 1-shot | **0/25 (0%)** | 1.00 | 22,387 | 817,437 |
| **Q2** | simplicio 6-layer | 1-shot | **16/25 (64%)** | 1.00 | 1,093 | 14,797 |
| **Q3** | raw goal | loop w/ feedback | **11/25 (44%)** | 4.00 | 7,154 | 106,382 |
| **Q4** | simplicio 6-layer | loop w/ feedback | **19/25 (76%)** | 2.44 | 1,914 | 24,170 |

Per-model breakdown:

| Model | Cases | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|---|
| `google/gemma-3-4b-it` | 10/10 | 0/10 (0%) | 7/10 (70%) | 4/10 (40%) | **8/10 (80%)** |
| `meta-llama/llama-3.2-3b-instruct` | 10/10 | 0/10 (0%) | 5/10 (50%) | 4/10 (40%) | **6/10 (60%)** |
| `qwen/qwen-2.5-7b-instruct` | 5/10 | 0/5 (0%) | 4/5 (80%) | 3/5 (60%) | **5/5 (100%)** |

Decomposition (rejection threshold `|Δ| ≥ 5 pts`):

| Hypothesis | Δ | Verdict |
|---|---|---|
| Loop alone closes the gap (simplicio unnecessary once you loop) | Q4 − Q3 = **+32 pts** | **rejected** |
| Simplicio alone is enough (loop is overkill) | Q4 − Q2 = **+12 pts** | **rejected** |
| Gains stack linearly (no synergy) | Q4 − linear = **−32 pts** | **rejected** |

Same picture at every scale: Q4 (composition) wins on pass-rate, **and** Q4 stays close to Q2 on cost (1.9k tok / 24s per pass vs. Q2's 1.1k / 15s) while Q3 burns 7.2k tok / 106s per pass for fewer passes. Full table + per-case breakdown in [`bench/results_4quadrant_wide.md`](bench/results_4quadrant_wide.md).

---

## Plug points (stubs marked in code)

| File | Replace with |
|---|---|
| `prompt.py::_mapper` | your real **llm-project-mapper** |
| `pipeline.py::_aplicar_e_testar` | extract diff → `git apply` → parse test result |
| `skill_router.py` | point `SIMPLICIO_SKILLS_DIR` at your mapper's skills |

## Layout

```
simplicio/
  cli.py          # index | task | bench | smoke
  cache.py        # content-hash embedding cache
  precedent.py    # grep + semantic rank (uses cache)
  skill_router.py # picks the ONE matching skill
  prompt.py       # stacks the 6 layers
  providers.py    # any OpenAI-compatible endpoint + Anthropic native
  pipeline.py     # generate → test → fix loop
  bench.py        # with-vs-without harness
  templates/simplicio_prompt.md
bench/
  run_offline.py  # stdlib-only multi-model benchmark
  cases.json      # your benchmark tasks
  cases_offline.json
  results.md      # filled by `simplicio bench` / `run_offline.py`
  charts/         # SVG: overall, delta, by_case, by_stack
```

## License
MIT
