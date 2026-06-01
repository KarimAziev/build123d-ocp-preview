from pathlib import Path

import pytest

from build123d_ocp_preview.config import create_app_config


def test_resolves_project_relative_entries(tmp_path: Path) -> None:
    project = tmp_path / "cad"
    project.mkdir()
    entry = project / "assembly.py"
    entry.write_text("print('ok')\n", encoding="utf-8")

    config = create_app_config(
        project_arg=str(project),
        entry_args=["assembly.py"],
        port=3939,
        debounce_ms=250,
        initial_run=True,
    )

    assert config.project_dir == project.resolve()
    assert config.entries == (entry.resolve(),)
    assert config.port == 3939
    assert config.debounce_seconds == 0.25
    assert config.initial_run is True


def test_rejects_missing_project(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Project directory does not exist"):
        create_app_config(
            project_arg=str(tmp_path / "missing"),
            entry_args=["assembly.py"],
            port=3939,
            debounce_ms=250,
            initial_run=True,
        )


def test_rejects_empty_entries(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="At least one entry file"):
        create_app_config(
            project_arg=str(tmp_path),
            entry_args=[],
            port=3939,
            debounce_ms=250,
            initial_run=True,
        )


def test_rejects_missing_entry(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Entry file does not exist"):
        create_app_config(
            project_arg=str(tmp_path),
            entry_args=["missing.py"],
            port=3939,
            debounce_ms=250,
            initial_run=True,
        )


def test_rejects_invalid_port(tmp_path: Path) -> None:
    entry = tmp_path / "assembly.py"
    entry.write_text("print('ok')\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Port must be"):
        create_app_config(
            project_arg=str(tmp_path),
            entry_args=["assembly.py"],
            port=70000,
            debounce_ms=250,
            initial_run=True,
        )
