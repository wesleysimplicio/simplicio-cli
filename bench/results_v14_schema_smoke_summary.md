# Schema Smoke Summary

incremental schema-smoke artifact summary; this does not replace the required Qwen2.5-Coder-1.5B GGUF quant curve

## Summary

- input files: 2
- go/no-go passes: 2
- go/no-go failures: 0
- Qwen 1.5B smokes: 0
- required quant smokes present: Q8_0=False, Q6_K=False, Q4_K_M=False
- required quant smokes passed: Q8_0=False, Q6_K=False, Q4_K_M=False
- missing quant smokes: Q8_0, Q6_K, Q4_K_M
- failed required quant smokes: none
- Qwen 1.5B quant curve complete: False
- release ready: False

## Rows

| source | model | quant | parse ok | calls | go/no-go |
| --- | --- | --- | ---: | ---: | --- |
| `bench/results_sp_schema_smoke_deepseek.json` | deepseek/deepseek-v4-flash | unknown | 3 | 4 | True |
| `bench/results_sp_schema_smoke_qwen3b.json` | Qwen/Qwen2.5-Coder-3B-Instruct | unknown | 4 | 4 | True |

## Missing Release Evidence

- Q8_0/Q6_K/Q4_K_M schema-v1 smoke JSONs for the named GGUF model
- bench/results_v14_qwen15b_quant_curve.{md,json,pdf}
