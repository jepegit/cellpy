# Issue #1128 — plan: fix the "Example" widget in the API docs

## Goal

Make docstring examples render as highlighted `pycon` code in the API
reference instead of nested blockquotes with plain text. Fix at docstring
level (the issue's preferred hypothesis — confirmed as the root cause).

## Root cause (verified)

- griffe's Google parser (`griffelib 2.1.0`,
  `griffe/_internal/docstrings/google.py`, `_section_kind`) recognises
  **`Examples:`** only. **`Example:`** (singular) is not a section title, so
  the block falls through to the generic admonition path
  (`DocstringSectionAdmonition(kind="example")`).
- mkdocstrings-python renders admonitions as `<details class="example">`
  with the body converted as **markdown**. A line starting with `>>> ` is
  three nested markdown blockquotes → the three vertical bars in the
  screenshot, and the code is plain paragraph text (prompt stripped).
- Local `zensical build` reproduces it: `site/api/cellpy/index.html` has
  `<details class="example"><blockquote><blockquote><blockquote>…` for
  `list_templates`. Existing `Examples:` sections on the same pages render
  as `language-pycon` highlighted blocks, so no renderer/theme work is
  needed.
- Secondary defect visible in the same screenshot: the `Returns:` of
  `list_templates` is one wrapped description whose continuation lines sit
  at the same indent as the first line, so griffe splits it into four
  `dict` items. Continuation lines must be indented deeper than the first.

## Constraints

- Docstrings only. No zensical / mkdocstrings template or CSS override
  (would mask a format bug and diverge from upstream Google style).
- Match the Google style griffe parses: `Examples:` title, body indented
  one level, doctest lines `>>>`/`...`, free text allowed between examples.
- Docs live on `master`, preview with `uv run --group docs zensical build`
  ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).
- `_old_docs/`, tests and notebooks untouched.

### Prior art

- #1015 (`show_source = true` in `zensical.toml`) and #1023 docs passes —
  same API pages; coexist.
- #1125 (just closed) touched `cellreader.py` docstrings — rebase-safe,
  different lines.
- `.issueflows/00-tools/check_docs_relative_links.py` — run after build.
- 27 docstrings already use `Examples:` correctly (`rg '^\s*Examples:\s*$'
  src/cellpy`) — the convention to mirror.
- Graph not needed.

## Approach

1. Rename the 11 `Example:` section titles to `Examples:`
   (`rg -n '^\s*Example:\s*$' src/cellpy`):
   `cli_api.py` (`list_templates`), `ica.py` ×3, `collect/ica.py`,
   `collect/dva.py`, `readers/cellreader.py` ×2 (`from_source`,
   `fetch_meta`), `parameters/internal_settings.py`, `batch/facade.py`
   (`load`), `readers/instruments/base.py` (`get_raw_units`).
2. The two non-doctest examples (`facade.load`, `base.get_raw_units`) use
   RST `::` literal blocks. Under `Examples:` the prose stays markdown and
   the `::` renders as a literal colon; convert them to fenced
   ```` ```python ```` blocks so they highlight.
3. Fix the `list_templates` `Returns:` continuation indent (one description,
   not four items).
4. Rebuild docs; assert zero `<details class="example">` remain under
   `site/api/` and the former spots now contain `language-pycon` /
   `language-python` blocks.
5. Guard against regression: a small test under `tests/` that scans
   `src/cellpy/**/*.py` docstrings for a bare `Example:` section title and
   fails with the file:line — cheap, pure stdlib (`ast` + regex), marked
   `essential`. Prevents the next copy-paste from reintroducing the bug.

## Files to touch

- `src/cellpy/cli_api.py`, `src/cellpy/ica.py`, `src/cellpy/collect/ica.py`,
  `src/cellpy/collect/dva.py`, `src/cellpy/readers/cellreader.py`,
  `src/cellpy/parameters/internal_settings.py`, `src/cellpy/batch/facade.py`,
  `src/cellpy/readers/instruments/base.py` — docstring section titles (and
  two fenced blocks, one Returns indent).
- `tests/test_docstring_sections.py` — new guard test.
- `.issueflows/01-current-issues/issue1128_status.md` — new.
- `HISTORY.md` at close.

## Test strategy

- `uv run pytest tests/test_docstring_sections.py` (new; fails before, passes
  after).
- `MPLBACKEND=Agg uv run pytest -m essential`.
- `uv run --group docs zensical build --clean` → no issues; grep `site/api`
  for `<details class="example"` → 0 hits.
- `uv run .issueflows/00-tools/check_docs_relative_links.py`.

## Open questions

1. Guard test: keep (recommended, ~25 lines, `essential`) or skip and rely
   on review?
2. Fix the `Returns:` wrap in `list_templates` here (recommended — same
   screenshot, one-line indent) or leave for a separate sweep of all
   `Returns:` blocks?
