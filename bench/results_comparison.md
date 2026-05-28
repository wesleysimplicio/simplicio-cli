# Benchmark - old vs new (with & without simplicio-cli)

Date: **2026-05-28**  
Old = pass-rate published in the README. New = re-run on the latest version (Qwen2.5-Coder + HF-served models via the HF router; the rest via OpenRouter). Same 10 cases/side, deterministic regex checks (same methodology as the README tables). `n/a` rows mean the new run did not complete for that model in this session - the multi-batch re-run stalled mid-way (Kimi-K2.6 + a temporarily-disabled provider for Qwen2.5-7B burned the retry budget), so only the Qwen2.5-Coder triplet finished cleanly. Old numbers still stand; the new column is honest about what was actually re-measured this round.

## Local offline - qwen2.5-coder (was Ollama; now HF)

| Model | Without (old -> new) | With (old -> new) | D without | D with |
|---|---|---|---|---|
| **Qwen 2.5 Coder 7B** | 36% -> **38%** | 92% -> **96%** | +2 | +4 |
| **Qwen 2.5 Coder 3B** | 34% -> **34%** | 82% -> **94%** | +0 | +12 |
| **Qwen 2.5 Coder 1.5B** | 32% -> **30%** | 88% -> **92%** | -2 | +4 |

## Tiny models - sub-4B

| Model | Without (old -> new) | With (old -> new) | D without | D with |
|---|---|---|---|---|
| **Gemma 3 4B** | 38% -> n/a | 96% -> n/a | n/a | n/a |
| **Llama 3.2 3B** | 28% -> n/a | 73% -> n/a | n/a | n/a |
| **Gemma 3n e4B** | 44% -> n/a | 88% -> n/a | n/a | n/a |
| **Phi-4 mini** | 36% -> n/a | 73% -> n/a | n/a | n/a |
| **Llama 3.2 1B** | 26% -> n/a | 40% -> n/a | n/a | n/a |

## Frontier 2026 models

| Model | Without (old -> new) | With (old -> new) | D without | D with |
|---|---|---|---|---|
| **GPT-5.5** | 38% -> n/a | 100% -> n/a | n/a | n/a |
| **Kimi K2.6** | 40% -> n/a | 100% -> n/a | n/a | n/a |
| **Gemini 3.5 Flash** | 42% -> n/a | 100% -> n/a | n/a | n/a |
| **Qwen 3.7 Max** | 44% -> n/a | 100% -> n/a | n/a | n/a |
| **Claude Opus 4.7** | 42% -> n/a | 98% -> n/a | n/a | n/a |
| **DeepSeek V4 Pro** | 44% -> n/a | 96% -> n/a | n/a | n/a |

## Mid-tier 7B-12B open models

| Model | Without (old -> new) | With (old -> new) | D without | D with |
|---|---|---|---|---|
| **Gemma 3 12B** | 34% -> n/a | 92% -> n/a | n/a | n/a |
| **Llama 3.1 8B** | 36% -> n/a | 90% -> n/a | n/a | n/a |
| **Qwen 2.5 7B** | 34% -> n/a | 88% -> n/a | n/a | n/a |

## Overall (models with a new re-run)

| Side | Old avg | New avg | Delta |
|---|---|---|---|
| Without simplicio | 34% | 34% | +0 |
| With simplicio | 87% | 94% | +7 |

Models re-run: **3**. Merged new dataset: `bench/results_all.json`.
