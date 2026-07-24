# Issue #676 — Plan

## Goal

Make cellpy 2.0 docs teach **native** frame headers and the `c.schema.*` API so
batch/notebook code that still hard-codes 1.x names (`type`, `cycle_index`,
`discharge_capacity`, …) has an obvious, correct migration path — including the
gotcha that `schema.raw` has `cumulative_discharge_capacity`, not
`discharge_capacity`.

## Constraints

- Docs/examples only; **no** runtime rename back to legacy on-frame names.
- Prefer `c.schema` in all new examples (matches #558 / `test_cell_schema.py`
  contract).
- Do not expand into a full rewrite of every shipped notebook output blob.
- Keep the authoritative rename table in
  [`docs/other/header_migration_map.md`](../../../docs/other/header_migration_map.md);
  other pages link to it rather than duplicating full tables.
- Default runtime is already native (`CellpyCell(native_schema=True)`).

### Prior art

- `docs/other/header_migration_map.md` — full old→new map (keep as source of truth).
- `docs/getting_started/migration_v1_to_v2.md` — user migration landing page; already
  points at the map and `cell.schema`, but still describes native as partly
  “bridge / opt-in” (stale vs rc1 default flip).
- `docs/fundamentals/data_structure.md` — still dumps legacy `HeadersNormal` /
  `HeadersStepTable` / `HeadersSummary` as if current.
- `tests/test_cell_schema.py` —
  `test_schema_columns_are_keys_into_the_frames` already checks
  `potential` / `charge_capacity` / `cycle_num`; easy place to add
  `step_type` + `cumulative_discharge_capacity`.
- `.issueflows/00-tools/scan_hardcoded_headers.py` — AST scanner for header
  literals in *code*; optional audit aid for notebooks/docs (not required).
- Batch docs notebook
  (`docs/examples/batch_utility/cellpy_batch_processing_docs.ipynb`) — **no**
  `steps.query("type==…")` / discharge-backfill cell found; the reporter’s
  template is external. Fix via migration recipe, not that notebook’s code.

## Approach

1. **Fundamentals (`data_structure.md`)**
   - Rewrite the “Column headings” section around **`c.schema`**
     (`raw` / `steps` / `summary`) and native names.
   - Show short native excerpts (or “key columns” tables) for raw + steps +
     summary; do **not** paste full legacy `Headers*` dataclasses as current API.
   - Note that legacy `headers_*` still resolve via shim (deprecated → 2.1) and
     link to the migration map + `migration_v1_to_v2.md`.
   - Fix step-types prose: values live in **`step_type`**, not the old `"step"` /
     `"type"` wording.

2. **Migration guide (`migration_v1_to_v2.md`)**
   - Correct the “Frames and column names” subsection so it matches **rc1
     default native headers** (not “bridge still default / native opt-in only”).
   - Add a short **“Notebook / batch post-processing”** recipe: the discharge
     capacity backfill pattern using `c.schema.steps.step_type`,
     `…step_num`, `…cycle_num`, `…datapoint_num`, and
     `c.schema.raw.cumulative_discharge_capacity` (call out the wrong
     `discharge_capacity` attribute explicitly).
   - Link `header_migration_map.md` from that subsection if not already adjacent.

3. **Migration map polish (`header_migration_map.md`)**
   - One-line intro update: flip is **on by default in 2.0**; map is for
     migrating notebooks/scripts.
   - Optional tiny cross-link to the new migration-guide recipe (no full table
     duplication).

4. **Batch / examples audit (narrow)**
   - Grep shipped docs + `examples/` for instructional source cells that query
     `type` / `cycle_index` / `step_index` / raw `discharge_capacity` as if
     current.
   - Fix **source** cells that teach those names as the default 2.0 API.
   - **Out of scope for this PR:** regenerating every stale HTML/output blob in
     old example notebooks unless a source cell we touch requires it.
   - If the batch utility notebook has no such cells: leave it; the recipe in
     the migration guide covers the reporter’s template.

5. **Guard test**
   - Extend `test_schema_columns_are_keys_into_the_frames` (essential) to assert
     `schema.steps.step_type` and `schema.raw.cumulative_discharge_capacity`
     are present on the loaded frames.
   - Optionally assert `not hasattr(schema.raw, "discharge_capacity")` (or
     equivalent) so the AttributeError gotcha stays documented in tests.

## Files to touch

| Path | Change |
|---|---|
| `docs/fundamentals/data_structure.md` | Native/`c.schema` column docs; drop legacy-as-current dumps |
| `docs/getting_started/migration_v1_to_v2.md` | Fix flip status; add notebook recipe + capacity attr gotcha |
| `docs/other/header_migration_map.md` | Intro + link to recipe |
| `tests/test_cell_schema.py` | Extend schema↔frame key smoke asserts |
| `examples/*.ipynb` / `docs/examples/**` | Only if grep finds instructional hard-coded 1.x headers in source cells |

## Test strategy

- `uv run pytest -m essential tests/test_cell_schema.py` (and full essential
  suite before close).
- Manual: skim rendered markdown for the new recipe; no notebook CI required
  unless we edit a notebook source cell.

## Open questions

1. **`data_structure.md` depth:** (A) replace legacy dataclass dumps with
   native `RawCols` / `StepCols` / `CycleCols` key-column lists + `c.schema`
   examples, or (B) keep a collapsed “Legacy headers (1.x / shim)” appendix?
   **Recommend A** (link map for full detail; no appendix dump).
2. **Example notebook scope:** keep this PR to docs + the one essential test,
   and only patch example **source** cells that clearly teach wrong 2.0 names —
   **not** a full examples/ refresh. **Recommend yes.**
3. **Stale migration prose:** treat fixing the “native still opt-in / bridge
   default” wording in `migration_v1_to_v2.md` as in-scope for this issue.
   **Recommend yes** (same landing page as the recipe).
