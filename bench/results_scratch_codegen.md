# Scratch Codegen Benchmark

synthetic deterministic executor benchmark; no LLM calls; does not replace the full 50-scratch release gate

## Summary

- cases: 60/60 passed
- codegen share: 100.00%
- expected executor match: 100.00%
- avg codegen latency: 61 ms
- post-validated cases: 20
- post-validation failures: 0
- planner calls: 0
- llm calls: 0

## Release Gate Status

- fifty_runs: True
- mechanical_share_ge_30: True
- executor_pass_rate_100: True
- executor_pass_rate_ge_llm: None
- typescript_next_route_compiles_and_responds_json: True
- llm_baseline_present: False
- latency_reduction_ge_50: None

## Cases

| case | stack | executor | mode | post-validation | passed | duration_ms |
| --- | --- | --- | --- | --- | --- | ---: |
| python-orm-field r01 | py-fastapi | python-add-orm-field | codegen | - | True | 142 |
| python-pydantic-schema r01 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 5 |
| python-fastapi-route r01 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r01 | py-fastapi | python-add-pytest-test | codegen | - | True | 3 |
| typescript-next-route r01 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 341 |
| typescript-next-page r01 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 2 |
| python-orm-field r02 | py-fastapi | python-add-orm-field | codegen | - | True | 6 |
| python-pydantic-schema r02 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 2 |
| python-fastapi-route r02 | py-fastapi | python-add-fastapi-route | codegen | - | True | 2 |
| python-pytest-test r02 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r02 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 343 |
| typescript-next-page r02 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
| python-orm-field r03 | py-fastapi | python-add-orm-field | codegen | - | True | 4 |
| python-pydantic-schema r03 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 3 |
| python-fastapi-route r03 | py-fastapi | python-add-fastapi-route | codegen | - | True | 2 |
| python-pytest-test r03 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r03 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 331 |
| typescript-next-page r03 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 1 |
| python-orm-field r04 | py-fastapi | python-add-orm-field | codegen | - | True | 5 |
| python-pydantic-schema r04 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 3 |
| python-fastapi-route r04 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r04 | py-fastapi | python-add-pytest-test | codegen | - | True | 3 |
| typescript-next-route r04 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 349 |
| typescript-next-page r04 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
| python-orm-field r05 | py-fastapi | python-add-orm-field | codegen | - | True | 3 |
| python-pydantic-schema r05 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 2 |
| python-fastapi-route r05 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r05 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r05 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 322 |
| typescript-next-page r05 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
| python-orm-field r06 | py-fastapi | python-add-orm-field | codegen | - | True | 3 |
| python-pydantic-schema r06 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 2 |
| python-fastapi-route r06 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r06 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r06 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 338 |
| typescript-next-page r06 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
| python-orm-field r07 | py-fastapi | python-add-orm-field | codegen | - | True | 5 |
| python-pydantic-schema r07 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 2 |
| python-fastapi-route r07 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r07 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r07 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 332 |
| typescript-next-page r07 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
| python-orm-field r08 | py-fastapi | python-add-orm-field | codegen | - | True | 3 |
| python-pydantic-schema r08 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 3 |
| python-fastapi-route r08 | py-fastapi | python-add-fastapi-route | codegen | - | True | 2 |
| python-pytest-test r08 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r08 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 367 |
| typescript-next-page r08 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
| python-orm-field r09 | py-fastapi | python-add-orm-field | codegen | - | True | 3 |
| python-pydantic-schema r09 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 3 |
| python-fastapi-route r09 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r09 | py-fastapi | python-add-pytest-test | codegen | - | True | 2 |
| typescript-next-route r09 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 327 |
| typescript-next-page r09 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 1 |
| python-orm-field r10 | py-fastapi | python-add-orm-field | codegen | - | True | 5 |
| python-pydantic-schema r10 | py-fastapi | python-add-pydantic-schema | codegen | - | True | 45 |
| python-fastapi-route r10 | py-fastapi | python-add-fastapi-route | codegen | - | True | 1 |
| python-pytest-test r10 | py-fastapi | python-add-pytest-test | codegen | - | True | 4 |
| typescript-next-route r10 | ts-nextjs | typescript-add-next-route | codegen | typescript_compile,get_json,post_json | True | 342 |
| typescript-next-page r10 | ts-nextjs | typescript-add-next-page | codegen | crud_page_marker,async_page_component,create_form,list_render | True | 0 |
