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

- **Without simplicio:** 125/312 (40%)
- **With simplicio:** 299/312 (95%)
- **Delta:** **+55 points** (+139% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-pro` | 10 | 21/52 (40%) | 46/52 (88%) | **+48** | +119% |
| `qwen/qwen3.7-max` | 10 | 22/52 (42%) | 48/52 (92%) | **+50** | +118% |
| `moonshotai/kimi-k2.6` | 10 | 19/52 (36%) | 52/52 (100%) | **+64** | +174% |
| `openai/gpt-5.5` | 10 | 19/52 (36%) | 51/52 (98%) | **+62** | +168% |
| `anthropic/claude-opus-4.7` | 10 | 23/52 (44%) | 50/52 (96%) | **+52** | +117% |
| `google/gemini-3.5-flash` | 10 | 21/52 (40%) | 52/52 (100%) | **+60** | +148% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 37% | 100% | **+63** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 100% | **+60** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 33% | 100% | **+67** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 47% | 94% | **+47** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 37% | 97% | **+60** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 47% | 100% | **+53** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 40% | 87% | **+47** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 37% | 97% | **+60** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 40% | 100% | **+60** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 83% | **+43** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 40% | 96% | **+56** |
| `dotnet` | 38% | 98% | **+60** |
| `react` | 42% | 95% | **+53** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 33% (20/60) | 95% (57/60) |
| TEST block present | 85% (51/60) | 95% (57/60) |
| target file mentioned | 0% (0/60) | 98% (59/60) |
| avg criteria-keywords hit / run | 9.2 | 10.2 |
| avg output length (chars) | 4207 | 4290 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `deepseek/deepseek-v4-pro` | without | 21 | 1557 | 1579 | 36990 ms |
| `deepseek/deepseek-v4-pro` | with    | 211 | 1440 | 1652 | 37307 ms |
| `qwen/qwen3.7-max` | without | 27 | 1516 | 1543 | 27023 ms |
| `qwen/qwen3.7-max` | with    | 226 | 3088 | 3314 | 48713 ms |
| `moonshotai/kimi-k2.6` | without | 24 | 3131 | 3155 | 112549 ms |
| `moonshotai/kimi-k2.6` | with    | 207 | 4730 | 4938 | 121925 ms |
| `openai/gpt-5.5` | without | 22 | 399 | 421 | 10243 ms |
| `openai/gpt-5.5` | with    | 207 | 1967 | 2174 | 43272 ms |
| `anthropic/claude-opus-4.7` | without | 35 | 962 | 998 | 14136 ms |
| `anthropic/claude-opus-4.7` | with    | 340 | 697 | 1037 | 8810 ms |
| `google/gemini-3.5-flash` | without | 16 | 1683 | 1700 | 11612 ms |
| `google/gemini-3.5-flash` | with    | 216 | 2786 | 3003 | 13797 ms |

**Aggregate over the full bench** (60 runs per side):

- without simplicio: 93,983 tokens total · 2125.6s wall-clock · 1566 tok/run · 35425 ms/run
- with simplicio:    161,211 tokens total · 2738.3s wall-clock · 2686 tok/run · 45637 ms/run
- token delta:       +67,228 (+71%)
- time delta:        +612.7s (+28%)

## How to reproduce

```bash
OPENROUTER_API_KEY=… \
  BENCH_MODELS="deepseek/deepseek-v4-pro,qwen/qwen3.7-max,moonshotai/kimi-k2.6,openai/gpt-5.5,anthropic/claude-opus-4.7,google/gemini-3.5-flash" \
  python3 bench/run_offline.py
```

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
