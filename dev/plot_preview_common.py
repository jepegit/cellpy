"""Shared helpers for manual plot preview scripts under ``dev/``.

These are for human eyeballs — structural oracle coverage stays in
``tests/test_figure_specs.py`` / ``dev/snapshot_figure_specs.py``.

Typical use::

    uv sync --extra batch
    uv run python dev/preview_ica_plots.py
    uv run python dev/preview_plots.py --list
    uv run python dev/preview_plots.py --function ica_plot --open
"""

from __future__ import annotations

import argparse
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = REPO_ROOT / "tmp" / "plot_previews"

if str(REPO_ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tests"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from figure_spec_support import (  # noqa: E402
    FIGURE_CASES,
    FigureCase,
    load_figure_cell,
    plotly_available,
    seaborn_available,
)


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "_", name)
    return cleaned.strip("._")


def select_cases(
    *,
    functions: Sequence[str] | None = None,
    backends: Sequence[str] | None = None,
    name_substr: str | None = None,
) -> list[FigureCase]:
    """Filter the oracle menu (``FIGURE_CASES``) for a preview run."""
    selected: list[FigureCase] = []
    for case in FIGURE_CASES:
        if functions and case.function not in functions:
            continue
        backend = case.kwargs.get("backend")
        if backends and backend is not None and backend not in backends:
            continue
        if name_substr and name_substr not in case.name:
            continue
        reason = case.skip_reason()
        if reason:
            print(f"skip {case.name}: {reason}")
            continue
        selected.append(case)
    return selected


def render_live(case: FigureCase, cell):
    """Render one case without the oracle's structural describe/close path."""
    from cellpy.utils import plotutils

    return getattr(plotutils, case.function)(cell, **dict(case.kwargs))


def save_figure(figure, out_dir: Path, case_name: str) -> Path | None:
    """Write a plotly HTML or matplotlib PNG; return the path (or None)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(case_name)

    if figure is None:
        print(f"skip save {case_name}: no figure returned")
        return None

    if hasattr(figure, "to_html") and hasattr(figure, "write_html"):
        path = out_dir / f"{stem}.html"
        figure.write_html(path, include_plotlyjs="cdn", full_html=True)
        return path

    if hasattr(figure, "savefig"):
        path = out_dir / f"{stem}.png"
        figure.savefig(path, dpi=120, bbox_inches="tight")
        return path

    print(f"skip save {case_name}: unsupported figure type {type(figure)!r}")
    return None


def preview_cases(
    cases: Iterable[FigureCase],
    *,
    out_dir: Path | None = None,
    open_files: bool = False,
) -> list[Path]:
    """Render *cases*, write artifacts under *out_dir*, optionally open them."""
    cases = list(cases)
    if not cases:
        raise SystemExit("no figure cases matched the selection")

    if out_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = DEFAULT_OUT_ROOT / stamp

    print(f"loading golden cell…")
    cell = load_figure_cell()
    print(f"writing {len(cases)} figure(s) under {out_dir}")

    written: list[Path] = []
    for case in cases:
        print(f"  render {case.name}")
        figure = render_live(case, cell)
        path = save_figure(figure, out_dir, case.name)
        if path is None:
            continue
        written.append(path)
        print(f"    -> {path}")
        if open_files:
            webbrowser.open(path.resolve().as_uri())

    print(f"done: {len(written)} file(s) in {out_dir}")
    return written


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"output directory (default: {DEFAULT_OUT_ROOT}/<utc-stamp>/)",
    )
    parser.add_argument(
        "--backend",
        action="append",
        choices=("plotly", "matplotlib"),
        default=None,
        help="limit to this backend (repeatable); default: both",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="open each written file with the system default handler",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list matching cases and exit",
    )


def run_preview_cli(
    *,
    functions: Sequence[str] | None = None,
    description: str,
    argv: Sequence[str] | None = None,
) -> None:
    """Shared CLI entry used by the thin family scripts and ``preview_plots``."""
    parser = argparse.ArgumentParser(description=description)
    add_common_args(parser)
    parser.add_argument(
        "--function",
        action="append",
        dest="functions",
        default=None,
        help="limit to this plotutils function (repeatable)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="substring filter on the oracle case name",
    )
    args = parser.parse_args(argv)

    selected_functions = list(functions or [])
    if args.functions:
        selected_functions.extend(args.functions)
    if not selected_functions:
        selected_functions = None

    cases = select_cases(
        functions=selected_functions,
        backends=args.backend,
        name_substr=args.name,
    )
    if args.list:
        for case in cases:
            print(case.name)
        print(f"{len(cases)} case(s)")
        return

    if not plotly_available:
        print("note: plotly not installed — plotly cases are skipped")
    if not seaborn_available:
        print("note: seaborn not installed — some matplotlib cases may look plain")

    preview_cases(cases, out_dir=args.out, open_files=args.open)
