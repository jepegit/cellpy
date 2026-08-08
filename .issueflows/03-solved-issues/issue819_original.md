# Issue #819: cellpy.get: when instrument= is set, do not auto-pick native .h5/.hdf5 format

Source: https://github.com/jepegit/cellpy/issues/819

## Original issue text

## Problem / context

`cellpy.get(..., auto_pick_cellpy_format=True)` (the default) treats `.h5` / `.hdf5` as native cellpy files whenever `instrument` is not exactly `arbin_sql_h5`. Other Arbin SQL variants (or a missing/mismatched instrument) then hit the native reader and fail with `No object named data_df in the file` — easy to misread as a corrupt file.

cellpy already special-cases `arbin_sql_h5`, but apps that always pass an explicit instrument still need `auto_pick_cellpy_format=False` for defense in depth.

**Workaround (cellpy-simple-gui #41):** `load_raw` always sets `auto_pick_cellpy_format=False`; Load cells stays on the native path and the UI hints that Arbin SQL HDF5 belongs under Import raw.

## Spec

When `instrument=` is set (any non-empty / non-native instrument), never auto-pick cellpy format from the `.h5`/`.hdf5` suffix — honour the instrument loader. Alternatively, document clearly that callers must disable auto-pick for every raw `.h5` loader.

## Acceptance criteria

- [ ] `cellpy.get(path_to_raw.h5, instrument=<raw_loader>)` does not route through the native cellpy reader solely because of the suffix.
- [ ] Native `.cellpy` / intentional cellpy hdf5 loads without an instrument still work.
- [ ] Regression test covers at least one raw `.h5` instrument path vs native pick.
- [ ] Docs mention the rule (instrument wins over suffix auto-pick).


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy ≥2.1.1.post4. Full write-up: [CELLPY_PAINPOINTS.md](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
