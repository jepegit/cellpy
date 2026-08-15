"""Split-time OtherPath remote ops (handshake vs transfer).

    set SPEEDTEST_JOURNAL=path/to/journal.json
    python dev/speed-test-01/time_otherpath.py
    python dev/speed-test-01/time_otherpath.py --cold
"""

from __future__ import annotations

import argparse
import logging

from _common import TMP, cell_label, journal_path, redact_name, step

logging.basicConfig(level=logging.WARNING)

from cellpy.batch.journal import read_journal
from cellpy.internals.connections import OtherPath


def _raw_uri() -> str:
    override = __import__("os").environ.get("SPEEDTEST_RAW")
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


def cold() -> None:
    raw = _raw_uri()
    out = TMP / "otherpath_cold"
    out.mkdir(parents=True, exist_ok=True)
    for leftover in out.iterdir():
        leftover.unlink()
    p = OtherPath(raw)
    import time

    t0 = time.perf_counter()
    ok = p.is_file()
    t1 = time.perf_counter()
    copied = p.copy(out)
    t2 = time.perf_counter()
    print(f"is_file {t1 - t0:.3f}s ok={ok}", flush=True)
    print(f"copy    {t2 - t1:.3f}s {copied.stat().st_size / 1e6:.1f} MB", flush=True)
    print(f"total   {t2 - t0:.3f}s", flush=True)


def warm() -> None:
    raw = _raw_uri()
    print(f"name={redact_name(raw)}", flush=True)
    out = TMP / "otherpath"
    out.mkdir(parents=True, exist_ok=True)
    d1, d2, d3 = out / "c1", out / "c2", out / "c3"
    for d in (d1, d2, d3):
        d.mkdir(exist_ok=True)
        for leftover in d.iterdir():
            leftover.unlink()

    p = step("OtherPath()", lambda: OtherPath(raw))
    print(f"  is_external={p.is_external} name={p.name}", flush=True)
    step("is_file() #1", p.is_file)
    step("is_file() #2 same object", p.is_file)
    st = step("stat()", p.stat)
    print(f"  st_size={getattr(st, 'st_size', None)}", flush=True)
    copied = step("copy() #1", lambda: p.copy(d1))
    print(f"  {copied.stat().st_size / 1e6:.1f} MB", flush=True)
    step("copy() #2 new OtherPath()", lambda: OtherPath(raw).copy(d2))
    upath = step("_upath_with_credentials()", p._upath_with_credentials)
    step("reuse UPath.exists()", upath.exists)
    step("reuse fs.info()", lambda: upath.fs.info(upath.path))
    dest3 = d3 / p.name
    step("reuse fs.get()", lambda: upath.fs.get(upath.path, str(dest3)))
    q = OtherPath(raw)
    step("from_raw pattern: is_file() + copy()", lambda: (q.is_file(), q.copy(d1)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cold", action="store_true")
    args = parser.parse_args()
    if args.cold:
        cold()
    else:
        warm()


if __name__ == "__main__":
    main()
