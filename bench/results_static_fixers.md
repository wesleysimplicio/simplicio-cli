# Static Fixers Benchmark

synthetic verify-loop fixer benchmark; package installs and LLM generation are faked; does not replace the full 50-scratch gate

## Summary

- cases: 50/50 passed
- fixed before LLM retry: 80.00%
- baseline LLM calls: 100
- with-fixer LLM calls: 60
- retry-call reduction: 40.00%

## Release Gate Status

- fifty_cases: True
- fixer_resolved_ge_80: True
- retry_calls_down_ge_30: True
- real_scratch_corpus: False

## Cases

| case | fixed_before_retry | baseline_calls | with_fixer_calls | passed |
| --- | --- | ---: | ---: | --- |
| missing-pip-01 | True | 2 | 1 | True |
| missing-pip-02 | True | 2 | 1 | True |
| missing-pip-03 | True | 2 | 1 | True |
| missing-pip-04 | True | 2 | 1 | True |
| missing-pip-05 | True | 2 | 1 | True |
| missing-pip-06 | True | 2 | 1 | True |
| missing-pip-07 | True | 2 | 1 | True |
| missing-pip-08 | True | 2 | 1 | True |
| missing-pip-09 | True | 2 | 1 | True |
| missing-pip-10 | True | 2 | 1 | True |
| missing-pip-11 | True | 2 | 1 | True |
| missing-pip-12 | True | 2 | 1 | True |
| missing-pip-13 | True | 2 | 1 | True |
| missing-pip-14 | True | 2 | 1 | True |
| missing-pip-15 | True | 2 | 1 | True |
| missing-pip-16 | True | 2 | 1 | True |
| missing-pip-17 | True | 2 | 1 | True |
| missing-pip-18 | True | 2 | 1 | True |
| missing-pip-19 | True | 2 | 1 | True |
| missing-pip-20 | True | 2 | 1 | True |
| missing-pip-21 | True | 2 | 1 | True |
| missing-pip-22 | True | 2 | 1 | True |
| missing-pip-23 | True | 2 | 1 | True |
| missing-pip-24 | True | 2 | 1 | True |
| missing-pip-25 | True | 2 | 1 | True |
| missing-pip-26 | True | 2 | 1 | True |
| missing-pip-27 | True | 2 | 1 | True |
| missing-pip-28 | True | 2 | 1 | True |
| missing-pip-29 | True | 2 | 1 | True |
| missing-pip-30 | True | 2 | 1 | True |
| missing-pip-31 | True | 2 | 1 | True |
| missing-pip-32 | True | 2 | 1 | True |
| missing-pip-33 | True | 2 | 1 | True |
| missing-pip-34 | True | 2 | 1 | True |
| missing-pip-35 | True | 2 | 1 | True |
| missing-pip-36 | True | 2 | 1 | True |
| missing-pip-37 | True | 2 | 1 | True |
| missing-pip-38 | True | 2 | 1 | True |
| missing-pip-39 | True | 2 | 1 | True |
| missing-pip-40 | True | 2 | 1 | True |
| assertion-01 | False | 2 | 2 | True |
| assertion-02 | False | 2 | 2 | True |
| assertion-03 | False | 2 | 2 | True |
| assertion-04 | False | 2 | 2 | True |
| assertion-05 | False | 2 | 2 | True |
| assertion-06 | False | 2 | 2 | True |
| assertion-07 | False | 2 | 2 | True |
| assertion-08 | False | 2 | 2 | True |
| assertion-09 | False | 2 | 2 | True |
| assertion-10 | False | 2 | 2 | True |
