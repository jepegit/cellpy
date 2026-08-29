# Plan — Issue #939: `from_cells` silently drops values that are not cells

## Goal

Make a non-cell value passed to `from_cells` fail loudly and by name, and make
`collect_summaries` say something when it narrows a collection, so a user never
again sees "a chart with fewer lines than I have cells" with no explanation.

## Findings (reproduced on `master` @ `82ab7e03`)

The issue's script still fails exactly as reported — three entries in, one out,
zero warnings:

```text
warnings: []
3 entries in -> ['good'] out
```

The drop is **not** in `from_cells`. `Batch.from_cells` writes all three labels
into `journal.pages` and hands all three values to `CellStore.from_cells`
unexamined ([`cellpy/batch/facade.py`](../../cellpy/batch/facade.py), the
`from_cells` classmethod). The narrowing happens later, in
`collect_summaries`: for each label it calls `ops.extract_cell_summary`, which
reads `getattr(getattr(cell, "data", None), "summary", None)`
([`cellpy/collect/_summary_ops.py`](../../cellpy/collect/_summary_ops.py)). A
`Path` or an `int` has no `.data`, so that resolves to `None`, the function
returns `None`, and [`cellpy/collect/summary.py`](../../cellpy/collect/summary.py)
hits `if frame is None or frame.height == 0: continue` — a bare `continue` with
no log line.

Two consequences worth designing around:

- `collect_summaries` **already knows** which cells contributed: it builds an
  `included` list and stores it on `CollectionMeta.cells_included`. The
  information needed for a warning is already computed and simply never used
  for feedback.
- `collect_cycles` does **not** share the bug — it calls
  `cell.get_cycle_numbers()`, so a `Path` raises `AttributeError` there. Only
  the summary path is silent.

### What counts as "a cell"

The issue asks to raise on anything that is not a `CellpyCell`. A literal
`isinstance(value, CellpyCell)` check is the wrong instrument here: the whole
codebase duck-types cells as "something with `.data`"
(`plotutils.py`, `collect/_summary_ops.py`, `batch/qc.py`, `batch/aggregate.py`,
`batch/facade.py`), and every cell stub in the test-suite
(`_SummaryCell`, `_StubCell`, the local `_Cell` classes) is a `SimpleNamespace`
holder, not a `CellpyCell`. A strict check would break `tests/test_from_cells.py`
wholesale while adding no safety a duck-type check does not already give:

| value | `hasattr(v, "data")` |
| --- | --- |
| `CellpyCell` | True |
| stub cell | True |
| `Path` | False |
| `int` / `str` / `None` | False |

So the guard is: **the value must expose `.data`** — the same contract every
downstream consumer already relies on.

## Constraints

- Validate in `Batch.from_cells` only. `CellStore.from_cells` is the internal
  loader path (`_store_from_result`, `benchmarks/conftest.py`,
  `tests/test_batch_v3_runner.py` passes `None` there deliberately) and must
  keep accepting whatever the runner produces.
- Duck-type, do not `isinstance`-check against `CellpyCell` (see above). This
  also avoids importing `cellreader` into `batch.facade` at module scope.
- Back-compat: no production caller of `Batch.from_cells` exists outside the
  two public wrappers, and no doc example passes a non-cell, so raising is not
  a breaking change for any working code.
- Keep the PR to the silent-drop story. The `example_data.cellpy_file()` (cell)
  vs `example_data.rate_file()` (path) asymmetry the reporter calls out is a
  public-API rename and is explicitly out of scope — it is addressed here only
  by making the error message name that mistake.

### Prior art

