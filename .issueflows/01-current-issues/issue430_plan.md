# Issue #430 — Plan

## Goal

Lock current `prms` / `prmreader` / `cellpy setup` behavior in characterization tests **before**
the pydantic-settings rework (Step 0 in
[`cellpy2-configuration-and-parameters-plan.md`](../../architecture-plan/cellpy2-configuration-and-parameters-plan.md)).
The inventory test becomes the field-by-field parity contract for Step 2.

## Constraints

- **Behavior-preserving only** — assert today's outputs; no production refactors (including
  fixing known type lies like `Reader.limit_loaded_cycles`).
- **Scope = save-able config sections only** — mirror `_pack_prms()`:
  `Paths`, `FileNames`, `Db`, `DbCols`, `CellInfo`, `Reader`, `Materials`, `Instruments`, `Batch`.
  Exclude module-level `_cellpyfile_*`, `_globals_*`, `DbColsUnitClass`, and other
  non-config constants (config plan Step 1).
- **Plan doc paths** — issue text says `code-reviews/`; read
  [`architecture-plan/cellpy2-configuration-and-parameters-plan.md`](../../architecture-plan/cellpy2-configuration-and-parameters-plan.md)
  and [`cellpy2-plans-gap-analysis.md`](../../architecture-plan/cellpy2-plans-gap-analysis.md) §G7.
- **Fast PR gate** — mark a small subset `@pytest.mark.essential`; keep Tier 1 under ~2 min.
- **Test isolation** — characterization tests must not depend on the developer's home-dir
  `.cellpy_prms_*.conf`; use `tmp_path` + `prmreader._read_prm_file` / `_write_prm_file`
  (existing `test_prms.py` pattern). Restore or avoid mutating global `prms` where practical
  (document accepted leak if full restore is impractical for a given test).

### Prior art

| Hit | Module / file | Reuse |
|-----|---------------|--------|
| Config round-trip (partial) | `tests/test_prms.py` | **Extend** — issue explicitly names this file; add missing behaviors. |
| OtherPath unit tests | `tests/test_otherpaths.py` | **Coexist** — deep OtherPath API; new tests cover *prmreader coercion* path only. |
| Setup CLI smoke (dry-run only) | `tests/test_cellpy_cmd.py` (`test_cli_setup*`) | **Extend** — add non-dry-run file/dir creation characterization. |
| Default YAML template | `cellpy/parameters/.cellpy_prms_default.conf` | **Reference** — cross-check inventory; code dataclass defaults are authoritative when they differ (e.g. `Materials.cell_class`). |
| `OTHERPATHS` | `cellpy/parameters/internal_settings.py` | **Reuse** — `rawdatadir`, `cellpydatadir` coercion rules. |
| Env fixtures | `tests/conftest.py` (`mock_env_cellpy_*`) | **Reuse** for OtherPath credential pickup tests. |
| Stage 0 pattern | `issue429_plan.md` (solved) | **Mirror** — `*_support.py` helper module + essential budget. |
| Step 0 spec | `architecture-plan/cellpy2-configuration-and-parameters-plan.md` § Step 0 | **Authoritative** acceptance checklist. |
| Graph | `prms.py`, `prmreader.py`, `cli.setup` | Confirms surface area. |
| Toolbox | `.issueflows/00-tools/` | Empty — no helpers to reuse. |

## Approach

### 1. Shared helpers — `tests/prms_support.py`

Small module (not production code):

- `fresh_section_defaults()` — build default-value dict per save-able section from dataclass
  `fields()` / fresh instances (`PathsClass()`, `ReaderClass()`, …). For `Instruments`,
  serialize via `prmreader._convert_instruments_to_dict(InstrumentsClass(...))` using the
  module's `_Arbin` / `_Maccor` / … seed dicts (matches runtime defaults).
- `collect_prms_inventory()` — flatten to sorted `(section, field, default)` triples with
  normalized values (`None`, `bool`, `int`, `float`, `str`, plain `list`/`dict` for
  `Instruments` nesting). Paths: serialize via `prmreader._convert_paths_to_dict` on a fresh
  `PathsClass()` rooted at a **fixed** `tmp_path` (avoids machine-specific home-dir noise in
  the inventory snapshot).
- `write_minimal_prm_file(path, overrides=None)` — thin wrapper around existing
  `config_file_txt` fixture content for precedence tests.
- `assert_inventory_equal(actual, expected)` — diff added/removed/changed triples with a
  readable pytest failure message.

### 2. Extend `tests/test_prms.py`

Organize by concern (same file, per issue):

#### A. Inventory parity (`@pytest.mark.essential`)

1. `collect_prms_inventory()` on fresh sections.
2. Assert exact match against frozen `EXPECTED_PRMS_INVENTORY` in `prms_support.py` (or
   adjacent constant block).
3. Fails if any field is added/removed or default changes without an intentional snapshot
   update — this is the Step 2 pydantic parity contract.

**Snapshot scope:** all `_pack_prms` sections and nested `Instruments.{Arbin,Maccor,Neware,Batmo}`
keys present in `_Arbin` et al. Include `Reader.ensure_summary_table`,
`Reader.max_raw_files_to_merge`, `FileNames.raw_extension`, `Batch.auto_use_file_list`, etc.
Record current values even when `.cellpy_prms_default.conf` differs (documents real code defaults).

#### B. Config file round-trip (`@pytest.mark.essential`)

Extend beyond existing `test_save_prm_file` / `test_save_otherpath_prms_cellpy`:

1. **Full section round-trip** — load `config_file_txt` into tmp yaml, mutate one field per
   section (Reader, Batch, DbCols, Materials, Instruments.tester, Paths.outdatadir), write,
   reload, assert all mutations persisted.
