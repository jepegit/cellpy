# Issue #937: Notebook tooling (ipykernel, matplotlib) is a hard runtime dependency — ~90 MB in a headless server image

Source: https://github.com/jepegit/cellpy/issues/937

## Original issue text

Found while building a container image for a cellpy-based web app
([cellpy-simple-gui#121](https://github.com/cellpy/cellpy-simple-gui/issues/121)).
Not a bug — a packaging pain-point for anyone deploying cellpy headless.

## What we measured

The app plots with plotly, runs FastAPI, and never opens a notebook. Yet the
image carries an interactive-notebook stack, traced with `importlib.metadata`
rather than guessed:

```
debugpy      <- ipykernel
ipykernel    <- cellpy
ipython      <- ipykernel
jedi         <- ipython
matplotlib   <- cellpy
```

Sizes in the built image (`python:3.13-slim-bookworm`, 128 packages, 1.18 GB venv):

| package | MB |
|---|---|
| `matplotlib` | 35 |
| `jedi` | 34 |
| `debugpy` | 22 |

~90 MB, plus `ipython`, `ipykernel`, `pyzmq`, `tornado`, `fontTools` (27 MB) and
friends behind them. None of it is reachable from the code paths a headless
server actually uses.

## Why it matters beyond size

- **Container images and frozen apps.** The same weight lands in a PyInstaller
  bundle, where it is also ~4000 extra files to scan on first run.
- **Attack surface.** `debugpy` in a server image is not something a deployer
  would choose.
- **Cold start.** Not import-time cost (these are lazy), but real disk and pull time.

## Suggestion

Move the interactive pieces to extras and import them where they are used:

```toml
[project.optional-dependencies]
notebook = ["ipykernel", "ipython"]
plotting-mpl = ["matplotlib"]
```

`cellpy[notebook]` would keep the current experience for notebook users — who
are surely the majority — while letting an app or a container install the
analysis core alone. If some module imports `matplotlib` at module scope, a
local import inside the plotting function would be enough to make the extra
genuinely optional.

Happy to test a branch against our container build and report the delta.
