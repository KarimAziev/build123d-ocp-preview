from pathlib import Path

import pytest

from build123d_ocp_preview.config import create_app_config, load_project_config


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
    assert config.ignored_paths == ()


def test_resolves_cli_ignored_paths_relative_to_project(tmp_path: Path) -> None:
    entry = tmp_path / "assembly.py"
    entry.write_text("print('ok')\n", encoding="utf-8")

    config = create_app_config(
        project_arg=str(tmp_path),
        entry_args=["assembly.py"],
        port=3939,
        debounce_ms=250,
        initial_run=True,
        ignore_args=["picar_cad/temp.py"],
    )

    assert config.ignored_paths == ((tmp_path / "picar_cad" / "temp.py").resolve(),)


def test_load_project_config_reads_ignore_list(tmp_path: Path) -> None:
    config_file = tmp_path / "ocp123d.toml"
    config_file.write_text(
        'ignore = ["picar_cad/temp.py", "generated.py"]\n',
        encoding="utf-8",
    )

    config = load_project_config(config_file)

    assert config.ignore == ("picar_cad/temp.py", "generated.py")


def test_create_app_config_merges_config_and_cli_ignores(tmp_path: Path) -> None:
    entry = tmp_path / "assembly.py"
    entry.write_text("print('ok')\n", encoding="utf-8")
    config_file = tmp_path / "ocp123d.toml"
    config_file.write_text('ignore = ["from_config.py"]\n', encoding="utf-8")

    config = create_app_config(
        project_arg=str(tmp_path),
        entry_args=["assembly.py"],
        port=3939,
        debounce_ms=250,
        initial_run=True,
        ignore_args=["from_cli.py"],
        config_arg=str(config_file),
    )

    assert config.ignored_paths == (
        (tmp_path / "from_config.py").resolve(),
        (tmp_path / "from_cli.py").resolve(),
    )


def test_load_project_config_rejects_invalid_ignore_type(tmp_path: Path) -> None:
    config_file = tmp_path / "ocp123d.toml"
    config_file.write_text("ignore = true\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ignore must be a list of strings"):
        load_project_config(config_file)


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
