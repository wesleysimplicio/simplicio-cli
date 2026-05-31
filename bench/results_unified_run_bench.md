# Unified Run F5 Bench Fixture

planned fixture comparison for cli+ag, unified feature/sprint, and Codex /goal; no LLM or external agent was invoked

## Summary

- issue: #41
- phase: F5
- fixture only: True
- cases: 3
- modes: 4
- rows: 12/12
- release ready: False
- ready for live run: True

## Modes

| mode | entrypoint | decomposition | replan | cost visibility |
| --- | --- | --- | --- | --- |
| cli+ag task loop | `simplicio task` | human | none | per atomic task |
| unified run feature | `simplicio run --scope feature` | planner | remaining feature tasks | cost governor |
| unified run sprint | `simplicio run --scope sprint --max-cost <usd>` | sprint loader and planner | feature tasks inside sprint | required cost governor |
| Codex /goal | `codex /goal` | external agent | opaque | opaque in this repo bench |

## Fixture Matrix

| case | scope | mode | outcome | task runs | planner calls | manual split | replan | cost observable |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| single-file-task | task | cli+ag task loop | covered_by_existing_atomic_loop | 1 | 0 | False | False | True |
| single-file-task | task | unified run feature | dispatches_to_task | 1 | 0 | False | False | True |
| single-file-task | task | unified run sprint | not_the_primary_scope | 1 | 0 | False | False | True |
| single-file-task | task | Codex /goal | external_baseline_placeholder | 1 | 0 | False | True | False |
| feature-auth-flow | feature | cli+ag task loop | requires_human_decomposition | 4 | 0 | True | False | True |
| feature-auth-flow | feature | unified run feature | covered_by_feature_orchestrator | 4 | 1 | False | True | True |
| feature-auth-flow | feature | unified run sprint | not_the_primary_scope | 4 | 0 | False | False | True |
| feature-auth-flow | feature | Codex /goal | external_baseline_placeholder | 4 | 0 | False | True | False |
| sprint-checkout-hardening | sprint | cli+ag task loop | requires_human_decomposition | 7 | 0 | True | False | True |
| sprint-checkout-hardening | sprint | unified run feature | feature_loop_only_after_sprint_decomposition | 7 | 2 | True | True | True |
| sprint-checkout-hardening | sprint | unified run sprint | covered_by_sprint_orchestrator | 7 | 2 | False | True | True |
| sprint-checkout-hardening | sprint | Codex /goal | external_baseline_placeholder | 7 | 0 | False | True | False |

## Missing Live Evidence

- real cli+ag runs on the controlled task, feature, and sprint cases
- real unified feature/sprint runs with cost governor telemetry
- real Codex /goal baseline runs with comparable success and cost data
- artifact collection for sprint DoD evidence
