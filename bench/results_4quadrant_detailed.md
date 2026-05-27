# Benchmark 4-quadrant — DETALHADO (% real por-check)

Date: **2026-05-27**  
Models: `google/gemma-3-4b-it`, `meta-llama/llama-3.2-3b-instruct`, `qwen/qwen-2.5-7b-instruct`  
Cases: **5**, max_iters: **3**, base: `https://openrouter.ai/api/v1`

> **Por que dois números?** O harness padrão reporta *pass binário por caso*: um caso só conta como pass se **todos** os checks do contrato batem de uma vez. Isso joga o Q1 (raw) pra 0% mesmo quando o modelo acerta parte do contrato. A **% real por-check** conta cada check individualmente (igual ao bench principal `bench/results.md`, que mede 'a real %'). Use a % por-check pra ver o progresso verdadeiro; o binário por-caso pra ver quantos casos ficaram 100% prontos.

## Headline — % real por-check vs binário por-caso

| Quadrante | Prompt | Execução | **% real (por-check)** | checks | binário (por-caso) |
|---|---|---|---|---|---|
| **Q1** | raw | 1-shot | **33%** | 26/78 | 0/15 (0%) |
| **Q2** | simplicio | 1-shot | **89%** | 70/78 | 11/15 (73%) |
| **Q3** | raw | loop | **76%** | 60/78 | 7/15 (46%) |
| **Q4** | simplicio | loop | **91%** | 71/78 | 11/15 (73%) |

> **Prompt effect (% real)**: Q2 − Q1 = **+56 pts** (33% → 89% por-check). Mesmo o quadrante 'raw 1-shot' (Q1) acerta **33%** dos checks — não é 0%, esse era o efeito do all-or-nothing por caso.

## % real por-check, por modelo

| Model | Q1 | Q2 | Q3 | Q4 | Δ real (Q2−Q1) |
|---|---|---|---|---|---|
| `google/gemma-3-4b-it` | 34% (9/26) | 96% (25/26) | 65% (17/26) | 96% (25/26) | **+62 pts** |
| `meta-llama/llama-3.2-3b-instruct` | 26% (7/26) | 73% (19/26) | 65% (17/26) | 76% (20/26) | **+47 pts** |
| `qwen/qwen-2.5-7b-instruct` | 38% (10/26) | 100% (26/26) | 100% (26/26) | 100% (26/26) | **+62 pts** |

## Por caso — % real por-check (média entre os 3 modelos)

| # | Stack | Goal | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|---|---|
| 1 | `angular` | Hide the Delete button when the current user i | 40% | 93% | 93% | 86% |
| 2 | `angular` | Disable the email field unless the profile rol | 40% | 80% | 86% | 100% |
| 3 | `angular` | Only show the audit log link for users with ro | 20% | 80% | 53% | 80% |
| 4 | `angular` | Show 'Approve' button only when the order stat | 27% | 100% | 72% | 94% |
| 5 | `react` | Render the export menu item only for users in  | 40% | 93% | 80% | 93% |

## Quais checks do contrato cada quadrante satisfaz (por tipo de check, todos modelos × casos)

Cada caso tem 5 checks na ordem: `[target-file, DIFF-block, TEST-block, role-keyword, structural-guard]`.

| Check (posição) | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| 1 · target file | 0% (0/15) | 100% (15/15) | 80% (12/15) | 100% (15/15) |
| 2 · DIFF block | 0% (0/15) | 100% (15/15) | 73% (11/15) | 93% (14/15) |
| 3 · TEST block | 0% (0/15) | 80% (12/15) | 66% (10/15) | 80% (12/15) |
| 4 · role keyword | 93% (14/15) | 86% (13/15) | 93% (14/15) | 93% (14/15) |
| 5 · structural guard | 73% (11/15) | 80% (12/15) | 73% (11/15) | 86% (13/15) |

## Leitura

- **% real por-check**: Q1 **33%** → Q2 **89%** (+56 pts só com o prompt). Q4 **91%** é o teto.
- O salto do prompt vem sobretudo dos checks **estruturais** (DIFF block, TEST block, menção ao arquivo-alvo) — o que o contrato de 6 camadas exige explicitamente no [OUTPUT].
- `qwen-2.5-7b` satura em **100%** por-check em Q2/Q3/Q4; o ganho marginal do loop concentra-se em `gemma`/`llama`.

Fonte: `bench/results_4quadrant.json` (run de 2026-05-27, OpenRouter).