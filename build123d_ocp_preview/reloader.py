import threading
from collections.abc import Callable
from pathlib import Path

ReloadCallback = Callable[[tuple[Path, ...]], None]


class DebouncedReloader:
    def __init__(self, debounce_seconds: float, callback: ReloadCallback) -> None:
        self._debounce_seconds = debounce_seconds
        self._callback = callback
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._paths: list[Path] = []
        self._running = False

    def request_reload(self, path: Path) -> None:
        with self._lock:
            if path not in self._paths:
                self._paths.append(path)
            if self._running:
                return
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_seconds, self._run_pending)
            self._timer.daemon = True
            self._timer.start()

    def close(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    def _run_pending(self) -> None:
        with self._lock:
            self._timer = None
            paths = tuple(self._paths)
            self._paths.clear()
            if not paths:
                return
            self._running = True

        try:
            self._callback(paths)
        finally:
            with self._lock:
                self._running = False
                has_pending = bool(self._paths)
                if has_pending:
                    self._timer = threading.Timer(
                        self._debounce_seconds,
                        self._run_pending,
                    )
                    self._timer.daemon = True
                    self._timer.start()
