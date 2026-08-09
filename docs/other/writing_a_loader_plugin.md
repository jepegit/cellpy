# Writing an instrument loader

cellpy can load data from an instrument it has never heard of, from a package
you maintain yourself. Your loader imports nothing from cellpy and inherits
from no cellpy class — it just has to have the right shape.

## The shape

```python
from pathlib import Path


class MyCyclerLoader:
    # How the registry finds and routes to you.
    name = "mycycler"                 # unique loader id
    instrument = "mycycler"           # instrument family
    supported_suffixes = (".mcx",)    # lowercase, dotted

    def can_load(self, source: Path) -> bool:
        """Cheap sniff — suffix or magic bytes. Must not parse the file."""
        return Path(source).suffix.lower() in self.supported_suffixes

    def load(self, source: Path, *, instrument_config=None, **kwargs):
        """Return one LoaderResult per test in the file — always a tuple."""
        ...
```

Two rules catch most mistakes:

- **`load()` always returns a tuple**, even when the format holds a single
  test (return a 1-tuple). Callers get one unpacking path, and a format that
  later grows multi-test support does not break its consumers.
- **Fill only what the file knows.** cellpy stamps provenance — where the file
  came from, when it was read, what identity it was given — because your loader
  is not in a position to know it. A draft `TestMeta` arriving with
  `source_uri` set is a contract violation and the conformance kit rejects it.

Failures are exceptions, never partial results: raise `LoaderError` (wrapping
whatever the vendor parser threw) rather than returning an empty tuple.

## A worked example

Say "AwesomeCycler" exports a semicolon-separated `.awe` file:

```text
Rec;Time_s;Timestamp;Voltage_V;Current_A;Cycle
1;0.0;2024-01-01 10:00:00;3.400;0.500;1
2;5.0;2024-01-01 10:00:05;3.412;0.500;1
3;10.0;2024-01-01 10:00:10;3.424;0.500;1
4;15.0;2024-01-01 10:00:15;3.436;-0.500;2
```

A conforming loader for it — no cellpy base class, just the vendor-column
mapping onto the native `RawCols` names:

```python
from __future__ import annotations

from pathlib import Path

import polars as pl
from cellpycore.config import default_schema
from cellpycore.metadata.models import TestMeta
from cellpycore.units import CellpyUnits

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.contract import LoaderResult

_SCHEMA = default_schema().raw


class AwesomeCyclerLoader:
    name = "awesomecycler"
    instrument = "awesomecycler"
    supported_suffixes = (".awe",)

    def can_load(self, source: Path) -> bool:
        return Path(source).suffix.lower() in self.supported_suffixes

    def load(self, source: Path, *, instrument_config=None, **kwargs):
        try:
            frame = pl.read_csv(source, separator=";")
        except Exception as exc:
            raise LoaderError(f"could not parse {source}: {exc}") from exc

        raw = frame.rename(
            {
                "Rec": _SCHEMA.datapoint_num,
                "Time_s": _SCHEMA.test_time,
                "Cycle": _SCHEMA.cycle_num,
                "Voltage_V": _SCHEMA.potential,
                "Current_A": _SCHEMA.current,
            }
        ).with_columns(
            pl.col(_SCHEMA.datapoint_num).cast(pl.Int64),
            pl.col(_SCHEMA.test_time).cast(pl.Float64),
            pl.col(_SCHEMA.cycle_num).cast(pl.Int64),
            pl.col(_SCHEMA.potential).cast(pl.Float64),
            pl.col(_SCHEMA.current).cast(pl.Float64),
            pl.col("Timestamp")
            .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
            .dt.replace_time_zone("UTC")
            .dt.epoch(time_unit="ns")
            .alias(_SCHEMA.epoch_time_utc),
        ).drop("Timestamp")

        raw_units = CellpyUnits(current="A", voltage="V", time="sec")
        test_meta = TestMeta(cell_name=source.stem, test_type="cycling")
        return (LoaderResult(raw=raw, raw_units=raw_units, test_meta=test_meta),)
```

Points worth calling out:

- Only the vendor columns that map onto a `RawCols` name get renamed and kept;
  anything else in the file is simply not selected. Cast every mapped column to
  the dtype the schema expects (`RawCols.dtype_map()` if you want to look it
  up rather than hard-code it) — `harmonize()` and the conformance kit are both
  strict about this.
- `epoch_time_utc` is int64 nanoseconds since the Unix epoch, UTC — not the raw
  `Timestamp` string and not a naive local time. Vendors that report local time
  need a timezone before `.dt.epoch(time_unit="ns")`.
- `raw_units` describes the units this loader actually emits (here plain SI:
  amperes, volts, seconds); cellpy converts from there, so get this right
  rather than pre-converting inside the loader.
- `test_meta` carries only what the file told you (a name, a type). No
  `source_uri`, no `loaded_datetime` — the framework fills those in once the
  file is on its way into a `CellpyCell`.

## Registering it

Declare an entry point; there is no registration call and no plugin API to
call into:

```toml
# your package's pyproject.toml
[project.entry-points."cellpy.loaders"]
awesomecycler = "my_package.loader:AwesomeCyclerLoader"
```

Install your package and cellpy finds it. Check with:

```python
import cellpy
cellpy.print_instruments()      # your loader appears under "installed by other packages"
```

Discovery is lazy and failure-tolerant: a plugin that cannot be imported is
reported as a warning and skipped, it does not stop cellpy from working. A
plugin that loads but does not satisfy the contract is rejected when it is
registered, with a message naming what is missing — rather than failing later,
mid-load, with something obscure.

## Proving it conforms

cellpy ships the conformance kit it uses on its own loaders:

```python
from pathlib import Path
from cellpy.readers.instruments.testing import check_loader

def test_my_loader_conforms():
    check_loader(AwesomeCyclerLoader, Path("tests/data/sample.awe"))
```

It checks the return shape, the frame schema and dtypes, the units, that your
draft metadata carries no provenance, that `can_load()` is fast enough to be
called during routing, and that two loads of the same file agree.

Commit a small real sample file as the fixture — a loader test with a
synthesised file mostly tests the synthesiser.

## Status

The contract and registry are in place as of cellpy 2.0. The built-in loaders
still route through the older module-scanning factory and move over to this
registry as they are ported; the entry-point path above is the supported way to
add a loader from outside cellpy.

## Harmonize / declaration notes (2.0)

These matter if your loader goes through `harmonize(parse())` (the default
single-file raw path when `Reader.use_harmonized_raw` is true):

- **Empty-column cast:** if casting a declared column to its schema dtype would
  null **every** row, `harmonize()` **raises** instead of returning an all-null
  column. Partial loss still warns and coerces to null (legacy
  `pd.to_numeric(errors="coerce")` shape). Point declarations at the right
  vendor column / dtype, or convert first.
- **`LoaderDeclarations.duration_columns`:** use for vendors that write elapsed
  times as strings (`"00:01:00"`, `"0d 00:01:00.00"`). Shipped configurations
  derive this from their `convert_*_to_timedelta` flags; out-of-tree loaders
  should set it explicitly when needed.
- **Deliberate drops:** undeclared vendor columns are dropped with a one-shot
  warning. Silence intentional discards via `LoaderDeclarations.dropped`.

End-user migration notes live in
[`migration_v1_to_v2.md`](../getting_started/migration_v1_to_v2.md).
