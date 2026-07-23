"""Manually preview ``summary_plot`` oracle cases.

```shell
uv sync --extra batch
uv run python dev/preview_summary_plots.py
uv run python dev/preview_summary_plots.py --backend plotly --open
uv run python dev/preview_summary_plots.py --name no_formation
```

Artifacts land under ``tmp/plot_previews/<utc-stamp>/`` (gitignored).
"""

from __future__ import annotations

from plot_preview_common import run_preview_cli


def main() -> None:
    run_preview_cli(
        functions=["summary_plot"],
        description="Preview summary_plot oracle cases as HTML/PNG.",
    )


if __name__ == "__main__":
    main()
