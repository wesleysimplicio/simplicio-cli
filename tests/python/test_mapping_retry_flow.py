import json

from simplicio import bench
from simplicio import pipeline
from simplicio import prompt as prompt_module
from simplicio.pipeline_fixers import FixerResult
from simplicio.precedent import build_precedent_block


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_mapper_consumes_project_map_and_precedent_index(tmp_path):
    target = tmp_path / "src" / "app.py"
    target.parent.mkdir(parents=True)
    target.write_text("from service import run\n\nrun()\n", encoding="utf-8")
    write_json(
        tmp_path / ".simplicio" / "project-map.json",
        {
            "schema": "simplicio.project-map/v1",
            "generated_at": "2026-05-27T00:00:00Z",
            "files": [
                {
                    "path": "src/app.py",
                    "language": "python",
                    "importance": 0.91,
                    "roles": ["entrypoint"],
                    "imports": ["service"],
                    "exports": ["run"],
                },
                {
                    "path": "tests/test_app.py",
                    "language": "python",
                    "importance": 0.72,
                    "roles": ["test"],
                },
            ],
            "entry_points": ["src/app.py"],
            "test_files": ["tests/test_app.py"],
            "architecture": {"signals": ["cli", "service-layer"]},
            "modules": [{"name": "src", "files": ["src/app.py"]}],
            "recent_changes": [{"path": "src/app.py", "status": "modified"}],
        },
    )
    write_json(
        tmp_path / ".simplicio" / "precedent-index.json",
        {
            "schema": "simplicio.precedent-index/v1",
            "items": [
                {
                    "path": "tests/test_app.py",
                    "line": 7,
                    "change_type": "test",
                    "summary": "Existing service-layer test",
                    "tags": ["service", "entrypoint"],
                    "snippet": "def test_run():\n    assert run() == 0",
                }
            ],
        },
    )

    block = prompt_module._mapper(
        str(tmp_path), "src/app.py", goal="update service test"
    )

    assert "project-map.json" in block
    assert "src/app.py" in block
    assert "tests/test_app.py" in block
    assert "service-layer" in block
    assert "Existing service-layer test" in block


def test_precedent_index_ranks_candidates_without_embedding(tmp_path):
    write_json(
        tmp_path / ".simplicio" / "precedent-index.json",
        {
            "items": [
                {
                    "path": "src/ui/Login.tsx",
                    "line": 12,
                    "change_type": "feature",
                    "summary": "Login guard checks permission before render",
                    "tags": ["react", "login", "permission"],
                    "snippet": "return can('login') && <Login />",
                },
                {
                    "path": "src/payments.ts",
                    "line": 3,
                    "summary": "Payment helper",
                    "tags": ["billing"],
                    "snippet": "export const pay = () => null",
                },
            ]
        },
    )

    block = build_precedent_block(str(tmp_path), "react", "fix login permission", k=1)

    assert "src/ui/Login.tsx:12" in block
    assert "Payment helper" not in block


def test_precedent_unknown_stack_falls_back_without_keyerror(tmp_path):
    block = build_precedent_block(
        str(tmp_path),
        "Python + FastAPI",
        "Add a FastAPI route",
        k=1,
    )

    assert "[PRECEDENT]" in block
    assert "no stack-specific precedent scanner" in block


def test_prompt_adds_model_adaptation_and_decomposition(tmp_path, monkeypatch):
    target = tmp_path / "src" / "feature.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setenv("SIMPLICIO_MODEL", "tiny-local")
    monkeypatch.setattr(
        prompt_module, "build_precedent_block", lambda *a, **k: "[PRECEDENT]\nnone"
    )
    monkeypatch.setattr(prompt_module, "build_skill_block", lambda *a, **k: "")

    rendered = prompt_module.build_prompt(
        str(tmp_path),
        "python",
        "Update mapper, add tests, and document the contract",
        "src/feature.py",
        "- tests pass",
        "- no new deps",
    )

    assert "[MODEL ADAPTATION]" in rendered
    assert "extra scaffolding" in rendered
    assert "[TASK DECOMPOSITION]" in rendered
    assert "1. Update mapper" in rendered


def test_retry_classification_and_pre_apply_validation():
    bad_output = "Here is a patch with no diff"
    assert pipeline.validate_generated_output(bad_output).ok is False
    assert pipeline.classify_failure("SyntaxError: invalid syntax").kind == "syntax"

    feedback = pipeline.build_retry_feedback(
        attempt=2,
        validation=pipeline.validate_generated_output(bad_output),
        test_log="AssertionError: expected 1 got 2",
    )

    assert "pre-apply validation failed" in feedback
    assert "assertion" in feedback
    assert "attempt 2" in feedback


def _valid_pipeline_diff():
    return "\n".join(
        [
            "diff --git a/src/app.py b/src/app.py",
            "--- a/src/app.py",
            "+++ b/src/app.py",
            "@@ -0,0 +1 @@",
            "+print('ok')",
            "",
            "TEST: pytest -q",
        ]
    )


