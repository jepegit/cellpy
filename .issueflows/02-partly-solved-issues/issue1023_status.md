# Issue #1023 — status

- [ ] Done

Issue stays open. Iteration 12 parked after `/iflow-close` (PR, not
`Closes #1023`).

## What's done

- Iterations 1–10 shipped as #1024–#1035 (see issue comment).
- Iteration 11 (glossary) shipped: `docs/fundamentals/glossary.md` plus nav/links.
- Iteration 12 (2026-09-23): tutorial-notebook pass on 01–04.
  - `examples/01_loading_data.ipynb`: `cycle_mode="full_cell"`, prefer
    `c.refresh_after(...)` over `c.make_summary()`, native `.cellpy` save/reload
    with legacy `.h5` fallback.
  - `examples/02_Initial_data_inspection.ipynb`: `.cellpy` candidates first.
  - Re-rendered `docs/examples/01_*.md` and `02_*.md` only.
  - Tutorials 03–04 already used 2.1 APIs; no notebook edits.
  - `docs/how_do_i.md` and `docs/getting_started/first_hour.md` link the
    numbered tutorials and cover `refresh_after` / `full_cell`.
  - `zensical build` clean; `pytest -m essential` 912 passed, 70 skipped.

## Remaining work

- Later: experienced-Python pass (typing / extending / plugins).
- Later: tutorials 05–09 / custom loaders / GITT / batch.
