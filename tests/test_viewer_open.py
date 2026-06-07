import subprocess
import sys
import time
from pathlib import Path

from build123d_ocp_preview.viewer import ViewerProcess, build_viewer_url


def test_build_viewer_url_uses_viewer_route() -> None:
    assert build_viewer_url(3940) == "http://127.0.0.1:3940/viewer"


def test_open_in_browser_uses_viewer_url(monkeypatch) -> None:
    opened_urls: list[str] = []
    viewer = ViewerProcess(3941)

    def fake_open(url: str) -> bool:
        opened_urls.append(url)
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)

    assert viewer.open_in_browser() is True
    assert opened_urls == ["http://127.0.0.1:3941/viewer"]


def test_wait_until_ready_returns_false_when_process_exited() -> None:
    viewer = ViewerProcess(3942)
    viewer.process = subprocess.Popen(
        ["true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    viewer.process.wait(timeout=5)

    assert viewer.wait_until_ready(timeout_seconds=0.1, poll_seconds=0.01) is False


def test_stop_removes_owned_pid_file(tmp_path: Path) -> None:
    viewer = ViewerProcess(3943, state_dir=tmp_path)
    viewer.process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    viewer.record_process()

    viewer.stop()

    assert not viewer.pid_file.exists()
    assert viewer.process.poll() is not None


def test_browser_registration_callback_runs_from_viewer_output(tmp_path: Path) -> None:
    registrations: list[None] = []
    viewer = ViewerProcess(
        3944,
        state_dir=tmp_path,
        on_browser_registered=lambda: registrations.append(None),
    )
    viewer.process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import sys, time; "
                "print('Info: Browser as viewer client registered', flush=True); "
                "time.sleep(0.2)"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    viewer.start_output_monitor()
    deadline = time.monotonic() + 2.0

    while not registrations and time.monotonic() < deadline:
        time.sleep(0.01)

    viewer.stop()

    assert registrations == [None]
