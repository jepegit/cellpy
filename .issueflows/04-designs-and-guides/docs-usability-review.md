# Making the cellpy docs easier to use

**Context.** A usability review of <https://cellpy.readthedocs.io/en/latest/>
(RTD `latest` builds `master`, see [`docs-on-master.md`](docs-on-master.md)),
done 2026-09-23 against `docs/` + `zensical.toml` at `e766f365`.
The local build (`uv run --group docs zensical build`) finishes with no
warnings, so this review is about how easy the docs are to *use*. It does not
cover build problems.

**The short version.** The structure is already good. The navigation is ordered
by what a researcher wants to do (Getting started → How do I…? → Tutorials →
How-to guides → Concepts → Reference), and *Your first hour*, *How do I…?* and
*Troubleshooting* are strong pages. What gets in the way now:

1. The newcomer path is crowded with agent and migration pages.
2. The tutorials are raw notebook exports with no framing, broken links and
   data that isn't available.
3. Some pages are in the wrong section, or not in the navigation at all.
4. The API pages are very large single pages.
5. There are almost no pictures in the guides.

Each recommendation below lists the problem, the evidence and the fix.
Priorities are **P1** (do first, cheap and high impact), **P2** and **P3**.

---

## 1. Landing page (`docs/index.md`)

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 1.1 | P1 | The H1 is `# - *a library for assisting in analysing batteries and cells*`. It starts with a stray dash, and it becomes the browser-tab title and the search-result title. | Change it to `# cellpy` and put the tagline under it as normal text. |
| 1.2 | P2 | "Where to start" is a list of seven bullets with equal weight, so a new user has to read all of them to pick one. | Use Zensical **grid cards** (`<div class="grid cards" markdown>`) with 4 large cards: *First hour*, *Load my data*, *How do I…?*, *Troubleshooting*. Keep the rest as a smaller line of links. |
| 1.3 | P2 | Before any "what next", the page spends two paragraphs on "History" and a note saying "cellpy 2 is still settling in". The note undersells a 2.1 release. | Move History to *About*. Keep a one-line "please cite" link. Replace the note with a "What's new in 2.1" line that links to the release history. |
| 1.4 | P3 | The hero example uses `my_cell.res`, which the reader doesn't have. | Show `example_data.raw_file()` so the snippet runs as written, and put the "your own file" form next to it (for example as a tab). |
| 1.5 | P3 | No supported-instruments list is visible. "Can it read my cycler's files?" is the first question most visitors have. | Add a short table (Arbin, Maccor, Neware, PEC, BatMo BDF, custom …) that links to *Other file formats* and the loader-plugin guide. |

## 2. Getting started section

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 2.1 | P1 | The section has 11 entries, and 3 of them are about coding agents or MCP. In `getting_started/index.md`, *Coming from cellpy 2.0* is listed after *Troubleshooting*, so the index and the nav are in different orders. | Split it up: **Getting started** = Installation → Setup → Check → First hour → Basic usage. Move the three agent/MCP pages to a new top-level **"Use with AI agents"** section. Move both migration pages to a **"Upgrading"** subsection (under Getting started or Reference). |
| 2.2 | P2 | *Your first hour* and *Basic usage* overlap: both load example data, inspect frames and export. | Make *Basic usage* a one-screen **cheat sheet** (load / inspect / plot / save, one block each) and link it from the end of *First hour*. Or merge the two pages. |
| 2.3 | P2 | *Your first hour* installs `cellpy[batch]` with pip only, while *Installation* recommends conda first. The two pages disagree. | Use the same tabbed install block (pip / conda / uv) on both pages. A `--8<--` snippet can hold the block so there is one copy. |
| 2.4 | P3 | The Getting started index page is just a list of links. | Add a 3-step "path" (Install → Check → First hour) with the time each step takes. |

## 3. Tutorials (`docs/examples/`)

