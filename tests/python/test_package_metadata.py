import tomllib
from pathlib import Path

from simplicio import __version__


def test_package_version_matches_release_metadata() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["version"] == "0.4.4"
    assert __version__ == project["version"]


def test_simplicio_ecosystem_dependency_floors_are_current() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert "simplicio-mapper>=0.6.1" in project["dependencies"]
    assert "simplicio-prompt>=1.12.0" in project["dependencies"]
