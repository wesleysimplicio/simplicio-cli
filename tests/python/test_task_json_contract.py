import json

from simplicio import cli


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _diff(path):
    return "\n".join([
        f"diff --git a/{path} b/{path}",
        f"--- a/{path}",
        f"+++ b/{path}",
        "@@ -1 +1 @@",
        "-old",
        "+new",
        "",
        "TEST:",
        "assert True",
    ])


def test_task_dry_run_json_does_not_touch_worktree(tmp_path, monkeypatch, capsys):
    _write(tmp_path / "frontend" / "app.ts", "old\n")
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")
    monkeypatch.setattr("simplicio.pipeline.generate", lambda *a, **k: _diff("frontend/app.ts"))

    code = cli.main([
        "task",
        "update app",
        "--root",
        str(tmp_path),
        "--stack",
        "angular",
        "--target",
        "frontend/app.ts",
        "--dry-run-task",
        "--json",
    ])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["task_id"] == "frontend/app.ts"
    assert payload["applied"] is False
    assert payload["files_changed"] == ["frontend/app.ts"]
    assert payload["tokens_used"]["prompt"] > 0
    assert payload["tokens_used"]["completion"] > 0
    assert payload["cost_usd"] == 0.0
    assert payload["warnings"] == []
    assert not (tmp_path / ".simplicio" / "last_output.txt").exists()
    assert (tmp_path / "frontend" / "app.ts").read_text(encoding="utf-8") == "old\n"


def test_task_json_reports_normal_run(tmp_path, monkeypatch, capsys):
    _write(tmp_path / "frontend" / "app.ts", "old\n")
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")
    monkeypatch.setenv("SIMPLICIO_TEST_CMD", "true")
    monkeypatch.setattr("simplicio.pipeline.generate", lambda *a, **k: _diff("frontend/app.ts"))

    code = cli.main([
        "task",
        "update app",
        "--root",
        str(tmp_path),
        "--stack",
        "angular",
        "--target",
        "frontend/app.ts",
        "--json",
    ])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["applied"] is True
    assert payload["files_changed"] == ["frontend/app.ts"]
    assert "frontend/app.ts" in payload["diff_summary"]
    assert payload["warnings"] == []
    assert (tmp_path / ".simplicio" / "last_output.txt").exists()


def test_task_bound_paths_refuses_out_of_scope_diff(tmp_path, monkeypatch, capsys):
    _write(tmp_path / "frontend" / "app.ts", "old\n")
    _write(tmp_path / "backend" / "app.ts", "old\n")
    monkeypatch.setenv("SIMPLICIO_SKIP_AUTO_INIT", "1")
    monkeypatch.setenv("SIMPLICIO_TEST_CMD", "true")
    monkeypatch.setattr("simplicio.pipeline.generate", lambda *a, **k: _diff("backend/app.ts"))

    code = cli.main([
        "task",
        "update app",
        "--root",
        str(tmp_path),
        "--stack",
        "angular",
        "--target",
        "frontend/app.ts",
        "--bound-paths",
        "frontend/**",
        "--json",
    ])

    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["applied"] is False
    assert payload["files_changed"] == ["backend/app.ts"]
    assert any("outside bound paths" in warning for warning in payload["warnings"])
