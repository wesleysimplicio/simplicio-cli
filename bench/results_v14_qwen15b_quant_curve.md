# Qwen 1.5B Quant Curve

final Qwen2.5-Coder-1.5B GGUF quant curve assembled from manifest-declared schema-v1 smoke artifacts

## Summary

- release ready: True
- quant curve complete: True
- decision: not viable for schema-v1: required quant smokes failed; skip full bench unless the smoke protocol changes
- required quant smokes present: Q8_0=True, Q6_K=True, Q4_K_M=True
- required quant smokes passed: Q8_0=False, Q6_K=False, Q4_K_M=False
- missing quant smokes: none
- failed required quant smokes: Q8_0, Q6_K, Q4_K_M

## Rows

| quant | smoke JSON | calls | parse ok | parse failed | pass | sha256 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Q8_0 | `bench/results_v14_qwen15b_q8_0_smoke_schema_v1.json` | 4 | 0 | 4 | False | `99d9bd6c7735` |
| Q6_K | `bench/results_v14_qwen15b_q6_k_smoke_schema_v1.json` | 4 | 0 | 4 | False | `9913146653c6` |
| Q4_K_M | `bench/results_v14_qwen15b_q4_k_m_smoke_schema_v1.json` | 4 | 0 | 4 | False | `cb190e0034c0` |
