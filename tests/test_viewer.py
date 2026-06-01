import sys

from build123d_ocp_preview.viewer import build_viewer_command


def test_build_viewer_command_uses_current_python_and_port() -> None:
    assert build_viewer_command(3940) == [
        sys.executable,
        "-u",
        "-m",
        "ocp_vscode",
        "--port",
        "3940",
    ]
