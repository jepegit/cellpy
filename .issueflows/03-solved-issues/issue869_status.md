# Issue #869 — status

- [x] Done

## What was done

Deduplicated the tutorials onto the top-level `examples/` folder, per the
maintainer's refinement during the cycle (the issue's own first option pointed
the other way).

- The **executed** `docs/examples/` notebooks were moved to `examples/`,
  overwriting the stale copies. They had to be the survivors: the render script
  does not execute, it renders whatever outputs a notebook carries, and only the
  docs copies had them (`02` alone is 40 MB of saved output against 524 KB).
- `examples/cellpy batch utility/` → `examples/batch_utility/`, and the notebook
  is now `cellpy_batch_processing.ipynb` (the `_docs` suffix is gone). The
  rendered page moved with it, so the two in-docs links to the old page name
  were updated.
- `docs/examples/templates/` moved to `examples/templates/`, screenshots
  included.
- Deleted the run artifacts that had been committed under `docs/examples/`:
  `data/`, `batch_utility/{data,dump,out}`, `cellpy_db.xlsx`, the batch JSON and
  `.ipynb_checkpoints/`. The pristine inputs live under `examples/`; the rest
  was output from somebody's run.
- `dev/render_example_notebooks.py` rewritten around a source → output split
  (`examples/` → `docs/examples/`), mirroring each notebook's relative path,
  copying sibling `images/` assets, and skipping `.ipynb_checkpoints` and the
  `cellpy project template/` cookiecutter tree (its notebook is a Jinja
  template). `dev/backfill_notebook_plotly_pngs.py` follows the same source.
- Rendering **all** notebooks means `08_batmo_bdf` and `09_loading_pec_data` now
  have documentation pages, added to the nav and the tutorial index.
- `examples/09_loading_pec_data.ipynb` set `prms.Reader.max_raw_files_to_merge`,
  which raises `AttributeError` in 2.1; it now uses
  `from cellpy import config` / `config.reader.max_raw_files_to_merge` with the
  `cellpy.toml` `[reader]` form for the permanent setting.

## Verification

- `docs/examples/` contains only `.md`, `*_files/`, `templates/images/` and
  `index.md` — checked with a find over the tree.
- Every `examples/*.md` nav target in `zensical.toml` exists on disk (12/12).
- The removed-API grep from the issue now returns only prose in the migration
  notes of `04` and the batch tutorial — no usages.
- `uv run pytest -m essential` green (the change is docs-side; the run guards
  against an accidental package edit).

## Remaining work

None. The notebooks that were written for 1.x still show 1.x idioms in places —
that is the pre-existing caveat already stated in the tutorial index, not part
of this issue.
