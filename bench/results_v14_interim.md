# v14 INTERIM — bench funcional (PHPUnit) 3 models × 12 cases × 5 sides

Snapshot: **2026-05-31 00:38:41**

Bench rodando em background, dados parciais dos logs. Modelos com `-> baseline...` fecharam; os outros ainda rodam.

## Configuração

| model | backend | tiers sp |
|---|---|---|
| `deepseek/deepseek-v4-flash` | OpenRouter API | 64 → 100 |
| `local:Qwen/Qwen2.5-Coder-3B-Instruct` | transformers CPU fp32 | 4 (single cycle) |
| `local:Qwen/Qwen2.5-Coder-1.5B-Instruct` | transformers CPU fp32 | 4 (single cycle) |

**Bench**: 12 cases reais sindico, PHPUnit como oracle. Schema v1 ativo em todos os lados sp.

## Status por modelo

### `deepseek-v4-flash`

**STATUS: EM ANDAMENTO** (6/12 cases)

Parcial: base **2**/6 · cli **6**/6 · cli+sp **6**/6 · cli+ag **6**/6 · cli+sp+ag **6**/6

| Case | base | cli | cli+sp (parse) | cli+ag | cli+sp+ag |
|---|---|---|---|---|---|
| password_strength | . | P |  PASS [N=64 u=62 modal=2 parse=59/64] | P(1/3) | P(1/3) |
| password_require_symbol | P | P |  PASS [N=64 u=60 modal=3 parse=57/64] | P(1/3) | P(1/3) |
| env_get_int | . | P |  PASS [N=64 u=57 modal=3 parse=59/64] | P(1/3) | P(1/3) |
| env_get_bool | . | P |  PASS [N=64 u=55 modal=4 parse=55/64] | P(1/3) | P(1/3) |
| admin_only_allowed_roles | P | P |  PASS [N=64 u=39 modal=8 parse=61/64] | P(1/3) | P(1/3) |
| rate_limit_bucket_key | . | P |  PASS [N=64 u=30 modal=18 parse=58/64] | P(1/3) | P(1/3) |

## Achados notáveis

_Quando o batch terminar, completo o relatório com PDF final + grand totals_

- **DeepSeek V4 Flash** honra schema v1 em média **91%** dos N=64 subagents (349 parse_ok de 384 totais)
- DeepSeek + cli+sp: **6/6 cases passam** (parou cycle 1 em todos, sem precisar escalar pra N=100)
