from pathlib import Path

from build123d_ocp_preview.filtering import should_handle_path


def test_handles_python_file_under_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    module = project / "pkg" / "part.py"
    module.parent.mkdir()
    module.write_text("VALUE = 1\n", encoding="utf-8")

    assert should_handle_path(project, module) is True


def test_ignores_non_python_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    readme = project / "README.md"
    readme.write_text("# docs\n", encoding="utf-8")

    assert should_handle_path(project, readme) is False


def test_ignores_noisy_directories(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    for dirname in (".git", ".venv", "venv", "__pycache__", ".ruff_cache"):
        path = project / dirname / "ignored.py"
        path.parent.mkdir()
        path.write_text("VALUE = 1\n", encoding="utf-8")
        assert should_handle_path(project, path) is False


def test_ignores_path_outside_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside.py"
    project.mkdir()
    outside.write_text("VALUE = 1\n", encoding="utf-8")

    assert should_handle_path(project, outside) is False
