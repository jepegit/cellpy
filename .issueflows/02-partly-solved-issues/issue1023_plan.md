# Issue #1023 — plan (iteration 15: page descriptions)

Drafted 2026-10-22 for the parked next slice (usability review item 7.3). Not confirmed yet.

## Goal

Give the top hand-written docs pages a `description:` so search and social previews say what the page is for.

## Constraints

- Docs front matter only. No product code, no generated tutorial pages (a re-render would drop a hand-added description).
- Do not redo iterations 1–14 or the #1108 metadata guide.
- One sentence, taken from the page's own opening. About 160 characters. Scientist-facing, no unexplained Python.
- Icons stay as they are. Item 7.3's fix is the description, not a new icon pass.
- 7.1, 7.4, notebook CI, the experienced-Python pass, and tutorial 05 stay later.
- Docs live on `master` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).

### Prior art

- Section indexes already set `icon:` in front matter (`docs/how_do_i.md`, `docs/troubleshooting.md`, `docs/getting_started/first_hour.md`, and the other section indexes). No page currently sets `description:`.
- Site-wide text is `site_description` in [zensical.toml](../../zensical.toml). Page `description:` is the per-page meta tag (Material / Zensical front matter).
- Usability review item 7.3 ([docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md)): "Add a `description:` to the front matter of the top ~15 pages."
- Toolbox: `check_docs_relative_links.py` still applies after front-matter edits. No description helper in `00-tools/`.

## Approach

Add `description:` next to the existing front matter on these 15 hand-written pages, in nav order:

1. `docs/index.md`
2. `docs/getting_started/index.md`
3. `docs/getting_started/installation.md`
4. `docs/getting_started/configuration.md`
5. `docs/getting_started/checkup.md`
6. `docs/getting_started/first_hour.md`
7. `docs/getting_started/basic_usage.md`
8. `docs/how_do_i.md`
9. `docs/troubleshooting.md`
10. `docs/examples/index.md`
11. `docs/guides/index.md`
12. `docs/guides/units.md`
13. `docs/fundamentals/data_structure.md`
14. `docs/reference/cli.md`
15. `docs/agents/index.md`

`docs/index.md` already has `hide:`; put `description:` in that same block.

## Files to touch

- The 15 pages above.
- `HISTORY.md` at close.
- The 7.3 line in `docs-usability-review.md` after the pages land.

## Test strategy

- `uv run --group docs zensical build --clean` — "No issues found".
- Built HTML for `first_hour` and the home page contains `<meta name="description"` with that page's sentence.
- `uv run python .issueflows/00-tools/check_docs_relative_links.py`.
- `uv run pytest -m essential` — docs-only; no new pytest.

## Open questions

1. **These 15 pages?** Recommended yes. They are the newcomer path plus units, the data structure, the CLI, and the agent index.
2. **Add icons in the same pass?** Recommended no.

---

## Previous iteration (14) plan, kept for reference

# Issue #1023 — plan (iteration 14: tutorials 01 and 02 on example data)

Confirmed by the user on 2026-10-22 ("Yes" to the recommended in-place plan).

## Goal

Make tutorials 01 and 02 runnable without a private `examples/data` folder, then re-execute and re-render them.

## Constraints

- Docs and notebooks only. No product-code, schema, or CLI changes.
- Do not redo iterations 1–13 or the #1108 metadata guide.
- `docs/examples/*.md` is generated. Edit the `.ipynb`, then `dev/render_example_notebooks.py`. The renderer does not execute notebooks.
- Tutorial 05 stays on `20210210_FC.h5`. Bundled `example_data` is a normal Arbin cycle (`raw_file` / `cellpy_file`). There is no GITT file (`ExampleData` has `# GITT = "gitt.h5"` commented out). Pointing 05 at `example_data` would change the lesson.
- Writing stays task-first. Every snippet is run, not assumed.
- Docs live on `master` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).

### Prior art

- `example_data.arbin_file_path`, `raw_file`, and `cellpy_file` in `src/cellpy/utils/example_data.py`.
- Tutorials 03 and 04 already call `example_data.cellpy_file()`.
- Tutorial 02 already falls back to `example_data.cellpy_file()` when the local file is missing.
- Renderer: [dev/render_example_notebooks.py](../../dev/render_example_notebooks.py). Header **Data:** lines live in its `TUTORIALS` table.
- Toolbox: `check_docs_relative_links.py`, `check_rtd_latest_links.py`. No notebook executor in `00-tools/`.
- Usability review item 3.2 ([docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md)) asked for this switch. Iteration 13 left the notebooks un-executed on purpose.

## Approach

1. In `examples/01_loading_data.ipynb`, load `example_data.arbin_file_path()` through `cellpy.get` (still show that a list of paths works). Save, export, and reload that cell under `out/example.cellpy`. Drop the `20210210_FC_01_cc_0*.res` paths.
2. In `examples/02_Initial_data_inspection.ipynb`, execute `example_data.cellpy_file()` as the path the page shows. One sentence points at `cellpy.get("out/example.cellpy")` for a file the reader saved.
3. Update the `TUTORIALS` data lines for 01 and 02, re-execute both notebooks, re-render the two markdown pages.
4. Tutorial 01 no longer writes `20210210_FC.cellpy`. Tutorial 05 keeps its own file and its header already says `cellpy pull --examples`.

## Files to touch

- `examples/01_loading_data.ipynb`
- `examples/02_Initial_data_inspection.ipynb`
- `docs/examples/01_loading_data.md` and `docs/examples/02_Initial_data_inspection.md` (generated)
- `dev/render_example_notebooks.py` (`TUTORIALS` data lines only)
- `HISTORY.md` at close

## Test strategy

- Run the changed cells with `uv run` (first `example_data` download needs network).
- `uv run --group docs python dev/render_example_notebooks.py`
- `uv run --group docs zensical build --clean`
- `uv run pytest -m essential` — docs-only; expect the existing suite green. No new pytest.

## Open questions

1. **This iteration = 01 and 02 only, leave 05?** Yes. Confirmed with the plan.
2. **Break the 01 → 05 file chain?** Yes. 01 uses bundled example data. 05 keeps `20210210_FC.h5`.

---

## Previous iteration (13) plan, kept for reference

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
