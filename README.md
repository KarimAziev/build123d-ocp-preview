[![codecov](https://codecov.io/gh/KarimAziev/build123d-ocp-preview/graph/badge.svg?token=8IL1WZN37H)](https://codecov.io/gh/KarimAziev/build123d-ocp-preview)

# About

This package provides a fast edit-preview workflow for `build123d` CAD projects, especially when working in editors like Emacs.

The `ocp123d` command starts a single long-lived `ocp_vscode` viewer server, watches your project directory recursively, and re-runs your entry script whenever Python files change.

Key behavior:

- starts the viewer server once and keeps it running
- watches the entire project recursively
- reloads when indirectly imported Python modules change
- avoids stale imports by running each reload in a fresh child process

**Table of Contents**

> - [About](#about)
> - [Installation](#installation)
>   - [Quick Start](#quick-start)
>   - [CLI](#cli)
>   - [Config File](#config-file)
>   - [Entry Scripts](#entry-scripts)
>   - [What Gets Watched](#what-gets-watched)
>   - [How Reloading Works](#how-reloading-works)
>   - [Current Limitations](#current-limitations)
>   - [Development](#development)

# Installation

Install this tool into the same virtual environment as your CAD project:

```bash
pip install build123d-ocp-preview
```

For local development from this repository:

```bash
pip install -e /path/to/build123d-ocp-preview
```

`build123d` is not a required dependency of this watcher because your CAD project
environment should normally provide it. For a fresh demo environment, install the
optional extra:

```bash
python -m pip install "build123d-ocp-preview[build123d]"
```

## Quick Start

Given a project like:

```text
/Users/me/my-build123-project/
  assembly.py
  my_cad/
    scratch.py
```

where `assembly.py` calls `ocp_vscode.show(...)`, run:

```bash
cd /Users/me/my-build123-project
source .venv/bin/activate
ocp123d -p . assembly.py
```

Open the viewer URL printed by `ocp_vscode`, usually:

```text
http://127.0.0.1:3939
```

By default, `ocp123d` also opens this viewer page in your browser before the
initial preview run. This gives `ocp_vscode` time to register the browser client,
so the first model is loaded immediately instead of leaving the splash preview on
screen.

Now saving `assembly.py` or any project Python module such as
`picar_cad/scratch.py` triggers a debounced re-run of `assembly.py`.

## CLI

```text
ocp123d [options] ENTRY [ENTRY ...]
```

Options:

```text
-p, --project PATH        Project directory to watch. Defaults to cwd.
-o, --port PORT           ocp_vscode port. Defaults to 3939.
-d, --debounce-ms N       Debounce window in milliseconds. Defaults to 250.
-i, --ignore PATH         Project-relative Python file path to ignore. Repeatable.
-c, --config PATH         TOML config file.
-n, --no-initial-run      Start watching without running entries immediately.
-b, --no-open             Do not open the browser viewer before the initial run.
-h, --help                Show help.
```

Examples:

```bash
ocp123d -p . assembly.py
ocp123d -p . -o 3940 -d 500 assembly.py
ocp123d -p . -i picar_cad/temp.py assembly.py
ocp123d -p . --no-open assembly.py
ocp123d -p . assembly.py second_preview.py
```

## Config File

The optional config file is TOML. Currently it supports exact ignored file paths:

```toml
ignore = [
  "picar_cad/temp.py",
  "picar_cad/generated.py",
]
```

Use it with:

```bash
ocp123d -p . -c ocp123d.toml assembly.py
```

CLI ignores and config ignores are merged:

```bash
ocp123d -p . -c ocp123d.toml -i picar_cad/scratch_experiment.py assembly.py
```

Ignore paths are resolved relative to the project directory unless absolute.
Wildcard and glob matching are not implemented yet.

## Entry Scripts

Your entry script should be a normal Python script that sends geometry to
`ocp_vscode`, for example:

```python
from build123d import Box
from ocp_vscode import show

show(Box(10, 20, 30), names=["box"])
```

`ocp123d` sets the viewer port before running the entry script. It also prepends the
project directory to `PYTHONPATH`, so project-local imports work when the command is
run from elsewhere.

## What Gets Watched

The watcher observes `.py` files under the project directory recursively.

It always ignores common noisy directories:

- `.git`
- `.venv`
- `venv`
- `__pycache__`
- `.mypy_cache`
- `.pytest_cache`
- `.ruff_cache`
- `node_modules`

## How Reloading Works

On each reload, `ocp123d` launches a fresh child process for each entry file. This
is intentionally simple and reliable:

```text
entry.py imports A
A imports B
B imports C
```

If `C.py` changes, the watcher sees the file change and re-runs `entry.py` in a new
process. Python imports the whole graph from disk again, so stale imported objects
from a previous run do not survive.

The tradeoff is that heavy CAD scripts pay their normal script execution cost on
each reload. The viewer server itself stays running.

## Current Limitations

- No persistent IPython/Jupyter console.
- No partial in-process module reload.
- Ignore rules are exact paths only, not globs.
- Only Python source changes trigger reloads.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q
ruff check .
pyright
```
