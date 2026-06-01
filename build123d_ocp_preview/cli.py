import argparse
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from watchdog.observers import Observer

from build123d_ocp_preview.config import AppConfig, create_app_config
from build123d_ocp_preview.reloader import DebouncedReloader
from build123d_ocp_preview.runner import RunResult, run_entries
from build123d_ocp_preview.viewer import ViewerProcess
from build123d_ocp_preview.watcher import ProjectEventHandler


def parse_args(argv: Sequence[str] | None = None) -> AppConfig:
    parser = argparse.ArgumentParser(
        description="Preview build123d scripts in ocp_vscode with hot reload."
    )
    parser.add_argument("entries", nargs="+", help="Entry Python file(s) to run.")
    parser.add_argument(
        "-p",
        "--project",
        default=None,
        help="Project directory to watch. Defaults to the current directory.",
    )
    parser.add_argument(
        "-o",
        "--port",
        type=int,
        default=3939,
        help="ocp_vscode port.",
    )
    parser.add_argument(
        "-d",
        "--debounce-ms",
        type=int,
        default=250,
        help="Debounce window for file changes in milliseconds.",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        action="append",
        default=[],
        help="Project-relative Python file path to ignore. Can be repeated.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help='TOML config file containing ignore = ["path.py", ...].',
    )
    parser.add_argument(
        "-n",
        "--no-initial-run",
        action="store_true",
        help="Start watching without running entries immediately.",
    )
    parser.add_argument(
        "-b",
        "--no-open",
        action="store_true",
        help="Do not open the browser viewer before the initial run.",
    )
    args = parser.parse_args(argv)
    return create_app_config(
        project_arg=args.project,
        entry_args=args.entries,
        port=args.port,
        debounce_ms=args.debounce_ms,
        initial_run=not args.no_initial_run,
        ignore_args=args.ignore,
        config_arg=args.config,
        open_viewer=not args.no_open,
    )


def print_run_results(results: Sequence[RunResult]) -> None:
    for result in results:
        print(
            f"[ocp123d] Finished {result.entry} with exit {result.returncode}",
            flush=True,
        )
        if result.stdout:
            print(result.stdout, end="", flush=True)
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr, flush=True)


def run_app(config: AppConfig) -> int:
    viewer = ViewerProcess(config.port)
    observer = Observer()
    observer_started = False

    def run_reload(paths: tuple[Path, ...]) -> None:
        changed = ", ".join(str(path) for path in paths)
        print(f"[ocp123d] Reload triggered by: {changed}", flush=True)
        print_run_results(run_entries(config))

    reloader = DebouncedReloader(config.debounce_seconds, run_reload)
    handler = ProjectEventHandler(
        config.project_dir,
        reloader.request_reload,
        ignored_paths=config.ignored_paths,
    )

    try:
        print(
            f"[ocp123d] Starting ocp_vscode on http://127.0.0.1:{config.port}",
            flush=True,
        )
        viewer.start()
        if config.open_viewer:
            if viewer.wait_until_ready():
                viewer.open_in_browser()
                time.sleep(1.0)
            else:
                print(
                    "[ocp123d] Viewer server did not become ready before initial run",
                    file=sys.stderr,
                    flush=True,
                )
        if config.initial_run:
            print("[ocp123d] Running initial preview", flush=True)
            print_run_results(run_entries(config))
        observer.schedule(handler, str(config.project_dir), recursive=True)
        observer.start()
        observer_started = True
        print(f"[ocp123d] Watching {config.project_dir}", flush=True)
        while observer.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[ocp123d] Stopping", flush=True)
    finally:
        reloader.close()
        if observer_started:
            observer.stop()
            observer.join(timeout=5)
        viewer.stop()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = parse_args(argv)
    except ValueError as exc:
        print(f"ocp123d: {exc}", file=sys.stderr, flush=True)
        return 2
    return run_app(config)


if __name__ == "__main__":
    raise SystemExit(main())
