
# Writing documentation

All contributions to documenting `cellpy` is highly welcomed.

## Types of documentation

Code can be documented by several means. All are valuable. For example:

- adding examples to the `examples` folder
- improving the documentation in the `docs` folder
- improving the doc-strings in the code
- adding descriptive tests to the code
- providing example data (e.g. raw-files in different formats)
- tutorials on YouTube
- blogs etc.
- apps

## Add examples to the examples folder

The examples folder is a good place to add examples of how to
use `cellpy`. The examples should be self-contained
and easy to understand. It is recommended to use Jupyter notebooks (but not required).

Another contribution could be to add example data.

## Working on the main documentation

Edit documentation on **`master`** (same branch as the code). There is no
separate docs integration branch — `v2-docs-stable` is retired.

The docs are hosted on Read the Docs:

- Stable: <https://cellpy.readthedocs.io/en/stable/> (built from the latest
  **release tag**, e.g. `v2.1.0`)
- Latest: <https://cellpy.readthedocs.io/en/latest/> (built from **`master`**)
- Admin: <https://readthedocs.org/projects/cellpy/>

[Zensical](https://zensical.org) renders the documentation (the successor to
Material for MkDocs). cellpy-core uses the same stack, so the two projects'
docs behave the same way.

!!! note "The header release badge always shows the *latest* release"

    The repository card in the top-right of every page (stars, forks, and a
    release tag) is populated from the live GitHub API when the page is viewed,
    independent of which tag Read the Docs built. So an older docs version
    (e.g. `v2.0.0`, selected via the RTD switcher) still shows the newest
    GitHub release in that badge. This is expected: the **bottom-right RTD
    version switcher is the source of truth** for which docs you are reading.
    The page *content* is always correct for the selected version.

### Building locally

```shell
uv run --group docs zensical serve   # live preview at http://localhost:8000
uv run --group docs zensical build   # one-off build into site/
```

The build reports broken links and missing anchors but still exits 0, so CI
greps its output — see `.github/workflows/docs.yml`. Treat "issues found" as a
failure.

### Layout

- `zensical.toml` at the repo root owns the navigation, theme and markdown
  extensions. **There is no toctree**: if you add a page, add it to `nav` there
  or it will not appear.
- Pages are plain markdown with
  [pymdownx](https://facelessuser.github.io/pymdown-extensions/) extensions.
  Admonitions are `!!! note`, not `:::{note}`.
- **Naming cellpy in prose:** write plain cellpy for the project/product
  name; use backticks only for the package, import, or CLI
  (`pip install cellpy`, `cellpy setup`). Bold is optional for brand emphasis
  on a landing page — do not scatter it through body text.
- Diagrams are ```mermaid fences, rendered client-side — no graphviz binary
  needed.
- Files outside `docs/` (`README.md`, `HISTORY.md`, `DEPRECATIONS.md`, …) are
  pulled in with `--8<-- "FILE.md"` snippets so they keep a single source of
  truth.

### API reference

Generated from the docstrings by
[mkdocstrings](https://mkdocstrings.github.io) via Griffe, which reads the
source statically — the docs build never imports cellpy. Pages live in
`docs/api/` and are a list of `::: module.path` directives; add a directive to
document something new.

### Example notebooks (Jupyter)

Zensical does not render `.ipynb`, so the notebooks under `docs/examples/` are
converted to committed markdown:

```shell
uv run --group docs python dev/render_example_notebooks.py
```

Re-run and commit the output whenever a notebook changes. The script strips
plotly's embedded HTML before converting — leaving it in produces ~50 MB of
generated markdown for nine notebooks — and keeps the static PNG renderings
plus pandas HTML tables (wrapped for styling via `docs/stylesheets/extra.css`).
The `.ipynb` files stay in the tree as the interactive source.

If a notebook was saved with Plotly outputs but no PNG (so the rendered page
shows code with no figure), backfill static images from the Plotly JSON first:

```shell
uv run --extra batch --group docs python dev/backfill_notebook_plotly_pngs.py
```

It renders the outputs already stored in the notebooks; it does **not** execute
them.

### Doc-strings

- Use Google-style doc-strings
- In addition to the standard admonitions, you can also use:
  - Transferred Arguments
  - See Also

## Tests

- Use pytest
- Use descriptive test names
- Use fixtures and try to keep the tests organized in a logical way
- Use the `conftest.py` file to keep fixtures and other common stuff
- Parameters and variables (e.g. filenames) can be defined in the `fdv.py` file.
