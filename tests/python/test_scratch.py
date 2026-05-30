"""Unit tests for simplicio.scratch — schema, registry, executor stub mode."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from simplicio.scratch.plan_schema import (
    EXAMPLE_PLAN,
    PlanValidationError,
    validate_plan,
)
from simplicio.scratch.stack_registry import Stack, StackRegistry, slugify_project


# ----- plan_schema ----- #


def test_example_plan_validates() -> None:
    plan = validate_plan(EXAMPLE_PLAN)
    assert plan.project_name == "condo-mgmt"
    assert plan.estimated_total_tasks == len(plan.tasks)


def test_rejects_bad_project_slug() -> None:
    bad = {**EXAMPLE_PLAN, "project_name": "Bad-CASE"}
    with pytest.raises(PlanValidationError) as exc:
        validate_plan(bad)
    assert any("project_name" in e for e in exc.value.errors)


def test_rejects_missing_required_field() -> None:
    bad = {k: v for k, v in EXAMPLE_PLAN.items() if k != "tasks"}
    with pytest.raises(PlanValidationError) as exc:
        validate_plan(bad)
    assert any("tasks missing" in e for e in exc.value.errors)


def test_rejects_estimated_count_mismatch() -> None:
    bad = {**EXAMPLE_PLAN, "estimated_total_tasks": 42}
    with pytest.raises(PlanValidationError) as exc:
        validate_plan(bad)
    assert any("estimated_total_tasks" in e for e in exc.value.errors)


def test_rejects_unknown_depends_on() -> None:
    bad = {
        **EXAMPLE_PLAN,
        "tasks": [{**EXAMPLE_PLAN["tasks"][0], "depends_on": ["T99-ghost"]}],
    }
    with pytest.raises(PlanValidationError) as exc:
        validate_plan(bad)
    assert any("ghost" in e for e in exc.value.errors)


def test_rejects_duplicate_task_id() -> None:
    bad = {
        **EXAMPLE_PLAN,
        "tasks": [EXAMPLE_PLAN["tasks"][0], EXAMPLE_PLAN["tasks"][0]],
        "estimated_total_tasks": 2,
    }
    with pytest.raises(PlanValidationError) as exc:
        validate_plan(bad)
    assert any("duplicated" in e for e in exc.value.errors)


def test_accepts_optional_required_skill_on_task() -> None:
    raw = {
        **EXAMPLE_PLAN,
        "tasks": [
            {
                **EXAMPLE_PLAN["tasks"][0],
                "required_skill": "Create Liquibase migrations safely",
            }
        ],
    }

    plan = validate_plan(raw)

    assert plan.tasks[0].required_skill == "Create Liquibase migrations safely"


def test_rejects_non_string_required_skill() -> None:
    raw = {
        **EXAMPLE_PLAN,
        "tasks": [
            {
                **EXAMPLE_PLAN["tasks"][0],
                "required_skill": ["liquibase"],
            }
        ],
    }

    with pytest.raises(PlanValidationError) as exc:
        validate_plan(raw)

    assert any("required_skill" in e for e in exc.value.errors)


# ----- stack_registry ----- #


def test_registry_lists_pilot_stacks() -> None:
    reg = StackRegistry()
    slugs = {s.slug for s in reg.list()}
    assert "py-fastapi" in slugs
    assert "ts-nextjs" in slugs
    assert "go-gin" in slugs
    assert "rust-axum" in slugs
    assert "php-laravel" in slugs


def test_registry_loads_full_metadata() -> None:
    reg = StackRegistry()
    py = reg.get("py-fastapi")
    assert py is not None
    assert py.language.startswith("Python")
    assert py.test_command == "pytest -q"
    assert py.install_command == "python3 -m pip install -e .[dev]"
    assert py.readme.startswith("# py-fastapi")
    assert "best practices" in py.practices.lower()


def test_registry_filters_by_tag() -> None:
    reg = StackRegistry()
    web_stacks = {s.slug for s in reg.by_tags(["web"])}
    assert "py-fastapi" in web_stacks
    assert "ts-nextjs" in web_stacks
    assert "go-gin" in web_stacks
    assert "rust-axum" in web_stacks
    assert "php-laravel" in web_stacks


def test_registry_loads_go_gin_stack_metadata() -> None:
    reg = StackRegistry()
    stack = reg.get("go-gin")
    assert stack is not None
    assert stack.language.startswith("Go")
    assert stack.framework == "Gin"
    assert stack.install_command == "go mod download"
    assert stack.test_command == "go test ./..."
    assert "best practices" in stack.practices.lower()


def test_registry_loads_rust_axum_stack_metadata() -> None:
    reg = StackRegistry()
    stack = reg.get("rust-axum")
    assert stack is not None
    assert stack.language.startswith("Rust")
    assert stack.framework == "Axum"
    assert stack.install_command == "cargo fetch"
    assert stack.test_command == "cargo test"
    assert "best practices" in stack.practices.lower()


def test_registry_loads_php_laravel_stack_metadata() -> None:
    reg = StackRegistry()
    stack = reg.get("php-laravel")
    assert stack is not None
    assert stack.language.startswith("PHP")
    assert stack.framework == "Laravel"
    assert stack.install_command == "composer install"
    assert stack.test_command == "php artisan test"
    assert "best practices" in stack.practices.lower()


def test_rust_axum_stack_renders_cargo_project_name() -> None:
    reg = StackRegistry()
    stack = reg.get("rust-axum")
    assert stack is not None

    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "out"
        written = stack.render_tree(dest, {"project_name": "demo-api"})

        assert (dest / "Cargo.toml").is_file()
        assert (dest / "src/main.rs").is_file()
        assert (
            (dest / "Cargo.toml")
            .read_text(encoding="utf-8")
            .startswith('[package]\nname = "demo-api"')
        )
        assert any(path.name == "main.rs" for path in written)


def test_php_laravel_stack_renders_composer_project_name() -> None:
    reg = StackRegistry()
    stack = reg.get("php-laravel")
    assert stack is not None

    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "out"
        written = stack.render_tree(dest, {"project_name": "demo-api"})

        assert (dest / "composer.json").is_file()
        assert (dest / "routes/api.php").is_file()
        assert '"name": "simplicio/demo-api"' in (dest / "composer.json").read_text(
            encoding="utf-8"
        )
        assert any(path.name == "HealthTest.php" for path in written)


def test_stack_render_tree_ignores_tool_cache_dirs() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "stack"
        tree = root / "tree"
        (tree / ".ruff_cache" / "0.15.13").mkdir(parents=True)
        (tree / ".ruff_cache" / "0.15.13" / "cache").write_bytes(b"\xff\xfe")
        (tree / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
        (tree / "README.md").write_text("# {project_name}\n", encoding="utf-8")

        dest = Path(td) / "out"
        stack = Stack(slug="test", path=root)
        written = stack.render_tree(dest, {"project_name": "demo"})

        assert sorted(p.relative_to(dest).as_posix() for p in written) == [
            ".gitignore",
            "README.md",
        ]
        assert (dest / "README.md").read_text(encoding="utf-8") == "# demo\n"
        assert not (dest / ".ruff_cache").exists()


def test_slugify_project_normalizes_name() -> None:
    assert slugify_project("Condo Mgmt App!") == "condo-mgmt-app"
    assert slugify_project("  ") == "scratch-project"
    assert slugify_project("123-num-only").startswith("p-")  # must start with letter


def test_generate_plan_passes_stack_template_version(monkeypatch) -> None:
    from simplicio.scratch import planner as planner_module

    seen = {}
    stack = Stack(
        slug="custom-stack",
        path=Path("."),
        meta={
            "language": "Python",
            "framework": "FastAPI",
            "template_version": "stack-v1",
        },
        readme="Custom stack readme",
        practices="Custom stack practices",
        verify={"test_runner": "pytest"},
    )
    plan_payload = {
        **EXAMPLE_PLAN,
        "stack": "custom-stack",
        "project_name": "cached-plan",
    }

    def fake_planner_complete(prompt, **kwargs):
        seen["prompt"] = prompt
        seen.update(kwargs)
        return json.dumps(plan_payload)

    monkeypatch.setattr(planner_module, "planner_complete", fake_planner_complete)

    plan = planner_module.generate_plan(
        stack,
        "Build a uniquely named planner-cache fixture",
        "cached-plan",
    )

    assert plan.project_name == "cached-plan"
    assert seen["template_version"] == "stack-v1"


# ----- executor stub mode ----- #


def test_executor_scaffolds_tree_in_stub_mode() -> None:
    """Without SIMPLICIO_MODEL, executor still scaffolds the tree, runs install
    (if not skipped), and logs each task as skipped. Used by smoke tests in CI
    that don't have an LLM key."""
    reg = StackRegistry()
    stack = reg.get("py-fastapi")
    assert stack is not None
    plan = validate_plan(EXAMPLE_PLAN)

    # ensure no SIMPLICIO_MODEL leak from the test runner
    prev = os.environ.pop("SIMPLICIO_MODEL", None)
    try:
        with tempfile.TemporaryDirectory() as td:
            from simplicio.scratch.executor import execute_plan

            report = execute_plan(plan, stack, Path(td), skip_install=True)
            assert report.project_dir.exists()
            assert report.project_dir.name == "condo-mgmt"
            assert len(report.files_written) > 0
            assert (report.project_dir / ".simplicio" / "plan.json").is_file()
            assert (report.project_dir / "pyproject.toml").is_file()
            # tasks in stub mode are recorded but not passed
            assert report.tasks_total == 1
            assert report.tasks_passed == 0
            assert report.metrics["tasks_skipped"] == 1
            assert report.metrics["codegen_share"] == 0.0
            assert report.task_results[0].skipped_reason is not None
    finally:
        if prev is not None:
            os.environ["SIMPLICIO_MODEL"] = prev


