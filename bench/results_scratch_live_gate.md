# Scratch Live Gate

live scratch v0.5 gate execution slice; partial runs are evidence only for the executed slice and do not replace the full 75-run gate

## Matrix

- release planned runs: 75
- selected matrix runs: 15
- selected runs: 15
- plan only: False
- skip install: False
- post verify: True

## Summary

- planner valid: 15/15 (100.00%)
- scaffold clean: 15 (100.00%)
- task all passed: 15 (100.00%)
- e2e green: 15 (100.00%)
- median wall-clock: 6.262 s
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
| 1 | py-fastapi | 1 | 0 | True | True | True | True | 6.151 |
| 2 | py-fastapi | 2 | 0 | True | True | True | True | 6.109 |
| 3 | py-fastapi | 3 | 0 | True | True | True | True | 6.198 |
| 4 | py-fastapi | 4 | 0 | True | True | True | True | 6.262 |
| 5 | py-fastapi | 5 | 0 | True | True | True | True | 6.254 |
| 6 | py-fastapi | 6 | 0 | True | True | True | True | 6.59 |
| 7 | py-fastapi | 7 | 0 | True | True | True | True | 6.228 |
| 8 | py-fastapi | 8 | 0 | True | True | True | True | 6.265 |
| 9 | py-fastapi | 9 | 0 | True | True | True | True | 6.118 |
| 10 | py-fastapi | 10 | 0 | True | True | True | True | 6.481 |
| 11 | py-fastapi | 11 | 0 | True | True | True | True | 6.442 |
| 12 | py-fastapi | 12 | 0 | True | True | True | True | 6.256 |
| 13 | py-fastapi | 13 | 0 | True | True | True | True | 6.597 |
| 14 | py-fastapi | 14 | 0 | True | True | True | True | 6.316 |
| 15 | py-fastapi | 15 | 0 | True | True | True | True | 6.507 |

## Missing Release Evidence

- full 15 goals x 5 pilot stacks live matrix
- average cost measurement
- SkillOpt human approval evidence >=80%
