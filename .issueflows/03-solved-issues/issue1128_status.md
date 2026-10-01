# Issue #1128 — status

- [x] Done

Branch: `cursor/1128-docs-example-widget-0881`. Plan accepted 2026-10-01 with
defaults (guard test kept; `Returns:` indent fixed here).

## What's done

- Root cause verified in `griffelib 2.1.0`
  (`griffe/_internal/docstrings/google.py::_section_kind`): only
  `Examples:` is a section title. `Example:` becomes a generic admonition
  rendered as markdown; `>>>` → three nested `<blockquote>`s (the vertical
  bars in the issue screenshot), code loses highlighting and prompts.
- Renamed all 11 `Example:` → `Examples:` (`cli_api.py`, `ica.py` ×3,
  `collect/ica.py`, `collect/dva.py`, `readers/cellreader.py` ×2,
  `parameters/internal_settings.py`, `batch/facade.py`,
  `readers/instruments/base.py`).
- `facade.load` and `base.get_raw_units` prose examples: RST `::` literal
  blocks → fenced ```` ```python ```` so they highlight under `Examples:`.
- `list_templates` `Returns:` continuation lines indented → one `dict`
  item instead of four.
- New `tests/test_docstring_sections.py` (`essential`): `ast` scan of
  `src/cellpy` docstrings, fails on any bare `Example:` title with
  `file:line`. Fails on master (lists all 11), passes here. Registry row
  added in `04-designs-and-guides/test-registry.md`.
- `HISTORY.md` bullet.

## Verification

- `uv run --group docs zensical build --clean` → `No issues found`;
  `rg '<details class="example"' site/api` → 0 files (was 4 pages).
- `site/api/cellpy/index.html`: `list_templates` now has one `Returns`
  item and a `language-pycon` block; `site/api/batch/index.html`:
  `Batch.load` examples are `language-python` blocks.
- Screenshot of the rebuilt page: `/opt/cursor/artifacts/issue1128_after_list_templates.png`.
- `uv run .issueflows/00-tools/check_docs_relative_links.py` → all resolve.
- `MPLBACKEND=Agg uv run pytest -m essential` → 982 passed, 74 skipped;
  the 2 `test_filefinder.py::test_find_by_project_*` failures are the same
  VM-only ones seen on `origin/master` (master CI green).

## Remaining work

- None. Other section-title or wrap defects in docstrings (e.g. multi-line
  `Returns:` elsewhere) were not swept; the guard only covers `Example:`.
