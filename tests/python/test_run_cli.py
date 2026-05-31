import json
import sys

from simplicio import cli


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _diff(path):
    return "\n".join(
        [
            f"diff --git a/{path} b/{path}",
            f"--- a/{path}",
            f"+++ b/{path}",
            "@@ -1 +1 @@",
            "-old",
            "+new",
            "",
            "TEST:",
            "assert True",
        ]
    )


def _true_cmd():
    return f'"{sys.executable}" -c "raise SystemExit(0)"'


def test_run_scope_task_preserves_task_json_contract(tmp_path, monkeypatch, capsys):
    _write(tmp_path / "frontend" / "app.ts", "old\n")
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")
    monkeypatch.setenv("SIMPLICIO_TEST_CMD", _true_cmd())
    monkeypatch.setattr(
        "simplicio.pipeline.generate", lambda *a, **k: _diff("frontend/app.ts")
    )

    code = cli.main(
        [
            "run",
            "update frontend/app.ts",
            "--scope",
            "task",
            "--root",
            str(tmp_path),
            "--target",
            "frontend/app.ts",
            "--json",
        ]
    )

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["applied"] is True
    assert payload["files_changed"] == ["frontend/app.ts"]
    assert "scope" not in payload


def test_run_auto_task_infers_target_from_goal(tmp_path, monkeypatch, capsys):
    _write(tmp_path / "src" / "auth.py", "old\n")
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")
    monkeypatch.setattr("simplicio.pipeline.generate", lambda *a, **k: _diff("src/auth.py"))

    code = cli.main(
        [
            "run",
            "fix bug in src/auth.py",
            "--root",
            str(tmp_path),
            "--dry-run-task",
            "--json",
        ]
    )

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["task_id"] == "src/auth.py"


def test_run_ambiguous_goal_requires_scope(monkeypatch, capsys):
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")

    code = cli.main(["run", "maybe later"])

    assert code == 2
    assert "goal is ambiguous" in capsys.readouterr().err


def test_run_scope_scratch_forwards_to_scratch_cli(monkeypatch):
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")
    seen = {}

    def fake_scratch_main(argv):
        seen["argv"] = argv
        return 0

    monkeypatch.setattr("simplicio.scratch.cli.main", fake_scratch_main)

    code = cli.main(
        [
            "run",
            "scaffold a new FastAPI project from scratch",
            "--scope",
            "scratch",
            "--stack",
            "py-fastapi",
            "--plan-only",
            "--json",
        ]
    )

    assert code == 0
    assert seen["argv"] == [
        "scaffold a new FastAPI project from scratch",
        "--stack",
        "py-fastapi",
        "--dest",
        ".",
        "--plan-only",
        "--json",
    ]


def test_run_scope_feature_outputs_orchestrator_result(monkeypatch, capsys):
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")

    def fake_run_feature(**kwargs):
        assert kwargs["stack_slug"] == "py-fastapi"
        return {
            "scope": "feature",
            "goal": kwargs["goal"],
            "stack": "py-fastapi",
            "applied": True,
            "tasks": [{"id": "T01-a", "passed": True}],
            "replans": 0,
            "warnings": [],
        }

    monkeypatch.setattr("simplicio.orchestrator.run_feature", fake_run_feature)

    code = cli.main(
        [
            "run",
            "implement JWT login flow",
            "--scope",
            "feature",
            "--stack",
            "py-fastapi",
            "--json",
        ]
    )

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["scope"] == "feature"
    assert payload["applied"] is True


def test_run_scope_sprint_requires_max_cost(monkeypatch, capsys):
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")

    code = cli.main(
        [
            "run",
            "finish sprint 1",
            "--scope",
            "sprint",
            "--stack",
            "py-fastapi",
        ]
    )

    assert code == 2
    assert "requires --max-cost" in capsys.readouterr().err
