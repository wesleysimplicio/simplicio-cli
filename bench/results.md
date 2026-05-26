# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-26**  
Models: `qwen/qwen-2.5-7b-instruct`, `meta-llama/llama-3.1-8b-instruct`, `google/gemma-3-12b-it`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `https://openrouter.ai/api/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 55/156 (35%)
- **With simplicio:** 141/156 (90%)
- **Delta:** **+55 points** (+156% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `qwen/qwen-2.5-7b-instruct` | 10 | 18/52 (34%) | 46/52 (88%) | **+54** | +156% |
| `meta-llama/llama-3.1-8b-instruct` | 10 | 19/52 (36%) | 47/52 (90%) | **+54** | +147% |
| `google/gemma-3-12b-it` | 10 | 18/52 (34%) | 48/52 (92%) | **+58** | +167% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 40% | 73% | **+33** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 100% | **+60** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 20% | 93% | **+73** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 39% | 100% | **+61** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 33% | 93% | **+60** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 94% | **+44** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 27% | 93% | **+67** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 33% | 93% | **+60** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 27% | 73% | **+47** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 87% | **+47** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 36% | 91% | **+55** |
| `dotnet` | 30% | 83% | **+53** |
| `react` | 38% | 94% | **+56** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/30) | 100% (30/30) |
| TEST block present | 80% (24/30) | 96% (29/30) |
| target file mentioned | 0% (0/30) | 96% (29/30) |
| avg criteria-keywords hit / run | 9.5 | 9.6 |
| avg output length (chars) | 3045 | 2111 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `qwen/qwen-2.5-7b-instruct` | without | 46 | 689 | 735 | 11871 ms |
| `qwen/qwen-2.5-7b-instruct` | with    | 228 | 534 | 763 | 9129 ms |
| `meta-llama/llama-3.1-8b-instruct` | without | 29 | 586 | 616 | 11451 ms |
| `meta-llama/llama-3.1-8b-instruct` | with    | 213 | 470 | 683 | 10358 ms |
| `google/gemma-3-12b-it` | without | 25 | 900 | 925 | 13983 ms |
| `google/gemma-3-12b-it` | with    | 225 | 640 | 866 | 10341 ms |

**Aggregate over the full bench** (30 runs per side):

- without simplicio: 22,774 tokens total · 373.1s wall-clock · 759 tok/run · 12435 ms/run
- with simplicio:    23,127 tokens total · 298.3s wall-clock · 770 tok/run · 9943 ms/run
- token delta:       +353 (+1%)
- time delta:        -74.8s (-21%)

## How to reproduce

```bash
OPENROUTER_API_KEY=… \
  BENCH_MODELS="qwen/qwen-2.5-7b-instruct,meta-llama/llama-3.1-8b-instruct,google/gemma-3-12b-it" \
  python3 bench/run_offline.py
```

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
