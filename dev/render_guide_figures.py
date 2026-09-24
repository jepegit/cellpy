"""Render the static figures shown in the how-to guides (#1023).

Every figure is drawn from the bundled example data with the plotting call the
guide shows, so the pictures stay honest when the plotting code changes. The
matplotlib backend is used because it needs no browser; plotly (the default
backend) needs kaleido *and* Chrome for image export.

Usage (needs network the first time, for the example data):

```shell
MPLBACKEND=Agg uv run --extra batch --group docs python dev/render_guide_figures.py
```

Re-run and commit the PNGs under ``docs/guides/figures/`` when a plot changes.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "docs" / "guides" / "figures"
DPI = 110


def _save(fig, name: str) -> None:
    path = OUTPUT / f"{name}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    print(f"{path.relative_to(REPO_ROOT)}: {path.stat().st_size / 1024:.0f} KB")


def main() -> None:
    from cellpy.utils import example_data
    from cellpy.utils.plotutils import (
        cycle_info_plot,
        cycles_plot,
        dva_plot,
        ica_plot,
        raw_plot,
        summary_plot,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c = example_data.raw_file()

    mpl = {"backend": "matplotlib"}
    _save(
        summary_plot(c, y="capacities_gravimetric_coulombic_efficiency", **mpl),
        "summary_plot",
    )
    _save(
        cycles_plot(c, cycles=[1, 5, 10, 15], return_figure=True, **mpl),
        "cycles_plot",
    )
    _save(raw_plot(c, plot_type="voltage-current", **mpl), "raw_plot")
    # get_axes=True returns a tuple of axes (not a figure) for matplotlib.
    axes = cycle_info_plot(c, cycle=3, get_axes=True, **mpl)
    _save(axes[0].get_figure(), "cycle_info_plot")
    _save(ica_plot(c, cycles=[2, 3], **mpl), "ica_plot")
    _save(dva_plot(c, cycles=2, direction="charge", **mpl), "dva_plot")


if __name__ == "__main__":
    main()
