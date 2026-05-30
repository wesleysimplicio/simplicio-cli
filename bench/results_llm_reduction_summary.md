# LLM Reduction Summary

aggregate issue #33 evidence view; separates local synthetic gates from the real release corpus and LLM-baseline gates

## Summary

- local synthetic gates pass: True
- release evidence complete: False
- target reduction met for release: False
- modeled local call path: 19 -> 6 (68.42% reduction)

## Lever Evidence

| lever | gate | key evidence | release gap |
| --- | --- | --- | --- |
| D cache | True | warm hit-rate 100.00%, hits/misses 2/0 | real corpus False |
| C static fixers | True | fixed 80.00%, retry calls down 40.00% | real corpus False |
| A recipes | True | match-rate 60.00%, planner calls saved 30 | LLM baseline False |
| B codegen | True | codegen share 100.00%, pass-rate 100.00%, avg 61 ms | LLM baseline False |
| scratch preflight | True | blockers 0 | ready for matrix execution |
| scratch live gate | True | 75/75 e2e green, median 6.262 s | full matrix True |

## Modeled Call Path

- baseline: 19 calls
- D_cache: 18 calls, gate=True
- C_static_fixers: 16 calls, gate=True
- A_recipes: 16 calls, gate=True
- B_codegen: 6 calls, gate=True

## Missing Release Evidence

- real 50-scratch corpus shared by cache, recipes, fixers, and executors
- aggregate call-reduction proof across cache, recipes, fixers, and executors
- real fixer evidence from actual install/import/lint failures with non-faked package managers
- recipe path pass-rate compared with equivalent LLM path
- captured LLM baseline for executor pass-rate and latency
- planner cache hit-rate measured across cold/warm real scratch runs
- SkillOpt human approval evidence >=80%
