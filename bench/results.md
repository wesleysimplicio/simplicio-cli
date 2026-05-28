# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-27**  
Models: `local:Qwen/Qwen2.5-Coder-1.5B-Instruct`, `Qwen/Qwen2.5-Coder-3B-Instruct`, `Qwen/Qwen2.5-Coder-7B-Instruct`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `https://router.huggingface.co/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 54/156 (34%)
- **With simplicio:** 147/156 (94%)
- **Delta:** **+60 points** (+172% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `local:Qwen/Qwen2.5-Coder-1.5B-Instruct` | 10 | 16/52 (30%) | 48/52 (92%) | **+62** | +200% |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | 10 | 18/52 (34%) | 49/52 (94%) | **+60** | +172% |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | 10 | 20/52 (38%) | 50/52 (96%) | **+58** | +150% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 40% | 93% | **+53** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 33% | 93% | **+60** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 20% | 100% | **+80** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 33% | 94% | **+61** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 27% | 93% | **+67** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 100% | **+50** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 40% | 93% | **+53** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 27% | 93% | **+67** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 33% | 87% | **+53** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 93% | **+53** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 33% | 95% | **+62** |
| `dotnet` | 30% | 90% | **+60** |
| `react` | 40% | 96% | **+56** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/30) | 100% (30/30) |
| TEST block present | 73% (22/30) | 100% (30/30) |
| target file mentioned | 0% (0/30) | 100% (30/30) |
| avg criteria-keywords hit / run | 8.8 | 9.9 |
| avg output length (chars) | 2047 | 2466 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `local:Qwen/Qwen2.5-Coder-1.5B-Instruct` | without | 46 | 412 | 458 | 90727 ms |
| `local:Qwen/Qwen2.5-Coder-1.5B-Instruct` | with    | 230 | 674 | 904 | 152316 ms |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | without | 46 | 443 | 489 | 4699 ms |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | with    | 230 | 533 | 763 | 5216 ms |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | without | 46 | 513 | 559 | 8117 ms |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | with    | 230 | 477 | 707 | 7605 ms |

**Aggregate over the full bench** (30 runs per side):

- without simplicio: 15,077 tokens total · 1035.4s wall-clock · 502 tok/run · 34514 ms/run
- with simplicio:    23,749 tokens total · 1651.4s wall-clock · 791 tok/run · 55045 ms/run
- token delta:       +8,672 (+57%)
- time delta:        +615.9s (+59%)

## How to reproduce

```bash
BENCH_BASE_URL="https://router.huggingface.co/v1" \
  BENCH_API_KEY=… \
  BENCH_MODELS="local:Qwen/Qwen2.5-Coder-1.5B-Instruct,Qwen/Qwen2.5-Coder-3B-Instruct,Qwen/Qwen2.5-Coder-7B-Instruct" \
  python3 bench/run_offline.py
```

Models prefixed `local:` run on CPU via `transformers` (downloaded from the 
Hugging Face Hub); all others go through the OpenAI-compatible endpoint at 
`BENCH_BASE_URL`. Cap local generation length with `BENCH_LOCAL_MAX_TOKENS`.

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
