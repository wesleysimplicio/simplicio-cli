# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-29**  
Models: `Qwen/Qwen3-Coder-30B-A3B-Instruct`, `Qwen/Qwen3-Coder-Next`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `https://router.huggingface.co/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 42/104 (40%)
- **With simplicio:** 99/104 (95%)
- **Delta:** **+55 points** (+136% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 10 | 19/52 (36%) | 47/52 (90%) | **+54** | +147% |
| `Qwen/Qwen3-Coder-Next` | 10 | 23/52 (44%) | 52/52 (100%) | **+56** | +126% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 40% | 100% | **+60** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 90% | **+50** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 20% | 90% | **+70** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 42% | 92% | **+50** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 40% | 100% | **+60** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 92% | **+42** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 50% | 90% | **+40** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 50% | 100% | **+50** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 30% | 100% | **+70** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 100% | **+60** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 37% | 94% | **+58** |
| `dotnet` | 40% | 100% | **+60** |
| `react` | 47% | 94% | **+47** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 25% (5/20) | 100% (20/20) |
| TEST block present | 95% (19/20) | 100% (20/20) |
| target file mentioned | 0% (0/20) | 75% (15/20) |
| avg criteria-keywords hit / run | 8.9 | 10.3 |
| avg output length (chars) | 3286 | 2562 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | without | 25 | 613 | 638 | 4838 ms |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | with    | 209 | 565 | 774 | 4432 ms |
| `Qwen/Qwen3-Coder-Next` | without | 25 | 947 | 972 | 6475 ms |
| `Qwen/Qwen3-Coder-Next` | with    | 209 | 661 | 871 | 4043 ms |

**Aggregate over the full bench** (20 runs per side):

- without simplicio: 16,111 tokens total · 113.1s wall-clock · 805 tok/run · 5656 ms/run
- with simplicio:    16,457 tokens total · 84.8s wall-clock · 822 tok/run · 4237 ms/run
- token delta:       +346 (+2%)
- time delta:        -28.4s (-26%)

## How to reproduce

```bash
BENCH_BASE_URL="https://router.huggingface.co/v1" \
  BENCH_API_KEY=… \
  BENCH_MODELS="Qwen/Qwen3-Coder-30B-A3B-Instruct,Qwen/Qwen3-Coder-Next" \
  python3 bench/run_offline.py
```

Models prefixed `local:` run on CPU via `transformers` (downloaded from the 
Hugging Face Hub); all others go through the OpenAI-compatible endpoint at 
`BENCH_BASE_URL`. Cap local generation length with `BENCH_LOCAL_MAX_TOKENS`.

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
