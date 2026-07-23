"""Manually preview the full figure menu (oracle cases).

```shell
uv sync --extra batch
uv run python dev/preview_plots.py --list
uv run python dev/preview_plots.py --function ica_plot --open
uv run python dev/preview_plots.py --backend matplotlib --name summary_plot
```

Artifacts land under ``tmp/plot_previews/<utc-stamp>/`` (gitignored).
"""

from __future__ import annotations

from plot_preview_common import run_preview_cli


def main() -> None:
    run_preview_cli(
        functions=None,
        description="Preview any/all oracle figure cases as HTML/PNG.",
    )


if __name__ == "__main__":
    main()
