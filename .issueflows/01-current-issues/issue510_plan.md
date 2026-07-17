# Issue #510 — plan

Source: https://github.com/jepegit/cellpy/issues/510

## Goal

Ship **v2 Phase 4**: a new on-disk cellpy-file that round-trips full `TestMetaCollection` (+ units/limits), cellpy-owned archive load/save (core stubs stay stubs), then release discipline (exact `cellpycore==` pin + v1→v2 migration guide) that gates the v2.0 tag.

## Constraints

- **Depends on Phases 1–3** — already landed: #506/#514, #507/#515, #508/#516, #509/#517. Follow-ups (#518–#520, #511) are **not** blockers for format work.
- **Boundary:** real persistence lives in **cellpy**; `cellpycore.metadata.io.load_archive` / `save_archive` stay `NotImplementedError` stubs.
- **Container already decided** ([architecture-plan `cellpy2-native-headers-migration-plan.md`](../../../architecture-plan/cellpy2-native-headers-migration-plan.md) / #438): **v9 = zip-of-parquet + sidecar `meta.json`**, not another HDF5 layout. Epic wording “HDF5 layer” is stale relative to that decision.
- **Back-compat:** keep reading v4–v8 HDF5 via existing `cellpy.readers.cellpy_file` readers; v1→v9 path is load(accept_old) → (optional `to_native`) → v9 save. Do not silently change v8 write behaviour for 1.x users until the default-write flip is explicit.
- **Release:** follow [`.issueflows/04-designs-and-guides/release-procedure.md`](../04-designs-and-guides/release-procedure.md) + [cellpy-v2-branching.md](../04-designs-and-guides/cellpy-v2-branching.md) (pre-releases on `v2`, stable `v2.0.0` on `master` after merge).
- **Scope:** this issue is the epic Phase 4 umbrella; implement as **three milestones / PRs** under #510 (do not re-open Phase 1–3 work; leave #511 native-schema opt-in and #518–#520 extract follow-ups alone).

### Prior art

| Hit | Role | Plan |
|-----|------|------|
| [`cellpy/readers/cellpy_file/`](../../cellpy/readers/cellpy_file/) (`format`, `read`, `write`, `legacy_read`, `meta`, `keys`) | Extracted HDF5 I/O seam (issue #446 / file-loading refactor) | **Extend** — add v9 writer/reader beside v8; keep HDF5 path for legacy |
| [`write.create_infotable` / `write.save`](../../cellpy/readers/cellpy_file/write.py) | v8 still only persists active test; already logs warning pointing at **#510** for `_extra_tests` | **Replace/extend** for v9 meta; leave v8 warning until v8 write retired or kept as `format="v8"` |
| [`Data.tests` / `_extra_tests` / `set_test_meta`](../../cellpy/readers/data_structures.py) + [`test_meta.py`](../../cellpy/readers/test_meta.py) | In-memory collection (Phase 1 hybrid) | **Serialize** via `cellpycore.metadata.to_dict` / `from_dict` into `meta.json` |
| [`cellpycore.metadata.io`](../../../cellpy-core/src/cellpycore/metadata/io.py) `to_dict`/`from_dict`/`to_json`/`from_json`; `save_archive`/`load_archive` stubs | Shape + tools in core; archive stubs | **Mirror** — implement cellpy helpers (e.g. `cellpy.readers.cellpy_file.archive` or `meta_io`) that call `to_dict`/`from_dict`; do **not** fill core stubs |
| [`tests/test_cellpy_file_roundtrip.py`](../../tests/test_cellpy_file_roundtrip.py), [`test_cellpy_file_format.py`](../../tests/test_cellpy_file_format.py), `testdata/hdf5/*` | v8 round-trip / version fixtures | **Extend** — add v9 fixtures + v8→v9→read essential test |
| Metadata plan Step 4 + native-headers Phase 2 | `meta.json` keys: `cell`, `tests`, `raw_units`, `cellpy_units`, `limits` | **Follow** |
| Toolbox `00-tools/` | No format helpers | None |
| Graph communities ~109 (`cellpy_file`), ~42 (`CellpyCell` load/save) | Persistence hub | Touch those modules |

## Approach

### Milestone A — V2-13: cellpy-file v9 (format + round-trip)

1. Bump `CELLPY_FILE_VERSION` / add `FORMAT_V9` (keep `FORMAT_V8` for legacy write if needed).
2. Define v9 container under `cellpy/readers/cellpy_file/`:
   - zip containing parquet tables for raw / steps / summary / fid (names in [`keys.py`](../../cellpy/readers/cellpy_file/keys.py) or a v9 keys module);
   - sidecar `meta.json`: typed meta per architecture plan (`cell`, `tests` keyed by `test_id`, `raw_units`, `cellpy_units`, `limits`, `cellpy_file_version`, header/schema version stamp).
3. Writer: `Data` → zip+parquet+`meta.json`, including **full** `tests` collection (active + `_extra_tests`).
4. Reader: v9 → `Data` (populate legacy boxes for active test **and** `_extra_tests`); dispatch in `read.load` when version ≥ 9 (extension / sniff zip vs HDF5).
5. Migration: existing v8 `.h5` loads unchanged; add convert path `load(v8)` → `save(v9)` (CLI optional in A; document in C).
6. **Done when:** essential test `v8 fixture → save v9 → load → TestMetaCollection (+ frames) match`.

### Milestone B — V2-14: metadata persistence policy (cellpy-owned)

1. Public-ish helpers used by save/load (and callable standalone for campaign meta):
   - `save_meta_archive(data|collection, path)` / `load_meta_archive(path) -> …` in cellpy (name bikeshed OK; must **not** be implemented by patching core stubs).
2. Wire `CellpyCell.save` / `load` (and `cellpy_file.write`/`read`) so merged multi-`test_id` objects round-trip without the current v8 “active only” warning path when writing v9.
3. Document policy: core stubs remain; consumers import cellpy helpers.
4. **Done when:** merged two-test object save→load preserves both `TestMeta` rows and matching `test_id` columns (reuse #515-style fixtures).

### Milestone C — V2-15: release discipline + migration guide

1. Pin exact `cellpycore==X.Y.Z` in `[project.dependencies]` for the release commit; `UV_NO_SOURCES=1 uv lock`.
2. Publish user-facing **v1→v2 migration guide** (file format, meta model, convert once, deprecations from #509).
3. Follow `release-procedure.md`: cut `v2.0.0aN` on `v2` (or agreed branch) before stable `v2.0.0` on `master`.
4. **Done when:** release checklist green; guide linked from README / HISTORY; pin exact.

### Ordering / PR split

```text
A (format + round-trip) → B (policy helpers + merge fixture) → C (docs + pin + tag)
```

Prefer **three stacked PRs** on `510-…`, all closing #510 only when C lands (or close #510 after B and track C as release checklist if tag timing slips).

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/readers/cellpy_file/format.py` (+ possibly `keys.py`) | v9 constants / `CellpyFileFormat` |
| `cellpy/readers/cellpy_file/write.py` (+ new `v9_write.py` if cleaner) | zip-of-parquet writer; stop warning for full collection on v9 |
| `cellpy/readers/cellpy_file/read.py` (+ `v9_read.py`) | sniff/dispatch v9; build `Data` + full `tests` |
| new `cellpy/readers/cellpy_file/meta_archive.py` (or similar) | cellpy `save`/`load` meta helpers using core `to_dict`/`from_dict` |
| `cellpy/parameters/internal_settings.py` | keep version constant in sync with `format.py` (single source — prefer `format.py` re-export) |
| `cellpy/readers/cellreader.py` | thin `save`/`load` wiring / default format flag only |
| `tests/test_cellpy_file_*.py`, new v9 fixtures under `testdata/` | round-trip + merge meta |
| `docs/` or `README` / `HISTORY.md` | migration guide (C) |
| `pyproject.toml` + `uv.lock` | exact `cellpycore==` pin (C) |

## Test strategy

- Gate: `uv run pytest -m essential` (mark new round-trip / merge-meta tests `@pytest.mark.essential`).
- Broader: `uv run pytest tests/test_cellpy_file_roundtrip.py tests/test_cellpy_file_format.py` (+ new module).
- Oracle: v8 HDF5 fixture → v9 → reload equality for meta collection + `test_id` presence; two-test merge fixture for B.
- Do **not** implement persistence inside `cellpy-core` tests; assert core stubs still raise if we touch that surface.

## Decisions (confirmed 2026-07-17)

1. **Container:** v9 = **zip-of-parquet + `meta.json`** (epic “HDF5 layer” wording outdated).
2. **Default write:** `save()` writes **v9** by default on the v2 line; explicit `format="v8"` escape kept where needed.
3. **Extension / sniff:** v9 uses **`.cellpy`**; `load` sniffs zip magic vs HDF5 (extension is a hint, not the only signal).
4. **Issue scope:** keep single GitHub issue **#510**; three stacked PRs (A→B→C); delay tag if needed.
5. **Column names:** v9 parquet stores **native** header names + schema version stamp (aligns with #511 / native-headers plan).

## Open questions

- None — ready for `/iflow-start` (Milestone A first).
