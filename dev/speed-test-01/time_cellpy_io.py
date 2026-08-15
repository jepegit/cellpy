"""Split v9 .cellpy load and save.

    set SPEEDTEST_CELLPY=path/to/one.cellpy
    python dev/speed-test-01/time_cellpy_io.py
"""

from __future__ import annotations

import io
import json
import logging
import tempfile
import zipfile
from pathlib import Path

from _common import env, redact_name, step

logging.basicConfig(level=logging.WARNING)


def _cellpy_path() -> Path:
    raw = env("SPEEDTEST_CELLPY")
    if raw:
        return Path(raw)
    raise SystemExit("Set SPEEDTEST_CELLPY to a local .cellpy file.")


def main() -> None:
    import pandas as pd

    from cellpy.readers.cellpy_file import v9
    from cellpy.readers.cellreader import get as cellpy_get

    path = _cellpy_path()
    print(f"file={redact_name(path)}  size={path.stat().st_size / 1e6:.1f} MB", flush=True)

    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            print(
                f"  {info.filename:20s}  stored={info.file_size/1e6:.2f} MB  "
                f"compress={info.compress_size/1e6:.2f} MB",
                flush=True,
            )

    zf = zipfile.ZipFile(path, "r")
    step("ZipFile open + namelist", zf.namelist)
    step("read+parse meta.json", lambda: json.loads(zf.read("meta.json")))
    raw_bytes = step("zf.read raw.parquet (inflate)", lambda: zf.read("raw.parquet"))
    print(f"  inflated raw={len(raw_bytes)/1e6:.1f} MB", flush=True)
    raw_df = step(
        "pandas.read_parquet raw (pyarrow)",
        lambda: pd.read_parquet(io.BytesIO(raw_bytes), engine="pyarrow"),
    )
    print(f"  raw shape={raw_df.shape}", flush=True)
    for name in ("steps.parquet", "summary.parquet", "fid.parquet"):
        if name in zf.namelist():
            step(f"read+parse {name}", lambda n=name: pd.read_parquet(io.BytesIO(zf.read(n)), engine="pyarrow"))
    zf.close()

    step("v9.load", lambda: v9.load(path))
    cell = step("cellpy.get", lambda: cellpy_get(path))
    cell = step("cellpy.get again", lambda: cellpy_get(path))

    out = Path(tempfile.gettempdir()) / "speedtest_rewrite.cellpy"
    if out.exists():
        out.unlink()
    step("CellpyCell.save v9", lambda: cell.save(out, overwrite=True))
    print(f"  wrote {out.stat().st_size / 1e6:.1f} MB", flush=True)
    step("to_parquet bytes raw", lambda: v9._frame_to_parquet_bytes(cell.data.raw))
    step("to_parquet bytes steps", lambda: v9._frame_to_parquet_bytes(cell.data.steps))
    step("to_parquet bytes summary", lambda: v9._frame_to_parquet_bytes(cell.data.summary))

    out_v8 = Path(tempfile.gettempdir()) / "speedtest_rewrite.h5"
    if out_v8.exists():
        out_v8.unlink()
    try:
        step("CellpyCell.save v8 hdf5", lambda: cell.save(out_v8, overwrite=True, cellpy_file_format="v8"))
        print(f"  wrote {out_v8.stat().st_size / 1e6:.1f} MB", flush=True)
        step("cellpy.get v8", lambda: cellpy_get(out_v8))
    except Exception as exc:
        print(f"  v8 save/load skipped: {type(exc).__name__}", flush=True)


if __name__ == "__main__":
    main()
