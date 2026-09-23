# Issue #1023 — plan (iteration 12: tutorial-notebook pass)

## Goal

Role-play a battery scientist walking the numbered tutorials on RTD latest,
fix whatever is missing, wrong, or unfindable in the **source notebooks**,
re-render the committed docs pages, and leave the issue open.

## Constraints

- Docs + example notebooks only. No product-code, schema, or CLI changes.
- Do not redo pages shipped in #1024–#1035 or the iteration-11 glossary.
  New links *into* those pages are fine.
- Out of this PR: experienced-Python pass (typing, extending, plugin surface).
- `docs/examples/*.md` are generated. Edit `examples/*.ipynb`, then
  `uv run --group docs python dev/render_example_notebooks.py`.
  The renderer does **not** execute notebooks; it converts committed outputs.
- Every identifier checked against source or executed (`uv run`) against
  bundled example data — no hoped-for names.
- Writing: task-first, scientist with limited Python. No unexplained idioms.
- Docs live on `master` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).
- Docs build must stay link-clean.

### Prior art

- Toolbox: `check_rtd_latest_links.py` — use if we add hard RTD `latest` URLs.
  No notebook helper in `00-tools/`.
- Graph: `graphify-out/` not in this worktree — skipped.
- Renderer: [dev/render_example_notebooks.py](../../dev/render_example_notebooks.py)
  (issue #571 / #869). Plotly HTML stripped; static PNG kept.
- Existing 2.1 note on [docs/examples/index.md](../../docs/examples/index.md):
  numbered tutorials + batch already claim `c.schema` / 2.1 names.
- Cookiecutter notebooks under `examples/cellpy project template/` are
  **out of scope** (separate tree, still `cellpy import prms` in places).

## Approach

Persona / trigger: scientist who finished [first_hour.md](../../docs/getting_started/first_hour.md)
and [how_do_i.md](../../docs/how_do_i.md), then opened **Loading data** /
**First look** / **Capacity vs voltage** / **ICA**.

Walk those four numbered tutorials (01–04) plus the examples index. For each:

1. Try to follow using only published docs + the tutorial page.
2. Fix stale 1.x APIs, wrong parameter names, or missing “what do I type next?”
   in the `.ipynb` (then re-render).
3. Add one `how_do_i.md` question if the path from a real task to that tutorial
   is missing.

Do **not** expand into 06–09 / custom loaders / GITT / batch unless a broken
cross-link forces a one-line fix. Those stay for a later iteration.

## Files to touch

- `examples/01_loading_data.ipynb` … `examples/04_incremental_capacity_analysis.ipynb`
  — source edits.
- `docs/examples/01_loading_data.md` … `04_*.md` — re-rendered only.
- `docs/examples/index.md` — only if the walk finds a discoverability hole
  (hand-written; not generated).
- `docs/how_do_i.md` — at most a few index questions.
- `HISTORY.md` — Unreleased docs bullet (close step).

## Test strategy

- Execute any new snippet against `example_data.raw_file()` (`uv run`).
- `uv run --group docs python dev/render_example_notebooks.py`
- `uv run --group docs zensical build` — no broken links / missing anchors.
- `uv run pytest -m essential` — docs-only; expect existing suite green.
  No new pytest.

## Open questions

1. **This iteration = tutorial notebooks 01–04?** Recommended yes.
   Alternative: experienced-Python pass, or widen to all `examples/*.ipynb`.
2. **Re-run notebooks** to refresh outputs, or only edit markdown cells /
   comments and re-render existing outputs? Recommended: edit text + API
   calls as needed; re-execute a notebook only when a snippet is actually
   wrong (kaleido/`batch` extra if plotly PNGs must be backfilled).
