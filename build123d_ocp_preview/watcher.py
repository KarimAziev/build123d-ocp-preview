from collections.abc import Callable
from pathlib import Path

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
)

from build123d_ocp_preview.filtering import should_handle_path

PathCallback = Callable[[Path], None]


class ProjectEventHandler(FileSystemEventHandler):
    def __init__(self, project_dir: Path, callback: PathCallback) -> None:
        self._project_dir = project_dir
        self._callback = callback

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        destination = getattr(event, "dest_path", "")
        if not isinstance(destination, str) or not destination:
            return
        self._handle_path(Path(destination))

    def _handle_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if not isinstance(event.src_path, str):
            return
        self._handle_path(Path(event.src_path))

    def _handle_path(self, path: Path) -> None:
        if should_handle_path(self._project_dir, path):
            self._callback(path)
