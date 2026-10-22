# Issue #1023 — status

- [ ] Done

The issue stays open (it is a series of docs passes). Iteration 15 is on
branch `1023-page-descriptions`. Iteration 14 merged as #1166.

## What's done (iteration 15)

- Plan accepted 2026-10-22 ("Yes").
- `description:` added to the 15 hand-written pages in the plan. Icons and generated tutorial pages were left unchanged.
- Verification: `zensical build --clean` "No issues found"; built HTML for all 15 pages has `<meta name="description">` with the page sentence; `check_docs_relative_links.py` "all relative links resolve"; `pytest -m essential` 1076 passed. Two filefinder failures (`test_find_by_project_cellpy_range`, `test_find_by_project_otherpath_local`) search `*.h5` because `~/.cellpy_prms_ubuntu.conf` sets `cellpy_file_extension: h5`. Those two tests pass with that file moved aside. No new tests; essential review left the suite unmarked. No version bump (git-tag versioning).

## What's done (iteration 14)

- Plan accepted 2026-10-22: tutorials 01 and 02 load bundled `example_data`; tutorial 05 stays on `20210210_FC.h5`.
- `examples/01_loading_data.ipynb` loads `example_data.arbin_file_path()`, then saves and reloads `out/example.cellpy`.
- `examples/02_Initial_data_inspection.ipynb` loads `example_data.cellpy_file()`.
- Both notebooks re-executed. Tutorial 02 plot PNGs backfilled with `dev/backfill_notebook_plotly_pngs.py`. Pages re-rendered. `TUTORIALS` data lines updated.
- Verification: `zensical build --clean` "No issues found"; `check_docs_relative_links.py` "all relative links resolve"; `pytest -m essential` 1076 passed. Two filefinder failures (`test_find_by_project_cellpy_range`, `test_find_by_project_otherpath_local`) search `*.h5` because `~/.cellpy_prms_ubuntu.conf` sets `cellpy_file_extension: h5`. Those two tests pass with that file moved aside. No new tests.
- PR: https://github.com/jepegit/cellpy/pull/1166 (#1166, ready).

## Remaining work

- Review item 7.1 (version banner on `latest`): RTD admin check.
- 7.4 feedback widget, running notebooks in CI.
- Experienced-Python pass (typing / extending / plugins).
- Tutorial 05 still needs the local GITT file.

## What's done

- Iterations 1–10 shipped as #1024–#1035 (see issue comment).
- Iteration 11 (glossary) shipped: `docs/fundamentals/glossary.md` plus nav/links.
- Iteration 12 (2026-09-23): tutorial-notebook pass on 01–04 (full_cell,
  refresh_after, native `.cellpy`).
- Iteration 13 (2026-09-23): implemented the usability review
  ([docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md),
  which has an item-by-item status section). Commits:
  - `d2b4b2dd` tutorials framed by the render script (header box, `.ipynb` link
    rewrite, table/text caps, CellpyCell repr dropped), nav restructure with
    redirects, pages moved to `agents/`, `guides/`, `reference/`, orphans
    removed, relative-link checker in CI (`00-tools/check_docs_relative_links.py`).
  - `cdf670d1` landing cards and instruments table, cheat sheet, top tabs.
  - `596fdea9` guide figures (`dev/render_guide_figures.py`), mermaid
    pipeline in Concepts.
  - `8dc7c1f4` `api/cell.md` grouped by task; wrapper docstrings and examples.
  - `e477e3d1` abbreviation tooltips.
  - Doc bugs found: old landing snippet read the raw-unit `charge_capacity`
    column; cheat-sheet draft had `batch.load` args reversed; `to_csv` needs
    an existing folder (now documented); a duplicated DVA section in the
    rendered ICA tutorial (render drift).
- Verification: `zensical build --clean` "No issues found"; both link checkers
  pass; `pytest -m essential` 914 passed; `tests/test_config_secrets.py` passed
  after moving the configuration reference; visual check with `zensical serve`.
