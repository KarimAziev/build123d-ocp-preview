import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence


@dataclass(frozen=True)
class AppConfig:
    project_dir: Path
    entries: tuple[Path, ...]
    port: int
    debounce_seconds: float
    initial_run: bool
    python_executable: Path


def create_app_config(
    project_arg: str | None,
    entry_args: Sequence[str],
    port: int,
    debounce_ms: int,
    initial_run: bool,
    python_executable: Path | None = None,
) -> AppConfig:
    project_dir = Path(project_arg or ".").expanduser().resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        raise ValueError(f"Project directory does not exist: {project_dir}")
    if not entry_args:
        raise ValueError("At least one entry file is required")
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    if debounce_ms < 0:
        raise ValueError("Debounce milliseconds must be non-negative")

    entries: list[Path] = []
    for entry_arg in entry_args:
        raw_entry = Path(entry_arg).expanduser()
        entry = raw_entry if raw_entry.is_absolute() else project_dir / raw_entry
        resolved_entry = entry.resolve()
        if not resolved_entry.exists() or not resolved_entry.is_file():
            raise ValueError(f"Entry file does not exist: {resolved_entry}")
        entries.append(resolved_entry)

    return AppConfig(
        project_dir=project_dir,
        entries=tuple(entries),
        port=port,
        debounce_seconds=debounce_ms / 1000,
        initial_run=initial_run,
        python_executable=python_executable or Path(sys.executable),
    )
