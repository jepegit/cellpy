# Issue #869 — plan

## Goal

One maintained copy of every tutorial notebook, living in the top-level
`examples/` folder. `docs/examples/` becomes purely generated output: markdown
pages plus their figure directories, nothing else.

Confirmed with the maintainer during the cycle: render **all** notebooks under
`examples/` (so `08_batmo_bdf` and `09_loading_pec_data` gain docs pages), and
normalise the batch-utility path to `examples/batch_utility/cellpy_batch_processing.ipynb`.

## Which copy wins

The `docs/examples/` notebooks, because they are the **executed** generation
(`02` alone carries 40 MB of saved outputs against 524 KB for the top-level
copy) and the render script deliberately does not execute — it renders whatever
outputs a notebook carries. The stale top-level copies are overwritten.

## Steps

1. **Move notebooks out of `docs/`**: `01`–`07` to `examples/`;
   `docs/examples/batch_utility/cellpy_batch_processing_docs.ipynb` to
   `examples/batch_utility/cellpy_batch_processing.ipynb` (the old
   `examples/cellpy batch utility/` folder is renamed, dropping the space, and
   keeps its inputs); `docs/examples/templates/` to `examples/templates/`.
2. **Delete the run artifacts committed under `docs/examples/`**:
   `data/`, `batch_utility/{data,dump,out}`, `cellpy_db.xlsx`,
   `cellpy_batch_paper01.json`, and `.ipynb_checkpoints/`. The pristine inputs
   already live under `examples/`; the rest is output from someone's run.
3. **Rewrite `dev/render_example_notebooks.py`** around a source → output split
   (`examples/` → `docs/examples/`), mirroring the relative path of each
   notebook, copying sibling `images/` asset directories, and cleaning stale
   `*_files` directories in the output tree. Skip `.ipynb_checkpoints` and the
   `cellpy project template/` cookiecutter tree (its notebook is a Jinja
   template, not a tutorial).
4. **Fix the one real removed-API use** that the new pages would publish:
   `examples/09_loading_pec_data.ipynb` sets `prms.Reader.max_raw_files_to_merge`,
   which raises `AttributeError` in 2.1. Replace with
   `from cellpy import config` / `config.reader.max_raw_files_to_merge`, and the
   permanent-config comment with the `cellpy.toml` `[reader]` form. (The other
   grep hits in the maintained copies are prose in migration notes describing the
   removals, not usages.)
5. **Update the pointers**: `docs/examples/index.md` (download location and the
   "About these pages" note), `zensical.toml` nav (new `08`/`09` entries, batch
   page renamed to `batch_utility/cellpy_batch_processing.md`),
   `docs/contributing/developers_guide/dev_docs.md`, and the default path in
   `dev/backfill_notebook_plotly_pngs.py`.
6. **Re-render** and commit the generated markdown.

## Files to touch

- `examples/**` (notebooks moved in, batch folder renamed, `09` fixed)
- `docs/examples/**` (notebooks and run artifacts removed, pages re-rendered)
- `dev/render_example_notebooks.py`, `dev/backfill_notebook_plotly_pngs.py`
- `zensical.toml`, `docs/examples/index.md`,
  `docs/contributing/developers_guide/dev_docs.md`
- `HISTORY.md` (changelog bullet at close)

## Test strategy

No unit tests cover the docs tree. Verification is:

- the render script runs clean and reproduces every page from `examples/`;
- `docs/examples/` afterwards contains only `.md`, `_files/`, `images/` and
  `index.md` — asserted with a find over the tree;
- no notebook under `examples/` uses removed API (the #869 grep comes back with
  prose-only hits);
- every nav target in `zensical.toml` exists on disk;
- `uv run pytest -m essential` stays green (guards against an accidental
  package-side edit).
