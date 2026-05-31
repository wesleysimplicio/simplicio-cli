# Bench v14 — Qwen2.5-Coder-1.5B — curva de quantização GGUF (issue #46)

Date: **2026-05-31**
Status: **PARCIAL / EM ABERTO** — apenas 1 dos pontos da curva tem medição real.
Os demais (`Q8_0`, `Q6_K`, `Q4_K_M`, ...) seguem **pendentes** por restrição de
infra/tempo (ver seção "Status de execução"). Este arquivo NÃO inventa números:
linhas sem medição real estão marcadas como `pendente`.

> Issue: [#46](https://github.com/wesleysimplicio/simplicio-dev-cli/issues/46)
> — "curva completa de quantização GGUF (Q4_K_S → Q8_0)".
> Infra de smoke já entregue na **PR #47** (`bench/smoke_schema_v1.py`).

---

## 1. O que a issue pede

Medir a mesma base `bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF` em várias
quantizações pra responder: **a conclusão "1.5B está abaixo da fronteira do
schema v1" é real, ou é artefato da quantização agressiva (Q5_K_M)?**

Plano mínimo viável (3 quants): **Q8_0** (teto) + **Q6_K** (sweet spot) +
**Q4_K_M** (piso agressivo). Protocolo: smoke schema-v1 barato (4 calls, 1 task)
como gate `parse_ok >= 2/4` ANTES do bench completo (12 cases × 5 lados, ~11h/quant).

---

## 2. Curva no harness-alvo (schema v1 / sindico, `llama-cpp-python`, CPU)

Este é o harness que a issue quer medir (structured output v1, 6 campos JSON,
lados `baseline | cli | cli+sp | cli+ag | cli+sp+ag`).

| quant   | tamanho | RAM peak | parse_ok % | cli+ag pass | min/case | fonte |
|---------|---------|----------|-----------|-------------|----------|-------|
| Q8_0    | 1.65 GB | pendente | pendente  | pendente    | pendente | — |
| Q6_K_L  | 1.33 GB | pendente | pendente  | pendente    | pendente | — |
| Q6_K    | 1.27 GB | pendente | pendente  | pendente    | pendente | — |
| Q5_K_L  | 1.18 GB | pendente | pendente  | pendente    | pendente | — |
| **Q5_K_M** | 1.13 GB | ~1.7 GB | **0% (0/8)** | **1/2** | **~55 min** | `results_v14_qwen15b_gguf_partial.md` (parcial 2/12) |
| Q4_K_M  | 0.99 GB | pendente | pendente  | pendente    | pendente | — |
| Q4_K_S  | ~0.94 GB| pendente | pendente  | pendente    | pendente | — |

**Único ponto real (Q5_K_M, parcial 2/12):** `parse_ok = 0/8`, `cli+ag = 1/2`
cases PASS, ~55 min/case (CPU 8 threads, ctx 4096, temp 0.7, `BENCH_SP_TIERS=4`).
Interrompido pelo operador em ~2h. Estatisticamente é indicativo, não conclusivo.

---

## 3. Evidência de apoio — harness `run_exec.py` (Python, single-shot, ollama)

Harness DIFERENTE do alvo: 6 cases Python, single-shot (sem verify-loop), via
ollama. Não mede schema v1, mas é o único lugar com **Q8_0 real** hoje.
Fonte: `bench/RESULTS_LOCAL_GGUF.md` (Apple M1, 8 GB, GPU/Metal).

| quant   | sem simplicio | com simplicio | throughput | RAM |
|---------|---------------|---------------|-----------|-----|
| Q5_K_M  | 66% (4/6)     | 66% (4/6)     | ~63 tok/s | 1.7 GB |
| **Q8_0**| **83% (5/6)** | 66% (4/6)     | ~42 tok/s | ~2.2 GB |

**Leitura:** o Q8_0 recupera qualidade no codegen Python bruto (83% vs 66%),
ao custo de ~33% mais lento e ~0.5 GB de RAM. Isso **sustenta a hipótese da
issue** de que precisão maior pode reabilitar o 1.5B — mas é noutro harness;
só o smoke schema-v1 do Q8_0 confirma se ele atravessa o gate de `parse_ok`.

---

## 4. Status de execução nesta sessão (medido, 2026-05-31)

Ambiente do container sondado diretamente:

| recurso | estado |
|---|---|
| `llama_cpp` | **ausente** (`ModuleNotFoundError`) |
| `huggingface_hub` | **ausente** |
| `numpy` / core deps do simplicio | **ausente** (só `simplicio` importa "puro") |
| `ollama` | **ausente** |
| GGUF em disco | nenhum (`models/` só tem Modelfiles apontando p/ paths do Mac do autor) |
| rede | **OK** (huggingface.co → 200, pypi.org → 200) |
| hardware | 4 vCPU, 15 GB RAM, 30 GB disco livre |

Consequência: rodar a curva exige (a) `pip install` do extra `local`
(`llama-cpp-python` compila C++), (b) baixar ~1.3 GB/quant, (c) ~11h CPU/quant
no bench completo. **Os 4 vCPU tornam o bench completo inviável dentro da janela
de uma sessão.**

### Resultado da sondagem de instalação (real, 2026-05-31)

Tentativa de preparar o backend neste container (`/tmp/venv46`):

| item | resultado |
|---|---|
| build tools | **presentes** — `cmake`, `gcc`, `g++`, `make` em `/usr/bin` |
| `numpy` | **instala** (2.4.6, wheel) |
| `huggingface-hub` | **instala** (1.17.0, wheel) — `hf download` viável |
| `llama-cpp-python` | **sem wheel prebuilt** p/ cp311/linux (`No matching distribution`) — precisa **compilar do source** (~10-20 min em 4 vCPU) |

Ou seja: o ambiente *consegue* preparar o backend (compilando), e tem rede pra
baixar os GGUF — mas o gargalo continua sendo o **tempo de CPU do bench completo**.
O smoke (4 calls) é o único passo barato o suficiente; mesmo ele depende de
compilar o `llama-cpp-python` primeiro.

## 5. Runbook para fechar a curva (máquina capaz, CPU 8t+ ou GPU)

---

## 5. Runbook para fechar a curva (máquina capaz, CPU 8t+ ou GPU)

```bash
# 0. deps
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[local,bench]"            # llama-cpp-python + huggingface-hub + fpdf2

# 1. por quant (Q8_0, Q6_K, Q4_K_M):
Q=Q8_0
hf download bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF \
    Qwen2.5-Coder-1.5B-Instruct-$Q.gguf --local-dir ./models

# 2. SMOKE gate (barato, ~min) — PR #47
BENCH_GGUF_PATH=./models/Qwen2.5-Coder-1.5B-Instruct-$Q.gguf \
BENCH_MODEL="local:qwen15b-$Q" \
python bench/smoke_schema_v1.py          # go/no-go: parse_ok >= 2/4

# 3. se passar o smoke -> bench completo (caro, ~11h CPU)
BENCH_GGUF_PATH=./models/Qwen2.5-Coder-1.5B-Instruct-$Q.gguf \
BENCH_SP_TIERS=4 BENCH_AGENTS_MAX_ATTEMPTS=3 \
python bench/run_exec_sindico.py
# salva em bench/results_v14_qwen15b_$Q.json
```

Preencher as linhas `pendente` da seção 2 com os JSONs gerados e regenerar o
PDF (curva `parse_ok × quant` e `pass_rate × quant`) via reportlab/fpdf2.

---

## 6. Decisão registrada

Ver **ADR-003** (`.specs/architecture/ADR-003-qwen15b-quant-viability.md`):
veredito interino "1.5B abaixo da fronteira do schema v1; 3B é o piso local
medido" — sujeito a revisão quando os smokes Q8_0/Q6_K/Q4_K_M existirem.

## Fontes

- `bench/results_v14_qwen15b_gguf_partial.md` (Q5_K_M schema-v1, parcial 2/12)
- `bench/RESULTS_LOCAL_GGUF.md` (Q5_K_M + Q8_0, harness `run_exec.py`)
- `bench/results_exec_sindico.md` (metodologia exec real, deepseek-v4-flash)
- issue #46 + comentário da PR #47
- sondagem direta do container (2026-05-31)
