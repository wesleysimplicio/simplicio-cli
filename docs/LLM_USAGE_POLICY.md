# Official LLM Usage Policy — Simplicio Ecosystem

**Status:** Official default (2026-05-31)

## Core Principle

- **Planning** (task decomposition, architecture decisions, high-level reasoning) → High-intelligence remote model
- **Execution** (writing code, applying changes, following a plan) → Fast, deterministic local model with strong contract + mapper context

## Default Configuration

### Planning
- Primary: **DeepSeek V4 Pro** (via Hugging Face or compatible router)
- Used for: `simplicio scratch --plan`, planner phase in SimplicioCode, high-level sprint analysis in simplicio-sprint

### Execution (Local)
- Primary local executor: **Qwen2.5-Coder-1.5B-Instruct-Q8_0.gguf**
- Fallback local executor: **Qwen2.5-Coder-1.5B-Instruct-Q6_K_L.gguf**

These GGUF files should be used via llama.cpp / llama-cpp-python (not the default Ollama tag) when maximum determinism and instruction following on the 1.5B class is required.

## Project-Specific Rules

### simplicio-code (mandatory)
- On project bootstrap / SessionStart / first run in a new workspace:
  - The system **must** verify that the local executor models (Q8_0 + Q6_K_L) are present.
  - If missing, it **must** download them before allowing agent execution.
- This is a hard requirement for the SimplicioCode product.

### simplicio-dev-cli and simplicio-sprint (recommended)
- The above split (DeepSeek for planning + Q8_0/Q6_K_L for execution) is the **recommended** configuration for local development.
- Not enforced at runtime, but all examples, benchmarks, and documentation use this setup.

## Rationale

From extensive benchmarking (see `simplicio-dev-cli` quant curves and live gates):
- Even the best 1.5B model struggles with complex structured output on its own.
- When combined with rich mapper precedent + strict 6-layer contract + verification loop, the small high-quant model becomes extremely effective and predictable for execution.
- Planning benefits much more from raw intelligence → use the best available remote model.

## How to Configure

```bash
# Planning (high intelligence)
export SIMPLICIO_PLANNER=deepseek-v4-pro
export HF_TOKEN=...          # or appropriate key

# Execution (local, deterministic)
export SIMPLICIO_MODEL=local-llama/qwen2.5-coder-1.5b-q8_0
# Fallback
export SIMPLICIO_EXECUTOR_FALLBACK=local-llama/qwen2.5-coder-1.5b-q6_k_l
```

In SimplicioCode the equivalent is done via the Simplicio1 tier system + explicit GGUF routing for the executor role.


## Default Usage Mode for simplicio-dev-cli

**Official default stack (recommended for all users):**

```bash
simplicio-dev-cli + simplicio-prompt + agents
```

- `simplicio-dev-cli`: core 6-layer contract + verification loop for task execution.
- `simplicio-prompt`: subagent runtime + fan-out + behavior consensus for complex or parallel work.
- `agents` / `.skills/` + `.agents/`: reusable skills and custom sub-agents from the Simplicio starter.

This combination is the **recommended and documented default** when using `simplicio-dev-cli`. All new examples, benchmarks, and onboarding materials assume this full stack.

When starting a new project with the Simplicio starter, the bootstrap configures the environment to use this trio by default.

