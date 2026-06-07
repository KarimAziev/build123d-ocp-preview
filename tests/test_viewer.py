import sys
from pathlib import Path

import build123d_ocp_preview.viewer as viewer_module
from build123d_ocp_preview.viewer import (
    ViewerProcess,
    build_pid_file,
    build_viewer_command,
)


def test_build_viewer_command_uses_current_python_and_port() -> None:
    assert build_viewer_command(3940) == [
        sys.executable,
        "-u",
        "-m",
        "ocp_vscode",
        "--port",
        "3940",
    ]


def test_build_pid_file_uses_state_directory(tmp_path: Path) -> None:
    assert build_pid_file(3940, tmp_path) == tmp_path / "ocp_vscode_3940.pid"


def test_cleanup_stale_viewer_removes_dead_pid_file(
    tmp_path: Path, monkeypatch
) -> None:
    pid_file = build_pid_file(3941, tmp_path)
    pid_file.write_text("12345\n", encoding="utf-8")

    monkeypatch.setattr(viewer_module, "is_process_alive", lambda pid: False)

    ViewerProcess(3941, state_dir=tmp_path).cleanup_stale()

    assert not pid_file.exists()


def test_cleanup_stale_viewer_terminates_orphaned_ocp_vscode_listener(
    tmp_path: Path,
    monkeypatch,
) -> None:
    terminated: list[int] = []

    monkeypatch.setattr(viewer_module, "listener_pids_on_port", lambda port: (12345,))
    monkeypatch.setattr(viewer_module, "is_process_alive", lambda pid: True)
    monkeypatch.setattr(
        viewer_module,
        "process_command",
        lambda pid: f"{sys.executable} -u -m ocp_vscode --port 3942",
    )
    monkeypatch.setattr(viewer_module, "parent_pid", lambda pid: 1)
    monkeypatch.setattr(viewer_module, "terminate_process", terminated.append)

    ViewerProcess(3942, state_dir=tmp_path).cleanup_stale()

    assert terminated == [12345]


def test_cleanup_stale_viewer_keeps_listener_with_active_ocp123d_parent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    terminated: list[int] = []

    monkeypatch.setattr(viewer_module, "listener_pids_on_port", lambda port: (12345,))
    monkeypatch.setattr(viewer_module, "is_process_alive", lambda pid: True)

    def fake_process_command(pid: int) -> str:
        if pid == 12345:
            return f"{sys.executable} -u -m ocp_vscode --port 3942"
        return f"{sys.executable} .venv/bin/ocp123d -p . assembly.py"

    monkeypatch.setattr(viewer_module, "process_command", fake_process_command)
    monkeypatch.setattr(viewer_module, "parent_pid", lambda pid: 54321)
    monkeypatch.setattr(viewer_module, "terminate_process", terminated.append)

    ViewerProcess(3942, state_dir=tmp_path).cleanup_stale()

    assert terminated == []


def test_cleanup_stale_viewer_keeps_unrecognized_live_process(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pid_file = build_pid_file(3942, tmp_path)
    pid_file.write_text("12345\n", encoding="utf-8")
    terminated: list[int] = []

    monkeypatch.setattr(viewer_module, "is_process_alive", lambda pid: True)
    monkeypatch.setattr(viewer_module, "process_command", lambda pid: "python app.py")
    monkeypatch.setattr(viewer_module, "terminate_process", terminated.append)

    ViewerProcess(3942, state_dir=tmp_path).cleanup_stale()

    assert terminated == []
    assert pid_file.exists()


def test_cleanup_stale_viewer_terminates_recorded_ocp_vscode_process(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pid_file = build_pid_file(3943, tmp_path)
    pid_file.write_text("12345\n", encoding="utf-8")
    terminated: list[int] = []

    monkeypatch.setattr(viewer_module, "is_process_alive", lambda pid: True)
    monkeypatch.setattr(
        viewer_module,
        "process_command",
        lambda pid: f"{sys.executable} -u -m ocp_vscode --port 3943",
    )
    monkeypatch.setattr(viewer_module, "terminate_process", terminated.append)

    ViewerProcess(3943, state_dir=tmp_path).cleanup_stale()

    assert terminated == [12345]
    assert not pid_file.exists()
