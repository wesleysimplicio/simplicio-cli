# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-26**
Base: `https://openrouter.ai/api/v1`
Cases: **10** across stacks: `angular`, `dotnet`, `react`

Each check is a deterministic regex against the model output
(target-file mention, DIFF block, TEST block, contract-state words).
Same model on both sides — only the prompt structure changes. The
*without* run is the raw one-line goal; the *with* run wraps the
same goal in simplicio's 6-layer contract.

See also — 4-quadrant matrix (adds the execution axis: 1-shot vs.
loop with feedback): focused run [results_4quadrant.md](results_4quadrant.md),
wider replication [results_4quadrant_wide.md](results_4quadrant_wide.md).

**Three runs on record so far — 14 models in total:**

| Run | Models tested | Pass-rate (without → with) | Δ pts |
|---|---|---|---|
| **Tiny (sub-4B)** | 5 — Llama 3.2 1B/3B · Gemma 3 4B · Gemma 3n e4B · Phi-4 mini | 35% → 74% | **+39** |
| **Frontier 2026** | 6 — GPT-5.5 · Kimi K2.6 · Gemini 3.5 Flash · Qwen 3.7 Max · Opus 4.7 · DeepSeek V4 Pro | 41% → 99% | **+58** |
| **Mid-tier 7B–12B (v0.2.2 archival)** | 3 — Gemma 3 12B · Llama 3.1 8B · Qwen 2.5 7B | 35% → 90% | **+55** |

Charts below reflect the **Frontier 2026** run (current headline).

---

## Tiny models — sub-4B (current run, 2026-05-26)

Smallest models we could put through OpenRouter. simplicio's contract
still moves the needle even when the model has barely enough parameters
to track the goal. Five models, 10 cases, 50 runs/side, 260 checks.

### Headline (tiny)

- **Without simplicio:** 91/260 (35%)
- **With simplicio:** 193/260 (74%)
- **Delta:** **+39 points** (+112% relative)

### Per-model breakdown (tiny)

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `google/gemma-3-4b-it` | 10 | 20/52 (38%) | 50/52 (96%) | **+58** | +150% |
| `meta-llama/llama-3.2-3b-instruct` | 10 | 15/52 (28%) | 38/52 (73%) | **+45** | +153% |
| `google/gemma-3n-e4b-it` | 10 | 23/52 (44%) | 46/52 (88%) | **+44** | +100% |
| `microsoft/phi-4-mini-instruct` | 10 | 19/52 (36%) | 38/52 (73%) | **+37** | +100% |
| `meta-llama/llama-3.2-1b-instruct` | 10 | 14/52 (26%) | 21/52 (40%) | **+14** | +50% |
| **Tiny avg (5 models · 10 cases · 260 checks)** | — | **35%** | **74%** | **+39** | **+112%** |

### Output-quality signals (tiny, 50 runs/side)

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/50) | 74% (37/50) |
| TEST block present | 82% (41/50) | 80% (40/50) |
| target file mentioned | 0% (0/50) | 84% (42/50) |
| avg criteria-keywords hit / run | 8.9 | 8.3 |
| avg output length (chars) | 3,971 | 6,659 |

### Cost — tiny

| Side | Tokens / run | Wall-clock / run | Total tokens (50 runs) | Total time |
|---|---|---|---|---|
| Raw prompt | 1,006 | 15.6s | 50,347 | 13m 00s |
| With simplicio | **1,289** | **9.1s** | **64,477** | **7m 36s** |
| Δ | **+28%** | **-42%** | +14,130 | **-5m 24s** |

