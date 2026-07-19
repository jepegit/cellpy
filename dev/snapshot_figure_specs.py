"""Snapshot the structure of every figure cellpy can draw (#567).

The snapshot is the contract ``tests/test_figure_specs.py`` checks against, so
that moving the plotting stack around cannot quietly change the figures.
Regenerate it only when a change to a figure is *intended*, and in the same
commit as the change, so review sees it:

```shell
uv sync --extra batch          # plotly + seaborn; the menu is skipped without them
uv run python dev/snapshot_figure_specs.py
```

Structural, not pixels: trace counts, trace names, axis assignment, series
lengths and endpoints, axis titles. See ``tests/figure_spec_support.py`` for
why.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tests"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from figure_spec_support import (  # noqa: E402
    FIGURE_CASES,
    SNAPSHOT_PATH,
    build_figure_specs,
    plotly_available,
    seaborn_available,
)


def main() -> None:
    if not (plotly_available and seaborn_available):
        raise SystemExit(
            "plotly and seaborn are both needed to render the full menu.\n"
            "Run `uv sync --extra batch` first — regenerating without them "
            "would silently drop cases from the snapshot."
        )

    specs = build_figure_specs()

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(specs, handle, indent=2, sort_keys=True)
        handle.write("\n")

    rendered = len(specs["figures"])
    print(f"wrote {SNAPSHOT_PATH}")
    print(f"figures: {rendered} of {len(FIGURE_CASES)} cases")


if __name__ == "__main__":
    main()
