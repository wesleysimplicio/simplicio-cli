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

```bash
export SIMPLICIO_MODEL="..."        # model id, exactly as your provider expects
export SIMPLICIO_BASE_URL="..."     # any OpenAI-compatible endpoint
export SIMPLICIO_API_KEY="..."      # your key (NEVER commit / paste in chat)
export SIMPLICIO_TEST_CMD="ng test --watch=false"   # your real test command
```

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

This repo ships the **harness**, not pre-baked numbers. To compare *with* vs
*without* the pipeline on **your** code:

```bash
simplicio bench --cases bench/cases.json --stack angular
```

It runs each case two ways — **without** (raw objective → LLM, baseline) and
**with** (full pipeline) — runs your real test command on each output, and
writes the true pass-rate to [`bench/results.md`](bench/results.md).

**No numbers are claimed until you run it.** The point of the tool is removing
guesswork; shipping invented benchmark figures would contradict that. Run it,
and the table fills with results you can defend.

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
