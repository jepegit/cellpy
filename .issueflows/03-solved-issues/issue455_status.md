# Issue #455 — Status

## Done

- [x] Priority 1: journal-page literals → `headers_journal.*` in batch, helpers, collectors, batch_journals, batch_plotters
- [x] Priority 2: steps/raw literals → `hdr_steps.*` / `hdr_raw.*` in ocv_rlx.py and plotutils.py
- [x] Priority 3: loader rename-dict `power`/`dv_dt` and post_processors groupbys → `headers_normal.*`
- [x] Deleted dead `easyplot.py` cyclelife_ir commented block
- [x] Essential suite green (86 passed)
- [x] Scanner clean on `batch.py`; journal literals resolved in all priority-1 files

## Remaining (out of scope for #455)

- §5 curve-frame columns (`capacity`, `voltage` on `get_cap` output) — tracked for a follow-up
- §6 string-keyed `hdr_summary["…"]` lookups — stylistic, optional
- Unit-dict keys in loader `raw_units`/`unit_labels` — not column-access findings

- [x] Done
