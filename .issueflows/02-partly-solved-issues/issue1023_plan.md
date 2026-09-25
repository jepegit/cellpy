# Issue #1023 — plan (iteration 13: usability review)

Confirmed by the user on 2026-09-23 ("implement the fixes … do not stop and
ask"). Source of truth for the individual items:
[docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md)
(numbers below refer to its sections).

Branch: `1023-docs-usability`. One PR, one commit per chunk.

## Chunks

1. **Quick fixes** — 1.1 landing H1, 3.1 `.ipynb` links (fixed in the render
   script so re-renders keep them), 3.6 nav/H1 titles, 4.3 orphans, 5.2 API
   table, §8 relative-link checker in `00-tools/` + `docs.yml`.
2. **Tutorial framing** — render script injects a per-tutorial header (what you
   learn, data, download link) and caps long dataframe tables; `##` headings
   in 05/09 notebooks; tutorial index as a table; render instructions moved to
   `dev_docs.md`. Notebooks are *not* re-executed (their data paths stay; the
   header says where the data comes from).
3. **Nav restructure** — "Use with AI agents" section, "Upgrading" subsection,
   tutorial core path vs other instruments, pages moved to match the nav
   (`guides/`, `reference/`) with Zensical `redirects` so old URLs keep
   working.
4. **Landing + getting started** — grid cards, instrument table, runnable hero,
   history → About, basic usage as cheat sheet, shared install snippet.
5. **Theme** — `navigation.tabs`/`sections`, `search.suggest`/`share`
   (check visually with `zensical serve`; revert if worse).
6. **Pictures** — generated figures for the plotting guide
   (`dev/render_guide_figures.py`), Mermaid pipeline diagram in Concepts.
7. **API** — `CellpyCell` on its own page grouped by task; missing docstrings
   on the 8 properties; short examples on the most-used methods; maintainer
   note on `api/cellpy.md` hidden. Keep `show_source` (#1015 decision).
8. **Development** — merge contributing landing; `issue-workflow.md` kept but
   de-emphasised.

## Not doing

- Version banner (7.1) — RTD addons already provide a flyout; needs an admin
  check, not a repo change.
- Page feedback widget (7.4) — not verified in Zensical.
- Running notebooks in CI (§8 P2) — separate issue.

## Verification

- `uv run --group docs zensical build --clean` clean ("No issues found").
- New relative-link checker + `check_rtd_latest_links.py` pass.
- `uv run pytest tests/test_config_secrets.py` (config reference path move).
- Visual pass with `zensical serve` after each chunk.

---

## Previous iteration (12) plan, kept for reference

## Issue #1023 — plan (iteration 12: tutorial-notebook pass)

### Goal

Role-play a battery scientist walking the numbered tutorials on RTD latest,
fix whatever is missing, wrong, or unfindable in the **source notebooks**,
re-render the committed docs pages, and leave the issue open.

### Constraints

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

#### Prior art

- Toolbox: `check_rtd_latest_links.py` — use if we add hard RTD `latest` URLs.
  No notebook helper in `00-tools/`.
- Graph: `graphify-out/` not in this worktree — skipped.
- Renderer: [dev/render_example_notebooks.py](../../dev/render_example_notebooks.py)
  (issue #571 / #869). Plotly HTML stripped; static PNG kept.
- Existing 2.1 note on [docs/examples/index.md](../../docs/examples/index.md):
  numbered tutorials + batch already claim `c.schema` / 2.1 names.
- Cookiecutter notebooks under `examples/cellpy project template/` are
  **out of scope** (separate tree, still `cellpy import prms` in places).

### Approach

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

### Files to touch

- `examples/01_loading_data.ipynb` … `examples/04_incremental_capacity_analysis.ipynb`
  — source edits.
- `docs/examples/01_loading_data.md` … `04_*.md` — re-rendered only.
- `docs/examples/index.md` — only if the walk finds a discoverability hole
  (hand-written; not generated).
- `docs/how_do_i.md` — at most a few index questions.
- `HISTORY.md` — Unreleased docs bullet (close step).

### Test strategy

- Execute any new snippet against `example_data.raw_file()` (`uv run`).
- `uv run --group docs python dev/render_example_notebooks.py`
- `uv run --group docs zensical build` — no broken links / missing anchors.
- `uv run pytest -m essential` — docs-only; expect existing suite green.
  No new pytest.

### Open questions

1. **This iteration = tutorial notebooks 01–04?** Recommended yes.
   Alternative: experienced-Python pass, or widen to all `examples/*.ipynb`.
2. **Re-run notebooks** to refresh outputs, or only edit markdown cells /
   comments and re-render existing outputs? Recommended: edit text + API
   calls as needed; re-execute a notebook only when a snippet is actually
   wrong (kaleido/`batch` extra if plotly PNGs must be backfilled).
