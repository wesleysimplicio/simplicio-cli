# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-27**  
Models: `qwen2.5-coder:1.5b`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `http://localhost:11434/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 17/52 (32%)
- **With simplicio:** 46/52 (88%)
- **Delta:** **+56 points** (+171% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `qwen2.5-coder:1.5b` | 10 | 17/52 (32%) | 46/52 (88%) | **+56** | +171% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 40% | 0% | **-40** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 100% | **+60** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 20% | 80% | **+60** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 33% | 100% | **+67** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 20% | 100% | **+80** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 100% | **+50** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 40% | 100% | **+60** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 20% | 100% | **+80** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 20% | 100% | **+80** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 100% | **+60** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 35% | 77% | **+42** |
| `dotnet` | 20% | 100% | **+80** |
| `react` | 38% | 100% | **+62** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/10) | 80% (8/10) |
| TEST block present | 60% (6/10) | 90% (9/10) |
| target file mentioned | 0% (0/10) | 80% (8/10) |
| avg criteria-keywords hit / run | 8.9 | 10.0 |
| avg output length (chars) | 1981 | 2368 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `qwen2.5-coder:1.5b` | without | 46 | 440 | 486 | 12579 ms |
| `qwen2.5-coder:1.5b` | with    | 208 | 542 | 750 | 28409 ms |

**Aggregate over the full bench** (10 runs per side):

- without simplicio: 4,861 tokens total · 125.8s wall-clock · 486 tok/run · 12579 ms/run
- with simplicio:    7,504 tokens total · 284.1s wall-clock · 750 tok/run · 28409 ms/run
- token delta:       +2,643 (+54%)
- time delta:        +158.3s (+125%)

## How to reproduce

```bash
OPENROUTER_API_KEY=… \
  BENCH_MODELS="qwen2.5-coder:1.5b" \
  python3 bench/run_offline.py
```

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
