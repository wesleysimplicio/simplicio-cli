# Relatório consolidado de benchmark — simplicio-cli

> Documento único que reúne todo o material de benchmark de `bench/`.
> **Regra de honestidade**: só aparecem aqui números que constam nos arquivos-fonte.
> Onde o valor não existe, está marcado `n/d` (não disponível). Cada tabela cita o
> arquivo de origem. Nada foi estimado ou extrapolado.
>
> Data de consolidação: 2026-05-31. Fontes completas no fim do arquivo (seção "Fontes").

---

## Sumário executivo

- **Uplift de capa = +55pt.** Na suíte 156-check com Qwen2.5-Coder-7B (Ollama), o pipeline completo `cli+sp+ag` sobe de **38% (base) para 93%**, ganho de **+55pt**. Fonte: `bench/results_exec.md`.
- **Maior alavanca isolada é o `cli` (prompt engineering = precedent + skill_router): +33pt** sozinho, superando `sp+ag` sem cli (+26pt). O teto (93%) só aparece com tudo combinado. Fonte: `bench/results_4quadrant_full.md`.
- **Teto absoluto medido = 96%** com `Qwen3-Coder-30B-A3B` (OpenRouter) em `cli+sp+ag`, na suíte 156-check. A variante coder bate a general no mesmo tamanho (96% vs 94% do Qwen3-30B-A3B). Fonte: `bench/results_full_qwen3.md`.
- **Melhor default rodável local (Ollama, sem GPU gigante) = Qwen2.5-Coder-7B a 93%** em `cli+sp+ag` (156-check). Alternativa local mais nova: Qwen3-8B a 88%. Fontes: `bench/results_exec.md`, `bench/results_full_qwen3.md`, `bench/results_comparison.md`.
- **Coder-tuned > general no mesmo tamanho.** Qwen2.5-Coder-3B (72%) supera Llama-3.2-3B (54%) com tamanho aproximado equivalente. Fonte: `bench/results_4quadrant_wide.md`.
- **Tarefas full-stack (suíte sindico) têm teto mais baixo: 69%** (base 22% → `cli+sp+ag` 69%, +47pt) com o 7B. Multi-arquivo não fecha sozinho no 7B; recomenda-se modelo maior ou mais iterações de agent. Fonte: `bench/results_exec_sindico.md`.
- **Efeito colateral do static-pass (sp) é real mas líquido positivo.** Conserta +13pt, quebra −2pt → líquido +11pt (v9); piora 6% das tasks. A versão v10 melhora para +12pt líquido e 4% de falsos positivos. Fontes: `bench/results_sp_v9.md`, `bench/results_sp_compare.md`.
- **O agent (ag) contribui mais que o static-pass (sp).** Isolados sobre o cru: `sp_only` +9pt vs `ag_only` +20pt. Sobre o cli: sp +8pt vs ag +17pt. Fontes: `bench/results_4quadrant_full.md`, `bench/results_exec.md`.
- **sp antes de ag reduz custo de LLM em ~29% e ainda sobe qualidade (88%→91%).** A política de escalonamento condicional (sp→ag se <80%) pega 86% a 1.4x de custo, contra 88% a 2.1x do ag-always. Fontes: `bench/results_llm_reduction_summary.md`, `bench/results_sp_escalation_v1.md`.
- **Número "honesto de produção" do 7B = 76%** sob o release gate completo (static+live+lint+coverage≥80%), contra 93% só estático. O live gate sozinho já derruba 93%→84%. Fontes: `bench/results_scratch_release_gate.md`, `bench/results_scratch_live_gate.md`.
- **Curva de quantização do 1.5B GGUF (issue #46) está incompleta:** só Q5_K_M tem dado **parcial (2/12 casos)**; Q8_0/Q6_K/Q4_K_M estão **pendentes** por infra (sem `llama_cpp`/`huggingface_hub`/arquivo GGUF/credenciais). Não há pass-rate% confiável para GGUF. Fontes: `bench/results_v14_qwen15b_gguf_partial.md`, `bench/RESULTS_LOCAL_GGUF.md`.

---

## Metodologia

O runner único (`bench/run_unified.py`) executa, para cada modelo e cada task, todos os
*sides* pedidos, gravando um JSON por execução e um agregado `.md`. Fontes desta seção:
`bench/SIMPLICIO_FLOW_GUIDE.md` e `bench/UNIFIED_RUN_ARCHITECTURE.md`.

### Sides (variações de pipeline)

| Side | Nome | O que injeta no LLM | Pós-processamento |
|---|---|---|---|
| `base` | Baseline | Prompt cru da task | Nenhum |
| `cli` | simplicio-cli | Prompt + precedent + skill_router | Nenhum |
| `cli+sp` | + static-pass | Prompt + precedent + skill_router | Static fixers (lint/format/imports) |
| `cli+ag` | + agent | Prompt + precedent + skill_router + agent loop | Agent revisa e corrige |
| `cli+sp+ag` | full | Tudo acima combinado | Static + agent |
| `sp_only` | só static-pass | Prompt cru | Static fixers |
| `ag_only` | só agent | Prompt cru | Agent loop |

### Componentes

- **precedent**: injeta exemplos canônicos (few-shot) por similaridade com a task.
- **skill_router**: detecta a categoria da task e injeta a skill certa (codegen, api, cli, etc.).
- **static-pass (sp)**: fixers determinísticos (ruff/black/isort equivalente), sem LLM.
- **agent (ag)**: loop de auto-revisão; o modelo relê o output, roda checagens e corrige.

### Suítes de avaliação

- **156-check suite**: bateria de 156 verificações estáticas/comportamentais (lint, imports, estrutura, naming, edge cases, error paths). É a suíte principal da maioria das rodadas.
- **suíte sindico**: cenário full-stack (app real de condomínio, multi-arquivo: backend + frontend + schema). Mede tarefas complexas.
- **suíte rust-check**: `cargo build` + `clippy` + `cargo test`, para geração de Rust.
- **gates incrementais** (família scratch): static → live (roda o código) → lint estrito → coverage ≥80% (release gate).

### Métrica

- **pass-rate** = checks aprovados / total de checks (0–100%).
- **uplift** = pass-rate(side) − pass-rate(base), em pontos percentuais (pt).
- Cada side roda **N vezes (default N=3)** e reporta **média + min/max**.
- **"min/case"** = pior caso observado entre as N execuções por tarefa.
- Determinismo: seeds fixas quando o backend suporta.

### Backends

| Backend | Como resolve | Exemplo |
|---|---|---|
| HF (transformers) | baixa peso do Hugging Face Hub | Qwen2.5-Coder-1.5B-Instruct |
| Ollama | daemon local `ollama serve` | qwen2.5-coder:7b |
| GGUF local | carrega `.gguf` via `llama_cpp` | qwen2.5-coder-1.5b-q5_k_m.gguf |
| OpenRouter | API remota (precisa key) | qwen/qwen-2.5-coder-32b-instruct |

---

## Resultados por bench

Uma subseção por arquivo de resultado. Tabelas copiadas fielmente da fonte.

### `bench/results.md` — smoke test de codegen (Qwen2.5-Coder)

**Mede:** geração básica funcional (parse / py_compile / pytest) das 4 tiers Qwen2.5-Coder em 3 tarefas (sum.py, api.py, cli_tool).

| Modelo | parse_ok | py_compile | pytest | nota |
|---|---|---|---|---|
| Qwen2.5-Coder-1.5B-Instruct (HF) — subtotal | 3/3 | 3/3 | 4/4 | aprovado |
| Qwen2.5-Coder-3B-Instruct (HF) — subtotal | 3/3 | 3/3 | 4/4 | aprovado |
| Qwen2.5-Coder-7B-Instruct (Ollama) — subtotal | 3/3 | 3/3 | 4/4 | aprovado |
| Qwen2.5-Coder-32B-Instruct (OpenRouter) — subtotal | 3/3 | 3/3 | 4/4 | aprovado |
| **TOTAL** | **12/12** | **12/12** | **16/16** | **aprovado** |

**Takeaway:** todas as 4 tiers (1.5B→32B) passam o smoke de codegen básico. É o piso; as suítes seguintes (156-check, sindico) é que medem pass-rate fino.

### `bench/results_exec.md` — uplift por side, 156-check (rodada de capa, +55pt)

**Mede:** os 5 sides na suíte 156-check com Qwen2.5-Coder-7B (Ollama), N=3. Origem do "+55pt".

| Side | pass-rate (média) | min/case | uplift vs base |
|---|---|---|---|
| base | 38% | 33% | — |
| cli | 71% | 66% | +33pt |
| cli+sp | 79% | 74% | +41pt |
| cli+ag | 88% | 82% | +50pt |
| cli+sp+ag | 93% | 88% | +55pt |

**Takeaway:** pipeline completo = +55pt sobre o cru; maior salto único é o `cli` (+33pt); sp+ag não é aditivo perfeito (teto 93%).

### `bench/results_exec_sindico.md` — suíte sindico (full-stack)

**Mede:** cenário full-stack multi-arquivo (backend+frontend+schema) com Qwen2.5-Coder-7B, N=3.

| Side | pass-rate (média) | min/case | uplift vs base |
|---|---|---|---|
| base | 22% | 18% | — |
| cli | 44% | 39% | +22pt |
| cli+sp | 51% | 46% | +29pt |
| cli+ag | 63% | 58% | +41pt |
| cli+sp+ag | 69% | 61% | +47pt |

**Takeaway:** teto mais baixo (69%) em tarefas complexas; uplift ainda forte (+47pt). 7B não fecha sozinho full-stack — sugere-se 32B ou mais iterações de agent.

### `bench/results_v13_5side.md` — v13, 5 sides (final)

**Mede:** os 5 sides na 156-check, pipeline v13, Qwen2.5-Coder-7B, N=3. Rodada final do v13.

| Side | pass-rate | min/case | uplift |
|---|---|---|---|
| base | 39% | 34% | — |
| cli | 70% | 64% | +31pt |
| cli+sp | 78% | 72% | +39pt |
| cli+ag | 87% | 81% | +48pt |
| cli+sp+ag | 92% | 86% | +53pt |

**Takeaway:** consistente com `results_exec` dentro da variância de seed (+53pt aqui vs +55pt lá). Base ~39%, teto ~92%.

### `bench/results_v13_interim.md` — v13 interim (parcial, superado)

**Mede:** snapshot interino do v13, N=2 (parcial). Substituído por `results_v13_5side.md`.

| Side | pass-rate (parcial) | status |
|---|---|---|
| base | 39% | completo |
| cli | 70% | completo |
| cli+sp | 78% | completo |
| cli+ag | 86% | parcial (1 task pendente) |
| cli+sp+ag | 91% | parcial |

**Takeaway:** apenas referência de progresso (N=2); usar a versão final `results_v13_5side.md`.

### `bench/results_4quadrant_full.md` — isolando sp e ag (7B)

**Mede:** quadrantes base / sp_only / ag_only / sp+ag (sem cli) vs cli vs full. Qwen2.5-Coder-7B, 156-check, N=3.

| Quadrante | pass-rate | uplift vs base |
|---|---|---|
| base | 38% | — |
| sp_only | 47% | +9pt |
| ag_only | 58% | +20pt |
| sp+ag (no cli) | 64% | +26pt |
| cli | 71% | +33pt |
| cli+sp+ag | 93% | +55pt |

**Takeaway:** `cli` sozinho (+33pt) supera `sp+ag` sem cli (+26pt) — prompt engineering é a maior alavanca; ag contribui mais que sp; teto só com tudo combinado.

### `bench/results_4quadrant_wide.md` — multi-modelo (base / cli / full)

**Mede:** mesmo desenho 4-quadrant varrendo vários modelos. 156-check, N=3.

| Modelo | base | cli | cli+sp+ag | uplift |
|---|---|---|---|---|
| Qwen2.5-Coder-1.5B | 19% | 41% | 58% | +39pt |
| Qwen2.5-Coder-3B | 28% | 55% | 72% | +44pt |
| Qwen2.5-Coder-7B | 38% | 71% | 93% | +55pt |
| Llama-3.2-3B-Instruct | 17% | 38% | 54% | +37pt |
| Gemma-3-4b-it | 24% | 49% | 66% | +42pt |

**Takeaway:** uplift consistente entre modelos (+37 a +55pt); coder-tuned > general no mesmo tamanho (Qwen-Coder-3B 72% vs Llama-3.2-3B 54%); modelos pequenos/não-coder ficam abaixo mesmo com pipeline completo.

### `bench/results_full_qwen3.md` — família Qwen3 (156-check)

**Mede:** varredura Qwen3 (general e coder) na 156-check, N=3. HF ≤4B, Ollama 8B+, OpenRouter 30B+.

| Modelo | size/quant | backend | base | cli | cli+sp+ag | uplift |
|---|---|---|---|---|---|---|
| Qwen3-0.6B | 0.6B / fp16 | HF | 12% | 29% | 43% | +31pt |
| Qwen3-1.7B | 1.7B / fp16 | HF | 21% | 44% | 60% | +39pt |
| Qwen3-4B | 4B / fp16 | HF | 31% | 58% | 74% | +43pt |
| Qwen3-8B | 8B / q4_K_M | Ollama | 40% | 69% | 88% | +48pt |
| Qwen3-14B | 14B / q4_K_M | Ollama | 45% | 74% | 91% | +46pt |
| Qwen3-30B-A3B | 30B MoE / q4_K_M | OpenRouter | 49% | 78% | 94% | +45pt |
| Qwen3-Coder-30B-A3B | 30B MoE / fp8 | OpenRouter | 54% | 83% | **96%** | +42pt |

**Takeaway:** Qwen3-Coder-30B-A3B é o teto absoluto (96%); coder bate general no mesmo tamanho (96% vs 94%); Qwen3-8B (88%) é o melhor custo/benefício local; escala monotônica com o tamanho.

### `bench/results_4side_qwen3.md` — Qwen3 detalhado (intermediários)

**Mede:** os 4 sides (+ teto) para Qwen3 selecionados, detalhando cli+sp e cli+ag. 156-check, N=3.

| Modelo | base | cli | cli+sp | cli+ag | cli+sp+ag |
|---|---|---|---|---|---|
| Qwen3-4B | 31% | 58% | 65% | 70% | 74% |
| Qwen3-8B | 40% | 69% | 76% | 83% | 88% |
| Qwen3-14B | 45% | 74% | 80% | 87% | 91% |
| Qwen3-Coder-30B-A3B | 54% | 83% | 88% | 93% | 96% |

**Takeaway:** padrão consistente cli+ag > cli+sp (agent > static) em todos; incremento por etapa ~5-7pt. Detalha o que `results_full_qwen3` condensa.

### `bench/results_comparison.md` — snapshot consolidado (teto por modelo)

**Mede:** snapshot lado a lado dos modelos no teto (cli+sp+ag), 156-check, com a fonte de cada número.

| Modelo | backend | cli+sp+ag pass-rate | fonte |
|---|---|---|---|
| Qwen2.5-Coder-1.5B | HF | 58% | results_4quadrant_wide |
| Qwen2.5-Coder-3B | HF | 72% | results_4quadrant_wide |
| Qwen2.5-Coder-7B | Ollama | 93% | results_exec |
| Qwen3-8B | Ollama | 88% | results_full_qwen3 |
| Qwen3-14B | Ollama | 91% | results_full_qwen3 |
| Qwen3-Coder-30B-A3B | OpenRouter | 96% | results_full_qwen3 |
| Llama-3.2-3B | HF | 54% | results_4quadrant_wide |
| Gemma-3-4b | HF | 66% | results_4quadrant_wide |
| Qwen3-30B-A3B | OpenRouter | 94% | results_full_qwen3 |

**Takeaway:** leitura rápida; 7B (93%) é o melhor local sem GPU enorme; Qwen3-Coder-30B-A3B (96%) é o teto, mas exige API/OpenRouter.

### `bench/results_rust_qwen.md` — Rust codegen (suíte rust-check)

**Mede:** geração de Rust (cargo build + clippy + cargo test), N=3, modelos coder Qwen. pass-rate = média ponderada de build/clippy/test.

| Modelo | backend | cargo build | clippy | cargo test | pass-rate |
|---|---|---|---|---|---|
| Qwen2.5-Coder-7B | Ollama | 82% | 71% | 64% | 72% |
| Qwen2.5-Coder-32B | OpenRouter | 91% | 84% | 79% | 85% |
| Qwen3-Coder-30B-A3B | OpenRouter | 94% | 88% | 83% | 88% |

**Takeaway:** Rust é mais difícil que Python (~10-15pt abaixo); 7B em 72% (gargalo: cargo test 64%); borrow checker exige modelo maior (32B e 30B-A3B passam de 85%). É a única rodada com pass-rate% para o Qwen2.5-Coder-32B.

### `bench/results_sp_v9.md` — static-pass v9 (efeitos colaterais)

**Mede:** o que o sp v9 conserta e o que quebra. Qwen2.5-Coder-7B, 156-check, N=3.

| Métrica | valor |
|---|---|
| checks consertados por sp | +13pt (média) |
| checks quebrados por sp | −2pt (média) |
| ganho líquido sp | +11pt |
| arquivos tocados | 0.8 por task |
| falsos positivos (sp piorou) | 6% das tasks |

**Takeaway:** o sp tem efeito colateral (piora 6% das tasks, −2pt), mas o ganho líquido (+11pt) justifica mantê-lo por padrão. Falsos positivos vêm de reformatação agressiva de imports.

### `bench/results_sp_compare.md` — sp v8 vs v9 vs v10

**Mede:** comparação de versões do static-pass na mesma suíte. Qwen2.5-Coder-7B, N=3.

| Versão sp | ganho líquido | falsos positivos | arquivos tocados |
|---|---|---|---|
| sp v8 | +9pt | 9% | 1.1 |
| sp v9 | +11pt | 6% | 0.8 |
| sp v10 | +12pt | 4% | 0.7 |

**Takeaway:** cada versão melhora o ganho líquido e reduz falsos positivos; **v10 é o recomendado** (+12pt, 4% FP); fixers mais conservadores → menos efeito colateral.

### `bench/results_sp_schema_validation.md` — schema fixer

**Mede:** o fixer de validação de schema (Pydantic/JSON-schema) no subconjunto de tasks com schema. Qwen2.5-Coder-7B, N=3.

| Métrica | sem fixer | com fixer |
|---|---|---|
| schema válido | 61% | 89% |
| campos faltando | 24% | 7% |
| tipos errados | 15% | 4% |

**Takeaway:** o schema fixer sobe validação 61%→89% (+28pt) onde há schema; é no-op fora desse subconjunto.

### `bench/results_sp_escalation_v1.md` — política de escalonamento

**Mede:** quando o sp falha, escala pro agent. Qwen2.5-Coder-7B, 156-check, N=3.

| Estratégia | pass-rate | custo LLM (rel.) |
|---|---|---|
| sp only | 79% | 1.0x |
| sp → escala ag se <80% | 86% | 1.4x |
| ag always | 88% | 2.1x |

**Takeaway:** escalonar condicionalmente pega 86% (quase o ag-always 88%) a 1.4x de custo (vs 2.1x) — economiza ~33% de chamadas perdendo só 2pt. É a política recomendada custo-consciente.

### `bench/results_llm_reduction_summary.md` — redução de chamadas LLM

**Mede:** quanto o sp economiza em chamadas de LLM ao evitar idas ao agent. Qwen2.5-Coder-7B, 156-check, N=3. Resumo executivo da família sp.

| Configuração | pass-rate | chamadas LLM/task | redução |
|---|---|---|---|
| ag always (sem sp) | 88% | 2.1 | — |
| sp + ag (sp primeiro) | 91% | 1.5 | −29% |
| sp + escala condicional | 86% | 1.4 | −33% |

**Takeaway:** rodar sp antes do ag reduz 29% das chamadas E sobe pass-rate (88→91%); a combinação sp+ag domina ag-sozinho em custo e qualidade.

### `bench/results_static_fixers.md` — breakdown por fixer

**Mede:** contribuição individual de cada fixer determinístico do sp. Qwen2.5-Coder-7B, 156-check, N=3.

| Fixer | checks consertados | quebras | ganho líquido |
|---|---|---|---|
| import sorter | +4pt | −1pt | +3pt |
| formatter (black-like) | +3pt | 0pt | +3pt |
| lint autofix (ruff-like) | +5pt | −1pt | +4pt |
| unused remover | +2pt | 0pt | +2pt |
| schema filler | +3pt | 0pt | +3pt |
| **total sp** | **+17pt** | **−2pt** | **+15pt** |

**Takeaway:** lint autofix é o fixer mais valioso (+4pt líquido); import sorter é o único com quebra relevante; total líquido +15pt (consistente com sp v10).

### `bench/results_scratch_codegen.md` — valor do precedent

**Mede:** geração from-scratch (sem precedent) vs com precedent. Isola o precedent. Qwen2.5-Coder-7B, 156-check, N=3.

| Configuração | pass-rate | uplift |
|---|---|---|
| scratch (sem precedent) | 52% | — |
| + precedent | 68% | +16pt |
| + precedent + skill_router | 71% | +19pt |

**Takeaway:** precedent (few-shot canônico) vale +16pt sozinho; skill_router adiciona +3pt; juntos formam o "cli". (Aqui "scratch" já tem o scaffold do cli sem precedent, então difere do "base" cru do exec.)

### `bench/results_scratch_recipes.md` — recipes (templates de task)

**Mede:** efeito das recipes (templates estruturados) na qualidade. Qwen2.5-Coder-7B, N=3.

| Configuração | pass-rate | uplift |
|---|---|---|
| sem recipe | 71% | — |
| + recipe genérica | 76% | +5pt |
| + recipe específica | 82% | +11pt |

**Takeaway:** recipe específica da categoria vale +11pt; alimentam o skill_router — quanto mais específica, melhor.

### `bench/results_scratch_live_gate.md` — live gate (execução real)

**Mede:** o "live gate" (roda o código gerado, não só checks estáticos). Qwen2.5-Coder-7B, N=3.

| Gate | pass-rate |
|---|---|
| static checks only | 93% |
| + live gate (roda o código) | 84% |
| + live gate + retry (1x) | 89% |

**Takeaway:** rodar o código de verdade derruba 93%→84% (alguns passam estático mas falham em runtime); 1 retry recupera +5pt. Live gate é mais honesto; recomendado para release.

### `bench/results_scratch_release_gate.md` — release gate (o mais rígido)

**Mede:** gate cumulativo static + live + lint estrito + coverage ≥80%. Qwen2.5-Coder-7B, N=3.

| Gate cumulativo | pass-rate |
|---|---|
| static | 93% |
| + live | 84% |
| + lint estrito | 81% |
| + coverage ≥ 80% | 76% |

**Takeaway:** o release gate completo fica em **76%** para o 7B — é o número "honesto de produção"; coverage é o filtro final (−5pt). Usar para decisão de merge.

### `bench/results_v14_interim.md` — v14 interim (GGUF em andamento)

**Mede:** snapshot interino do v14: revalidação do 7B + início da varredura GGUF local do 1.5B (issue #46). 156-check.

| Item | status | pass-rate |
|---|---|---|
| 7B Ollama (revalidação v14) | completo | 93% |
| 1.5B GGUF Q5_K_M | parcial | ver `results_v14_qwen15b_gguf_partial` |
| 1.5B GGUF Q8_0 | pendente | n/d |
| 1.5B GGUF Q6_K | pendente | n/d |
| 1.5B GGUF Q4_K_M | pendente | n/d |

**Takeaway:** 7B revalidado em 93% (consistente com v13); a varredura GGUF do 1.5B só tem Q5_K_M parcial, o resto pendente por infra.

### `bench/results_v14_qwen15b_gguf_partial.md` — GGUF 1.5B parcial (issue #46)

**Mede:** rodada parcial do 1.5B em GGUF local (`llama_cpp`). Só Q5_K_M tem dado. Valores são **contagem de casos (x/12), não taxa%**.

| Quant | parse_ok | cli+ag pass | min/case | status |
|---|---|---|---|---|
| Q5_K_M | 2/12 | 2/12 | 0/12 | parcial (infra) |
| Q8_0 | n/d | n/d | n/d | pendente |
| Q6_K | n/d | n/d | n/d | pendente |
| Q4_K_M | n/d | n/d | n/d | pendente |

**Takeaway:** só 2 de 12 casos rodaram para Q5_K_M; não é representativo (smoke parcial). Resto pendente por falta de `llama_cpp`/`huggingface_hub`/arquivo GGUF/credenciais (issue #46). Não extrapolar.

### `bench/RESULTS_LOCAL_GGUF.md` — resumo GGUF local (issue #46)

**Mede:** estado da varredura GGUF local (espelho de leitura rápida do parcial acima).

| Quant | status | parse_ok | cli+ag pass | nota |
|---|---|---|---|---|
| Q5_K_M | parcial | 2/12 | 2/12 | só 2 casos rodaram (infra) |
| Q8_0 | pendente | n/d | n/d | falta llama_cpp/hub/cred |
| Q6_K | pendente | n/d | n/d | falta llama_cpp/hub/cred |
| Q4_K_M | pendente | n/d | n/d | falta llama_cpp/hub/cred |

**Takeaway:** não há pass-rate% confiável para GGUF (2/12 é contagem, não taxa). Espelha `results_v14_qwen15b_gguf_partial`.

---

## Modelos testados — visão consolidada

Tabela master cruzando todas as rodadas. **"melhor pass-rate visto"** = maior pass-rate
medido para aquele modelo na suíte indicada (156-check Python, salvo nota). Para modelos
sem rodada de pass-rate, o estado real está marcado (smoke / Rust / parcial / n/d).

| Modelo | size/quant | backend | melhor pass-rate visto | suíte | fonte |
|---|---|---|---|---|---|
| Qwen2.5-Coder-1.5B | 1.5B (HF) | HF | 58% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |
| Qwen2.5-Coder-1.5B (GGUF) | 1.5B / Q5_K_M | GGUF local (llama_cpp) | parcial 2/12 casos (cli+ag), **não é %** | 156-check (parcial) | results_v14_qwen15b_gguf_partial / RESULTS_LOCAL_GGUF |
| Qwen2.5-Coder-3B | 3B | HF | 72% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |
| Qwen2.5-Coder-7B | 7B | Ollama | **93% (cli+sp+ag)** | 156-check | results_exec / results_4quadrant_full / results_comparison / results_v13_5side (92%) |
| Qwen2.5-Coder-32B | 32B | OpenRouter | 85% (Rust); 156-check **n/d** (só smoke) | rust-check | results_rust_qwen / results.md (smoke) |
| Qwen3-0.6B | 0.6B / fp16 | HF | 43% (cli+sp+ag) | 156-check | results_full_qwen3 |
| Qwen3-1.7B | 1.7B / fp16 | HF | 60% (cli+sp+ag) | 156-check | results_full_qwen3 |
| Qwen3-4B | 4B / fp16 | HF | 74% (cli+sp+ag) | 156-check | results_full_qwen3 / results_4side_qwen3 |
| Qwen3-8B | 8B / q4_K_M | Ollama | 88% (cli+sp+ag) | 156-check | results_full_qwen3 / results_4side_qwen3 / results_comparison |
| Qwen3-14B | 14B / q4_K_M | Ollama | 91% (cli+sp+ag) | 156-check | results_full_qwen3 / results_4side_qwen3 / results_comparison |
| Qwen3-30B-A3B | 30B MoE / q4_K_M | OpenRouter | 94% (cli+sp+ag) | 156-check | results_full_qwen3 / results_comparison |
| Qwen3-Coder-30B-A3B | 30B MoE / fp8 | OpenRouter | **96% (cli+sp+ag)** — teto absoluto | 156-check | results_full_qwen3 / results_4side_qwen3 / results_comparison |
| Qwen3-Coder-30B-A3B (Rust) | 30B MoE / fp8 | OpenRouter | 88% | rust-check | results_rust_qwen |
| Llama-3.2-3B-Instruct | 3B | HF | 54% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |
| Gemma-3-4b-it | 4B | HF | 66% (cli+sp+ag) | 156-check | results_4quadrant_wide / results_comparison |

> **DeepSeek**: nenhum modelo DeepSeek aparece em qualquer arquivo de `bench/`. Não há dado para reportar (n/d).
>
> Nota sobre o 7B: o melhor pass-rate visto é 93% (results_exec, 4quadrant_full, comparison, v14 interim); `results_v13_5side` registra 92% na mesma suíte (variância de seed/run). Em suítes mais rígidas o mesmo 7B cai: sindico 69%, Rust 72%, release gate completo 76%.

---

## Curva de quantização Qwen2.5-Coder-1.5B (issue #46)

Único ponto de dado **real** que existe na curva de quantização do 1.5B em GGUF local.
Fontes: `bench/results_v14_qwen15b_gguf_partial.md`, `bench/RESULTS_LOCAL_GGUF.md`,
`bench/results_v14_qwen15b_gguf_partial.json`.

| Quant | parse_ok | cli+ag pass | min/case | status |
|---|---|---|---|---|
| Q5_K_M | 2/12 | 2/12 | 0/12 | **parcial** (só 2 de 12 casos rodaram) |
| Q8_0 | n/d | n/d | n/d | **pendente** |
| Q6_K | n/d | n/d | n/d | **pendente** |
| Q4_K_M | n/d | n/d | n/d | **pendente** |

- **Os valores de Q5_K_M são contagem de casos (x/12), NÃO pass-rate%.** 2/12 é um smoke parcial e **não deve ser extrapolado**.
- **Q8_0, Q6_K e Q4_K_M NÃO foram rodados.** Estão bloqueados por infra: o ambiente não tem `llama_cpp`, `huggingface_hub`, o arquivo `.gguf`, nem credenciais (conforme comentário da issue #46). Linhas mantidas como **pendente**.
- Não há nenhum pass-rate% confiável para nenhuma quantização GGUF do 1.5B neste momento.
- Próximo passo registrado nas fontes: rodar a curva completa quando a infra permitir.

---

## Lacunas e pendências

- **Curva de quantização GGUF do 1.5B incompleta** — só Q5_K_M parcial (2/12 casos); Q8_0/Q6_K/Q4_K_M pendentes por infra (issue #46). Sem `llama_cpp`/`huggingface_hub`/GGUF/credenciais. Fontes: `results_v14_qwen15b_gguf_partial.md`, `RESULTS_LOCAL_GGUF.md`, `results_v14_interim.md`.
- **Qwen2.5-Coder-32B sem 156-check** — só tem smoke (`results.md`) e Rust 85% (`results_rust_qwen.md`). O pass-rate na suíte 156-check principal é **n/d**, então o teto real do 32B em Python não foi medido.
- **sindico medido só no 7B** — a suíte full-stack só tem dado para Qwen2.5-Coder-7B (69%). Não há sindico para 3B, 32B, nem família Qwen3, apesar de a recomendação ser "usar modelo maior para sindico".
- **Rust restrito a 3 modelos** — só 7B, 32B e Qwen3-Coder-30B-A3B têm rust-check. Sem Rust para 1.5B/3B/Qwen3 menores.
- **Família Qwen3 sem live/release gate e sem Rust (exceto 30B)** — os gates incrementais (live/release) e o sindico só existem para o 7B.
- **v13_interim e v14_interim são parciais** (N=2 / em andamento); servem só de progresso, superados pelas versões finais.
- **Sem artefatos visuais versionados** — não há `.svg`/`.pdf`/`.html`/`.png` rastreados no repo, embora `UNIFIED_RUN_ARCHITECTURE.md` e os scripts `consolidate_*.py` mencionem geração de SVG/PDF "quando gerados". Os gráficos não estão no git.
- **Variância de seed não detalhada por modelo** — só o 7B tem min/case reportado em várias rodadas; para os demais modelos só há a média no teto.
- **"base" vs "scratch" têm definições diferentes** entre famílias (o "scratch" da família scratch já inclui scaffold do cli sem precedent), o que impede comparar os uplifts entre famílias de forma 1:1.

---

## Recomendação preliminar de modelo default

Baseada **estritamente** nos pass-rates medidos (suíte 156-check, side `cli+sp+ag`, salvo nota).

- **Default geral (melhor qualidade absoluta): `Qwen3-Coder-30B-A3B` (OpenRouter) — 96%.**
  É o teto medido em toda a base (`results_full_qwen3.md`, `results_4side_qwen3.md`, `results_comparison.md`), bate a variante general no mesmo tamanho (96% vs 94%) e lidera também em Rust (88%, `results_rust_qwen.md`). Caveat: precisa de API/OpenRouter (não roda offline) e key.

- **Default LOCAL/offline recomendado: `Qwen2.5-Coder-7B` (Ollama) — 93%.**
  É o melhor "rodável local sem GPU gigante" (`results_exec.md`, `results_comparison.md`), revalidado em 93% no v14 (`results_v14_interim.md`). Roda via Ollama sem API externa. Para quem prefere a geração mais nova, **`Qwen3-8B` (Ollama) — 88%** é a melhor alternativa local de custo/benefício (`results_full_qwen3.md`); `Qwen3-14B` sobe para 91% se houver mais VRAM.

- **Default local mínimo (hardware fraco): `Qwen2.5-Coder-3B` (HF) — 72%.**
  Melhor entre os pequenos com pipeline completo (`results_4quadrant_wide.md`); supera claramente alternativas general de tamanho parecido (Llama-3.2-3B 54%, Gemma-3-4b 66%). Abaixo disso, Qwen2.5-Coder-1.5B só atinge 58% — aceitável para tarefas triviais, frágil para o resto.

**Caveats importantes para tarefas full-stack complexas (sindico):**
- O número de capa (93%) é da suíte 156-check. Em **sindico (full-stack), o mesmo 7B fica em 69%** (`results_exec_sindico.md`) e não fecha sozinho tarefas multi-arquivo.
- O número **"honesto de produção" do 7B sob release gate completo (static+live+lint+coverage≥80%) é 76%** (`results_scratch_release_gate.md`), não 93%.
- Para sindico/Rust/produção rigorosa, preferir modelo maior (32B em Rust = 85%; Qwen3-Coder-30B-A3B = 96% em 156-check e 88% em Rust) ou mais iterações de agent.
- **Sempre rodar com `cli+sp+ag`**: a pilha completa vale +47 a +55pt sobre o cru, e `sp` antes de `ag` ainda reduz ~29% das chamadas de LLM (`results_llm_reduction_summary.md`). Em produção custo-consciente, usar a escalation v1 (sp→ag condicional): 86% a 1.4x de custo (`results_sp_escalation_v1.md`).

---

## Índice de artefatos

Todos os artefatos rastreados em `bench/` (via `git ls-files`), agrupados por família.
**Observação:** não há `.pdf`/`.html`/`.svg`/`.png` versionados no repositório — apenas `.md`, `.json` e `.py`.

### Documentação de metodologia
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/SIMPLICIO_FLOW_GUIDE.md` | md | O que roda em cada side; componentes; métrica |
| `bench/UNIFIED_RUN_ARCHITECTURE.md` | md | Pipeline do runner único; backends; saídas |

### Smoke / inicial
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results.md` | md | Smoke codegen Qwen2.5-Coder 1.5B→32B (12/12, 16/16) |

### exec / sides principais (156-check + sindico)
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_exec.md` | md | 5 sides 7B, +55pt (rodada de capa) |
| `bench/results_exec_sindico.md` | md | Suíte sindico full-stack, +47pt (teto 69%) |

### v13 / v14 (pipeline)
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_v13_5side.md` | md | v13 final, 5 sides, +53pt |
| `bench/results_v13_interim.md` | md | v13 parcial (N=2, superado) |
| `bench/results_v14_interim.md` | md | v14 interim (7B 93% + início GGUF) |

### 4-quadrant (isolamento sp/ag e multi-modelo)
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_4quadrant_full.md` | md | Quadrantes sp/ag isolados (7B) |
| `bench/results_4quadrant_wide.md` | md | base/cli/full multi-modelo |

### Família Qwen3
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_full_qwen3.md` | md | Qwen3 0.6B→30B (teto 96%) |
| `bench/results_4side_qwen3.md` | md | Qwen3 detalhado (intermediários) |

### Comparação / snapshot
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_comparison.md` | md | Snapshot teto por modelo, com fontes |

### Rust
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_rust_qwen.md` | md | Rust codegen (7B 72%, 32B 85%, 30B-A3B 88%) |

### Família static-pass (sp)
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_sp_v9.md` | md | sp v9 efeitos colaterais (+11pt líquido) |
| `bench/results_sp_compare.md` | md | sp v8/v9/v10 |
| `bench/results_sp_schema_validation.md` | md | schema fixer (61%→89%) |
| `bench/results_sp_escalation_v1.md` | md | escalonamento sp→ag |
| `bench/results_static_fixers.md` | md | breakdown por fixer (+15pt líquido) |
| `bench/results_llm_reduction_summary.md` | md | redução de chamadas LLM (−29%) |

### Família scratch (precedent / gates)
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_scratch_codegen.md` | md | valor do precedent (+16pt) |
| `bench/results_scratch_recipes.md` | md | recipes (+11pt) |
| `bench/results_scratch_live_gate.md` | md | live gate (93%→84%) |
| `bench/results_scratch_release_gate.md` | md | release gate (76%) |

### GGUF local (issue #46)
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/results_v14_qwen15b_gguf_partial.md` | md | 1.5B GGUF Q5_K_M parcial (2/12) |
| `bench/results_v14_qwen15b_gguf_partial.json` | json | Mesmo dado em JSON (issue 46, pending quants, infra blockers) |
| `bench/RESULTS_LOCAL_GGUF.md` | md | Resumo GGUF (espelho do parcial) |

### Scripts de consolidação
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/consolidate_full_report.py` | py | Gera relatório master + SVG (ordem de modelos/sides) |
| `bench/consolidate_v13_report.py` | py | Consolida rodada v13 (5 sides) |
| `bench/consolidate_4side_report.py` | py | Consolida 4-side Qwen3 |

### Este documento
| Arquivo | Tipo | Conteúdo |
|---|---|---|
| `bench/CONSOLIDATED_REPORT.md` | md | Este relatório consolidado (pt-BR) |
| `bench/CONSOLIDATED_REPORT.en.md` | md | Companion em inglês (sumário + tabela master + recomendação) |

---

## Fontes

Arquivos lidos para produzir este relatório (todos em `/home/user/simplicio-dev-cli`):

- `README.md` (seção "Benchmarks", linhas ~34-75)
- `CHANGELOG.md` (topo, ~120 linhas)
- `bench/SIMPLICIO_FLOW_GUIDE.md`
- `bench/UNIFIED_RUN_ARCHITECTURE.md`
- `bench/results.md`
- `bench/results_exec.md`
- `bench/results_exec_sindico.md`
- `bench/results_v13_5side.md`
- `bench/results_v13_interim.md`
- `bench/results_v14_interim.md`
- `bench/results_4quadrant_full.md`
- `bench/results_4quadrant_wide.md`
- `bench/results_full_qwen3.md`
- `bench/results_4side_qwen3.md`
- `bench/results_comparison.md`
- `bench/results_rust_qwen.md`
- `bench/results_sp_v9.md`
- `bench/results_sp_compare.md`
- `bench/results_sp_schema_validation.md`
- `bench/results_sp_escalation_v1.md`
- `bench/results_static_fixers.md`
- `bench/results_llm_reduction_summary.md`
- `bench/results_scratch_codegen.md`
- `bench/results_scratch_recipes.md`
- `bench/results_scratch_live_gate.md`
- `bench/results_scratch_release_gate.md`
- `bench/results_v14_qwen15b_gguf_partial.md`
- `bench/results_v14_qwen15b_gguf_partial.json`
- `bench/RESULTS_LOCAL_GGUF.md`
- `bench/consolidate_full_report.py`
- `bench/consolidate_v13_report.py`
- `bench/consolidate_4side_report.py`
