# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-27**  
Models: `qwen2.5-coder:3b`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `http://localhost:11434/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 18/52 (34%)
- **With simplicio:** 43/52 (82%)
- **Delta:** **+48 points** (+139% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `qwen2.5-coder:3b` | 10 | 18/52 (34%) | 43/52 (82%) | **+48** | +139% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 60% | 100% | **+40** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 60% | **+20** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 20% | 80% | **+60** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 33% | 67% | **+33** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 20% | 100% | **+80** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 100% | **+50** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 40% | 100% | **+60** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 20% | 60% | **+40** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 20% | 60% | **+40** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 100% | **+60** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 38% | 81% | **+42** |
| `dotnet` | 20% | 60% | **+40** |
| `react` | 38% | 100% | **+62** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/10) | 100% (10/10) |
| TEST block present | 80% (8/10) | 100% (10/10) |
| target file mentioned | 0% (0/10) | 70% (7/10) |
| avg criteria-keywords hit / run | 9.3 | 10.2 |
| avg output length (chars) | 2712 | 1836 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `qwen2.5-coder:3b` | without | 46 | 614 | 660 | 28748 ms |
| `qwen2.5-coder:3b` | with    | 230 | 422 | 652 | 19661 ms |

**Aggregate over the full bench** (10 runs per side):

- without simplicio: 6,602 tokens total · 287.5s wall-clock · 660 tok/run · 28748 ms/run
- with simplicio:    6,529 tokens total · 196.6s wall-clock · 652 tok/run · 19661 ms/run
- token delta:       -73 (-2%)
- time delta:        -90.9s (-32%)

## How to reproduce

```bash
OPENROUTER_API_KEY=… \
  BENCH_MODELS="qwen2.5-coder:3b" \
  python3 bench/run_offline.py
```

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
