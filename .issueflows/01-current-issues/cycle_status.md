# Cycle status

- queue: `yolo v.2.1.2` → resolved `label:yolo` (identical to open issues in milestone `v.2.1.2`)
- repo: jepegit/cellpy
- onfail: stop
- started: 2026-08-09T19:50:00+02:00
- preflight: clean tree on `master`; `uv run pytest -m essential` → 703 passed, 1 skipped, 2 xfailed (`conda` not on PATH in this shell)

## Up-front design decisions (from the consolidated confirm)

- **#867** — add *both* `max_points=` (min/max decimation per bucket) and `cycles=` to `raw_plot`.
- **#868** — Option 1: `PlotFamily.summary_options(hdr)` returning a ready `SummaryOptions` (transforms as callables, `partition_by_cv` set where required).
- **#869** — Deduplicate the other way round (refined by the user after the first confirm): the
  notebooks stay in the **top-level `examples/`** folder as the single maintained copy, and
  `docs/examples/` keeps only the generated markdown plus figure directories.
  - The executed `docs/examples/*.ipynb` are the current generation, so they move to `examples/`,
    overwriting the stale top-level copies. `docs/examples/templates/` moves too.
  - `dev/render_example_notebooks.py` gains a source (`examples/`) → output (`docs/examples/`)
    split instead of rendering in place; **all** notebooks under `examples/` are rendered, so
    `08_batmo_bdf` and `09_loading_pec_data` gain docs pages.
  - `examples/cellpy batch utility/cellpy_batch_processing.ipynb` is normalised to
    `examples/batch_utility/cellpy_batch_processing.ipynb`; the rendered page stays under
    `docs/examples/batch_utility/`.
  - Scope is larger than the original yolo estimate; the user chose to keep it in the cycle.

## Queue

- [ ] #867 — raw_plot has no way to limit points (or select cycles) — 18 MiB of JSON for one demo cell — in-progress
- [ ] #868 — fullcell_standard_* families can't be collected: family.transforms() shape doesn't match SummaryOptions.transforms — pending
- [ ] #869 — Top-level examples/ notebooks still use removed 1.x API — pending

blocked: none
skipped (closed): none

- [ ] Done
