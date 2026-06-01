import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass, field
from socket import AF_INET, SOCK_STREAM, socket


def build_viewer_command(port: int) -> list[str]:
    return [sys.executable, "-u", "-m", "ocp_vscode", "--port", str(port)]


def build_viewer_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/viewer"


@dataclass
class ViewerProcess:
    port: int
    process: subprocess.Popen[str] | None = field(default=None, init=False)

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        self.process = subprocess.Popen(
            build_viewer_command(self.port),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            text=True,
        )

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
