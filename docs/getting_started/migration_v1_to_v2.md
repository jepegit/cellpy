# Migrating from cellpy 1.x to 2.x

This guide maps **user-visible breaks** between the 1.x line and cellpy 2.0
(including current 2.0 alphas on `master`) to a named fix or workaround. Keep
the `v1.x` branch / 1.x PyPI releases if you need unchanged 1.x behaviour.

After **cellpy 2.0 GA**, the `v1.x` line is **bugfix-only for 12 months** from
the 2.0 release date (decision #438-6). Feature work lands only on 2.x.

## Support matrix (files)

| | 1.x | 2.x (current alphas / intended GA) |
|---|-----|-------------------------------------|
| Default `save()` | HDF5 (`.h5` / `.hdf5` / `.cellpy` as HDF5) | **v9** zip-of-parquet + `meta.json` (`.cellpy`) |
| `load()` | v4–v8 HDF5 | **v4–v8 HDF5 and v9** (sniffs zip vs HDF5) |
| Write v8 / HDF5 | default | Escape: `save("out.h5")` or `cellpy_file_format="hdf5"` / `"v8"` |
| Very old (pre-v8) rewrite | `cellpy convert` on **1.x** | Prefer convert on 1.x, then open in 2.x; or `load` + `save` to v9 when 2.x still reads that vintage |

v9 stores raw / steps / summary (and optional fid) as parquet members inside a
zip, with typed metadata in `meta.json`. Parquet columns use **native** header
names plus a schema version stamp.

### Convert once

```bash
# CLI (2.x): default output is v9
cellpy convert old.h5                 # → .cellpy (v9)
cellpy convert old.h5 --to v8         # keep HDF5 if you must
```

```python
from cellpy.readers.cellreader import CellpyCell

cell = CellpyCell()
cell.load("legacy_run.h5")          # v4–v8 HDF5
cell.save("legacy_run.cellpy")      # v9 zip-of-parquet
```

**Pip vs conda for legacy HDF5:** on pip, PyTables is **not** a required
dependency anymore (`#570`). Install `pip install cellpy[legacy-files]` (or
`cellpy[all]`) to read/write v4–v8 `.h5`. Without it, cellpy raises
`OptionalDependencyError` with that install hint. **Conda packages still ship
pytables** — conda users are unaffected. After a one-time convert to v9, you
can drop the extra.

## Frames and column names

### What is true on current 2.0 alphas

- **Default `CellpyCell` frames are still pandas**, with a legacy↔native bridge
  in play for many paths. A full **polars** user-facing frame flip is the
  remaining flag-day — watch `HISTORY.md` when it lands; do not assume every
  API already returns `polars.DataFrame`.
- Prefer **`cell.schema`** for column identities:
  `cell.schema.raw` / `.steps` / `.summary` (native `cellpycore` column
  objects). Legacy `headers_normal` / `headers_summary` / `headers_step_table`
  still work via a shim and warn once per attribute (removal **2.1**). See
  [`DEPRECATIONS.md`](../reference/deprecations.md).
- Column renames (raw examples): `voltage` → `potential`, `cycle_index` →
  `cycle_num`, capacity/energy columns gain a `cumulative_` prefix in the
  native schema. Full table:
  [`header_migration_map.md`](../other/header_migration_map.md).

### Opt-in native schema (advanced)

`CellpyCell(native_schema=True)` keeps frames in native names and runs the
polars engine for the supported pipeline (`from_raw` / `load` → steps →
summary → v9 `save`). Legacy-named consumers (`get_cap`, exporters, plotting,
campaign merge) are **not** all supported on that path yet — see `HISTORY`
(#511).

### Breaking: `get_cap` frame columns (#540)

| was (1.x / early v2) | now |
|---|---|
| `voltage` | `potential` |
| `cycle` | `cycle_num` |
| `capacity` | `capacity` (unchanged) |
| `direction` | `direction` (unchanged) |

If you index the `get_cap` result directly, rename. In-repo consumers
(`plotutils.cycles_plot`, collectors, `ica`, CSV/Excel exporters) are updated.

## Configuration: `prms` → `cellpy.config`

- Runtime config is the pydantic-settings stack under **`cellpy.config`**
  (TOML: `cellpy.toml`). See [configuration](configuration.md) and the
  generated [configuration reference](configuration_reference.md).
- Legacy **`prms.Section.field`** still forwards through a shim with a
  one-shot `DeprecationWarning` per name; prefer `cellpy.config` for new code.
- **`import cellpy` no longer performs config file I/O** — first access /
  explicit setup loads settings (`#453`).
- `cellpy setup` writes/migrates TOML; `cellpy info --config` inspects the
  active stack (`#454`).

## Plotting

- **`cellpy.utils.easyplot` was removed in 2.0** (#544). Use
  `cellpy.utils.plotutils` and `cellpy.utils.collectors`.
- Prefer native x names (`x="cycle_num"`). Legacy `x="cycle_index"` is accepted
  again with a warning (#593).
- `plotutils.summary_plot_legacy` is a deprecated alias of `summary_plot`
  (removal 2.1).

### If a 2.0.0a5 script hit plotting bugs (#593 / #567 Phase 0)

These were fixed on master; worth knowing if you ran alphas:

| Symptom on 2.0.0a5 | What to do |
|---|---|
| `raw_plot` / `cycle_info_plot` → `KeyError: 'voltage'` | Upgrade; plots work again |
| `summary_plot(..., x="cycle_index")` → `KeyError` | Upgrade; or use `x="cycle_num"` |
| `summary_plot(..., y="capacities_*_split_constant_voltage")` **mutated** `c.data.summary` in memory | **Re-load the cell** (or upgrade first). Nothing was written to disk — unlike the Maccor case below |
| Hard-coded legacy step-table names inside `cycle_info_plot` | Upgrade |

Plotting tests now run under `MPLBACKEND=Agg` in Tier-1 CI and the nightly
matrix (#594).

## ICA / DVA (#566, #591)

`cellpy.ica.dqdv()` (also re-exported as `cellpy.utils.ica`) returns a **long
frame**: `cycle`, `direction`, `voltage`, `capacity`, `dqdv` (plus deprecated
duplicate column `dq` for one release).

- **`direction` is cell-centric** — `"charge"` means the *cell* is charging
  (same sense as `get_ccap` / `get_dcap` / summary). For **anode** cells, batch
  ICA film plots labelled "charge" may show the branch that used to be labelled
  "discharge" under the old electrode-centric convention — one flip, then
  labels agree everywhere.
- No NaN "splitter" row between half-cycles (one fewer row per cycle vs 1.x).
- Failed half-cycles emit `RuntimeWarning` and record
  `frame.attrs["failures"]` instead of silent empty arrays.
- New: `ica.dvdq()` for differential voltage analysis.
- Deprecated (removal **2.1**): `Converter`, `dqdv_cycle`, `dqdv_cycles`,
  `dqdv_np`, old `dqdv(split=…/tidy=…/cycle=…/label_direction=…)` kwargs, and
  the `dq` column — see [`DEPRECATIONS.md`](../reference/deprecations.md).

`BatchICACollector.data` is the same specced frame; filter on string
`direction` labels, not ±1 codes.

## Metadata and campaign merge

2.x exposes `Data.tests` — a `TestMetaCollection` keyed by compact `test_id`
(0 for a single unmerged test). Legacy boxes (`meta_common` /
`meta_test_dependent`) remain the in-memory source of truth for the active
test; extras live in the collection.

- **v8 HDF5** still persists only the **active** test.
- **v9 `.cellpy`** persists the **full** collection (+ units/limits /
  provenance where available).

```python
left.merge(right)                 # campaign (default for distinct tests)
left.save("campaign.cellpy")      # keeps tests + test_id columns on v9
```

## API cleanups (#509 and friends)

- Prefer `cellpy.get` as the entry point; `merge_cells` / `print_instruments`
  are package-level exports.
- `make_summary(exclude_step_types=[...])` replaces old no-effect selector
  exclusion kwargs (those still warn only).
- Curve helpers live in `cellpy.readers.capacity_curves` with thin
  `CellpyCell` delegates — call sites on `CellpyCell` stay the same.

## Dependencies (#570)

Dropped from the **required** pip set: `python-box`, `ruamel.yaml`,
`python-dotenv` (env-file behaviour still available transitively via
pydantic-settings). **`tables` (PyTables)** moved to the `legacy-files` extra
(see [Support matrix](#support-matrix-files)).

cellpy 2.x depends on **`cellpycore`** with an exact pin on releases. Dual-repo
dev: see `CONTRIBUTING.md` — do not commit path overrides.

## Loaders and raw ingestion (#560)

Single-file raw loads default to **`harmonize(parse())`**
(`Reader.use_harmonized_raw=True`). Set `False` for the legacy rename
fallback. Practical deltas:

- Arbin wide-aux columns keep values under `aux_<quantity>_<name>`
  (e.g. `aux_0_u_C` → `aux_temperature_0`).
- Vendor `data_point` / `datapoint_num` is preserved (not re-minted as `0..n-1`).
- Unknown undeclared vendor columns are still dropped, but now **warn once**
  naming them; loader authors can mark deliberate drops via
  `LoaderDeclarations.dropped`.
- Maccor model-one: vendor `Watt-hr` maps to **energy**
  (`cumulative_charge_energy`), not power — same values, corrected name.

Custom / out-of-tree loaders: see
[Writing an instrument loader](../other/writing_a_loader_plugin.md) for
`harmonize()` cast behaviour and `duration_columns`.

## If you used 2.0.0a5

### Maccor `.txt` → zero capacities (#580 / #581)

Maccor txt files loaded with **zero capacities** on 2.0.0a5
(`Series.update(inplace=True)` broke under pandas 3; the failure was
swallowed). Fixed on master.

**cellpy files saved from Maccor raw on 2.0.0a5 can have zeros baked in.**
Upgrading alone does **not** repair them — re-load from the raw `.txt` and
save again. Only `maccor_txt` was affected (the shipped config with
`split_capacity: True`).

### Do **not** re-load Neware for the loader-port oracle

Bugs found while building the `#560` value-parity oracle were on a
pre-flag-day path (`harmonize` limited to the maccor pilot). **Neware
capacities loaded on 2.0.0a5 were correct.** There is no user-facing Neware
re-load advisory.

## Behavior deltas (1.0.3 → 1.0.4 / 2.0)

Architecture plan §7 tracks known summary/step deltas (CE inversion, coulombic
difference sign, dropped `shifted_*` / `reference_voltage_*` columns, etc.).
**Unsigned rows stay under review before 2.0 GA** (release checklist #574).
When a verdict lands, it will appear here and in `HISTORY.md`.

| ID | Topic | Status in this guide |
|---|---|---|
| Δ1 | `coulombic_difference` family sign | Under review before GA |
| Δ2 | `coulombic_efficiency` inversion (headline) | Under review before GA |
| Δ3 | Dropped `shifted_*` specific columns | Under review before GA |
| Δ4 | Dropped `reference_voltage_*` step aggregates | Under review before GA |
| Δ5 | Cycle-9 step misclassification fix | Treated as bug fix (keep) |
| Δ6 | steps `sub_type` `"None"` → null | Under review before GA |
| Δ7 | `discharge_c_rate` engine disagreement | Under review before GA |

## Deprecations

Every 2.0 shim with a 2.1 removal date is listed in
[`DEPRECATIONS.md`](../reference/deprecations.md) (generated from
`cellpy._deprecation`). Regenerate with:

```bash
uv run python -m cellpy._deprecation
```
