# Issue #680 — Plan

## Goal

Bring the user-facing **Data structure** fundamentals chapter up to date with
cellpy **2.x** object layout (`CellpyCell` / `Data` / frames / metadata /
`c.schema`), without redoing the column-header work already landed in #676.

## Constraints

- Docs only — no runtime / API changes.
- Prefer linking to existing sources of truth over duplicating long tables:
  [`migration_v1_to_v2.md`](../../../docs/getting_started/migration_v1_to_v2.md),
  [`header_migration_map.md`](../../../docs/other/header_migration_map.md),
  [`DEPRECATIONS.md`](../../../docs/reference/deprecations.md).
- Keep statements that are still true: public frames are **pandas**; default
  `CellpyCell` uses **native headers** (`native_schema=True`); default save is
  **v9** zip-of-parquet (not HDF5).
- Do not invent a polars user-facing flip — migration guide still says that is
  later.
- Preserve MkDocs/Zensical link targets used elsewhere (`data_structure.md`
  anchors if any; `dev_cellpy_data_structure.md` cross-links).

### Prior art

- `#676` — rewrote the **Column headings** section of
  `docs/fundamentals/data_structure.md` around `c.schema` + native key-column
  tables. **Reuse that section**; this issue fixes the *structure* prose above
  (and leftover dumps below) that #676 left alone.
- `docs/getting_started/migration_v1_to_v2.md` — authoritative user story for
  v9 files, `Data.tests` / campaign merge, `prms` → `config`, pandas-still.
- `cellpy/readers/data_structures.py` (`Data`) — current attributes:
  `raw` / `steps` / `summary`, `meta_common` / `meta_test_dependent`,
  `tests` (`TestMetaCollection`), `raw_units` / `raw_limits`, `raw_data_files`
  (`FileID`), property shims (`mass`, …).
- `cellpy/readers/cellreader.py` (`CellpyCell`) — thin facade + `schema`
  property; headers no longer “owned” as HDF5 definitions on the class.
- `.issueflows/04-designs-and-guides/cellpycell-di-restructuring.md` — core
  seam / DI detail for *developers*; keep user chapter lighter (link, don’t
  re-teach).
- Toolbox: `scan_member_usage.py` / `scan_hardcoded_headers.py` — not needed
  for a docs rewrite.
- Graph: `graphify-out/` absent — skipped.

## Approach

1. **Audit stale claims in**
   [`docs/fundamentals/data_structure.md`](../../../docs/fundamentals/data_structure.md)
   against code + migration guide. Confirmed stale / misleading today:
   - CellpyCell “owns header definitions for the cellpy HDF5 format” and
     “several tests stored in a list”.
   - Metadata as a flat `prms.*` attribute dump.
   - Leftover `HeadersJournal` dataclass paste + “tester-dependent attributes
     injected from `internal_settings`” closing section.
   - Weak / missing mention of `c.schema`, `Data.tests`, v9 default file
     format (column section is already good after #676).

2. **Rewrite the structure sections** (CellpyCell, Methods, Data, Metadata,
   FileID) to the v2 mental model:
   - `CellpyCell` = facade (load / process / save) + `data` + `schema`.
   - `Data` = three pandas frames (`raw` / `steps` / `summary`) + meta boxes +
     `tests` collection + units/limits + `FileID` list.
   - Metadata: document preferred access (`c.data.mass`, …) and point at
     `meta_common` / `Data.tests` / migration “Metadata and campaign merge”
     for multi-test / v9 persistence — **no** full field dump of every
     `TestMeta` / `CellpyMeta*` attribute unless a short “common fields”
     table helps.
   - File format: one short paragraph + link to
     [`file_formats.md`](../../../docs/fundamentals/file_formats.md) /
     migration guide (do not duplicate the support matrix).
   - Update mermaid diagrams only if labels are wrong (e.g. add `schema` /
     `tests`; drop “cellpy metadata” vagueness). No new figure assets
     required.

3. **Keep the #676 Column headings block** (with light editorial pass only if
   something contradicts the new structure prose). Remove the leftover
   journal/`internal_settings` dumps at the bottom or shrink to a pointer
   (“batch journal columns live in the batch docs”).

4. **Sibling Concepts pages (same PR, small accuracy pass)** — recommended so
   adjacent links don’t contradict the chapter:
   - [`fundamentals.md`](../../../docs/fundamentals/fundamentals.md) — still
     says pandas *(OK)* but “usually stored in HDF5” *(wrong)*.
   - [`file_formats.md`](../../../docs/fundamentals/file_formats.md) — still
     says default HDF5 *(wrong)*.
   - Deep rewrite / new JPG figures / full
     `dev_cellpy_data_structure.md` rewrite → **out of scope** unless you
     expand scope in Open questions.

5. **Verify** with `uv run --group docs zensical build` (and spot-check the
   rendered Fundamentals pages). No new pytest.

## Files to touch

| Path | Change |
|---|---|
| `docs/fundamentals/data_structure.md` | Main rewrite: structure/metadata/FileID; trim leftover dumps; keep #676 columns |
| `docs/fundamentals/fundamentals.md` | Accuracy: v9 default file story; keep pandas-as-frames |
| `docs/fundamentals/file_formats.md` | Accuracy: default v9; HDF5 as escape / legacy read |
| `.issueflows/01-current-issues/issue680_status.md` | Track progress during `/iflow-build` |

Out of scope unless confirmed: `docs/contributing/.../dev_cellpy_data_structure.md`,
`docs/fundamentals/figures/*.jpg`, architecture-plan docs.

## Test strategy

- Docs build: `uv run --group docs zensical build` (see
  [`dev_docs.md`](../../../docs/contributing/developers_guide/dev_docs.md)).
- Manual: open Fundamentals → Data structure / File formats and confirm no
  “default HDF5” / `prms.Materials…` as current API.
- No `pytest` changes expected (docs-only).

## Open questions

1. **Sibling page scope:** Accept the recommended small accuracy pass on
   `fundamentals.md` + `file_formats.md` in this PR, or restrict to
   `data_structure.md` only?
   - **Recommendation:** include the sibling accuracy pass (same Concepts
     trio; ~small edit each).
2. **Metadata depth:** Short “how to read/set common fields” + link to
   migration `Data.tests`, or a fuller field table?
   - **Recommendation:** short how-to + link (avoids another stale dump).
3. **Developer chapter:** leave
   `dev_cellpy_data_structure.md` for a follow-up?
   - **Recommendation:** yes, follow-up (user chapter is what #680 names).
