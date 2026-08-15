"""Print top cumulative rows from a ``python -X importtime`` stderr dump.

    python -X importtime -c "import pandas" 2> importtime.txt
    python dev/speed-test-01/summarize_importtime.py importtime.txt
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    path = Path(sys.argv[1])
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("import time:"):
            continue
        rest = line[len("import time:") :].strip()
        parts = [x.strip() for x in rest.split("|")]
        if len(parts) < 3:
            continue
        try:
            self_us = int(parts[0])
            cum_us = int(parts[1])
        except ValueError:
            continue
        rows.append((cum_us, self_us, parts[2]))
    rows.sort(reverse=True)
    print(f"file={path.name} rows={len(rows)} bytes={path.stat().st_size}")
    print("top 20 by cumulative (ms):")
    for cum, self, name in rows[:20]:
        print(f"{cum / 1000:10.1f}  self={self / 1000:8.1f}  {name}")


if __name__ == "__main__":
    main()
