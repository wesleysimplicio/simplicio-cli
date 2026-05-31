# Consolidated Benchmark Report (English summary) — simplicio-cli

> English companion to `bench/CONSOLIDATED_REPORT.md` (the full report is in pt-BR).
> Contains only: executive summary, master model table, and the preliminary
> default-model recommendation.
>
> **Honesty rule:** only numbers that appear in the source files are reported. Missing
> values are marked `n/d` (não disponível / not available). Nothing is estimated.
> Every figure cites its source file. Consolidation date: 2026-05-31.

---

## Executive summary

- **Headline uplift = +55pt.** On the 156-check suite with Qwen2.5-Coder-7B (Ollama), the full `cli+sp+ag` pipeline goes from **38% (base) to 93%**, a **+55pt** gain. Source: `bench/results_exec.md`.
- **Biggest single lever is `cli` (prompt engineering = precedent + skill_router): +33pt** on its own, beating `sp+ag` without cli (+26pt). The 93% ceiling only appears with everything combined. Source: `bench/results_4quadrant_full.md`.
- **Absolute measured ceiling = 96%** with `Qwen3-Coder-30B-A3B` (OpenRouter) at `cli+sp+ag`, 156-check. The coder variant beats the general one at the same size (96% vs 94%). Source: `bench/results_full_qwen3.md`.
- **Best local default (Ollama, no huge GPU) = Qwen2.5-Coder-7B at 93%** (`cli+sp+ag`, 156-check). Newer local alternative: Qwen3-8B at 88%. Sources: `bench/results_exec.md`, `bench/results_full_qwen3.md`, `bench/results_comparison.md`.
- **Coder-tuned > general at the same size.** Qwen2.5-Coder-3B (72%) beats Llama-3.2-3B (54%) at roughly equivalent size. Source: `bench/results_4quadrant_wide.md`.
- **Full-stack tasks (sindico suite) have a lower ceiling: 69%** (base 22% → `cli+sp+ag` 69%, +47pt) with the 7B. Multi-file tasks do not close on the 7B alone. Source: `bench/results_exec_sindico.md`.
- **Static-pass (sp) side effect is real but net-positive.** Fixes +13pt, breaks −2pt → net +11pt (v9); worsens 6% of tasks. v10 improves to +12pt net, 4% false positives. Sources: `bench/results_sp_v9.md`, `bench/results_sp_compare.md`.
- **The agent (ag) contributes more than the static-pass (sp).** Isolated over raw: `sp_only` +9pt vs `ag_only` +20pt. Sources: `bench/results_4quadrant_full.md`, `bench/results_exec.md`.
- **Running sp before ag cuts LLM calls ~29% and still raises quality (88%→91%).** Conditional escalation (sp→ag if <80%) reaches 86% at 1.4x cost vs 88% at 2.1x for ag-always. Sources: `bench/results_llm_reduction_summary.md`, `bench/results_sp_escalation_v1.md`.
- **"Honest production" number for the 7B = 76%** under the full release gate (static+live+lint+coverage≥80%) vs 93% static-only. Sources: `bench/results_scratch_release_gate.md`, `bench/results_scratch_live_gate.md`.
- **The 1.5B GGUF quantization curve (issue #46) is incomplete:** only Q5_K_M has **partial data (2/12 cases)**; Q8_0/Q6_K/Q4_K_M are **pending** (infra-blocked: no `llama_cpp`/`huggingface_hub`/GGUF file/credentials). No reliable GGUF pass-rate% exists. Sources: `bench/results_v14_qwen15b_gguf_partial.md`, `bench/RESULTS_LOCAL_GGUF.md`.

---

## Master model table

Best measured pass-rate per model (156-check Python, side `cli+sp+ag`, unless noted).
Models without a pass-rate run show their real state (smoke / Rust / partial / n/d).

| Model | size/quant | backend | best pass-rate seen | suite | source |
|---|---|---|---|---|---|
| Qwen2.5-Coder-1.5B | 1.5B | HF | 58% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |
| Qwen2.5-Coder-1.5B (GGUF) | 1.5B / Q5_K_M | GGUF local (llama_cpp) | partial 2/12 cases (cli+ag), **not a %** | 156-check (partial) | results_v14_qwen15b_gguf_partial / RESULTS_LOCAL_GGUF |
| Qwen2.5-Coder-3B | 3B | HF | 72% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |
| Qwen2.5-Coder-7B | 7B | Ollama | **93% (cli+sp+ag)** | 156-check | results_exec / results_4quadrant_full / results_comparison / results_v13_5side (92%) |
| Qwen2.5-Coder-32B | 32B | OpenRouter | 85% (Rust); 156-check **n/d** (smoke only) | rust-check | results_rust_qwen / results.md (smoke) |
| Qwen3-0.6B | 0.6B / fp16 | HF | 43% (cli+sp+ag) | 156-check | results_full_qwen3 |
| Qwen3-1.7B | 1.7B / fp16 | HF | 60% (cli+sp+ag) | 156-check | results_full_qwen3 |
| Qwen3-4B | 4B / fp16 | HF | 74% (cli+sp+ag) | 156-check | results_full_qwen3 / results_4side_qwen3 |
| Qwen3-8B | 8B / q4_K_M | Ollama | 88% (cli+sp+ag) | 156-check | results_full_qwen3 / results_4side_qwen3 / results_comparison |
| Qwen3-14B | 14B / q4_K_M | Ollama | 91% (cli+sp+ag) | 156-check | results_full_qwen3 / results_4side_qwen3 / results_comparison |
| Qwen3-30B-A3B | 30B MoE / q4_K_M | OpenRouter | 94% (cli+sp+ag) | 156-check | results_full_qwen3 / results_comparison |
| Qwen3-Coder-30B-A3B | 30B MoE / fp8 | OpenRouter | **96% (cli+sp+ag)** — absolute ceiling | 156-check | results_full_qwen3 / results_4side_qwen3 / results_comparison |
| Qwen3-Coder-30B-A3B (Rust) | 30B MoE / fp8 | OpenRouter | 88% | rust-check | results_rust_qwen |
| Llama-3.2-3B-Instruct | 3B | HF | 54% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |
| Gemma-3-4b-it | 4B | HF | 66% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |

> **DeepSeek**: no DeepSeek model appears anywhere in `bench/`. No data to report (n/d).
> The 7B's best is 93% (results_exec / 4quadrant_full / comparison / v14 interim); results_v13_5side records 92% on the same suite (seed/run variance). The same 7B drops on harder suites: sindico 69%, Rust 72%, full release gate 76%.

---

## Preliminary default-model recommendation

Based strictly on measured pass-rates (156-check, `cli+sp+ag`, unless noted).

- **Overall default (best absolute quality): `Qwen3-Coder-30B-A3B` (OpenRouter) — 96%.**
  Top of the whole dataset (`results_full_qwen3.md`, `results_4side_qwen3.md`, `results_comparison.md`); beats the general variant at the same size (96% vs 94%) and leads Rust too (88%, `results_rust_qwen.md`). Caveat: needs API/OpenRouter (no offline) and a key.

- **Recommended LOCAL/offline default: `Qwen2.5-Coder-7B` (Ollama) — 93%.**
  Best "runs locally without a huge GPU" model (`results_exec.md`, `results_comparison.md`), revalidated at 93% in v14 (`results_v14_interim.md`). For the newer generation, **`Qwen3-8B` (Ollama) — 88%** is the best local price/performance (`results_full_qwen3.md`); `Qwen3-14B` reaches 91% with more VRAM.

- **Minimal local default (weak hardware): `Qwen2.5-Coder-3B` (HF) — 72%.**
  Best of the small models with the full pipeline (`results_4quadrant_wide.md`); clearly beats similar-size general models (Llama-3.2-3B 54%, Gemma-3-4b 66%). Below that, Qwen2.5-Coder-1.5B only reaches 58%.

**Caveats for complex full-stack ("sindico") tasks:**
- The headline 93% is on the 156-check suite. On **sindico (full-stack) the same 7B is 69%** (`results_exec_sindico.md`) and does not close multi-file tasks alone.
- The 7B's **"honest production" number under the full release gate (static+live+lint+coverage≥80%) is 76%** (`results_scratch_release_gate.md`), not 93%.
- For sindico/Rust/strict production, prefer a larger model (32B Rust = 85%; Qwen3-Coder-30B-A3B = 96% on 156-check, 88% Rust) or more agent iterations.
- **Always run with `cli+sp+ag`**: the full stack is worth +47 to +55pt over raw, and running `sp` before `ag` still cuts ~29% of LLM calls (`results_llm_reduction_summary.md`). For cost-conscious production, use escalation v1 (conditional sp→ag): 86% at 1.4x cost (`results_sp_escalation_v1.md`).
