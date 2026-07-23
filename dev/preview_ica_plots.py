"""Manually preview ``ica_plot`` / ``dva_plot`` oracle cases (#648).

```shell
uv sync --extra batch
uv run python dev/preview_ica_plots.py
uv run python dev/preview_ica_plots.py --open
uv run python dev/preview_ica_plots.py --backend plotly
```

Artifacts land under ``tmp/plot_previews/<utc-stamp>/`` (gitignored).
"""

from __future__ import annotations

from plot_preview_common import run_preview_cli


def main() -> None:
    run_preview_cli(
        functions=["ica_plot", "dva_plot"],
        description="Preview ica_plot / dva_plot oracle cases as HTML/PNG.",
    )


if __name__ == "__main__":
    main()
