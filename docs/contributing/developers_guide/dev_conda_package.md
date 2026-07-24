# Conda packages (conda-forge)

`cellpy` on conda-forge is built from the **PyPI sdist**. Publish to PyPI first
(see [Packaging for PyPI](dev_cellpy_packaging_pypi.md)); the feedstock then
picks up that release.

Feedstock: [conda-forge/cellpy-feedstock](https://github.com/conda-forge/cellpy-feedstock).

## Happy path: autotick bot

The feedstock enables the conda-forge version bot (`bot.automerge: true` in
`conda-forge.yml`). After a new version appears on PyPI:

1. Wait for **regro-cf-autotick-bot** to open a PR on the feedstock (version,
   URL, and sha256 updated).
2. Review CI. If dependencies changed in `pyproject.toml`, edit the bot branch
   (especially the `cellpycore` pin and other run requirements in
   `recipe/meta.yaml`) and push to that branch.
3. Merge when green. Packages appear on the `conda-forge` channel shortly after.

Check availability:

```shell
conda search -c conda-forge cellpy
```

!!! note
    Rerender (CI config / platforms) when needed by commenting on the PR:
    `@conda-forge-admin, please rerender`

## Manual update (fallback)

Use this when the bot stalls, or you need a recipe-only change (deps, skips,
tests) without a new upstream version.

1. Fork and clone [cellpy-feedstock](https://github.com/conda-forge/cellpy-feedstock)
   (or sync your existing fork with `upstream/main`).
2. Branch, then edit `recipe/meta.yaml`:
   - `version` — normalized form (*e.g.* `0.5.2a3`, not `0.5.2.a3`)
   - `sha256` — from the PyPI “Download files” page for that sdist
   - `build/number` — `0` for a new version; bump only when the version is unchanged
   - run requirements — keep in sync with PyPI deps (conda package names)
3. Push the branch and open a PR against `conda-forge/cellpy-feedstock`.
4. Wait for CI, merge when green.

Example clone setup:

```shell
git clone https://github.com/<you>/cellpy-feedstock.git
cd cellpy-feedstock
git remote add upstream https://github.com/conda-forge/cellpy-feedstock
git fetch upstream
git switch -c update_x_x_x upstream/main
```

Local rerender (optional; the admin comment above is usually enough):

```shell
conda install -c conda-forge conda-smithy
conda smithy rerender -c auto
```
