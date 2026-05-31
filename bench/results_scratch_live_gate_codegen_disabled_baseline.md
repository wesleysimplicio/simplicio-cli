# Scratch Live Gate

live scratch v0.5 gate execution slice; partial runs are evidence only for the executed slice and do not replace the full 75-run gate

## Matrix

- release planned runs: 75
- selected matrix runs: 4
- selected runs: 4
- plan only: False
- skip install: False
- post verify: True
- codegen disabled: True

## Summary

- planner valid: 3/4 (75.00%)
- scaffold clean: 3 (100.00%)
- task all passed: 1 (25.00%)
- e2e green: 1 (33.33%)
- median wall-clock: 262.135 s
- average cost: None
- lines generated: 0
- lines modified: 0
- release ready: False

## Release Gate Status

- full_75_run_matrix: False
- planner_valid_ge_90: False
- scaffold_clean_ge_95: True
- e2e_green_ge_80: False
- median_wall_clock_le_8m: True
- average_cost_le_1: None
- skillopt_human_approval_ge_80: False
- release_ready: False

## SkillOpt Review Evidence

- source: inline
- reviewed skills: 0/0 approved
- approval rate: 0.00%
- invalid review rows: 0

## Runs

| # | stack | goal_index | rc | planner | scaffold | tasks | e2e | duration_s |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | ---: |
| 1 | py-fastapi | 1 | None | False | None | False | None | 900.047 |
| 2 | go-gin | 1 | 0 | True | True | True | True | 204.707 |
| 3 | go-gin | 2 | 1 | True | True | False | False | 262.135 |
| 4 | go-gin | 3 | 1 | True | True | False | False | 393.191 |

## Missing Release Evidence

- full 15 goals x 5 pilot stacks live matrix
- average cost measurement
- SkillOpt human approval evidence >=80%
