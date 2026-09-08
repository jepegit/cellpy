# Issue #982 — plan: db group text as default group labels

## Goal

Text in the cellpy_db `group` column becomes the journal `group_label`, so
`summary_collector` uses it as the default legend labels without
`custom_group_labels`.

## Constraints

- Numeric group cells stay unlabeled (today’s plot still shows 1, 2, 3).
- Explicit `custom_group_labels=` still wins (`collect/summary.py` already merges).
- `fix_groups` still renumbers to consecutive ints; do not change grouping ids.

### Prior art

- `cellpy/batch/_dbengine.py::fix_groups` — discards original values while numbering.
- `HeadersJournal.group_label` — already on the journal frame.
- `collect/summary.py` — `group_it` already maps `group` → `group_label` from pages.

## Approach

1. Before `fix_groups`, copy each raw group cell through a small helper: non-numeric text → `group_label`, else `None`.
2. Write that list onto `pages_dict[hdr_journal.group_label]`.
3. Leave `collect_summaries` / `custom_group_labels` as they are.

## Files to touch

- `cellpy/batch/_dbengine.py` — preserve text group labels.
- `tests/test_batch.py` — helper + numbering tests.
- `HISTORY.md` — unreleased bullet (close).

## Test strategy

`uv run pytest tests/test_batch.py -q` plus `uv run pytest -m essential`.

## Open questions

None.