def test_executor_report_records_codegen_metrics() -> None:
    reg = StackRegistry()
    stack = reg.get("ts-nextjs")
    assert stack is not None
    plan = validate_plan(
        {
            **EXAMPLE_PLAN,
            "stack": "ts-nextjs",
            "project_name": "next-api",
            "tasks": [
                {
                    "id": "T01-next-route",
                    "depends_on": [],
                    "goal": "Create Next.js route handlers for Unit CRUD",
                    "target": "src/app/api/units/route.ts",
                    "criteria": "- exports GET and POST handlers\n- returns JSON",
                    "constraints": "- use deterministic codegen",
                    "verify": "pnpm vitest run",
                }
            ],
            "estimated_total_tasks": 1,
        }
    )

    with tempfile.TemporaryDirectory() as td:
        from simplicio.scratch.executor import execute_plan

        report = execute_plan(plan, stack, Path(td), skip_install=True)
        data = report.to_dict()

        assert report.metrics["tasks_codegen"] == 1
        assert report.metrics["codegen_share"] == 1.0
        assert data["tasks"][0]["execution_mode"] == "codegen"
        assert data["tasks"][0]["codegen_executor"] == "typescript-add-next-route"
        assert (report.project_dir / "src/app/api/units/route.ts").is_file()


def test_executor_refuses_existing_project_dir() -> None:
    reg = StackRegistry()
    stack = reg.get("py-fastapi")
    plan = validate_plan(EXAMPLE_PLAN)
    with tempfile.TemporaryDirectory() as td:
        existing = Path(td) / plan.project_name
        existing.mkdir()
        from simplicio.scratch.executor import execute_plan

        with pytest.raises(FileExistsError):
            execute_plan(plan, stack, Path(td), skip_install=True)