def test_pipeline_static_fixer_skips_llm_retry_when_verify_passes(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SIMPLICIO_DISABLE_RUN_LOG", "1")
    generate_calls = []
    apply_calls = {"count": 0}

    def fake_generate(prompt, feedback=None):
        generate_calls.append(feedback)
        return _valid_pipeline_diff()

    def fake_apply_and_test(output, root, bound_paths=None):
        apply_calls["count"] += 1
        if apply_calls["count"] == 1:
            return False, "ModuleNotFoundError: No module named 'fastapi'"
        return True, "1 passed"

    monkeypatch.setattr(pipeline, "generate", fake_generate)
    monkeypatch.setattr(pipeline, "build_prompt", lambda *args, **kwargs: "prompt")
    monkeypatch.setattr(pipeline, "_apply_and_test", fake_apply_and_test)
    monkeypatch.setattr(
        pipeline,
        "try_static_fixers",
        lambda log, root: FixerResult("missing-pip-package", True, "installed fastapi"),
    )

    result = pipeline.run_task(
        str(tmp_path),
        "python",
        "add api",
        "src/app.py",
        "- passes",
        "- small",
        quiet=True,
    )

    assert result["applied"] is True
    assert len(generate_calls) == 1
    assert apply_calls["count"] == 2


def test_pipeline_retries_with_llm_when_static_fixer_does_not_resolve(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SIMPLICIO_DISABLE_RUN_LOG", "1")
    generate_calls = []
    apply_calls = {"count": 0}

    def fake_generate(prompt, feedback=None):
        generate_calls.append(feedback)
        return _valid_pipeline_diff()

    def fake_apply_and_test(output, root, bound_paths=None):
        apply_calls["count"] += 1
        if apply_calls["count"] == 1:
            return False, "ModuleNotFoundError: No module named 'fastapi'"
        if apply_calls["count"] == 2:
            return False, "AssertionError: still failing after fixer"
        return True, "1 passed"

    def fake_fixers(log, root):
        if "No module named" in log:
            return FixerResult("missing-pip-package", True, "installed fastapi")
        return FixerResult("none", False, "no static fixer matched")

    monkeypatch.setattr(pipeline, "generate", fake_generate)
    monkeypatch.setattr(pipeline, "build_prompt", lambda *args, **kwargs: "prompt")
    monkeypatch.setattr(pipeline, "_apply_and_test", fake_apply_and_test)
    monkeypatch.setattr(pipeline, "try_static_fixers", fake_fixers)

    result = pipeline.run_task(
        str(tmp_path),
        "python",
        "add api",
        "src/app.py",
        "- passes",
        "- small",
        quiet=True,
    )

    assert result["applied"] is True
    assert len(generate_calls) == 2
    assert generate_calls[1] is not None


def test_static_fixers_reduce_retry_calls_in_synthetic_pipeline_case(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SIMPLICIO_DISABLE_RUN_LOG", "1")

    def run_case(root, fixer_enabled):
        generate_calls = []
        apply_calls = {"count": 0}

        def fake_generate(prompt, feedback=None):
            generate_calls.append(feedback)
            return _valid_pipeline_diff()

        def fake_apply_and_test(output, run_root, bound_paths=None):
            apply_calls["count"] += 1
            if apply_calls["count"] == 1:
                return False, "ModuleNotFoundError: No module named 'fastapi'"
            return True, "1 passed"

        def fake_fixers(log, run_root):
            if fixer_enabled:
                return FixerResult("missing-pip-package", True, "installed fastapi")
            return FixerResult("none", False, "disabled for synthetic baseline")

        monkeypatch.setattr(pipeline, "generate", fake_generate)
        monkeypatch.setattr(pipeline, "build_prompt", lambda *args, **kwargs: "prompt")
        monkeypatch.setattr(pipeline, "_apply_and_test", fake_apply_and_test)
        monkeypatch.setattr(pipeline, "try_static_fixers", fake_fixers)
        pipeline.run_task(
            str(root),
            "python",
            "add api",
            "src/app.py",
            "- passes",
            "- small",
            quiet=True,
        )
        return len(generate_calls)

    baseline_calls = run_case(tmp_path / "baseline", fixer_enabled=False)
    fixer_calls = run_case(tmp_path / "fixer", fixer_enabled=True)

    assert baseline_calls == 2
    assert fixer_calls == 1
    assert (baseline_calls - fixer_calls) / baseline_calls >= 0.3


def test_benchmark_writes_observability_log(tmp_path, monkeypatch):
    cases = [
        {
            "goal": "avoid hallucinated files",
            "target": "src/app.py",
            "criteria": "- output captured",
            "constraints": "- no hallucinated paths",
            "test_cmd": "test -f .simplicio/bench_out.txt",
        }
    ]
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(json.dumps(cases), encoding="utf-8")
    monkeypatch.setattr(
        bench,
        "generate",
        lambda prompt, *args, **kwargs: "diff --git a/src/app.py b/src/app.py",
    )
    monkeypatch.setattr(
        bench, "build_prompt", lambda *args, **kwargs: "structured prompt"
    )
    monkeypatch.setenv("SIMPLICIO_PROMPT_VARIANT", "mapper-v1")

    bench.run_bench(str(tmp_path), "python", str(cases_path))

    run_log = tmp_path / ".simplicio" / "runs.jsonl"
    assert run_log.exists()
    events = [
        json.loads(line) for line in run_log.read_text(encoding="utf-8").splitlines()
    ]
    assert {event["mode"] for event in events} == {"baseline", "pipeline"}
    assert all(event["prompt_variant"] == "mapper-v1" for event in events)
    assert all("tokens_estimated" in event for event in events)
