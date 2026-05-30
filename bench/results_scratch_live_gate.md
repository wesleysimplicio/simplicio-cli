# Scratch Live Gate

live scratch v0.5 gate execution slice; partial runs are evidence only for the executed slice and do not replace the full 75-run gate

## Matrix

- release planned runs: 75
- selected matrix runs: 30
- selected runs: 30
- plan only: False
- skip install: False
- post verify: True

## Summary

- planner valid: 30/30 (100.00%)
- scaffold clean: 30 (100.00%)
- task all passed: 30 (100.00%)
- e2e green: 30 (100.00%)
- median wall-clock: 8.728 s
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
| 2 | ts-nextjs | 1 | 0 | True | True | True | True | 10.858 |
| 3 | py-fastapi | 2 | 0 | True | True | True | True | 6.109 |
| 4 | ts-nextjs | 2 | 0 | True | True | True | True | 11.426 |
| 5 | py-fastapi | 3 | 0 | True | True | True | True | 6.198 |
| 6 | ts-nextjs | 3 | 0 | True | True | True | True | 11.84 |
| 7 | py-fastapi | 4 | 0 | True | True | True | True | 6.262 |
| 8 | ts-nextjs | 4 | 0 | True | True | True | True | 11.572 |
| 9 | py-fastapi | 5 | 0 | True | True | True | True | 6.254 |
| 10 | ts-nextjs | 5 | 0 | True | True | True | True | 12.685 |
| 11 | py-fastapi | 6 | 0 | True | True | True | True | 6.59 |
| 12 | ts-nextjs | 6 | 0 | True | True | True | True | 13.979 |
| 13 | py-fastapi | 7 | 0 | True | True | True | True | 6.228 |
| 14 | ts-nextjs | 7 | 0 | True | True | True | True | 14.402 |
| 15 | py-fastapi | 8 | 0 | True | True | True | True | 6.265 |
| 16 | ts-nextjs | 8 | 0 | True | True | True | True | 14.231 |
| 17 | py-fastapi | 9 | 0 | True | True | True | True | 6.118 |
| 18 | ts-nextjs | 9 | 0 | True | True | True | True | 14.38 |
| 19 | py-fastapi | 10 | 0 | True | True | True | True | 6.481 |
| 20 | ts-nextjs | 10 | 0 | True | True | True | True | 14.618 |
| 21 | py-fastapi | 11 | 0 | True | True | True | True | 6.442 |
| 22 | ts-nextjs | 11 | 0 | True | True | True | True | 14.138 |
| 23 | py-fastapi | 12 | 0 | True | True | True | True | 6.256 |
| 24 | ts-nextjs | 12 | 0 | True | True | True | True | 16.544 |
| 25 | py-fastapi | 13 | 0 | True | True | True | True | 6.597 |
| 26 | ts-nextjs | 13 | 0 | True | True | True | True | 15.563 |
| 27 | py-fastapi | 14 | 0 | True | True | True | True | 6.316 |
| 28 | ts-nextjs | 14 | 0 | True | True | True | True | 16.422 |
| 29 | py-fastapi | 15 | 0 | True | True | True | True | 6.507 |
| 30 | ts-nextjs | 15 | 0 | True | True | True | True | 16.384 |

## Missing Release Evidence

- full 15 goals x 5 pilot stacks live matrix
- average cost measurement
- SkillOpt human approval evidence >=80%
