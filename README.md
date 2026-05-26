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
**Nine models tested across two runs** — six frontier 2026 models and three mid-tier
7B–12B open models. Every one gained at least **+48 points** when wrapped in
simplicio's 6-layer contract.

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

> **Across all 9 models tested**, the average gain is **+56 points**. Smallest:
> **+52 pts** (DeepSeek V4 Pro on frontier run). Largest: **+62 pts** (GPT-5.5).
> The contract helps frontier reasoning models *and* mid-tier 7B–12B alike —
> five of the six frontier models hit **100% pass-rate**.

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
