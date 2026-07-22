# Issue #636 — Status

- [ ] Done

## What's done

- Plan accepted (recommended defaults for unknown-`y`, minimal panels, `SUMMARY_FAMILIES` from registry).

## Remaining work

- Add `cellpy/plotting/spec.py` and `registry.py`.
- Thin-adapt `SummaryPlotInfo._create_col_info`; validate via `registry.get(y)`.
- Export new API; derive `SUMMARY_FAMILIES` from `families()`.
- Essential registry tests; keep figure-spec oracle green.
