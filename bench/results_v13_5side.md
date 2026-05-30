# 5-side comparison — v13 (baseline / cli / cli+sp / cli+ag / cli+sp+ag)

Date: **2026-05-30**

Five sides on **two metrics** (functional/PHPUnit + regex), three models.

## Sides

| key | label | description |
|---|---|---|
| `sem`  | baseline       | raw one-line goal. No simplicio anywhere. |
| `com`  | cli alone      | the simplicio-cli 6-layer task contract (role/stack, goal, target, criteria, constraints, output shape). |
| `sp`   | cli + sp       | simplicio-prompt v1.9 runtime wrapping the cli 6-layer as user-input-X. Composition. |
| `ag`   | cli + ag       | cli 6-layer as the seed of the verify-loop (PHPUnit tail / missing-pattern feedback over up to 3 attempts). |
| `spag` | cli + sp + ag  | **full stack:** sp-wrapped cli as the verify-loop seed. Composition + retry. |

## Benches

| bench | n | oracle |
|---|---|---|
| exec   | 12 | real `vendor/bin/phpunit` on `wesleysimplicio/sistema-sindico` |
| regex  | 10 | structural pattern match per `bench/cases_offline.json` |

## Models

- `meta-llama/llama-3.2-3b-instruct` (n=1)

## Headline — pct per side, both metrics

| Model | metric | base | cli | cli+sp | cli+ag | cli+sp+ag | Δcli | Δsp | Δag | Δsp+ag |
|---|---|---|---|---|---|---|---|---|---|---|
| `llama-3.2-3b-instruct` | exec | 0% | 0% | 0% | 0% | 0% | **+0** | **+0** | **+0** | **+0** |
| `llama-3.2-3b-instruct` | regex | 40% | 80% | 80% | 80% | 80% | **+40** | **+40** | **+40** | **+40** |

## Verify-loop convergence (exec)

Average attempts consumed by the ag-based sides (1=passed first try; 3=ran loop to exhaustion).

| Model | cli+ag avg | cli+sp+ag avg |
|---|---|---|
| `llama-3.2-3b-instruct` | 2.00 | 2.00 |

## Cost & latency (exec, per call avg)

Tokens/call and ms/call averaged across the 12 cases. ag-based sides sum across attempts.

| Model | side | tokens/call | ms/call |
|---|---|---|---|
| `llama-3.2-3b-instruct` | baseline | 950 | 2310 |
| `llama-3.2-3b-instruct` | cli alone | 1029 | 1729 |
| `llama-3.2-3b-instruct` | cli + sp | 1688 | 780 |
| `llama-3.2-3b-instruct` | cli + ag | 1982 | 3710 |
| `llama-3.2-3b-instruct` | cli + sp + ag | 2225 | 2197 |

## Per-task × model (exec, base / cli / cli+sp / cli+ag / cli+sp+ag)

Format per cell: `b/c/s/a/sa` where each char is `P` (pass) or `.` (fail).

| Task | llama-3.2-3b-instruct |
|---|---|
| password_strength | ././././. |
