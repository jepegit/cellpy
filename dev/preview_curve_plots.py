"""Manually preview cycles / raw / cycle_info oracle cases.

```shell
uv sync --extra batch
uv run python dev/preview_curve_plots.py
uv run python dev/preview_curve_plots.py --function cycles_plot --open
uv run python dev/preview_curve_plots.py --backend matplotlib
```

Artifacts land under ``tmp/plot_previews/<utc-stamp>/`` (gitignored).
"""

from __future__ import annotations

from plot_preview_common import run_preview_cli


def main() -> None:
    run_preview_cli(
        functions=["cycles_plot", "raw_plot", "cycle_info_plot"],
        description="Preview cycles/raw/cycle_info oracle cases as HTML/PNG.",
    )


if __name__ == "__main__":
    main()