2. **YAML stability** — after round-trip, re-read with `_read_prm_file_without_updating` and
   assert key subtrees still present (guards `_pack_prms` / `_update_prms` symmetry).

#### C. Precedence: file vs runtime mutation (`@pytest.mark.essential`)

Document and lock current semantics:

1. `_read_prm_file` **overwrites** prior runtime `prms.Reader.cycle_mode` with file value.
2. Runtime `setattr` after load **wins in memory** until next `_read_prm_file`.
3. `_write_prm_file` persists runtime values (partially covered today — make explicit with
   a field that differs from loaded file, assert file on disk after write).

#### D. OtherPath coercion in `Paths` (full suite; one essential smoke)

Extend existing OtherPath tests:

1. **OTHERPATHS fields** (`rawdatadir`, `cellpydatadir`) → `OtherPath` after `_update_prms`;
   `full_path` preserved for `scp://…` URIs (existing test).
2. **Local resolve** — relative path under `tmp_path` with `resolve_paths=True` resolves to
   absolute local path (records `_update_prms` `resolve()` behavior).
3. **`db_filename` exception** — stays `str`, not `Path`/`OtherPath`.
4. **Non-OTHERPATHS path fields** — `outdatadir` becomes `pathlib.Path` and resolves locally.
5. **Property round-trip** — setting `prms.Paths.rawdatadir = OtherPath(...)` then
   `_convert_paths_to_dict` yields `full_path` string (write path).

#### E. `.env_cellpy` secret pickup (`@pytest.mark.essential`)

Chain under test: `Paths.env_file` → `prmreader._load_env_file()` → `os.getenv` consumed by
`internals/otherpath.py` / `connections.py`:

1. Write tmp `.env_cellpy` with `CELLPY_USER`, `CELLPY_HOST`, `CELLPY_PASSWORD` (or key).
2. Point `prms.Paths.env_file` at it; call `_load_env_file()`.
3. Assert `os.getenv("CELLPY_*")` matches (reuses `parameters` / `mock_env` values pattern).
4. One smoke asserting `OtherPath` remote URI + loaded env vars reach
   `OtherPath._connect_kwargs` / fabric prep without network (monkeypatch fabric connect;
   mirror `test_copy_remote_simple` pattern but entry via prmreader env load).

#### F. `cellpy setup` file/folder creation (full suite)

Extend `tests/test_cellpy_cmd.py` (keeps CLI tests together; import `NUMBER_OF_DIRS`):

1. **Non-dry-run setup** — `CliRunner.isolated_filesystem()`, invoke
   `setup --test_user <name> --silent` (non-interactive reset path creates dirs).
2. Assert **11** directories created under expected root (existing `NUMBER_OF_DIRS` constant).
3. Assert `.cellpy_prms_<test_user>.conf` written and parseable by `_read_prm_file_without_updating`.
4. Assert `.env_cellpy` example written when missing (content contains `CELLPY_PASSWORD` placeholder).
5. Keep existing `--dry-run` tests unchanged.

### 3. Documentation

Short **Configuration characterization** subsection in `tests/README.md`: points at extended
`test_prms.py`, `prms_support.py`, essential subset, and how to update `EXPECTED_PRMS_INVENTORY`
when defaults change intentionally.

## Files to touch

| Path | Change |
|------|--------|
| `tests/prms_support.py` | **New** — inventory collection, snapshot, helpers |
| `tests/test_prms.py` | **Extend** — inventory, precedence, round-trip, OtherPath, env integration |
| `tests/test_cellpy_cmd.py` | **Extend** — non-dry-run `setup` dir/file creation test |
| `tests/README.md` | Document new/extended characterization coverage |

No changes to `cellpy/parameters/prms.py`, `prmreader.py`, or `cli.py`.

## Test strategy

```bash
# During development (inner loop)
uv run pytest tests/test_prms.py tests/test_cellpy_cmd.py::test_cli_setup_creates_dirs_and_files -v

# PR gate subset (after marking essential)
uv run pytest -m essential --ignore=tests/test_plotutils_summary_plot.py

# Before merge
uv run pytest tests/test_prms.py tests/test_cellpy_cmd.py
uv run pytest   # full suite green on master
```

**Essential budget:** target **4–5** new essential tests (inventory + round-trip + precedence +
env pickup + one OtherPath/prm coercion smoke). Setup non-dry-run and deep OtherPath resolve
stay unmarked.

## Open questions

1. **Inventory snapshot for `Paths` defaults** — plan uses fresh `PathsClass()` rooted at a
   fixed `tmp_path` so the snapshot is machine-independent. **Recommended:** accept this;
   alternative is field-name-only inventory without path values (weaker parity contract).
2. **`.cellpy_prms_default.conf` vs code mismatches** — e.g. `Materials.cell_class` (`Li-Ion`
   in code vs `LIB` in default conf), `Instruments.Arbin` SQL defaults. **Recommended:** inventory
   records **code/dataclass** defaults (runtime truth); note mismatches in `tests/README.md` only.
3. **`test_set_prm_inside_cellpy`** — currently `pass`. **Recommended:** leave as stub or delete
   in `/iflow-start` only if we confirm no external reference; not required for acceptance.
4. **Global `prms` mutation cleanup** — **Recommended:** save/restore key fields in new tests via
   fixture; accept that full isolation waits for v2 `override()` (out of scope).

## Branch

Suggest `430-prms-characterization-tests` off current `master` before `/iflow-start`.

**Branch preflight (2026-07-09):** on `master`, clean except untracked issue-flow files; 0 behind /
1 ahead of `origin/master`.
