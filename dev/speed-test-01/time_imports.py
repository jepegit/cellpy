"""Split-time the batch-cookie import list (fresh process).

    python dev/speed-test-01/time_imports.py
"""

from __future__ import annotations

import sys
import time

from _common import redact

PROBES = (
    "cellpy.readers.cellreader",
    "cellpy.batch.runner",
    "cellpy.config.loader",
    "plotly",
    "paramiko",
    "fsspec",
)


def _present() -> set[str]:
    return {name for name in PROBES if name in sys.modules}


def _step(label: str, fn) -> None:
    before = _present()
    t0 = time.perf_counter()
    fn()
    dt = time.perf_counter() - t0
    appeared = sorted(_present() - before)
    extra = f"  appeared={appeared}" if appeared else ""
    print(f"{dt:8.3f}s  {label}{extra}", flush=True)


def main() -> None:
    print(f"python={sys.executable}", flush=True)

    def import_cellpy():
        import cellpy

        print(f"  cellpy.__version__={cellpy.__version__}", flush=True)

    _step("import cellpy", import_cellpy)
    _step("import numpy", lambda: __import__("numpy"))
    _step("import pandas", lambda: __import__("pandas"))
    _step("import matplotlib.pyplot", lambda: __import__("matplotlib.pyplot"))
    _step("import cellpy.config", lambda: __import__("cellpy.config"))

    def touch_rawdatadir():
        import cellpy.config as config

        path = config.paths.rawdatadir
        print(f"  rawdatadir={redact(path)}", flush=True)

    _step("config.paths.rawdatadir", touch_rawdatadir)
    _step("from cellpy import batch", lambda: __import__("cellpy.batch"))
    _step("from cellpy.utils import helpers", lambda: __import__("cellpy.utils.helpers"))
    _step("from cellpy.utils import plotutils", lambda: __import__("cellpy.utils.plotutils"))


if __name__ == "__main__":
    main()
