import sys

from simplicio.dod import parse_dod, run_dod_gates
from simplicio.sprint_loader import load_sprint


def test_load_sprint_reads_task_goals(tmp_path):
    sprint_dir = tmp_path / ".specs" / "sprints" / "sprint-01"
    sprint_dir.mkdir(parents=True)
    (sprint_dir / "SPRINT.md").write_text("# Sprint 01\n", encoding="utf-8")
    (sprint_dir / "01-login.task.md").write_text(
        "# Login\n\n## Goal\nImplement login flow\n\n## Notes\nx",
        encoding="utf-8",
    )

    sprint = load_sprint(tmp_path, "sprint-01")

    assert sprint.title == "Sprint 01"
    assert len(sprint.tasks) == 1
    assert sprint.tasks[0].title == "Login"
    assert sprint.tasks[0].goal == "Implement login flow"


def test_parse_and_run_dod_command_gate(tmp_path):
    command = f'"{sys.executable}" -c "raise SystemExit(0)"'
    gates = parse_dod(f"- [ ] Unit tests pass (`{command}`)\n- [ ] Evidence attached\n")

    assert [gate.command for gate in gates] == [command, None]
    results = run_dod_gates(tmp_path, gates)
    assert [row["passed"] for row in results] == [True, True]
