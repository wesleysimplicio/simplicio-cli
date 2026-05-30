# Benchmark — simplicio-cli (offline harness)

Date: **2026-05-30**  
Models: `meta-llama/llama-3.2-3b-instruct`  
Cases: **1** across stacks: `angular`  
Base: `https://openrouter.ai/api/v1`

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract-state words). 
Same model on both sides — only the prompt structure changes. The 
*without* run is the raw one-line goal; the *with* run wraps the 
same goal in simplicio's 6-layer contract.

## Headline

- **Without simplicio:** 2/5 (40%)
- **With simplicio:** 4/5 (80%)
- **Delta:** **+40 points** (+100% relative)

![pass rate by model](charts/overall.svg)

![gain in points](charts/delta.svg)

## Per-model breakdown

| Model | Cases | Without | With | Delta (pts) | Relative gain |
|---|---|---|---|---|---|
| `meta-llama/llama-3.2-3b-instruct` | 1 | 2/5 (40%) | 4/5 (80%) | **+40** | +100% |

## Per-case (averaged across models)

![per case](charts/by_case.svg)

| # | Stack | Task | Without | With | Δ |
|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user is not an admin | 40% | 80% | **+40** |

## Per-stack

![per stack](charts/by_stack.svg)

| Stack | Without | With | Δ |
|---|---|---|---|
| `angular` | 40% | 80% | **+40** |

## Output-quality signals (rate across all runs)

Beyond pass-rate, the same outputs are scored on structural quality. 
Each row = % of runs (cases × models) where the signal is present.

| Signal | Without simplicio | With simplicio |
|---|---|---|
| DIFF block present | 0% (0/1) | 100% (1/1) |
| TEST block present | 100% (1/1) | 100% (1/1) |
| target file mentioned | 0% (0/1) | 100% (1/1) |
| avg criteria-keywords hit / run | 6.0 | 5.0 |
| avg output length (chars) | 2496 | 1989 |

## Cost — tokens & wall-clock (measured, per run)

Reported straight from the provider's `usage` field and `time.perf_counter()`. 
*Per-run* = one model call (one case, one side). With simplicio uses more input 
tokens (the 6-layer wrap) and fewer output tokens (model stops guessing earlier).

| Model | Side | Avg prompt tok | Avg completion tok | Avg total tok | Avg latency |
|---|---|---|---|---|---|
| `meta-llama/llama-3.2-3b-instruct` | without | 48 | 534 | 582 | 2232 ms |
| `meta-llama/llama-3.2-3b-instruct` | with    | 227 | 434 | 661 | 1758 ms |

**Aggregate over the full bench** (1 runs per side):

- without simplicio: 582 tokens total · 2.2s wall-clock · 582 tok/run · 2232 ms/run
- with simplicio:    661 tokens total · 1.8s wall-clock · 661 tok/run · 1758 ms/run
- token delta:       +79 (+13%)
- time delta:        -0.5s (-22%)

## How to reproduce

```bash
BENCH_BASE_URL="https://openrouter.ai/api/v1" \
  BENCH_API_KEY=… \
  BENCH_MODELS="meta-llama/llama-3.2-3b-instruct" \
  python3 bench/run_offline.py
```

Models prefixed `local:` run on CPU via `transformers` (downloaded from the 
Hugging Face Hub); all others go through the OpenAI-compatible endpoint at 
`BENCH_BASE_URL`. Cap local generation length with `BENCH_LOCAL_MAX_TOKENS`.

Raw model outputs are saved under `.simplicio/bench_runs/<model>/case_NN/{sem,com}.txt` 
so you can audit what the LLM actually produced on each side. Charts are 
SVG under `bench/charts/`; raw aggregated data under `bench/results.json`.
