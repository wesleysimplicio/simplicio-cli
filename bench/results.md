# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-31**  
Models: `gguf:/root/models/Qwen2.5-Coder-1.5B-Instruct-Q6_K.gguf`  
Cases: **10** across stacks: `angular`, `dotnet`, `react`  
Base: `https://router.huggingface.co/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 17/52 (32%)
- **With simplicio:** 49/52 (94%)
- **Delta:** **+62 points** (+188% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `gguf:/root/models/Qwen2.5-Coder-1.5B-Instruct-Q6_K.gguf` | 10 | 17/52 (32%) | 49/52 (94%) | **+62** | +188% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 40% | 100% | **+60** |
| 2 | `angular` | Disable the email field unless the profile role is editor. | 40% | 80% | **+40** |
| 3 | `angular` | Only show the audit log link for users with role 'auditor'. | 20% | 100% | **+80** |
| 4 | `angular` | Show 'Approve' button only when the order status is 'pending | 33% | 100% | **+67** |
| 5 | `react` | Render the export menu item only for users in the 'analytics | 20% | 100% | **+80** |
| 6 | `react` | Disable the 'Save Draft' button while the form is invalid OR | 50% | 100% | **+50** |
| 7 | `react` | Show a 'No results' empty state when the search returns zero | 20% | 100% | **+80** |
| 8 | `dotnet` | Require the 'CanApprove' policy on the Approve endpoint of t | 40% | 80% | **+40** |
| 9 | `dotnet` | Restrict the GET /reports endpoint so only users in the Mana | 20% | 100% | **+80** |
| 10 | `angular` | Show a warning banner if the user has unsaved changes and tr | 40% | 80% | **+40** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 35% | 92% | **+58** |
| `dotnet` | 30% | 90% | **+60** |
| `react` | 31% | 100% | **+69** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/10) | 90% (9/10) |
| TEST block present | 30% (3/10) | 100% (10/10) |
| target file mentioned | 0% (0/10) | 100% (10/10) |
| avg criteria-keywords hit / run | 8.7 | 9.2 |
| avg output length (chars) | 1558 | 2150 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `gguf:/root/models/Qwen2.5-Coder-1.5B-Instruct-Q6_K.gguf` | without | 36 | 358 | 394 | 43282 ms |
| `gguf:/root/models/Qwen2.5-Coder-1.5B-Instruct-Q6_K.gguf` | with    | 220 | 492 | 712 | 62001 ms |

**Aggregate over the full bench** (10 runs per side):

- without simplicio: 3,946 tokens total · 432.8s wall-clock · 394 tok/run · 43282 ms/run
- with simplicio:    7,125 tokens total · 620.0s wall-clock · 712 tok/run · 62001 ms/run
- token delta:       +3,179 (+80%)
- time delta:        +187.2s (+43%)

## How to reproduce

```bash
BENCH_BASE_URL="https://router.huggingface.co/v1" \
  BENCH_API_KEY=… \
  BENCH_MODELS="gguf:/root/models/Qwen2.5-Coder-1.5B-Instruct-Q6_K.gguf" \
  python3 bench/run_offline.py
```

Models prefixed `local:` run on CPU via `transformers` (downloaded from the 
Hugging Face Hub); all others go through the OpenAI-compatible endpoint at 
`BENCH_BASE_URL`. Cap local generation length with `BENCH_LOCAL_MAX_TOKENS`.

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
