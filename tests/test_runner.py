import os
import sys
from pathlib import Path

from build123d_ocp_preview.config import AppConfig
from build123d_ocp_preview.runner import (
    build_child_environment,
    build_entry_command,
    run_entries,
)


def test_build_child_environment_prepends_project_pythonpath(tmp_path: Path) -> None:
    env = build_child_environment(
        project_dir=tmp_path,
        port=3940,
        base_env={"PYTHONPATH": "/existing", "KEEP": "yes"},
    )

    assert env["PYTHONPATH"] == f"{tmp_path}{os.pathsep}/existing"
    assert env["OCP_PORT"] == "3940"
    assert env["KEEP"] == "yes"


def test_run_entries_uses_fresh_import_graph(tmp_path: Path) -> None:
    project = tmp_path / "project"
    package = project / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text("from pkg.b import value_from_b\n", encoding="utf-8")
    (package / "b.py").write_text(
        "from pkg.c import VALUE\n\ndef value_from_b() -> str:\n    return VALUE\n",
        encoding="utf-8",
    )
    c_module = package / "c.py"
    c_module.write_text("VALUE = 'first'\n", encoding="utf-8")
    entry = project / "assembly.py"
    entry.write_text(
        "from pkg.a import value_from_b\nprint(value_from_b())\n",
        encoding="utf-8",
    )
    config = AppConfig(
        project_dir=project,
        entries=(entry,),
        port=3939,
        debounce_seconds=0.0,
        initial_run=True,
        python_executable=Path(sys.executable),
    )

    first = run_entries(config)
    c_module.write_text("VALUE = 'second'\n", encoding="utf-8")
    second = run_entries(config)

    assert first[0].returncode == 0
    assert "first" in first[0].stdout
    assert second[0].returncode == 0
    assert "second" in second[0].stdout


def test_build_entry_command_uses_runner_child_module(tmp_path: Path) -> None:
    entry = tmp_path / "assembly.py"

    assert build_entry_command(Path("/python"), 3940, entry) == [
        "/python",
        "-m",
        "build123d_ocp_preview.runner_child",
        "3940",
        str(entry),
    ]
