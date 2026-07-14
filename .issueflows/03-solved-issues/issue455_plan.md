# Issue #455 — Plan

## Goal

Replace hard-coded column-header string literals in Stage 1.10 priority 1–3 files with canonical `headers_*` lookups. Behavior-preserving pure refactor; full essential suite green.

## Approach

1. **Priority 1 — journal pages:** Replace `info_df["group"]`, `pages["selected"]`, `groupby("group")`, etc. with `headers_journal.*` / `hdr_journal.*` in `batch.py`, `helpers.py`, `collectors.py`, `batch_journals.py`, `batch_plotters.py`.
2. **Priority 2 — steps/raw:** Add `hdr_raw`/`hdr_steps` in `ocv_rlx.py`; replace step/raw column subscripts. Fix remaining journal + raw/steps sites in `plotutils.py` (lines ~313, 5371–5563).
3. **Priority 3 — loaders:** Replace rename-dict `power`/`dv_dt` values and `groupby` column literals in `neware_nda.py`, `arbin_sql_csv/xlsx.py`, maccor configs, `post_processors.py`.
4. **Dead code:** Delete commented `cyclelife_ir` block in `easyplot.py` (lines 729–747).

## Files to touch

- `cellpy/utils/batch.py`, `helpers.py`, `collectors.py`
- `cellpy/utils/batch_tools/batch_journals.py`, `batch_plotters.py`
- `cellpy/utils/ocv_rlx.py`, `plotutils.py`, `easyplot.py`
- `cellpy/readers/instruments/neware_nda.py`, `arbin_sql_csv.py`, `arbin_sql_xlsx.py`
- `cellpy/readers/instruments/configurations/maccor_txt_one.py`, `maccor_txt_zero.py`
- `cellpy/readers/instruments/processors/post_processors.py`

## Test strategy

- `uv run pytest -m essential` before and after
- `uv run .issueflows/00-tools/scan_hardcoded_headers.py` on priority files — journal-page literals should be zero; §5 curve-frame and unit-dict hits remain out of scope

## Constraints

### Prior art

- `.issueflows/00-tools/scan_hardcoded_headers.py` — AST scanner for verification
- `architecture-plan/hardcoded-column-headers-report.md` — file:line replacement tables
- Existing `headers_journal` / `hdr_journal` imports in batch tools
