# Issue #724 — plan: include marimo notebooks

## Goal

Prove that marimo notebooks can ship in the Zensical docs: editable sources under
`docs/examples/marimo/`, pages in the Tutorials nav via
[`marimo-md-export`](https://jmarshrossney.github.io/marimo-md-export/),
documented render workflow. No Pyodide / live Python in the site; client-side
interactive embeds are welcome when the export produces them.

## Decisions (confirmed)

1. **Scope:** spike — one sample + pipeline + docs. No Jupyter→marimo migration.
2. **Tooling:** `marimo-md-export` for `.py` → markdown-with-outputs. **Commit**
   the generated `.md` (same as Jupyter examples); keep the sample small so
   base64 figures stay manageable.
3. **Layout:** sources in a separate folder: `docs/examples/marimo/`.
4. **Interactivity:** no docs-site Python process / Pyodide / marimo WASM.
   Prefer whatever static-but-interactive HTML the exporter can embed (e.g.
   zoomable figures) without a backend. Also link the `.py` on GitHub for
   readers who want `marimo edit` locally.

## Constraints

- Docs-only. No library/runtime API changes.
- Zensical does **not** render marimo natively; Markdown in, site out.
- Keep the Jupyter pipeline (`dev/render_example_notebooks.py`) untouched.
- Pages listed in `zensical.toml` `nav`; contributor notes in `dev_docs.md`.
- Watch generated size (`marimo-md-export` base64 figures); use a small demo
  and/or `# @suppress` on heavy cells.
- Rebase onto `origin/master` before build work (branch was 1 behind).

### Prior art

- `dev/render_example_notebooks.py` — Jupyter → committed markdown (#571 / #673).
  **Mirror** with a separate marimo script; do not merge the two CLIs.
- `docs/examples/index.md`, `dev_docs.md` — extend for marimo.
- `zensical.toml` Tutorials nav — must list the new `.md`.
- `.github/workflows/docs.yml` — add path triggers for the marimo script / folder.
- Toolbox: nothing relevant. Graphify: `render_example_notebooks.py` is the
  docs-notebook seam (community 918).

## Approach

1. **Deps** — add `marimo` and `marimo-md-export` to the `docs` group; lock.
2. **Sample** — `docs/examples/marimo/01_hello_cellpy.py` (or similar): load
   example data, one light plot, short prose. Enough to show code + outputs.
3. **Render script** — `dev/render_marimo_notebooks.py`: discover
   `docs/examples/marimo/*.py`, run `marimo-md-export` → committed sibling `.md`,
   clear error if the tool is missing.
4. **Wire docs** — commit generated `.md`, nav entry, `examples/index.md` link +
   note, `dev_docs.md` workflow, GitHub link to the `.py`.
5. **CI** — extend Docs workflow path filters for the new script / marimo folder.
   Site build still reads committed markdown (no execute-on-RTD).
6. **Non-goals** — convert existing `.ipynb` set; replace Jupyter; WASM embeds;
   cookie-template changes.

## Files to touch

| Path | Change |
| --- | --- |
| `pyproject.toml` (+ lock) | `docs` group: `marimo`, `marimo-md-export` |
| `docs/examples/marimo/*.py` (+ generated `.md`) | Sample + rendered page |
| `dev/render_marimo_notebooks.py` | New render helper |
| `zensical.toml` | Nav entry |
| `docs/examples/index.md` | Link + marimo note |
| `docs/contributing/developers_guide/dev_docs.md` | Marimo render workflow |
| `.github/workflows/docs.yml` | Path triggers |

## Test strategy

- `uv run --group docs python dev/render_marimo_notebooks.py`
- `uv run --group docs zensical build` (no `[N] issues found`)
- Jupyter render unchanged if sources untouched
- PR Docs workflow green

## Open questions

_None — ready for `/iflow-build` once accepted._
