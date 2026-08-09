"""Backfill missing ``image/png`` outputs for Plotly figures in example notebooks.

Some notebooks were saved with interactive Plotly MIME data but without the
static PNG that ``dev/render_example_notebooks.py`` keeps for the docs site.
This script reconstructs each figure from ``application/vnd.plotly.v1+json``
and writes a PNG via kaleido — no notebook re-execution.

Usage:

```shell
uv run --extra batch --group docs python dev/backfill_notebook_plotly_pngs.py
uv run --extra batch --group docs python dev/backfill_notebook_plotly_pngs.py examples/06_loading_different_formats.ipynb
```

Then re-render markdown:

```shell
uv run --group docs python dev/render_example_notebooks.py
```
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"
#: Mirrors ``dev/render_example_notebooks.py`` — the cookiecutter tree is Jinja.
SKIP_DIRS = (".ipynb_checkpoints", "cellpy project template")
PLOTLY_MIME = "application/vnd.plotly.v1+json"
PNG_MIME = "image/png"


def _require_engines() -> tuple:
    try:
        import plotly.io as pio
        from plotly.graph_objects import Figure
    except ImportError as exc:
        raise SystemExit(
            "plotly is required; run with: uv run --extra batch --group docs ..."
        ) from exc
    try:
        import kaleido  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "kaleido is required; run with: uv run --extra batch --group docs ..."
        ) from exc
    return pio, Figure


def _figure_from_payload(payload: dict, Figure) -> object:
    """Build a Figure from notebook Plotly JSON, tolerating stale template keys."""
    fig_dict = {k: v for k, v in payload.items() if k in ("data", "layout", "frames")}
    return Figure(fig_dict, skip_invalid=True)


def _png_for_figure(fig, pio) -> bytes:
    width = int(fig.layout.width or 1200)
    height = int(fig.layout.height or 500)
    return pio.to_image(fig, format="png", scale=1, width=width, height=height)


def backfill_notebook(path: Path, pio, Figure, *, dry_run: bool = False) -> int:
    """Add PNG outputs where Plotly JSON exists but PNG does not. Return count."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    added = 0
    for cell in notebook.get("cells", []):
        for output in cell.get("outputs") or []:
            data = output.get("data")
            if not data or PLOTLY_MIME not in data or PNG_MIME in data:
                continue
            payload = data[PLOTLY_MIME]
            if not isinstance(payload, dict):
                continue
            fig = _figure_from_payload(payload, Figure)
            png = _png_for_figure(fig, pio)
            data[PNG_MIME] = base64.b64encode(png).decode("ascii")
            added += 1
    if added and not dry_run:
        path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    return added


def _iter_notebooks(paths: list[Path]) -> list[Path]:
    if paths:
        return [p.resolve() for p in paths]
    return sorted(
        p
        for p in EXAMPLES.rglob("*.ipynb")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notebooks",
        nargs="*",
        type=Path,
        help="Notebook paths (default: all under examples/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many PNGs would be added without writing",
    )
    args = parser.parse_args(argv)

    pio, Figure = _require_engines()
    total = 0
    for path in _iter_notebooks(args.notebooks):
        if not path.is_file():
            raise SystemExit(f"not a file: {path}")
        added = backfill_notebook(path, pio, Figure, dry_run=args.dry_run)
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        mode = "would add" if args.dry_run else "added"
        print(f"{rel}: {mode} {added} PNG(s)")
        total += added
    print(f"total: {total}")


if __name__ == "__main__":
    main()
