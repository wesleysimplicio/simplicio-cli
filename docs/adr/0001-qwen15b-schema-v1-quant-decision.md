# ADR 0001: Qwen2.5-Coder 1.5B GGUF Is Not Viable For Schema V1

Date: 2026-05-31

## Status

Accepted.

## Context

Issue #46 asks whether Qwen2.5-Coder-1.5B-Instruct can satisfy the schema-v1
structured-output contract when less aggressive GGUF quantizations are used.
The minimum required smoke points are Q8_0, Q6_K, and Q4_K_M from
`bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF`.

The go/no-go protocol is `bench/smoke_schema_v1.py --calls 4`. A quant only
deserves the expensive full v14 bench when `parse_ok >= 2/4`.

## Decision

Qwen2.5-Coder-1.5B-Instruct GGUF is not viable for schema-v1 on the tested
CPU smoke protocol.

The three required quant smokes all failed:

| quant | parse_ok | artifact contract | go/no-go |
| --- | ---: | ---: | --- |
| Q8_0 | 0/4 | 0/4 | fail |
| Q6_K | 0/4 | 0/4 | fail |
| Q4_K_M | 0/4 | 0/4 | fail |

Because Q8_0 also failed, the expensive 12-case v14 bench is intentionally not
run for these quants. The result is a negative viability decision, not missing
bench evidence.

## Evidence

- `bench/results_v14_qwen15b_q8_0_smoke_schema_v1.json`
- `bench/results_v14_qwen15b_q6_k_smoke_schema_v1.json`
- `bench/results_v14_qwen15b_q4_k_m_smoke_schema_v1.json`
- `bench/results_v14_qwen15b_quant_curve.json`
- `bench/results_v14_qwen15b_quant_curve.md`
- `bench/results_v14_qwen15b_quant_curve.pdf`

## Consequences

- Use 3B-class or larger local coder models as the practical lower bound for
  schema-v1 work until a different 1.5B model or prompt protocol proves
  otherwise.
- Do not spend CPU time on the full v14 bench for these 1.5B quants under the
  current smoke protocol.
- Keep future model-family tests separate from this Qwen2.5-Coder-1.5B result.
