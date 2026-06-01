import subprocess
import sys
from dataclasses import dataclass, field


def build_viewer_command(port: int) -> list[str]:
    return [sys.executable, "-u", "-m", "ocp_vscode", "--port", str(port)]


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
