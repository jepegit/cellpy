"""Render the example notebooks to committed markdown pages (#571).

Zensical does not render ``.ipynb`` — it copies them verbatim — so the example
notebooks are converted to markdown and the result is committed, following the
same approach as cellpy-core.

**Why this script rather than plain nbconvert.** The notebooks contain plotly
figures, and plotly embeds a self-contained HTML+JS blob per figure. A straight
``jupyter nbconvert --to markdown`` produces ~50 MB of generated markdown for
nine notebooks — one page alone is 15 MB — which is not something to put in a
git repository, and not something a reader wants to download either.

So heavy interactive output is stripped before conversion and the static
``image/png`` rendering is kept. Readers get the plots; the repository does not
get 50 MB of base64. Notebooks that only ever produced interactive figures will
show their code and text without a figure — the ``.ipynb`` stays in the docs
tree, linked as a download, for anyone who wants the interactive version.

Usage:

```shell
uv run --group docs python dev/render_example_notebooks.py
```

Re-run and commit the output whenever a notebook changes. This does **not**
execute the notebooks — it renders the outputs their authors committed. See the
note in ``docs/examples/index.md``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "docs" / "examples"

#: Output types that embed an entire JS runtime per figure.
HEAVY_MIMETYPES = (
    "text/html",
    "application/vnd.plotly.v1+json",
    "application/javascript",
    "application/vnd.jupyter.widget-view+json",
)


def strip_heavy_outputs(notebook: dict) -> tuple[dict, int]:
    """Drop interactive output blobs, keeping static images and text."""
    stripped = 0
    for cell in notebook.get("cells", []):
        for output in cell.get("outputs", []) or []:
            data = output.get("data")
            if not data:
                continue
            for mimetype in HEAVY_MIMETYPES:
                if mimetype in data:
                    del data[mimetype]
                    stripped += 1
    return notebook, stripped


def render(notebook_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / notebook_path.name
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook, stripped = strip_heavy_outputs(notebook)
        staged.write_text(json.dumps(notebook), encoding="utf-8")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "nbconvert",
                "--to",
                "markdown",
                "--output-dir",
                str(notebook_path.parent),
                "--output",
                notebook_path.stem,
                str(staged),
            ],
            check=True,
            capture_output=True,
        )

    rendered = notebook_path.with_suffix(".md")
    size_kb = rendered.stat().st_size / 1024 if rendered.exists() else 0
    print(
        f"{notebook_path.relative_to(REPO_ROOT)}: "
        f"{size_kb:.0f} KB (stripped {stripped} interactive outputs)"
    )


def main() -> None:
    notebooks = sorted(EXAMPLES.rglob("*.ipynb"))
    if not notebooks:
        raise SystemExit(f"no notebooks under {EXAMPLES}")

    # Remove previously rendered support directories so deleted figures do not
    # linger as orphans in the repository.
    for support in EXAMPLES.rglob("*_files"):
        if support.is_dir():
            shutil.rmtree(support)

    for notebook in notebooks:
        render(notebook)


if __name__ == "__main__":
    main()
