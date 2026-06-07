import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket
from typing import TextIO


BROWSER_REGISTERED_MESSAGE = "Browser as viewer client registered"
DEFAULT_STATE_DIR = Path(tempfile.gettempdir()) / "build123d_ocp_preview"


def build_viewer_command(port: int) -> list[str]:
    return [sys.executable, "-u", "-m", "ocp_vscode", "--port", str(port)]


def build_viewer_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/viewer"


def build_pid_file(port: int, state_dir: Path | None = None) -> Path:
    return (state_dir or DEFAULT_STATE_DIR) / f"ocp_vscode_{port}.pid"


def read_pid_file(pid_file: Path) -> int | None:
    try:
        raw_pid = pid_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    try:
        return int(raw_pid)
    except ValueError:
        return None


def remove_pid_file(pid_file: Path, expected_pid: int | None = None) -> None:
    if expected_pid is not None and read_pid_file(pid_file) != expected_pid:
        return
    try:
        pid_file.unlink()
    except FileNotFoundError:
        return


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_command(pid: int) -> str | None:
    completed = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        return None
    command = completed.stdout.strip()
    if not command:
        return None
    return command


def parent_pid(pid: int) -> int | None:
    completed = subprocess.run(
        ["ps", "-p", str(pid), "-o", "ppid="],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        return None
    raw_parent_pid = completed.stdout.strip()
    try:
        return int(raw_parent_pid)
    except ValueError:
        return None


def listener_pids_on_port(port: int) -> tuple[int, ...]:
    completed = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        return ()

    pids: list[int] = []
    for line in completed.stdout.splitlines():
        try:
            pids.append(int(line.strip()))
        except ValueError:
            continue
    return tuple(pids)


def is_ocp_vscode_command(command: str, port: int) -> bool:
    return "ocp_vscode" in command and (
        f"--port {port}" in command or f"--port={port}" in command
    )


def is_ocp123d_command(command: str) -> bool:
    return "ocp123d" in command or "build123d_ocp_preview" in command


def terminate_process(pid: int, timeout_seconds: float = 5.0) -> None:
    if not is_process_alive(pid):
        return

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not is_process_alive(pid):
            return
        time.sleep(0.05)

    kill_signal = getattr(signal, "SIGKILL", signal.SIGTERM)
    os.kill(pid, kill_signal)


@dataclass
class ViewerProcess:
    port: int
    state_dir: Path | None = None
    on_browser_registered: Callable[[], None] | None = None
    process: subprocess.Popen[str] | None = field(default=None, init=False)
    _output_thread: threading.Thread | None = field(default=None, init=False)

    @property
    def pid_file(self) -> Path:
        return build_pid_file(self.port, self.state_dir)

    def cleanup_stale(self) -> None:
        stale_pid = read_pid_file(self.pid_file)
        if stale_pid is None:
            remove_pid_file(self.pid_file)
            for listener_pid in listener_pids_on_port(self.port):
                self._terminate_if_stale_viewer(listener_pid, check_parent=True)
            return
        if not is_process_alive(stale_pid):
            remove_pid_file(self.pid_file)
            return

        if self._terminate_if_stale_viewer(stale_pid, check_parent=False):
            remove_pid_file(self.pid_file)

    def _terminate_if_stale_viewer(self, pid: int, check_parent: bool) -> bool:
        command = process_command(pid)
        if command is None or not is_ocp_vscode_command(command, self.port):
            return False

        if check_parent:
            stale_parent_pid = parent_pid(pid)
            if stale_parent_pid is not None:
                parent_command = process_command(stale_parent_pid)
                if parent_command is not None and is_ocp123d_command(parent_command):
                    return False

        terminate_process(pid)
        return True

    def record_process(self) -> None:
        if self.process is None:
            return
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(f"{self.process.pid}\n", encoding="utf-8")

    def start_output_monitor(self) -> None:
        if self.process is None or self.process.stdout is None:
            return
        if self._output_thread is not None and self._output_thread.is_alive():
            return
        self._output_thread = threading.Thread(
            target=self._monitor_output,
            args=(self.process.stdout,),
            daemon=True,
        )
        self._output_thread.start()

    def _monitor_output(self, stdout: TextIO) -> None:
        for line in stdout:
            if (
                self.on_browser_registered is not None
                and BROWSER_REGISTERED_MESSAGE in line
            ):
                self.on_browser_registered()

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        self.cleanup_stale()
        self.process = subprocess.Popen(
            build_viewer_command(self.port),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.record_process()
        self.start_output_monitor()

    def wait_until_ready(
        self,
        timeout_seconds: float = 10.0,
        poll_seconds: float = 0.1,
    ) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                return False
            with socket(AF_INET, SOCK_STREAM) as sock:
                sock.settimeout(poll_seconds)
                if sock.connect_ex(("127.0.0.1", self.port)) == 0:
                    return True
            time.sleep(poll_seconds)
        return False

    def open_in_browser(self) -> bool:
        return webbrowser.open(build_viewer_url(self.port))

    def stop(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        remove_pid_file(self.pid_file, expected_pid=self.process.pid)
        if self._output_thread is not None:
            self._output_thread.join(timeout=2)
