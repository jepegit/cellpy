# Issue #985 status

Interactive `/iflow-fix` session: improve ICA docs.

- [ ] Done

## Iterative fixes log

- 2026-09-02 — Add `docs/guides/ica.md` how-to (`dqdv` / `dvdq` / `ica_plot` / collect) and wire it into `zensical.toml` + `docs/guides/index.md`.
- 2026-09-02 — Expand `docs/api/ica.md` as the ICA/DVA hub (preferred import, `to_wide`, plot/collect table, `IcaOptions` name clash).
- 2026-09-02 — Fix API index “Where to look”: ICA and Plotting were buried under Utils; add DVA to `docs/api/collect.md`; point `docs/api/plotting.md` at `ica_plot` / `dva_plot`.
- 2026-09-02 — Agent recipe: `docs/getting_started/agents.md` + root `AGENTS.md` quick fact; basic-usage + 2.1 migration pointers.
- 2026-09-02 — Tutorial: prefer `from cellpy import ica`; add DVA/plotting closer in `examples/04_incremental_capacity_analysis.ipynb` and the rendered docs copy.
- 2026-09-02 — Stale docstrings: drop “`dq` until 2.1” from `cellpy/collect/ica.py`; update `cellpy/utils/ica.py` re-export note; fundamentals no longer call ICA a utils-only tool.