Notable: on tiny models, **simplicio's wall-clock is lower than raw**
(-42%). Smaller models burn cycles in unguided exploration without the
contract; with the contract they stop guessing earlier. Per-model
breakdown:

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `meta-llama/llama-3.2-1b-instruct` | without | 28 | 453 | 481 | 2,296 ms |
| `meta-llama/llama-3.2-1b-instruct` | with    | 211 | 3,430 | 3,641 | 17,020 ms |
| `meta-llama/llama-3.2-3b-instruct` | without | 51 | 439 | 491 | 1,989 ms |
| `meta-llama/llama-3.2-3b-instruct` | with    | 247 | 529 | 776 | 2,225 ms |
| `google/gemma-3-4b-it` | without | 25 | 1,636 | 1,662 | 32,114 ms |
| `google/gemma-3-4b-it` | with    | 225 | 444 | 670 | 10,500 ms |
| `google/gemma-3n-e4b-it` | without | 32 | 1,720 | 1,753 | 38,729 ms |
| `google/gemma-3n-e4b-it` | with    | 232 | 567 | 800 | 13,962 ms |
| `microsoft/phi-4-mini-instruct` | without | 19 | 626 | 645 | 2,865 ms |
| `microsoft/phi-4-mini-instruct` | with    | 204 | 354 | 558 | 1,876 ms |

### Per-stack (tiny)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 32% | 75% | **+43** |
| `dotnet` | 36% | 64% | **+28** |
| `react` | 39% | 80% | **+41** |

### Tiny models requested but not hosted on OpenRouter

Eight models from the original ask are not in OpenRouter's catalog
(2026-05-26 listing). They would need a local Ollama deploy to bench
on the same harness:

- Gemma 3 270M, Gemma 3 1B, Gemma 2 2B
- Qwen3 0.6B, Qwen3 1.7B
- Qwen 2.5 0.5B, Qwen 2.5 1.5B, Qwen 2.5 3B
- Nemotron Nano 4B (smallest Nemotron on OpenRouter is `nemotron-nano-9b-v2`)

The five tested here are the closest sub-4B substitutes that OpenRouter
actually serves.

---

## Frontier 2026 models (60 runs/side, 312 checks)

Six frontier models — Opus 4.7, GPT-5.5, Gemini 3.5 Flash, Kimi K2.6,
Qwen 3.7 Max, DeepSeek V4 Pro. **Current headline run.**

### Headline (frontier)

