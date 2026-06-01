import subprocess

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
