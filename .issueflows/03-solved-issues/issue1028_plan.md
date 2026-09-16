# Issue #1028 — plan

## Goal

Ship `"cellpy"` as the packaged default for `file_names.cellpy_file_extension`,
so a fresh install (no user `cellpy.toml`) looks for and writes
`<run_name>.cellpy` instead of `<run_name>.h5`. Existing configs that set the
key stay unchanged.

## Constraints

- Keep `FileNamesConfig` (`config/models.py`) and `FileNamesClass`
  (`parameters/prms.py`) in lockstep — both are live defaults today.
- Value is the suffix **without** a leading dot (`"cellpy"`), matching
  `filefinder.search_for_files` (`V9_EXTENSION` is `".cellpy"`).
- Do not migrate user `cellpy.toml` / legacy `~/.cellpy_prms_*.conf`.
- Do not retarget real HDF5 fixtures or explicit `save(..., format="hdf5")` /
  `.h5` paths. Those are the legacy layout, not this setting.
- Docs live on `master` in the same PR (`docs-on-master.md`).
- `HISTORY.md` Unreleased bullet in this PR (`/iflow-close` also writes one;
  one bullet is enough — build writes it, close does not duplicate).

### Prior art

- `cellpy.config.models.FileNamesConfig.cellpy_file_extension` — pydantic
  source of truth for `config.file_names`.
- `cellpy.parameters.prms.FileNamesClass.cellpy_file_extension` — parallel
  dataclass default; same string today.
- `cellpy/parameters/.cellpy_prms_default.conf` — packaged legacy-conf
  mirror of the same default.
- `cellpy.readers.filefinder.search_for_files` — only runtime consumer of the
  setting when `cellpy_file_extension` is omitted; builds
  `f"{run_name}.{ext}"`.
- `tests/conftest.py::default_file_names` — pins packaged `file_names`
  defaults so a developer `cellpy.toml` cannot hide CI. After the flip this
  fixture yields `"cellpy"`; keep it, update assertions that expected `.h5`.
- `tests/prms_support.py::EXPECTED_PRMS_INVENTORY` — characterization of
  packaged defaults (`#430`); must list `"cellpy"`.
- `cellpy.readers.cellpy_file.format.V9_EXTENSION` (`".cellpy"`) — native
  format suffix; do not change it. Do not import it into the config default
  (dot vs no-dot).
- Hardcoded `.h5` elsewhere is **not** this setting: HDF5 fixtures
  (`tests/fdv.py` paths), `arbin_sql_h5` raw ext, `cli_api` v8 target suffix,
  `cellreader` suffix routing, `helpers.py` deprecated convert helper
  (`+ ".h5"`, warned for removal in v0.4.0). Leave those.
- Toolbox (`00-tools/`): nothing for config defaults.
- Graph: `graphify-out/graph.json` absent; grep-only.

## Approach

1. Change the three packaged defaults from `"h5"` / `h5` to `"cellpy"` /
   `cellpy`:
   - `cellpy/config/models.py`
   - `cellpy/parameters/prms.py`
   - `cellpy/parameters/.cellpy_prms_default.conf`
2. Docs: `docs/getting_started/configuration_reference.md` default column
   `h5` → `cellpy`. `docs/guides/batch_database.md` already names the setting
   without a default — no change.
3. Tests that assert the **constructed default filename** (not a fixture
   path):
   - `tests/prms_support.py`: inventory expected value `"cellpy"`.
   - `tests/test_filefinder.py`: `runA.h5` → `runA.cellpy`;
     `test_search_for_files_with_dirs` currently compares to
     `parameters.cellpy_file_name` (`20160805_test001_45_cc.h5`, a real
     HDF5 fixture name). Assert `f"{parameters.run_name}.cellpy"` instead.
   - `tests/test_cell_readers.py::test_search_for_files`: same assertion
     swap.
   - `tests/conftest.py::default_file_names` docstring: say the packaged
     default is `.cellpy`, and the fixture still isolates developer toml.
4. Leave `tests/fdv.py` fixture paths and `get_cellpy_file_path` on `.h5`
   (those files exist under `testdata/hdf5/`).
5. `HISTORY.md` Unreleased: default flip, existing toml untouched, `#1028`.
6. No `agents.md` / `AGENTS.md` edit — those already show `.cellpy` save
   paths and do not document this config default.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/config/models.py` | `FileNamesConfig.cellpy_file_extension` default `"cellpy"` |
| `cellpy/parameters/prms.py` | `FileNamesClass.cellpy_file_extension` default `"cellpy"` |
| `cellpy/parameters/.cellpy_prms_default.conf` | `cellpy_file_extension: cellpy` |
| `docs/getting_started/configuration_reference.md` | default column |
| `tests/prms_support.py` | inventory expected value |
| `tests/test_filefinder.py` | constructed-name asserts |
| `tests/test_cell_readers.py` | constructed-name assert |
| `tests/conftest.py` | fixture docstring |
| `HISTORY.md` | Unreleased bullet |

## Test strategy

- `uv run pytest -m essential` — merge gate; includes
  `test_prms.py` inventory (uses `EXPECTED_PRMS_INVENTORY`) and several
  `test_cell_readers` essentials (the search-for-files test itself is
  unmarked).
- Targeted: `uv run pytest tests/test_filefinder.py tests/test_prms.py tests/test_cell_readers.py::test_search_for_files -q`
- Full `uv run pytest` before close if essential is green and the targeted
  filefinder/prms tests pass.
- New tests: none. The inventory + filefinder asserts are the contract.
- Essential marker: no new tests. Do not mark the existing filefinder
  tests essential (name-construction only; inventory already essential via
  `test_prms.py`).

## Open questions

- **Deprecated `helpers.py` hardcoded `.h5`?** Recommend leave it. Dead
  convert helper, already `DeprecationWarning`. Not the config default.
- **`agents.md` mention?** Recommend skip. No current mention of this key;
  save examples already use `.cellpy`.
