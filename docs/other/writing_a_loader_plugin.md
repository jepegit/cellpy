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

## Registering it

Declare an entry point; there is no registration call and no plugin API to
call into:

```toml
# your package's pyproject.toml
[project.entry-points."cellpy.loaders"]
mycycler = "my_package.loader:MyCyclerLoader"
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
    check_loader(MyCyclerLoader, Path("tests/data/sample.mcx"))
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
