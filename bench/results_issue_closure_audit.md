# Issue Closure Audit

close-readiness audit for GitHub issues #32, #33, #41, and #46; partial evidence is reported as blockers

## Summary

- issues close-ready: 1/4
- all issues close-ready: False

## Issues

| issue | title | close-ready | blockers |
| --- | --- | --- | ---: |
| #32 | from-scratch mode + planner + SkillOpt | False | 2 |
| #33 | reduce LLM dependency across simplicio flow | False | 6 |
| #41 | unified simplicio run orchestrator | False | 9 |
| #46 | Qwen2.5-Coder-1.5B GGUF quant curve | True | 0 |

## Open Blockers

### #32
- skillopt_human_approval_ge_80
- live_gate_release_ready

### #33
- B_real_executor_pass_rate_ge_llm
- B_real_latency_reduction_ge_50
- SkillOpt_human_approval_ge_80
- release_evidence_complete
- real scratch LLM baseline for B/codegen pass-rate and latency
- SkillOpt human approval evidence >=80%

### #41
- not_fixture_only
- live_evidence_level
- real_llm_runs_present
- external_codex_goal_run_present
- release_ready
- real cli+ag runs on the controlled task, feature, and sprint cases
- real unified feature/sprint runs with cost governor telemetry
- real Codex /goal baseline runs with comparable success and cost data
- artifact collection for sprint DoD evidence
