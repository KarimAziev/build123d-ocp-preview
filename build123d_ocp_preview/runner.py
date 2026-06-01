import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from build123d_ocp_preview.config import AppConfig


@dataclass(frozen=True)
class RunResult:
    entry: Path
    returncode: int
    stdout: str
    stderr: str


def build_child_environment(
    project_dir: Path,
    port: int,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(base_env if base_env is not None else os.environ)
    project_path = str(project_dir)
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{project_path}{os.pathsep}{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = project_path
    env["OCP_PORT"] = str(port)
    return env


def build_entry_command(
    python_executable: Path,
    port: int,
    entry: Path,
) -> list[str]:
    return [
        str(python_executable),
        "-m",
        "build123d_ocp_preview.runner_child",
        str(port),
        str(entry),
    ]


def run_entries(config: AppConfig) -> list[RunResult]:
    env = build_child_environment(config.project_dir, config.port)
    results: list[RunResult] = []
    for entry in config.entries:
        completed = subprocess.run(
            build_entry_command(config.python_executable, config.port, entry),
            cwd=config.project_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            RunResult(
                entry=entry,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )
    return results
