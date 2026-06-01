import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass(frozen=True)
class ProjectConfig:
    ignore: tuple[str, ...] = ()


@dataclass(frozen=True)
class AppConfig:
    project_dir: Path
    entries: tuple[Path, ...]
    port: int
    debounce_seconds: float
    initial_run: bool
    python_executable: Path
    ignored_paths: tuple[Path, ...] = ()
    open_viewer: bool = True


def load_project_config(config_file: Path) -> ProjectConfig:
    if not config_file.exists() or not config_file.is_file():
        raise ValueError(f"Config file does not exist: {config_file}")

    data = tomllib.loads(config_file.read_text(encoding="utf-8"))
    ignore_value = data.get("ignore", ())
    if not isinstance(ignore_value, list):
        raise ValueError("Config field ignore must be a list of strings")

    ignore: list[str] = []
    for item in ignore_value:
        if not isinstance(item, str):
            raise ValueError("Config field ignore must be a list of strings")
        ignore.append(item)

    return ProjectConfig(ignore=tuple(ignore))


def create_app_config(
    project_arg: str | None,
    entry_args: Sequence[str],
    port: int,
    debounce_ms: int,
    initial_run: bool,
    ignore_args: Sequence[str] = (),
    config_arg: str | None = None,
    open_viewer: bool = True,
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

    config_ignores: tuple[str, ...] = ()
    if config_arg is not None:
        raw_config_file = Path(config_arg).expanduser()
        config_file = (
            raw_config_file
            if raw_config_file.is_absolute()
            else project_dir / raw_config_file
        )
        config_ignores = load_project_config(config_file.resolve()).ignore

    entries: list[Path] = []
    for entry_arg in entry_args:
        raw_entry = Path(entry_arg).expanduser()
        entry = raw_entry if raw_entry.is_absolute() else project_dir / raw_entry
        resolved_entry = entry.resolve()
        if not resolved_entry.exists() or not resolved_entry.is_file():
            raise ValueError(f"Entry file does not exist: {resolved_entry}")
        entries.append(resolved_entry)

    ignored_paths = tuple(
        _resolve_project_path(project_dir, path_arg)
        for path_arg in (*config_ignores, *ignore_args)
    )

    return AppConfig(
        project_dir=project_dir,
        entries=tuple(entries),
        port=port,
        debounce_seconds=debounce_ms / 1000,
        initial_run=initial_run,
        python_executable=python_executable or Path(sys.executable),
        ignored_paths=ignored_paths,
        open_viewer=open_viewer,
    )


def _resolve_project_path(project_dir: Path, path_arg: str) -> Path:
    raw_path = Path(path_arg).expanduser()
    path = raw_path if raw_path.is_absolute() else project_dir / raw_path
    return path.resolve()
