"""Render marimo example notebooks to committed markdown pages (#724).

Zensical builds from Markdown and does not execute marimo. Sources under
``docs/examples/marimo/`` are exported with ``marimo-md-export`` (markdown plus
embedded outputs) and the result is committed, mirroring the Jupyter path in
``dev/render_example_notebooks.py``.

Usage:

```shell
uv run --group docs python dev/render_marimo_notebooks.py
```

Re-run and commit the output whenever a marimo notebook changes. This **does**
execute the notebooks (via ``marimo export``) so cellpy and its deps must be
importable in the environment.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARIMO_DIR = REPO_ROOT / "docs" / "examples" / "marimo"


def _exporter() -> str:
    """Return the ``marimo-md-export`` executable path, or raise a clear error."""
    exe = shutil.which("marimo-md-export")
    if exe:
        return exe
    raise SystemExit(
        "marimo-md-export is not on PATH. "
        "Install/run via the docs group: uv run --group docs python "
        "dev/render_marimo_notebooks.py"
    )


def render(notebook_path: Path, exporter: str) -> None:
    """Export one marimo notebook to a sibling ``.md`` file."""
    notebook_path = notebook_path.resolve()
    output = notebook_path.with_suffix(".md")
    cmd = [exporter, str(notebook_path), str(output)]

    print(f"exporting {notebook_path.relative_to(REPO_ROOT)} -> {output.name}")
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)
    size_kb = output.stat().st_size / 1024
    print(f"  wrote {output.relative_to(REPO_ROOT)} ({size_kb:.0f} KB)")


def main() -> None:
    if not MARIMO_DIR.is_dir():
        raise SystemExit(f"missing marimo examples dir: {MARIMO_DIR}")

    notebooks = sorted(
        p for p in MARIMO_DIR.glob("*.py") if not p.name.startswith("_")
    )
    if not notebooks:
        raise SystemExit(f"no marimo notebooks under {MARIMO_DIR}")

    exporter = _exporter()
    for notebook in notebooks:
        render(notebook, exporter)


if __name__ == "__main__":
    main()
