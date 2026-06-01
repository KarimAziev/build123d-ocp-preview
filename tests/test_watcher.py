from pathlib import Path

from watchdog.events import (
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileMovedEvent,
)

from build123d_ocp_preview.watcher import ProjectEventHandler


def test_handler_requests_reload_for_modified_python_file(tmp_path: Path) -> None:
    paths: list[Path] = []
    project = tmp_path / "project"
    project.mkdir()
    module = project / "part.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    handler = ProjectEventHandler(project, paths.append)

    handler.on_modified(FileModifiedEvent(str(module)))

    assert paths == [module]


def test_handler_ignores_directories_and_non_python_files(tmp_path: Path) -> None:
    paths: list[Path] = []
    project = tmp_path / "project"
    project.mkdir()
    handler = ProjectEventHandler(project, paths.append)

    handler.on_modified(DirModifiedEvent(str(project)))
    handler.on_created(FileCreatedEvent(str(project / "README.md")))

    assert paths == []


def test_handler_uses_move_destination(tmp_path: Path) -> None:
    paths: list[Path] = []
    project = tmp_path / "project"
    project.mkdir()
    module = project / "renamed.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    handler = ProjectEventHandler(project, paths.append)

    handler.on_moved(FileMovedEvent(str(project / "old.py"), str(module)))

    assert paths == [module]
