# Plan — #825

Implemented on branch `auto-prefer-cellpy-newest-source` during dogfooding.

- AUTO: local `.cellpy` if present, else raw (no FID check)
- NEWEST: previous AUTO (both paths → freshness check)
- Persist: skip rewrite when loaded from cellpy unless NEWEST/recalc
- force_recalc: make_step_table + make_summary after load
- Forward nom_cap_specifics from journal