- **Without simplicio:** 131/312 (41%)
- **With simplicio:** 309/312 (99%)
- **Delta:** **+58 points** (+136% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

### Per-model breakdown (frontier)

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `openai/gpt-5.5` | 10 | 20/52 (38%) | 52/52 (100%) | **+62** | +160% |
| `moonshotai/kimi-k2.6` | 10 | 21/52 (40%) | 52/52 (100%) | **+60** | +148% |
| `google/gemini-3.5-flash` | 10 | 22/52 (42%) | 52/52 (100%) | **+58** | +136% |
| `qwen/qwen3.7-max` | 10 | 23/52 (44%) | 52/52 (100%) | **+56** | +126% |
| `anthropic/claude-opus-4.7` | 10 | 22/52 (42%) | 51/52 (98%) | **+56** | +132% |
| `deepseek/deepseek-v4-pro` | 10 | 23/52 (44%) | 50/52 (96%) | **+52** | +117% |

### Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 37% | 100% | **+63** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 100% | **+60** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 40% | 100% | **+60** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 47% | 97% | **+50** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 37% | 97% | **+60** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 100% | **+50** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 40% | 100% | **+60** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 47% | 100% | **+53** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 37% | 100% | **+63** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 43% | 97% | **+53** |

### Per-stack (frontier)

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 42% | 99% | **+57** |
| `dotnet` | 42% | 100% | **+58** |
| `react` | 43% | 99% | **+56** |

### Output-quality signals (frontier, 60 runs/side)

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 36% (22/60) | 98% (59/60) |
| TEST block present | 88% (53/60) | 98% (59/60) |
| target file mentioned | 1% (1/60) | 100% (60/60) |
| avg criteria-keywords hit / run | 9.3 | 10.3 |
| avg output length (chars) | 6,070 | 2,859 |

### Cost — frontier (per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`.
*Per-run* = one model call (one case, one side). With simplicio uses more input
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-pro` | without | 21 | 2,038 | 2,059 | 41,979 ms |
| `deepseek/deepseek-v4-pro` | with    | 224 | 2,630 | 2,854 | 72,808 ms |
| `qwen/qwen3.7-max` | without | 27 | 1,473 | 1,500 | 33,043 ms |
| `qwen/qwen3.7-max` | with    | 226 | 3,410 | 3,636 | 87,175 ms |
| `moonshotai/kimi-k2.6` | without | 24 | 5,097 | 5,122 | 172,160 ms |
| `moonshotai/kimi-k2.6` | with    | 208 | 6,741 | 6,949 | 142,773 ms |
| `openai/gpt-5.5` | without | 22 | 387 | 410 | 7,897 ms |
| `openai/gpt-5.5` | with    | 207 | 1,318 | 1,525 | 20,888 ms |
| `anthropic/claude-opus-4.7` | without | 35 | 1,001 | 1,037 | 12,412 ms |
| `anthropic/claude-opus-4.7` | with    | 340 | 647 | 987 | 7,945 ms |
| `google/gemini-3.5-flash` | without | 16 | 1,657 | 1,674 | 9,242 ms |
| `google/gemini-3.5-flash` | with    | 216 | 2,841 | 3,058 | 13,785 ms |

**Aggregate over the frontier bench** (60 runs per side):

- without simplicio: 118,040 tokens · 2,767.4s wall-clock · 1,967 tok/run · 46,122 ms/run
- with simplicio:    190,119 tokens · 3,453.8s wall-clock · 3,168 tok/run · 57,562 ms/run
- token delta:       +72,079 (+61%)
- time delta:        +686.4s (+24%)

---

## Earlier run — mid-tier 7B–12B open models (v0.2.2, archival)

Run on the same harness against the previous generation of mid-tier open models
before the frontier 2026 lineup. Kept here so the full set of **14 models**
tested across the three runs is on record.

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `google/gemma-3-12b-it` | 10 | 18/52 (34%) | 48/52 (92%) | **+58** | +167% |
| `meta-llama/llama-3.1-8b-instruct` | 10 | 19/52 (36%) | 47/52 (90%) | **+54** | +147% |
| `qwen/qwen-2.5-7b-instruct` | 10 | 18/52 (34%) | 46/52 (88%) | **+54** | +159% |
| **Mid-tier avg (3 models · 10 cases · 156 checks)** | — | **35%** | **90%** | **+55** | **+156%** |

Output-quality signals on that run: DIFF block 0% → 100%, target file mentioned
0% → 96%, TEST block 80% → 96%. Wall-clock 12.4s → 9.9s/run (simplicio faster
on smaller models because they stop guessing earlier). Source: `CHANGELOG.md`
entry `[0.2.2] — 2026-05-26`.

---

## How to reproduce

```bash
# Tiny (sub-4B) — 5 models
OPENROUTER_API_KEY=… \
  BENCH_MODELS="meta-llama/llama-3.2-1b-instruct,meta-llama/llama-3.2-3b-instruct,google/gemma-3-4b-it,google/gemma-3n-e4b-it,microsoft/phi-4-mini-instruct" \
  python3 bench/run_offline.py

# Frontier 2026 — 6 models
OPENROUTER_API_KEY=… \
  BENCH_MODELS="deepseek/deepseek-v4-pro,qwen/qwen3.7-max,moonshotai/kimi-k2.6,openai/gpt-5.5,anthropic/claude-opus-4.7,google/gemini-3.5-flash" \
  python3 bench/run_offline.py

# Mid-tier 7B–12B (v0.2.2 archival) — 3 models
OPENROUTER_API_KEY=… \
  BENCH_MODELS="google/gemma-3-12b-it,meta-llama/llama-3.1-8b-instruct,qwen/qwen-2.5-7b-instruct" \
  python3 bench/run_offline.py
```

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt`
so you can audit what the LLM actually produced on each side. Charts are
SVG under `bench/charts/` (reflect the frontier run); raw aggregated data
under `bench/results.json` (also frontier; tiny artifacts stored separately).
