# Issue #778 plan — L6: golden equality test (incremental update == full load)

## Goal

Add the Stage 5 Epic L correctness anchor: a test proving that loading a
**truncated** tester file and then feeding the **tail rows** through the
incremental-update path yields the same `raw` / `steps` / `summary` as one
**full load** of the whole file. Written first, against the shipped core
primitive (`update_core_data`), so L1–L5 (#779/#780/#164/#781/#782) have an
oracle to land against.

## Constraints

- Test-only issue: **no library code changes**. `CellpyCell.update()` and
  `load_since()` do not exist yet (L3/L2); the test drives the seam that does
  exist — `c.core.update_core_data(data, new_raw, …)` (cellpycore 0.2.5
  `merge.update_data`). The helper that produces the "tail" is written so L3
  can swap it for `c.update()` in one place.
- Must run on the merge gate (`@pytest.mark.essential`) → fast, no mdbtools:
  use a **text** fixture. `testdata/data/neware_uio.csv` (`instrument="neware_txt"`,
  `model="UIO"`): 1 header line + 9064 rows, 4 cycles / 32 steps, `datapoint_num`
  1…9065, loads in ~0.4 s. (`maccor_001.txt` is 5 s and has 1 cycle — not the
  anchor; `custom_data_001.csv` has non-integer `datapoint_num` — unsuitable.)
- Truncated files are written to `tmp_path`, never into `testdata/` (input data
  read-only).
- `update_data` contract (core): `new_raw` may **overlap** the tail; overlap is
  trimmed on `source_datapoint_num` → falls back to `datapoint_num` (cellpy
  loaders set no `source_datapoint_num`). Rejects `new_raw` starting at/before
  the existing range. Both branches (`gap_append` vs overlap) exercised.
- Per-cell frames are **pandas** in cellpy; `update_core_data` converts.
  Comparisons use `pandas.testing` with a small float tolerance, columns
  aligned by name, `test_id` normalised.
- Summary scope **now**: `update_core_data(refresh_derived=True)` produces the
  *core* summary (cycle-end columns + C-rates + IR). cellpy's `make_summary`
  additionally runs `add_scaled_summary_columns` (gravimetric/areal, equivalent
  cycles). Until L3 defines what `c.update()` does after the core step, the
  summary assertion compares the **intersection of columns**; the test records
  the missing columns so L3 flips it to full-column equality. `raw` and `steps`
  are compared on the **full** column set.

### Prior art

- `cellpycore.merge.update_data` / `CellpyCellCore.update_core_data`
  (`../cellpy-core/src/cellpycore/merge.py:173`, `cell_core.py:528`) — the
  engine under test; core has its own unit tests on synthetic frames, none
  through a real loader.
- `CellpyCell.merge(cells, mode="campaign")` (`cellpy/readers/cellreader.py:1852`)
  — the *campaign* merge (renumber cycles); not the incremental path. Coexist.
- `tests/parity.py::assert_value_parity` — legacy↔native comparator with
  named exceptions; heavier than needed here (same-schema frames). Mirror its
  spirit (explicit tolerance, no silent widening) with `pandas.testing`.
- `tests/loader_golden_support.py` / `tests/golden_support.py` — committed
  golden snapshots. **Not** used: this oracle is *self-referential* (full load
  is the reference), so no new golden files and no `regenerate_goldens.py`
  suite.
- `tests/test_cellpy_splitting.py` (`cell.split`, `drop_to`) — cycle-level
  splitting of a loaded cell; different axis (cycles, not file rows). Coexist.
- `.issueflows/00-tools/` — nothing applicable (AST scanners, prms migrator).

## Approach

1. **`tests/incremental_support.py`** (small, reused by L2/L3/L5 tests later):
   - `truncate_text_file(src, dst, *, n_data_rows, header_lines=1)` → writes
     header + first `n_data_rows` data lines. Returns `dst`.
   - `tail_rows(full_raw, *, since, overlap, datapoint_col)` → pandas slice
     `datapoint_num > since - overlap` — this is what a future `load_since`
     returns for marker `since`; the only place L3 has to replace.
   - `incremental_update(head_cell, new_raw)` → today:
     `head_cell.core.update_core_data(head_cell.data, new_raw, nom_cap_abs=…,
     current_conversion_factor=…)` with the same factors cellpy's
     `make_summary` computes (`core_units.calculate_current_conversion_factor`,
     nominal capacity from `head_cell.data.meta`). Returns the new `Data`.
   - `assert_frames_equal(left, right, *, columns=None, rtol)` thin wrapper
     over `pandas.testing.assert_frame_equal` (reset index, sort by
     `datapoint_num` / `cycle_num`, `check_dtype=False`).
2. **`tests/test_incremental_update.py`**:
   - Fixtures: `full_cell` (module-scoped load of `neware_uio.csv`);
     `head_cell(tmp_path, n)` via `truncate_text_file` + `cellpy.get`.
   - `test_head_matches_full_prefix` — sanity: head `raw` == first `n` rows of
     full `raw` (proves the truncation + `datapoint_num` assignment are
     deterministic; without this the oracle proves nothing).
   - `test_incremental_update_equals_full_load[cut]` — parametrised over cut
     points: **mid-step** inside cycle 2, **on a step boundary**, **on a cycle
     boundary**; `overlap=0` (gap-append branch). Assert `raw` full equality,
     `steps` full equality, `summary` equality on shared columns.
   - `test_incremental_update_with_overlap` — same cut, `overlap=50` rows
     (trim branch).
   - `test_incremental_update_noop_on_empty_tail` — empty `new_raw` returns an
     equal copy (poll tick with nothing new).
   - `test_summary_column_gap_is_documented` — asserts the set of full-summary
     columns missing after the core-only update equals a **named** list
     (`add_scaled_summary_columns` outputs). When L3 lands and closes the gap,
     this test is deleted and the main test flips to full-column equality.
   - Marker `@pytest.mark.essential` on the equality tests (golden-oracle rule
     in `this-project.md`); whole file well under 5 s.
3. **`tests/README.md`** — one short subsection "Incremental-update oracle
   (Stage 5 L6)" stating the invariant, the fixture, and the L3 flip rule.
4. **Status file** `issue778_status.md`; HISTORY entry at close (test-only —
   a one-liner under Unreleased is enough).

## Files to touch

| Path | Change |
|---|---|
| `tests/incremental_support.py` | new — truncate / tail / update / compare helpers |
| `tests/test_incremental_update.py` | new — the L6 oracle tests (essential) |
| `tests/README.md` | add "Incremental-update oracle" subsection |
| `.issueflows/01-current-issues/issue778_status.md` | new |

No changes under `cellpy/`.

## Test strategy

- `uv run pytest tests/test_incremental_update.py -q` during build.
- `uv run pytest -m essential` before close (merge gate).
- If a cut point exposes a real `update_data` defect (e.g. step-table rows at
  the cut not refreshed identically), **do not** widen tolerance or drop the
  case: record it in the status file and open a `cellpy-core` issue — that is
  precisely what the oracle is for.

## Open questions

1. Summary scope: OK to compare **shared columns only** now (with the
   documented gap test) and defer full-column equality to L3 (#164)? The
   alternative — calling cellpy `make_summary()` after the core update — would
   make the summary assertion trivially true and is rejected.
2. Second fixture: add `maccor_001.txt` as a non-essential parametrisation
   (5 s, single cycle) for loader diversity, or keep neware-only? Proposal:
   neware-only now; L2 (#780) adds per-loader cases when `load_since` exists.
