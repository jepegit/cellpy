# Issue #1023 — status

- [ ] Done

The issue stays open (it is a series of docs passes). Iteration 13 is on
branch `1023-docs-usability`.

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

## Remaining work

- Review item 7.1 (version banner on `latest`): RTD admin check.
- 7.3 page descriptions, 7.4 feedback widget, running notebooks in CI.
- Re-execute tutorials 01/02/05 against `example_data` so they need no local
  files.
- Later: experienced-Python pass (typing / extending / plugins).
