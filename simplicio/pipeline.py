"""pipeline.py — build -> generate -> validate -> test -> fix (loop)."""
from dataclasses import dataclass
import os, re, subprocess
from .observability import estimate_tokens, log_run
from .prompt import build_prompt
from .providers import generate

MAX_ATTEMPTS = 3

@dataclass
class ValidationResult:
    ok: bool
    reason: str
    hints: list[str]

@dataclass
class FailureClassification:
    kind: str
    guidance: str

def validate_generated_output(output):
    text = output or ""
    hints = []
    has_diff = bool(re.search(r"^diff --git |^--- .+\n\+\+\+ ", text, flags=re.M))
    has_test = "TEST:" in text or re.search(r"(^|\n)(test|it|def test_|describe)\b", text)
    if not has_diff:
        hints.append("include a unified diff with exact target files")
    if not has_test:
        hints.append("include a TEST block or concrete test code")
    if re.search(r"(?i)\b(pseudocode|placeholder|todo: implement)\b", text):
        hints.append("replace placeholders with executable code")
    return ValidationResult(
        ok=not hints,
        reason="ok" if not hints else "; ".join(hints),
        hints=hints,
    )

def classify_failure(log):
    text = (log or "").lower()
    if "syntaxerror" in text or "unexpected token" in text or "parse error" in text:
        return FailureClassification("syntax", "Fix syntax first; keep the patch minimal and rerun the same test.")
    if "assertionerror" in text or "expected" in text and "actual" in text:
        return FailureClassification("assertion", "The test ran but behavior is wrong; inspect the asserted contract and adjust logic.")
    if "modulenotfound" in text or "no module named" in text or "cannot find module" in text:
        return FailureClassification("dependency", "Use existing project dependencies or correct imports; do not invent packages.")
    if "timeout" in text or "timed out" in text:
        return FailureClassification("timeout", "Reduce scope, avoid long-running work, and make the verification deterministic.")
    if "traceback" in text or "exception" in text or "typeerror" in text or "referenceerror" in text:
        return FailureClassification("runtime", "Fix the runtime exception at the reported callsite.")
    return FailureClassification("unknown", "Re-read the mapper context and produce a smaller, directly testable diff.")

def build_retry_feedback(attempt, validation=None, test_log=""):
    classification = classify_failure(test_log)
    lines = [
        f"Retry feedback for attempt {attempt}:",
        f"failure_class={classification.kind}",
        classification.guidance,
    ]
    if validation and not validation.ok:
        lines.append(f"pre-apply validation failed: {validation.reason}")
    if test_log:
        lines.append("test/runtime tail:")
        lines.append(test_log[-1600:])
    lines.append("Return the full corrected DIFF + TEST block only.")
    return "\n".join(lines)

def _apply_and_test(output, root):
    os.makedirs(os.path.join(root, ".simplicio"), exist_ok=True)
    open(os.path.join(root, ".simplicio/last_output.txt"), "w").write(output or "")
    validation = validate_generated_output(output)
    if not validation.ok:
        return False, f"pre-apply validation failed: {validation.reason}"
    # PLUG: extract diff -> git apply; extract test. Here we run the test command.
    cmd = os.environ.get("SIMPLICIO_TEST_CMD", "echo 'configure SIMPLICIO_TEST_CMD'")
    p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr)[-2000:]

def run(root, stack, goal, target, criteria, constraints):
    prompt = build_prompt(root, stack, goal, target, criteria, constraints)
    feedback = None
    for t in range(1, MAX_ATTEMPTS + 1):
        print(f"--- attempt {t} (provider={os.environ.get('SIMPLICIO_PROVIDER','claude')}) ---")
        output = generate(prompt, feedback)
        ok, log = _apply_and_test(output, root)
        log_run(root, {
            "mode": "pipeline",
            "attempt": t,
            "ok": ok,
            "failure_class": "none" if ok else classify_failure(log).kind,
            "tokens_estimated": estimate_tokens(prompt) + estimate_tokens(output),
            "target": target,
            "stack": stack,
        })
        if ok:
            print("PASSED the contract. DONE.")
            return output
        print("failed:", log[:300])
        feedback = build_retry_feedback(t + 1, validate_generated_output(output), log)
    print("attempts exhausted — manual review needed.")
    return None
