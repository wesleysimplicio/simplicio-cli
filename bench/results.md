# Benchmark — simplicio-cli (offline harness)

Model: `qwen/qwen-2.5-7b-instruct` · Base: `https://openrouter.ai/api/v1`  
Date: 2026-05-26  
Cases: 3 · Total checks: 15

Each check is a deterministic regex against the model output 
(target-file mention, DIFF block, TEST block, contract state words). 
Same model on both sides — only the prompt structure changes.

| # | Task | Without (checks ✓) | With simplicio (checks ✓) |
|---|---|---|---|
| 1 | Hide the Delete button when the current user is not an  | 2/5 | 2/5 |
| 2 | Disable the email field unless the profile role is edit | 2/5 | 5/5 |
| 3 | Only show the audit log link for users with role 'audit | 1/5 | 5/5 |

**Overall** — without: **5/15 (33%)** · with simplicio: **12/15 (80%)** · delta: **+47 pts**

Raw model outputs saved under `.simplicio/bench_runs/`. 
Reproduce: `OPENROUTER_API_KEY=… python3 bench/run_offline.py`.
