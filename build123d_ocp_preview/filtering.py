from pathlib import Path

IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
    }
)


def should_handle_path(project_dir: Path, path: Path) -> bool:
    resolved_project = project_dir.resolve()
    resolved_path = path.resolve()
    try:
        relative_path = resolved_path.relative_to(resolved_project)
    except ValueError:
        return False

    if resolved_path.suffix != ".py":
        return False

    return not any(part in IGNORED_DIR_NAMES for part in relative_path.parts)
