# Rust hot-path validation — simplicio-core + qwen2.5-coder:3b (local Ollama)

Date: **2026-05-28**
Subject: Rust update `simplicio-core` (PyO3 crate, `build_6layer_prompt`, commit `ea3655b`, closes #17/#18)
Model: `qwen2.5-coder:3b` (Ollama, OpenAI-compatible endpoint `http://localhost:11434/v1`)
Toolchain: `rustc 1.95.0` · `cargo 1.95.0` · `pyo3 0.22.6` · `bumpalo 3.20.3` · `maturin 1.13.3`

The Rust crate re-implements the prompt substitution + comment-strip step of
`simplicio.prompt.build_prompt`. Python stays the source of truth and the
fallback; Rust only takes over when `simplicio_core` is importable. This report
validates the update on four axes: **build → correctness → speed → live model**.

---

## Headline

- **Build:** OK — `simplicio_core` cp313 release wheel built in 12.14 s, installed, `_rs_build` live on the hot path.
- **Correctness:** 5/5 parity tests green + byte-identical to Python on a realistic 2294-char prompt.
- **Speed:** **9.12x faster** than the Python reference (2.711 µs vs 24.735 µs per call). Beats the "~5x" claim in `prompt.py`.
- **Live model:** rust-assembled 6-layer prompt drives `qwen2.5-coder:3b` to **5/6 (83%)** real-pytest pass — same as the contract baseline.
- **Finding:** PyO3 0.22 caps at Python 3.13; the machine default is **3.14.5 (unsupported)**. Built against a 3.13 venv. See [Blocker](#blocker--python-314).

---

## 1. Build status

```
maturin develop --release  (VIRTUAL_ENV=py3.13)
Compiling pyo3 v0.22.6 / bumpalo v3.20.3 / simplicio-core v0.1.0
Finished `release` profile [optimized] in 12.14s
Built wheel: simplicio_core-0.1.0-cp313-cp313-macosx_11_0_arm64.whl
Installed simplicio-core-0.1.0
```

Hot-path activation confirmed:

```
>>> from simplicio.prompt import _rs_build
_rs_build = <built-in function build_6layer_prompt>
>>> simplicio_core.hello("rust")
'hello, rust!'
```

## 2. Correctness — parity suite

`tests/python/test_rust_prompt.py` — Rust output asserted byte-identical to the
Python `_assemble_python` reference.

| Test | Result |
|---|---|
| `test_hello_smoke` | PASS |
| `test_substitution_parity_basic` (real template) | PASS |
| `test_substitution_parity_utf8_em_dash` (multibyte safe) | PASS |
| `test_substitution_unknown_placeholder_passthrough` | PASS |
| `test_comment_strip_multiline` | PASS |

**5 passed in 0.07s.** Parity also held on the realistic 2294-char prompt used
in the microbench (`rs == py`).

## 3. Performance — Rust vs Python

Real 6-layer template (1540 chars) + realistic pre-built blocks, 200 000 iterations:

| Impl | µs/call | ops/s | Speedup |
|---|---|---|---|
| Python `_assemble_python` | 24.735 | 40 428 | 1.00x |
| Rust `build_6layer_prompt` | 2.711 | 368 828 | **9.12x** |

Output: 2294-char assembled prompt, parity OK.

## 4. Live model — qwen2.5-coder:3b (real pytest)

### 4a. Contract effect (`bench/run_exec.py`, inlined contract)

| Model | Without | With | Delta |
|---|---|---|---|
| `qwen2.5-coder:3b` | 4/6 (66%) | 5/6 (83%) | **+17 pts** |

`validate_password` flips fail→pass with the contract. `merge_intervals` fails
both sides (genuine 3B reasoning limit, not a prompt issue).

### 4b. Rust-assembled prompt → qwen → hidden pytest

Prompt built by `simplicio_core.build_6layer_prompt` (substitution + comment-strip
on the Rust hot path), then sent to the local model and scored:

| Task | Result | Latency |
|---|---|---|
| can_delete | PASS | 2504 ms |
| email_editable | PASS | 1444 ms |
| slugify | PASS | 6782 ms |
| apply_discount | PASS | 7298 ms |
| merge_intervals | fail | 8110 ms |
| validate_password | PASS | 5365 ms |

**5/6 (83%)** — matches the contract baseline. The Rust-built prompt yields the
same model behaviour as Python, confirming end-to-end parity under a live LLM.

---

## Blocker — Python 3.14

PyO3 `0.22` supports Python ≤ 3.13. The machine default interpreter is
**3.14.5**, against which the crate will not build (PyO3 hard-errors on a newer
interpreter for non-abi3 builds). Worked around by building in a Python 3.13
venv. To run on 3.14 the crate needs **PyO3 ≥ 0.25** (3.14 support); the current
`#[pyfunction]` / `Bound<'_, PyModule>` API is forward-compatible, so the bump is
likely a one-line `Cargo.toml` change. Out of scope for this validation run.

## Reproduce

```bash
# build (py3.13 venv — pyo3 0.22 ceiling)
python3.13 -m venv /tmp/scv && /tmp/scv/bin/pip install maturin numpy pytest
cd rust/simplicio-core && VIRTUAL_ENV=/tmp/scv /tmp/scv/bin/maturin develop --release

# correctness
PYTHONPATH=. /tmp/scv/bin/python -m pytest tests/python/test_rust_prompt.py -v

# live model (Ollama serving qwen2.5-coder:3b)
BENCH_BASE_URL=http://localhost:11434/v1 BENCH_API_KEY=ollama \
  BENCH_MODELS=qwen2.5-coder:3b PYTHONPATH=. /tmp/scv/bin/python bench/run_exec.py
```
