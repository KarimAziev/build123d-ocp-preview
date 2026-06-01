from pathlib import Path

from build123d_ocp_preview.cli import parse_args


def test_parse_args_uses_defaults(tmp_path: Path) -> None:
    entry = tmp_path / "assembly.py"
    entry.write_text("print('ok')\n", encoding="utf-8")

    config = parse_args(["--project", str(tmp_path), "assembly.py"])

    assert config.project_dir == tmp_path.resolve()
    assert config.entries == (entry.resolve(),)
    assert config.port == 3939
    assert config.debounce_seconds == 0.25
    assert config.initial_run is True
    assert config.open_viewer is True


def test_parse_args_accepts_multiple_entries_and_options(tmp_path: Path) -> None:
    first = tmp_path / "assembly.py"
    second = tmp_path / "other.py"
    first.write_text("print('first')\n", encoding="utf-8")
    second.write_text("print('second')\n", encoding="utf-8")

    config = parse_args(
        [
            "--project",
            str(tmp_path),
            "--port",
            "3941",
            "--debounce-ms",
            "100",
            "--ignore",
            "ignored.py",
            "--no-initial-run",
            "assembly.py",
            "other.py",
        ]
    )

    assert config.entries == (first.resolve(), second.resolve())
    assert config.port == 3941
    assert config.debounce_seconds == 0.1
    assert config.initial_run is False
    assert config.ignored_paths == ((tmp_path / "ignored.py").resolve(),)


def test_parse_args_accepts_short_aliases(tmp_path: Path) -> None:
    entry = tmp_path / "assembly.py"
    entry.write_text("print('ok')\n", encoding="utf-8")
    config_file = tmp_path / "ocp123d.toml"
    config_file.write_text('ignore = ["from_config.py"]\n', encoding="utf-8")

    config = parse_args(
        [
            "-p",
            str(tmp_path),
            "-o",
            "3942",
            "-d",
            "150",
            "-i",
            "from_cli.py",
            "-c",
            str(config_file),
            "-n",
            "--no-open",
            "assembly.py",
        ]
    )

    assert config.port == 3942
    assert config.debounce_seconds == 0.15
    assert config.initial_run is False
    assert config.open_viewer is False
    assert config.ignored_paths == (
        (tmp_path / "from_config.py").resolve(),
        (tmp_path / "from_cli.py").resolve(),
    )
