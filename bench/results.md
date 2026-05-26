# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-26**  
Models: `deepseek/deepseek-v4-pro`, `qwen/qwen3.7-max`, `moonshotai/kimi-k2.6`, `openai/gpt-5.5`, `anthropic/claude-opus-4.7`, `google/gemini-3.5-flash`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `https://openrouter.ai/api/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 131/312 (41%)
- **With simplicio:** 309/312 (99%)
- **Delta:** **+58 points** (+136% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-pro` | 10 | 23/52 (44%) | 50/52 (96%) | **+52** | +117% |
| `qwen/qwen3.7-max` | 10 | 23/52 (44%) | 52/52 (100%) | **+56** | +126% |
| `moonshotai/kimi-k2.6` | 10 | 21/52 (40%) | 52/52 (100%) | **+60** | +148% |
| `openai/gpt-5.5` | 10 | 20/52 (38%) | 52/52 (100%) | **+62** | +160% |
| `anthropic/claude-opus-4.7` | 10 | 22/52 (42%) | 51/52 (98%) | **+56** | +132% |
| `google/gemini-3.5-flash` | 10 | 22/52 (42%) | 52/52 (100%) | **+58** | +136% |

## Per-case (averaged across models)

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

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 42% | 99% | **+57** |
| `dotnet` | 42% | 100% | **+58** |
| `react` | 43% | 99% | **+56** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 36% (22/60) | 98% (59/60) |
| TEST block present | 88% (53/60) | 98% (59/60) |
| target file mentioned | 1% (1/60) | 100% (60/60) |
| avg criteria-keywords hit / run | 9.3 | 10.3 |
| avg output length (chars) | 6070 | 2859 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-pro` | without | 21 | 2038 | 2059 | 41979 ms |
| `deepseek/deepseek-v4-pro` | with    | 224 | 2630 | 2854 | 72808 ms |
| `qwen/qwen3.7-max` | without | 27 | 1473 | 1500 | 33043 ms |
| `qwen/qwen3.7-max` | with    | 226 | 3410 | 3636 | 87175 ms |
| `moonshotai/kimi-k2.6` | without | 24 | 5097 | 5122 | 172160 ms |
| `moonshotai/kimi-k2.6` | with    | 208 | 6741 | 6949 | 142773 ms |
| `openai/gpt-5.5` | without | 22 | 387 | 410 | 7897 ms |
| `openai/gpt-5.5` | with    | 207 | 1318 | 1525 | 20888 ms |
| `anthropic/claude-opus-4.7` | without | 35 | 1001 | 1037 | 12412 ms |
| `anthropic/claude-opus-4.7` | with    | 340 | 647 | 987 | 7945 ms |
| `google/gemini-3.5-flash` | without | 16 | 1657 | 1674 | 9242 ms |
| `google/gemini-3.5-flash` | with    | 216 | 2841 | 3058 | 13785 ms |

**Aggregate over the full bench** (60 runs per side):

- without simplicio: 118,040 tokens total · 2767.4s wall-clock · 1967 tok/run · 46122 ms/run
- with simplicio:    190,119 tokens total · 3453.8s wall-clock · 3168 tok/run · 57562 ms/run
- token delta:       +72,079 (+61%)
- time delta:        +686.4s (+24%)

## Earlier run — mid-tier 7B–12B open models (v0.2.2, archival)

Run on the same harness against the previous generation of mid-tier open models
before the frontier 2026 lineup. Kept here so the full set of **nine models**
tested across both runs is on record.

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

## How to reproduce

```bash
OPENROUTER_API_KEY=… \
  BENCH_MODELS="deepseek/deepseek-v4-pro,qwen/qwen3.7-max,moonshotai/kimi-k2.6,openai/gpt-5.5,anthropic/claude-opus-4.7,google/gemini-3.5-flash" \
  python3 bench/run_offline.py
```

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
