"""Time batch primitives for one journal cell (not ``batch.load``).

    set SPEEDTEST_JOURNAL=path/to/journal.json
    set SPEEDTEST_LABEL=optional-cell-label
    python dev/speed-test-01/time_one_cell.py
"""

from __future__ import annotations

import logging

from _common import cell_label, journal_path, redact_name, step

logging.basicConfig(level=logging.WARNING)

from cellpy.batch.journal import read_journal
from cellpy.batch.policy import LoadPolicy, SourcePreference, resolve_specs
from cellpy.batch.runner import load_cell
from cellpy.internals.connections import OtherPath
from cellpy.readers.cellreader import get as cellpy_get


def main() -> None:
    from pathlib import Path

    journal_file = journal_path()
    journal = step("read_journal", lambda: read_journal(journal_file))
    label = cell_label(journal)
    print(f"  n_cells={journal.pages.height}  label={label}", flush=True)

    specs = step("resolve_specs AUTO", lambda: resolve_specs(journal, LoadPolicy()))
    spec = next(s for s in specs if s.label == label)
    print(
        f"  raw={redact_name(spec.raw_files[0]) if spec.raw_files else None}  "
        f"cellpy={redact_name(spec.cellpy_file)}  instrument={spec.instrument}",
        flush=True,
    )

    local_cellpy = Path(spec.cellpy_file) if spec.cellpy_file else None
    if local_cellpy and local_cellpy.is_file():
        step("cellpy.get local .cellpy", lambda: cellpy_get(local_cellpy))
        step("load_cell AUTO", lambda: load_cell(spec, LoadPolicy()))
    else:
        print("  no local .cellpy — skip those steps", flush=True)

    if not spec.raw_files:
        print("  no raw path — stop", flush=True)
        return

    remote = OtherPath(spec.raw_files[0])
    copied = step("OtherPath.copy remote raw", remote.copy)
    print(f"  copied size={copied.stat().st_size / 1e6:.1f} MB", flush=True)

    cell = step(
        "cellpy.get local raw auto_summary=False refuse_copying",
        lambda: cellpy_get(
            copied,
            instrument=spec.instrument,
            mass=spec.mass,
            area=spec.area,
            auto_summary=False,
            refuse_copying=True,
        ),
    )
    step("make_step_table", cell.make_step_table)
    step("make_summary", cell.make_summary)
    step(
        "load_cell RAW_ONLY",
        lambda: load_cell(spec, LoadPolicy(source=SourcePreference.RAW_ONLY)),
    )


if __name__ == "__main__":
    main()