- `_known_cells_hint` + `_MAX_LISTED_CELLS` in
  [`cellpy/batch/facade.py`](../../cellpy/batch/facade.py) — added for #950
  (merged as #973) to name a batch's cells in an unknown-label error. Same
  file, same problem shape (bad label / bad value), so **mirror** its style:
  truncate long lists at 8 entries with a total count.
- `mark_as_bad` raises `ValueError` for an unknown label while `drop` warns
  (#950). Precedent for the raise-vs-warn split used below.
- `_warn_ignored_export_kwargs` in the same file — the project's shape for a
  `UserWarning` that names the offending keys.
- `CollectionMeta.cells_included` in
  [`cellpy/collect/summary.py`](../../cellpy/collect/summary.py) — the existing
  included/excluded bookkeeping to reuse rather than recompute.
- Toolbox (`.issueflows/00-tools/`): nothing applicable
  (`scan_member_usage.py`, `scan_hardcoded_headers.py`, `migrate_prms_calls.py`
  are migration scanners). No `graphify-out/`, so grep-only.

## Approach

**1. Raise in `Batch.from_cells` (the fix the issue asks for).**

After `cell_map` is built (so it covers both the mapping and the sequence
form), collect every label whose value has no `.data` attribute and raise a
single `ValueError` naming all of them with their types, in the style of
`_known_cells_hint`:

```
from_cells got 2 values that are not cells: 'a_path' (PosixPath), 'an_int' (int).
A cell is what cellpy.get(...) / example_data.cellpy_file() returns; a path is not.
```

One error listing every offender, not one per value, so a user fixing a
dict-comprehension sees the whole problem at once. When an offender is a
`str`/`Path`, append the `cellpy.get(...)` hint — that is the reported trap.

**2. Warn in `collect_summaries` when it narrows.**

Track the labels that were iterated but produced no frame, excluding those
skipped deliberately by `only_selected`, and emit one `UserWarning` naming
them when the list is non-empty. This is the guard that also covers cells that
came from a journal and simply have an empty summary — the case `from_cells`
validation cannot see.

The raise/warn split follows #950: a constructor given the wrong type is a
programming error (raise); a collector finding one cell with nothing to
contribute is a data condition the caller may legitimately continue past
(warn).

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/batch/facade.py` | Validate `cell_map` in `Batch.from_cells`; raise `ValueError` naming offending labels + types. Reuse `_MAX_LISTED_CELLS` truncation style; add a small `_non_cell_hint` helper next to `_known_cells_hint`. |
| `cellpy/collect/summary.py` | Record skipped labels alongside `included`; emit one `UserWarning` when cells were dropped for want of a summary. |
| `tests/test_from_cells.py` | New tests: the issue's exact mapping raises and names both bad keys; a `Path` value gets the `cellpy.get` hint; the sequence form is validated too; valid stub cells still build a batch (regression guard on the duck-type choice). |
| `tests/test_collect.py` | New test: a batch containing a summary-less cell warns and names it, and the good cells still come through. |
| `docs/getting_started/agents.md` | Update the `from_cells` guidance to state that non-cell values now raise. |
| `AGENTS.md` | One clause on the same in the batch bullet (per the agent-docs convention in `this-project.md`). |
| `.issueflows/04-designs-and-guides/batch-load-orchestrator.md` | Extend the "Feedback on unknown labels (#950)" section with the #939 raise/warn decision, so the two live together. |
| `.issueflows/04-designs-and-guides/test-registry.md` | Register the new essential tests. |
| `HISTORY.md` | `[Unreleased]` bullet (written in the `/iflow-close` commit). |

## Test strategy

Per [`this-project.md`](../04-designs-and-guides/this-project.md): `uv run pytest`,
never bare `python`, never conda.

- New tests carry `@pytest.mark.essential` — they guard a public entry point
  that app-building agents rely on, which is the documented bar for the marker.
- Targeted first: `uv run pytest tests/test_from_cells.py tests/test_collect.py -q`.
- Then the merge gate: `uv run pytest -m essential`.
- Then the full suite: `uv run pytest` — specifically to catch any existing
  test that trips the new `collect_summaries` warning (the main regression risk
  in this change; see Open questions).
- Manual: re-run the issue's own script and show it now raises instead of
  printing `3 entries in -> ['good'] out`.

## Open questions

1. **Is the `collect_summaries` warning too noisy?** It is the part of this
   change that can touch unrelated tests, since any fixture whose cell has an
   empty summary would start warning. My recommendation is to keep it and fix
   the handful of call sites if the full suite turns any up, because
   downgrading it to `logging.debug` would recreate exactly the silence #939 is
   about. If the full run shows this is widespread, I will report back before
   forcing it through.
2. **Raise or warn in `from_cells`?** Plan says raise, per the issue's stated
   preference and the #950 precedent. Say so now if you would rather it warn
   and keep going.
3. **Follow-ups deliberately not in this PR:** `collect_cycles` reports
   `cells_included=list(batch.cells)` (every label, not the contributing ones),
   which is the same bookkeeping gap in the sibling collector; and the
   `example_data` return-type asymmetry. Both can be issues of their own if you
   want them.
