# Scratch Codegen Benchmark

synthetic deterministic executor benchmark; no LLM calls; does not replace the full 50-scratch release gate

## Summary

- cases: 50/50 passed
- codegen share: 100.00%
- expected executor match: 100.00%
- avg codegen latency: 70 ms
- planner calls: 0
- llm calls: 0

## Release Gate Status

- fifty_runs: True
- mechanical_share_ge_30: True
- executor_pass_rate_100: True
- llm_baseline_present: False
- latency_reduction_ge_50: None

## Cases

| case | stack | executor | mode | passed | duration_ms |
| --- | --- | --- | --- | --- | ---: |
| python-orm-field r01 | py-fastapi | python-add-orm-field | codegen | True | 135 |
| python-pydantic-schema r01 | py-fastapi | python-add-pydantic-schema | codegen | True | 4 |
| python-fastapi-route r01 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r01 | py-fastapi | python-add-pytest-test | codegen | True | 4 |
| typescript-next-route r01 | ts-nextjs | typescript-add-next-route | codegen | True | 325 |
| python-orm-field r02 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r02 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r02 | py-fastapi | python-add-fastapi-route | codegen | True | 2 |
| python-pytest-test r02 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r02 | ts-nextjs | typescript-add-next-route | codegen | True | 316 |
| python-orm-field r03 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r03 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r03 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r03 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r03 | ts-nextjs | typescript-add-next-route | codegen | True | 327 |
| python-orm-field r04 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r04 | py-fastapi | python-add-pydantic-schema | codegen | True | 3 |
| python-fastapi-route r04 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r04 | py-fastapi | python-add-pytest-test | codegen | True | 3 |
| typescript-next-route r04 | ts-nextjs | typescript-add-next-route | codegen | True | 389 |
| python-orm-field r05 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r05 | py-fastapi | python-add-pydantic-schema | codegen | True | 3 |
| python-fastapi-route r05 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r05 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r05 | ts-nextjs | typescript-add-next-route | codegen | True | 325 |
| python-orm-field r06 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r06 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r06 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r06 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r06 | ts-nextjs | typescript-add-next-route | codegen | True | 306 |
| python-orm-field r07 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r07 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r07 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r07 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r07 | ts-nextjs | typescript-add-next-route | codegen | True | 320 |
| python-orm-field r08 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r08 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r08 | py-fastapi | python-add-fastapi-route | codegen | True | 2 |
| python-pytest-test r08 | py-fastapi | python-add-pytest-test | codegen | True | 3 |
| typescript-next-route r08 | ts-nextjs | typescript-add-next-route | codegen | True | 332 |
| python-orm-field r09 | py-fastapi | python-add-orm-field | codegen | True | 3 |
| python-pydantic-schema r09 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r09 | py-fastapi | python-add-fastapi-route | codegen | True | 1 |
| python-pytest-test r09 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r09 | ts-nextjs | typescript-add-next-route | codegen | True | 318 |
| python-orm-field r10 | py-fastapi | python-add-orm-field | codegen | True | 4 |
| python-pydantic-schema r10 | py-fastapi | python-add-pydantic-schema | codegen | True | 2 |
| python-fastapi-route r10 | py-fastapi | python-add-fastapi-route | codegen | True | 2 |
| python-pytest-test r10 | py-fastapi | python-add-pytest-test | codegen | True | 2 |
| typescript-next-route r10 | ts-nextjs | typescript-add-next-route | codegen | True | 332 |
