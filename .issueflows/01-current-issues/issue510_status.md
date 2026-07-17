# Issue #510 — status

- [ ] Done

## What's done

- Plan confirmed (2026-07-17): v9 zip-of-parquet + `.cellpy`, default write v9, native cols; three milestones A→B→C.
- **Milestone A (V2-13)** — merged via PR #521.
- **Milestone B (V2-14)** — implemented:
  - `cellpy/readers/cellpy_file/meta_archive.py` — `save_meta_archive` / `load_meta_archive` / `apply_meta_document` (core stubs stay stubs)
  - v9 uses shared meta document; preserves campaign `test_id` columns on steps/summary
  - Essential tests: `tests/test_meta_archive.py` + campaign v9 round-trip in `test_merge_campaign.py`

## Remaining work

- **C (V2-15):** exact `cellpycore==` pin + migration guide + release procedure
