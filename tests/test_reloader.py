import threading
import time
from pathlib import Path

from build123d_ocp_preview.reloader import DebouncedReloader


def test_debounce_coalesces_quick_reload_requests(tmp_path: Path) -> None:
    calls: list[tuple[Path, ...]] = []
    done = threading.Event()

    def callback(paths: tuple[Path, ...]) -> None:
        calls.append(paths)
        done.set()

    reloader = DebouncedReloader(debounce_seconds=0.05, callback=callback)
    try:
        reloader.request_reload(tmp_path / "a.py")
        reloader.request_reload(tmp_path / "b.py")

        assert done.wait(1.0) is True
        assert len(calls) == 1
        assert calls[0] == (tmp_path / "a.py", tmp_path / "b.py")
    finally:
        reloader.close()


def test_change_during_run_schedules_one_follow_up(tmp_path: Path) -> None:
    calls: list[tuple[Path, ...]] = []
    first_call_started = threading.Event()
    allow_first_call_to_finish = threading.Event()
    second_call_done = threading.Event()

    def callback(paths: tuple[Path, ...]) -> None:
        calls.append(paths)
        if len(calls) == 1:
            first_call_started.set()
            assert allow_first_call_to_finish.wait(1.0) is True
        else:
            second_call_done.set()

    reloader = DebouncedReloader(debounce_seconds=0.01, callback=callback)
    try:
        reloader.request_reload(tmp_path / "a.py")
        assert first_call_started.wait(1.0) is True

        reloader.request_reload(tmp_path / "b.py")
        reloader.request_reload(tmp_path / "c.py")
        time.sleep(0.05)
        assert len(calls) == 1

        allow_first_call_to_finish.set()
        assert second_call_done.wait(1.0) is True
        assert calls == [
            (tmp_path / "a.py",),
            (tmp_path / "b.py", tmp_path / "c.py"),
        ]
    finally:
        reloader.close()
