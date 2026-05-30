# Scratch Planner Cache Gate

cold/warm scratch planner cache measurement; this proves planner cache replay for identical prompts. Optional live-gate input links the cache evidence to the shared real scratch release corpus without overstating the cold/warm sample size.

## Summary

- goals: 18
- cold valid plans: 18
- warm valid plans: 18
- warm cache hit-rate: 100.00%
- warm hits/misses: 18/0
- cold cache puts: 18
- selected corpus goals: 18/50
- merged slices: 7

## Live Corpus Link

- source: bench/results_scratch_live_gate.json
- runs: 75
- e2e green: 75
- e2e green rate: 100.00%
- stacks: go-gin, php-laravel, py-fastapi, rust-axum, ts-nextjs

## Release Gate Status

- warm_hit_rate_ge_80: True
- warm_plans_all_valid: True
- cold_populated_cache: True
- real_50_scratch_corpus: True
- cold_warm_measured_on_50_real_scratches: False

## Missing Release Evidence

- planner cache hit-rate measured across cold/warm real scratch runs

## Warm Cases

| goal | passed | tasks | duration_ms |
| --- | --- | ---: | ---: |
| Build a FastAPI audit log service with export filters and retention policy | True | 20 | 3 |
| Build a FastAPI feature flag service with rollout rules and audit trail | True | 28 | 2 |
| Build a FastAPI webhook ingestion service with replay controls | True | 30 | 3 |
| Build a FastAPI data export service with signed download links | True | 36 | 2 |
| Build a FastAPI notification preference service with channel rules | True | 27 | 5 |
| Build a FastAPI incident escalation service with severity routing | True | 28 | 3 |
| Build a FastAPI maintenance scheduling service with recurring windows | True | 30 | 3 |
| Build a FastAPI resident profile merge service with conflict reports | True | 32 | 2 |
| Build a FastAPI document indexing service with access policy checks | True | 44 | 3 |
| Build a FastAPI visitor preapproval service with expiry reminders | True | 29 | 2 |
| Build a FastAPI package pickup workflow with identity verification | True | 35 | 3 |
| Build a FastAPI payment reconciliation service with exception queues | True | 29 | 2 |
| Build a FastAPI amenity capacity service with blackout dates | True | 38 | 2 |
| Build a FastAPI parking allocation service with waitlist promotion | True | 33 | 2 |
| Build a FastAPI vendor insurance tracker with renewal alerts | True | 25 | 4 |
| Build a FastAPI board vote recording service with quorum rules | True | 25 | 2 |
| Build a FastAPI announcement targeting service with audience segments | True | 31 | 2 |
| Build a FastAPI key fob lifecycle service with revocation audits | True | 28 | 2 |
