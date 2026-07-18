# Migrating from cellpy 1.x to 2.x

This guide covers the user-visible breaks between the 1.x line and cellpy 2.0:
on-disk files, the per-test metadata model, campaign merges, and selected API
cleanups. Keep the `v1.x` branch / 1.x PyPI releases if you need the old
behaviour unchanged until July 2027 (see the project maintenance note).

## File format

| | 1.x / v8 | 2.x / v9 |
|---|----------|----------|
| Default `save()` | HDF5 (`.h5` / `.hdf5` / `.cellpy` as HDF5) | **zip-of-parquet** + `meta.json` (`.cellpy`) |
| Escape hatch | — | `save("out.h5")` or `cellpy_file_format="hdf5"` / `"v8"` |
| What `load()` reads | v4–v8 HDF5 | **v4–v8 HDF5 and v9** (sniffs zip vs HDF5) |

v9 stores raw / steps / summary (and optional fid) as parquet members inside a
zip, with typed metadata in `meta.json`. Parquet columns use **native** header
names plus a schema version stamp.

### Convert once

Old files keep working under `load()`. To rewrite a library to v9:

```python
from cellpy import cellreader

cell = cellreader.CellpyCell()
cell.load("legacy_run.h5")          # v4–v8 HDF5
cell.save("legacy_run.cellpy")      # v9 zip-of-parquet
```

After conversion, prefer `.cellpy` for new writes. Keep a `.h5` copy only if a
downstream tool still requires HDF5.

## Metadata model

2.x exposes `Data.tests` — a `TestMetaCollection` keyed by compact `test_id`
(0 for a single unmerged test). The legacy boxes (`meta_common` /
`meta_test_dependent`) remain the in-memory source of truth for the active
test; extra tests live in the collection.

- **v8 HDF5** still persists only the **active** test (legacy limitation).
- **v9 `.cellpy`** persists the **full** collection (active + extras), plus
  units/limits and load provenance where available.

Standalone helpers (cellpy-owned; `cellpycore.metadata.io` archive stubs stay
stubs):

```python
from cellpy.readers.cellpy_file.meta_archive import (
    save_meta_archive,
    load_meta_archive,
)
```

## Campaign merge

`CellpyCell.merge(..., mode="campaign")` folds different tests into one object
with distinct `test_id` values on raw (and on steps after `make_step_table`).
Saving that object as **v9** round-trips both `TestMeta` rows and the
`test_id` columns. Saving as **v8** still drops non-active test metadata.

```python
left.merge(right)                 # campaign (default for distinct tests)
left.save("campaign.cellpy")      # keeps tests [0, 1] + test_id columns
```

## API cleanups worth knowing (#509)

- Prefer `cellpy.get` as the entry point; `merge_cells` / `print_instruments`
  are exported at package level.
- `make_summary(exclude_step_types=[...])` replaces the old no-effect selector
  exclusion kwargs (those still warn only).
- Curve helpers live in `cellpy.readers.capacity_curves` with thin
  `CellpyCell` delegates — call sites on `CellpyCell` stay the same.
- `cellpy.utils.easyplot` was **removed** in 2.0 (deprecated since 1.1); use
  `cellpy.utils.plotutils` and `cellpy.utils.collectors` instead.
- See [`DEPRECATIONS.md`](../../DEPRECATIONS.md) for the remaining registered
  removal schedule.

## Breaking change: `get_cap` frame columns (#540)

The DataFrame returned by `CellpyCell.get_cap` (and the collectors built on it)
now uses the **native** `cellpycore` curve-column names:

| was (1.x / early v2) | now (v2) |
|---|---|
| `voltage` | `potential` |
| `cycle` | `cycle_num` |
| `capacity` | `capacity` (unchanged) |
| `direction` | `direction` (unchanged) |

If you index the `get_cap` result directly (e.g. `df["voltage"]`,
`df.groupby("cycle")`), rename to `potential` / `cycle_num`. The in-repo
consumers (`plotutils.cycles_plot`, the batch collectors, `ica`, the CSV/Excel
exporters) are already updated. The OCV-curve frame and `ica`'s dQ/dV output
frame keep their own column names for now.

## Dependencies

cellpy 2.x depends on **`cellpycore`**. Release builds pin an exact
`cellpycore==X.Y.Z` so a given cellpy tag maps to one core revision. If you
develop against an editable sibling checkout, follow
`CONTRIBUTING.md` / the dual-repo sync notes — do not commit path overrides.
