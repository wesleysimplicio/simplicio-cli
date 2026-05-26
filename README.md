# simplicio-cli

**Portable task-to-code pipeline that works with any LLM.**

Turn a one-line task (*"hide the Delete button for non-admins"*) into a verified
code change — diff + test + visual evidence. Runs **outside** the agent (Claude
Code, Codex, Hermes), so the model is swappable via one env var.

The idea in one line: **don't ask the model to guess — hand it the path.**
Each layer removes one decision the model would otherwise hallucinate.

---

## How it works

```
mapper        WHERE   project structure + latest state
precedent     HOW-1   the real snippet in THIS repo that already does it
skill-router  HOW-2   the ONE mapper skill that matches (ranked, not all)
simplicio     BUILD   stacks the 6 layers into one prompt (cache-friendly)
test          JUDGE   contract written as testable states
verify        PROOF   ran it — did it actually pass? loop-fix up to 3x
```

Why it's more accurate: not because the LLM got smarter, but because every
layer **terminates an uncertain decision** before the model sees the task.
Relevant > complete — each layer injects the *right* context, never *all* of it.

---

## Install

```bash
pip install -e .          # from this repo
```

## Configure — any LLM, nothing hardcoded

Three env vars define the model. No provider list, no built-in model names.

Examples (verify model ids / endpoints against each vendor's current docs):

| Provider | SIMPLICIO_MODEL | SIMPLICIO_BASE_URL |
|---|---|---|
| OpenRouter | `anthropic/claude-opus-4` | `https://openrouter.ai/api/v1` |
| GLM (z.ai) | `glm-4.6` | `https://api.z.ai/api/paas/v4` |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com` |
| OpenAI | `gpt-4.1` | `https://api.openai.com/v1` |
| Local (Ollama) | `llama3` | `http://localhost:11434/v1` |
| Anthropic native | `claude-opus-4-7` | *(leave unset)* |

If `SIMPLICIO_BASE_URL` is unset and the key is `ANTHROPIC_API_KEY`, it uses the
native Anthropic SDK. Otherwise it uses an OpenAI-compatible client pointed at
your `base_url` — so **any** OpenAI-like provider works without code changes.

Quick check it connects:

```bash
simplicio smoke      # prints provider config + one test call
```

## Use

```bash
# index once (caches embeddings; re-run after big changes)
simplicio index --stack angular

# run a task
simplicio task "hide Delete button for non-admins" \
  --stack angular \
  --alvo src/app/screen/screen.component.html \
  --criterios "- no admin perm: button absent from DOM
- with admin perm: button present" \
  --restricoes "- don't touch save flow
- build passes"
```

Each `task`: precedent (from cache) → skill match → 6 layers → LLM generates
(diff + test + Playwright) → apply → run `SIMPLICIO_TEST_CMD` → pass? **done** :
send the error back → fix → retry (up to 3x).

---

## Cache — why it doesn't re-map every time

Embeddings are keyed by **content hash**, stored in `.simplicio/`. Unchanged
code block → vector reused. Change one file → only that block re-embeds.

Measured on a tiny sample repo (model already loaded):

| Run | Blocks embedded | Time |
|---|---|---|
| 1st (cold cache) | 3 | ~baseline |
| 2nd (no change) | **0** | **~instant** |
| after editing 1 file | **1** | partial |

The second run skips embedding entirely. On a real repo this is the difference
between seconds and sub-second per call.

---

## Benchmark — honest & reproducible

Two harnesses are shipped. Both are real, both are deterministic, no LLM
judges the LLM.

### Offline harness (no project required — stdlib only)

`bench/run_offline.py` runs each case twice on the **same model**:
**without** (raw one-line objective) vs **with simplicio** (the 6-layer
contract: target, criteria, constraints, output shape). Scoring is a list
of regex checks per case (target-file mention, DIFF block, TEST block,
contract state words). No real Angular project needed.

```bash
OPENROUTER_API_KEY=… python3 bench/run_offline.py
```

Last run on this repo — `qwen/qwen-2.5-7b-instruct`, 3 cases, 15 checks:

| # | Task | Without | With simplicio |
|---|---|---|---|
| 1 | Hide Delete button for non-admin | 2/5 | 2/5 |
| 2 | Disable email field unless editor | 2/5 | 5/5 |
| 3 | Show audit-log link only for auditor | 1/5 | 5/5 |

**Overall:** without **5/15 (33%)** · with simplicio **12/15 (80%)** ·
delta **+47 pts**. Full report (md / pdf):
[`bench/results.md`](bench/results.md) · [`bench/results.pdf`](bench/results.pdf).
Raw model outputs of each run are saved under `.simplicio/bench_runs/` so
you can audit what the LLM actually produced on each side.

### Full harness (your real project, your real tests)

```bash
simplicio bench --cases bench/cases.json --stack angular
```

Runs each case two ways and runs **your real test command** (e.g. `ng test
--watch=false`) on each output. Writes the true pass-rate to
[`bench/results.md`](bench/results.md). **No numbers are claimed until you
run it on your repo.**

---

## Plug points (stubs marked in code)

| File | Replace with |
|---|---|
| `prompt.py::_mapper` | your real **llm-project-mapper** |
| `pipeline.py::_aplicar_e_testar` | extract diff → `git apply` → parse test result |
| `skill_router.py` | point `SIMPLICIO_SKILLS_DIR` at your mapper's skills |

## Layout

```
simplicio/
  cli.py          # index | task | bench
  cache.py        # content-hash embedding cache
  precedent.py    # grep + semantic rank (uses cache)
  skill_router.py # picks the ONE matching skill
  prompt.py       # stacks the 6 layers
  providers.py    # claude / gpt / glm / deepseek
  pipeline.py     # generate → test → fix loop
  bench.py        # with-vs-without harness
  templates/simplicio_prompt.md
bench/
  cases.json      # your benchmark tasks
  results.md      # filled by `simplicio bench`
```

## License
MIT
