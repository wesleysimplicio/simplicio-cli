# Scratch Live Gate

live scratch v0.5 gate execution slice; partial runs are evidence only for the executed slice and do not replace the full 75-run gate

## Matrix

- release planned runs: 75
- selected matrix runs: 1
- selected runs: 1
- plan only: False
- skip install: False
- post verify: True

## Summary

- planner valid: 1/1 (100.00%)
- scaffold clean: 1 (100.00%)
- task all passed: 1 (100.00%)
- e2e green: 1 (100.00%)
- median wall-clock: 6.04 s
- release ready: False

## Release Gate Status

- full_75_run_matrix: False
- planner_valid_ge_90: True
- scaffold_clean_ge_95: True
- e2e_green_ge_80: True
- median_wall_clock_le_8m: True
- average_cost_le_1: None
- skillopt_human_approval_ge_80: False
- release_ready: False

## Runs

| # | stack | goal_index | rc | planner | scaffold | tasks | e2e | duration_s |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | ---: |
| 1 | py-fastapi | 1 | 0 | True | True | True | True | 6.04 |

## Missing Release Evidence

- full 15 goals x 5 pilot stacks live matrix
- average cost measurement
- SkillOpt human approval evidence >=80%
