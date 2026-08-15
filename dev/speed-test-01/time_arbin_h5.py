"""Split arbin_sql_h5 parse (local raw after one copy).

    set SPEEDTEST_JOURNAL=path/to/journal.json
    python dev/speed-test-01/time_arbin_h5.py
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from _common import TMP, cell_label, env, journal_path, redact_name, step

logging.basicConfig(level=logging.WARNING)

import pandas as pd

import cellpy.config as config
from cellpy.batch.journal import read_journal
from cellpy.internals.connections import OtherPath
from cellpy.readers.cellreader import get as cellpy_get
from cellpy.readers.instruments import arbin_sql_h5
from cellpy.readers.instruments.harmonize import harmonize


def _raw_uri() -> str:
    override = env("SPEEDTEST_RAW")
    if override:
        return override
    journal = read_journal(journal_path())
    label = cell_label(journal)
    for row in journal.pages.iter_rows(named=True):
        if row.get("filename") == label:
            files = row.get("raw_file_names")
            if files:
                return files[0]
    raise SystemExit(f"no raw URI for label {label}")


def _loader_on(path: Path) -> arbin_sql_h5.DataLoader:
    loader = arbin_sql_h5.DataLoader()
    loader.name = path
    loader._temp_file_path = path
    loader._refuse_copying = True
    return loader


def main() -> None:
    local = Path(env("SPEEDTEST_RAW_LOCAL") or (TMP / "raw_local.h5"))
    local.parent.mkdir(parents=True, exist_ok=True)
    if not local.is_file():
        copied = step("OtherPath.copy remote raw", OtherPath(_raw_uri()).copy)
        shutil.copy2(copied, local)
    print(f"local={redact_name(local)}  size={local.stat().st_size / 1e6:.1f} MB", flush=True)

    loader = _loader_on(local)
    frames = step("HDFStore select data/info/stat", loader._parse_h5_data)
    data_df = frames["data_df"]
    print(f"  data_df shape={data_df.shape}  Date_Time dtype={data_df['Date_Time'].dtype}", flush=True)
    step("drop_duplicates", data_df.drop_duplicates)
    sample = data_df["Date_Time"]
    converted = step(
        "Series.apply(from_arbin_to_datetime)",
        lambda: sample.apply(arbin_sql_h5.from_arbin_to_datetime),
    )
    step(
        "pd.to_datetime on those strings",
        lambda: pd.to_datetime(converted, format=arbin_sql_h5.DATE_TIME_FORMAT),
    )

    dest = local.with_name(local.stem + "_copy2.h5")
    if dest.exists():
        dest.unlink()
    step("shutil.copy2 local raw", lambda: shutil.copy2(local, dest))

    loader_p = arbin_sql_h5.DataLoader()
    loader_p._refuse_copying = True
    vendor = step("parse() refuse_copying", lambda: loader_p.parse(local))
    decls = loader_p.declarations()
    native = step("harmonize(vendor) arbin_epoch", lambda: harmonize(vendor, decls, strict=False))
    step("harmonized.to_pandas()", native.to_pandas)
    step("legacy loader()", lambda: _loader_on(local).loader(local))

    step(
        "cellpy.get auto_summary=False (harmonize ON)",
        lambda: cellpy_get(local, instrument="arbin_sql_h5", auto_summary=False, refuse_copying=True),
    )
    config.reader.use_harmonized_raw = False
    step(
        "cellpy.get auto_summary=False (harmonize OFF)",
        lambda: cellpy_get(local, instrument="arbin_sql_h5", auto_summary=False, refuse_copying=True),
    )
    config.reader.use_harmonized_raw = True


if __name__ == "__main__":
    main()
