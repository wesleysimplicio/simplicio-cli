# Scratch Live Gate

live scratch v0.5 gate execution slice; partial runs are evidence only for the executed slice and do not replace the full 75-run gate

## Matrix

- release planned runs: 75
- selected matrix runs: 45
- selected runs: 45
- plan only: False
- skip install: False
- post verify: True

## Summary

- planner valid: 45/45 (100.00%)
- scaffold clean: 45 (100.00%)
- task all passed: 45 (100.00%)
- e2e green: 45 (100.00%)
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
| 2 | ts-nextjs | 1 | 0 | True | True | True | True | 10.858 |
| 3 | rust-axum | 1 | 0 | True | True | True | True | 0.996 |
| 4 | py-fastapi | 2 | 0 | True | True | True | True | 6.109 |
| 5 | ts-nextjs | 2 | 0 | True | True | True | True | 11.426 |
| 6 | rust-axum | 2 | 0 | True | True | True | True | 0.81 |
| 7 | py-fastapi | 3 | 0 | True | True | True | True | 6.198 |
| 8 | ts-nextjs | 3 | 0 | True | True | True | True | 11.84 |
| 9 | rust-axum | 3 | 0 | True | True | True | True | 0.631 |
| 10 | py-fastapi | 4 | 0 | True | True | True | True | 6.262 |
| 11 | ts-nextjs | 4 | 0 | True | True | True | True | 11.572 |
| 12 | rust-axum | 4 | 0 | True | True | True | True | 0.675 |
| 13 | py-fastapi | 5 | 0 | True | True | True | True | 6.254 |
| 14 | ts-nextjs | 5 | 0 | True | True | True | True | 12.685 |
| 15 | rust-axum | 5 | 0 | True | True | True | True | 1.321 |
| 16 | py-fastapi | 6 | 0 | True | True | True | True | 6.59 |
| 17 | ts-nextjs | 6 | 0 | True | True | True | True | 13.979 |
| 18 | rust-axum | 6 | 0 | True | True | True | True | 0.719 |
| 19 | py-fastapi | 7 | 0 | True | True | True | True | 6.228 |
| 20 | ts-nextjs | 7 | 0 | True | True | True | True | 14.402 |
| 21 | rust-axum | 7 | 0 | True | True | True | True | 1.394 |
| 22 | py-fastapi | 8 | 0 | True | True | True | True | 6.265 |
| 23 | ts-nextjs | 8 | 0 | True | True | True | True | 14.231 |
| 24 | rust-axum | 8 | 0 | True | True | True | True | 0.777 |
| 25 | py-fastapi | 9 | 0 | True | True | True | True | 6.118 |
| 26 | ts-nextjs | 9 | 0 | True | True | True | True | 14.38 |
| 27 | rust-axum | 9 | 0 | True | True | True | True | 0.727 |
| 28 | py-fastapi | 10 | 0 | True | True | True | True | 6.481 |
| 29 | ts-nextjs | 10 | 0 | True | True | True | True | 14.618 |
| 30 | rust-axum | 10 | 0 | True | True | True | True | 2.793 |
| 31 | py-fastapi | 11 | 0 | True | True | True | True | 6.442 |
| 32 | ts-nextjs | 11 | 0 | True | True | True | True | 14.138 |
| 33 | rust-axum | 11 | 0 | True | True | True | True | 3.212 |
| 34 | py-fastapi | 12 | 0 | True | True | True | True | 6.256 |
| 35 | ts-nextjs | 12 | 0 | True | True | True | True | 16.544 |
| 36 | rust-axum | 12 | 0 | True | True | True | True | 2.792 |
| 37 | py-fastapi | 13 | 0 | True | True | True | True | 6.597 |
| 38 | ts-nextjs | 13 | 0 | True | True | True | True | 15.563 |
| 39 | rust-axum | 13 | 0 | True | True | True | True | 0.689 |
| 40 | py-fastapi | 14 | 0 | True | True | True | True | 6.316 |
| 41 | ts-nextjs | 14 | 0 | True | True | True | True | 16.422 |
| 42 | rust-axum | 14 | 0 | True | True | True | True | 1.415 |
| 43 | py-fastapi | 15 | 0 | True | True | True | True | 6.507 |
| 44 | ts-nextjs | 15 | 0 | True | True | True | True | 16.384 |
| 45 | rust-axum | 15 | 0 | True | True | True | True | 0.719 |

## Missing Release Evidence

- full 15 goals x 5 pilot stacks live matrix
- average cost measurement
- SkillOpt human approval evidence >=80%
