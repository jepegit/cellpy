# Issue #779 plan — SupportsIncrementalLoad protocol

## Goal

Add the optional cellpy-side loader capability from the live-incremental
design §3: `SupportsIncrementalLoad`, `LoadMarker`, and `IncrementalChunk`.
A loader can advertise `load_since` without cellpycore knowing the protocol.
No loader implements it in this issue.

## Constraints

- Cellpy only. Do not add these types to cellpycore. Core `update_data`
  stays the merge primitive and never sees `LoadMarker`.
- Optional. `InstrumentLoader` and `check_loader` stay unchanged. A loader
  that omits `load_since` still conforms and still full-reloads later
  (#164).
- Out of scope: `load_since` on arbin/neware/maccor (#780),
  `CellpyCell.update()` and marker persistence (#164), `live.py` (#781),
  batch poll (#782).
- `new_raw` is a polars frame. `cellpycore.merge.update_data` already takes
  `new_raw: pl.DataFrame`, and `LoaderResult.raw` is polars. Overlap may
  include the tail; core trims on `source_datapoint_num`, then
  `datapoint_num`.
- Design: `cellpy-design-and-development/active/cellpy2-live-incremental-design.md`
  §3, and epic #783 stage 2.

### Prior art

- `InstrumentLoader` / `LoaderResult` in
  `cellpy/readers/instruments/contract.py` — structural Protocol, methods
  only, so `@runtime_checkable` + `issubclass` works. Mirror that split.
  `LoaderCapabilities` holds non-method members separately for the same
  reason. Coexist: do not add `load_since` to `InstrumentLoader`.
- `tests/test_loader_contract.py` — structural conformance tests (#210).
  New tests sit beside that idea, in their own file, so the frozen 2.0
  loader contract stays untouched.
- `cellpycore.merge.update_data` — overlap contract this marker must match.
  Do not call it from L1.
- `tests/incremental_support.py` (#778) — tail slicing for the golden
  oracle. L2 will use it. Not used here.
- `.issueflows/00-tools/` — nothing for a Protocol. Graph absent.

## Approach

1. In `contract.py`, add two dataclasses and one Protocol. Methods only on
   the Protocol (same `issubclass` rule as `InstrumentLoader`).

   - `LoadMarker` — `frozen=True`, `slots=True`. Fields, all optional:
     `last_source_datapoint_num: int | None = None`,
     `byte_offset: int | None = None`,
     `row_count: int | None = None`.
     No validator. `None` passed to `load_since` means "no marker yet"
     (return every row). An all-None `LoadMarker` is allowed and means
     the same thing; L2 loaders set the one field their source uses.
   - `IncrementalChunk` — `frozen=True`, `slots=True`, matching
     `LoaderResult`. Fields: `new_raw: pl.DataFrame`, `marker: LoadMarker`,
     `complete: bool = False`. `complete` is a hint only.
   - `SupportsIncrementalLoad` — `@runtime_checkable` Protocol with
     `load_since(self, source: Path, marker: LoadMarker | None) -> IncrementalChunk`.
     `source` is a local path, same rule as `InstrumentLoader.load`.
     Docstring: rows may overlap the existing tail; do not trim here.

2. Do not register the protocol, do not change `testing.check_loader`, and
   do not add `load_since` to any shipped loader.

3. Short design note
   `.issueflows/04-designs-and-guides/incremental-load-protocol.md`:
   cellpy hosts the protocol, `new_raw` is polars, core is unchanged.
   Link #779.

## Files to touch

- `cellpy/readers/instruments/contract.py` — the three types and docstrings.
- `tests/test_incremental_protocol.py` — essential structural tests.
- `.issueflows/04-designs-and-guides/test-registry.md` — one row per new test.
- `.issueflows/04-designs-and-guides/incremental-load-protocol.md` — the note above.

## Test strategy

`uv run pytest tests/test_incremental_protocol.py tests/test_loader_contract.py -m essential`

New tests, all `@pytest.mark.essential`:

- A class with only `load_since` is a `SupportsIncrementalLoad` via
  `issubclass` and `isinstance`, and is not an `InstrumentLoader`.
- `GoodLoader` from the existing contract tests (or a local twin without
  `load_since`) is an `InstrumentLoader` and is not a
  `SupportsIncrementalLoad`.
- A class with both `load` and `load_since` matches both protocols.
- `LoadMarker()` and `IncrementalChunk` are frozen.
- `check_loader` still accepts a loader that has no `load_since`.

No file fixtures and no `update_data` call.

## Open questions

None.