The biggest gap is here. The pages come from notebooks by
`dev/render_example_notebooks.py`, so most fixes go into the notebooks in
`examples/` or into the render script.

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 3.1 | P1 | **Broken links.** They point to `.ipynb` files that are not in the site: `01_loading_data.md` → `06_loading_different_formats.ipynb` and `07_custom_loaders.ipynb`, and `06_loading_different_formats.md` → `07_custom_loaders.ipynb` (twice). | In the render script, rewrite `NN_name.ipynb` links to `NN_name.md`. Also extend the CI link check (see §8). |
| 3.2 | P1 | **Tutorials cannot be reproduced.** `01_loading_data` and `02_…` read `data/20210210_FC_01_cc_0*.res`, which the reader doesn't have. The page doesn't say where to get it (it's `cellpy pull` / the examples folder). | Switch them to `example_data.*`, as `03_capacity_vs_voltage` already does. Otherwise, add a standard admonition at the top: "Data used: … get it with `cellpy pull`". |
| 3.3 | P1 | **No framing.** Most pages open straight into an `import` cell. `01`, `02`, `03` and `07` have no introduction, `05` and `09` have no `##` sections, so the right-hand table of contents is empty. | Have the render script inject a header block from notebook metadata: *What you'll learn*, *Prerequisites*, *Data*, *Time*, plus a **"Download this notebook"** button (a GitHub raw link) and a "Run in Colab/Binder" badge. Add `##` headings to 05 and 09. |
| 3.4 | P2 | **Order.** The nav puts *Other file formats / BDF / PEC / custom loader* before *First look at your data*, so a learner goes through four format-specific pages before any analysis. | Reorder into two groups: **Core path** (Loading → First look → Capacity vs voltage → ICA → GITT → Batch) and **Loading other instruments** (formats, BDF, PEC, custom loaders). The numbers in the filenames can stay. |
| 3.5 | P2 | **Very large dataframe dumps.** `08_batmo_bdf.md` is 1752 lines with 10 HTML tables, and `04_…` has 7. Readers scroll past walls of numbers. | In the notebooks, use `.head(3)` or select a few columns before displaying. Or have the render script cap tables at N rows. |
| 3.6 | P3 | The titles don't match: the nav says "Loading data" but the page H1 says "Loading, saving and exporting data", and the nav says "First look" but the H1 says "Initial data inspection and plotting". | Make each nav label and H1 the same. |
| 3.7 | P3 | The tutorial index says "Here we provide a few basic examples…" and ends with a maintainer command (`render_example_notebooks.py`). | Replace the intro with a table (tutorial, what you'll learn, level). Move the render instructions to `dev_docs.md`. |

## 4. How-to guides, Concepts, Reference

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 4.1 | P1 | **Pictures are missing where they matter most.** `guides/plotting.md` (263 lines), `guides/ica.md`, `guides/step_table.md` and `guides/units.md` have no images at all. | Add one rendered figure per plotting recipe (a static PNG generated by a small `dev/` script so it stays current). Add a labelled voltage/current trace to *Understand the step table* showing how steps are split. |
| 4.2 | P2 | Several pages are filed in the wrong source folder for their nav section: `getting_started/remote_paths.md` and `other/writing_a_loader_plugin.md` are under How-to, and `getting_started/configuration_reference.md` is under Reference. Their URLs don't match where the reader found them, and contributors can't find the source files. | Move the files to match the nav (`guides/`, `reference/`) and add redirects. RTD page redirects keep the old links working (check whether Zensical supports a redirects plugin yet). |
| 4.3 | P2 | **Pages that exist but aren't in the nav:** `other/writing_a_cli_plugin.md` is linked from the How-to index but isn't in the nav. `adapted_readme.md` and `cursor-issue-workflow.md` (264 lines) aren't reachable at all. | Add the CLI plugin page to the nav under How-to. Delete `adapted_readme.md` if nothing uses it. Delete `cursor-issue-workflow.md` or merge it into `issue-workflow.md`. |
| 4.4 | P2 | The Concepts pages are short (`file_formats.md` is 40 lines) and have no diagram of the raw → steps → summary pipeline. That pipeline is the one idea every user needs. | Add a Mermaid diagram (already enabled in `zensical.toml`) to *How cellpy is organised*, and link to it from *First hour* step 2. |
| 4.5 | P3 | The glossary is good, but no other page uses it. | Turn on `pymdownx.snippets` auto-append with `abbr` so terms like *C-rate* and *step table* get hover tooltips on every page (`content.tooltips` is already on). |

## 5. API reference

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 5.1 | P1 | **Huge single pages.** The rendered `api/readers/` is **1.7 MB** with ~150 documented objects, `api/utils/` is 1.6 MB, and `collect`, `batch` and `cellpy` are each around 0.5 MB. They load slowly, and the right-hand table of contents is too long to use. | Split `CellpyCell` onto its own page. Group its members with mkdocstrings `members:` lists under headings (Loading, Selecting cycles, Extracting curves, Units, Saving). Set `show_source: false` by default (it adds a lot of page weight) and keep source links through `content.action.view`. |
| 5.2 | P2 | The "Where to look" table says "cellpy — `get`, `CellpyCell`", but `CellpyCell` is documented on *Readers*, not on *cellpy*. | Fix the table, or move `CellpyCell` onto a page of its own as in 5.1. |
| 5.3 | P2 | **Docstring quality.** Of the 90 public members of `CellpyCell`, 8 have no docstring (`mass`, `active_mass`, `tot_mass`, `nom_cap`, `nominal_capacity`, `cycle_mode`, …), 18 have a docstring under 60 characters, and only **5** have an `Examples` section. | Add docstrings and a one-line example to the ~20 methods users call most (`get_cap`, `get_ocv`, `get_cycle_numbers`, `save`, `to_csv`, `make_summary`, the unit properties, …). Consider adding `interrogate` or ruff `D1` checks to CI for `cellreader.py`. |
| 5.4 | P3 | The module intro on `api/cellpy.md` explains PEP 562 and Griffe. That's a maintainer note. | Move it into an HTML comment. |

## 6. Development section

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 6.1 | P2 | `issue-workflow.md` (647 lines) documents the maintainers' issue-flow tooling inside the user docs, and it's the largest non-tutorial page. | Link to it from `contributing/index.md` in one line and host it in the repo (for example `.issueflows/` or `CONTRIBUTING.md`) instead of the published nav. Or keep it, collapsed under *Developer guide*. |
| 6.2 | P3 | `contributing/contributing.md` is a 2-line snippet include, and `contributing/index.md` is 14 lines. | Merge them into one "Contributing" landing page. |

## 7. Site-wide features and theme

| # | Pri | Problem | Fix |
|---|-----|---------|-----|
| 7.1 | P2 | *(Check on the live site.)* There doesn't seem to be a version switch or banner, so users of `latest` don't know if they are reading unreleased (master) docs. | Turn on the RTD version flyout / addons, and add a banner on `latest`: "You are reading development docs — see *stable* for 2.1". |
| 7.2 | P2 | Navigation features: `navigation.tabs` and `navigation.sections` are off, so everything sits in one long left sidebar. | Try `navigation.tabs` (the top-level sections become tabs) plus `navigation.sections`. Also add `search.suggest` and `search.share`. |
| 7.3 | P3 | Many pages have no `icon:` front matter, and there are no page descriptions for search or social previews. | Add a `description:` to the front matter of the top ~15 pages. |
| 7.4 | P3 | There's no feedback path on each page. | Turn on the Material-style page feedback widget, if Zensical supports it, ("Was this page helpful?") pointing to GitHub issues. |

## 8. Keep it from regressing

- **P1:** extend the link check. The `Docs` workflow already fails when
  Zensical reports broken links or anchors, but Zensical does not check
  links to non-page files, so the four `.ipynb` links above pass. Add a small
  step that fails on any relative link in `docs/**/*.md` whose target does not
  exist; 20 lines of Python found these.
- **P2:** run the tutorial notebooks in CI (nbmake / `pytest --nbmake`) against
  `example_data`, so that rendered outputs can't go stale against the 2.x API.
- **P3:** add a "docs checklist" to the PR template: nav entry added? images
  current? `how_do_i.md` entry added for new features?

---

## Suggested order of work (issue-sized chunks)

1. **Quick fixes (P1, one PR):** 1.1, 3.1, 3.6, 4.3, 5.2, plus the link-check extension in §8.
2. **Tutorial framing:** 3.2, 3.3, 3.5, 3.7 (render-script changes + notebook edits).
3. **Restructure the nav:** 2.1, 3.4, 4.2 (with redirects), 6.1.
4. **Landing page and theme:** 1.2–1.5, 7.1–7.2.
5. **Pictures:** 4.1, 4.4.
6. **API:** 5.1, 5.3, 5.4.

Chunk 1 fits `/iflow-yolo`. Chunks 2–6 fit an epic (`/iflow-epic`).

## Alternatives considered

- **A full Diátaxis rewrite:** not needed. The current IA already separates
  tutorials, how-tos, concepts and reference. The problems are what the pages
  contain and where they sit, not the overall framework.
- **Bringing marimo back for interactive tutorials:** still blocked, for the
  reasons in [`marimo-docs.md`](marimo-docs.md). Binder/Colab links (3.3) give
  interactivity without it.
