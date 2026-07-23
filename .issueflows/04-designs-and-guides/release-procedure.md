# Release procedure — GitHub release → PyPI

**Context.** cellpy publishes to **PyPI as `cellpy`**. A published GitHub release triggers
`.github/workflows/release.yml`: test → build → PyPI trusted publishing. Pattern mirrors
[`cellpy-core/release-procedure.md`](../../cellpy-core/.issueflows/04-designs-and-guides/release-procedure.md).

Branch policy for releases lives in [`cellpy-v2-branching.md`](cellpy-v2-branching.md)
(Releases and PyPI).

## The moving parts

- **Version** is derived from **git tags** via `uv-dynamic-versioning` (see
  [`build-and-versioning.md`](build-and-versioning.md)). There is no hand-edited
  `project.version` in `pyproject.toml`. The **GitHub release tag** (`vX.Y.Z`) is the version
  source at build time.
- **Cut a release** by creating a GitHub release on the correct branch (usually `master` for
  1.x). The tag name must match the version you intend to ship (`v1.0.4` → PyPI `1.0.4`).
- **`.github/workflows/release.yml`** runs on `release: published`:
  - **validate** — tag/branch rules (1.x on `master`, v2.0 pre-releases on `v2`, stable 2.x on
    `master`)
  - **test** — `UV_NO_SOURCES=1 uv sync` (PyPI `cellpycore` only) → `pytest -m essential`
  - **publish** — `uv build` → PyPI **trusted publishing** (`pypi` environment,
    `id-token: write` — configure once in GitHub repo settings, same as cellpy-core)

## Which branch to release from

| Tag pattern | Branch | PyPI channel |
|-------------|--------|--------------|
| `v1.x.y` / `v1.x.y.postN` (stable 1.x) | **`v1.x`** (preferred); **`master`** still accepted for older tags | stable (default `pip install cellpy`) |
| `v1.x.yaN` / `bN` / `rcN` (1.x pre) | **`v1.x`** or **`master`** | pre-release (`pip install cellpy --pre`) |
| `v2.0.0aN` / `bN` / `rcN` | **`v2`** | pre-release (v2 integration testing only) |
| `v2.0.0` and later `v2.x.y` | **`master`** (after v2 merge) | stable |

The workflow **fails** if e.g. `v1.1.0.post2` points at a commit that is on neither
`origin/v1.x` nor `origin/master`.

## Bootstrap: first automated PyPI release

After merging PR #403 (or whenever `release.yml` first lands on `master`), cut an **alpha**
before the first **stable** 1.x tag:

| Step | Tag | Why |
|------|-----|-----|
| 1 | **`v1.0.4a1`** on `master` | Smoke-test trusted publishing + workflow; stays off default `pip install` |
| 2 | `v1.0.4a2`, … | Fix-ups if the pipeline or PyPI metadata needs iteration |
| 3 | **`v1.0.4`** on `master` | Stable 1.x once CI publish is proven and you are happy with the tree |

This matches the current line: latest tag is `v1.0.3a6`, `HISTORY.md` still documents 1.0.3
as pre-release, and post-seam / `cellpycore` integration has not yet shipped on a stable
PyPI tag.

Install the alpha with `pip install cellpy --pre` (or `pip install cellpy==1.0.4a1`).

## Cutting a 1.x release (happy path)

Maintenance releases ship from the **`v1.x`** branch (post-2.0 split). Older 1.x tags
that still live on `master` remain valid for the workflow check.

```bash
git switch v1.x && git pull --ff-only

# 1. Ensure dependency pin is release-ready
#    Pin exact cellpycore for the release if needed (see checklist below).
UV_NO_SOURCES=1 uv lock
UV_NO_SOURCES=1 uv sync
uv run pytest -m essential

# 2. Clean tree — everything for this release is merged on v1.x
git status   # must be clean

# 3. Create the GitHub release (tag = version)
gh release create v1.1.0.post2 --target v1.x --generate-notes

# 4. Watch CI
gh run watch --workflow release.yml
```

**Version preview locally** (optional): checkout the tag you plan to ship, then `uv build` and
inspect `dist/` metadata.

### Failure modes

- **Test job red:** fix on `master`, merge, cut a **new** patch tag — tags are not reused.
- **Publish job red but release exists:** PyPI may not have the version; fix and release
  `v1.0.5` (or next appropriate tag).
- **Wrong branch:** validation job fails; delete the GitHub release/tag and recreate on the
  correct branch.

## Pre-release checklist

- [ ] All changes for this release are merged to **`v1.x`** (1.x line), **`master`**
      (legacy 1.x / 2.x stable), or **`v2`** (v2.0 alphas only).
- [ ] **`cellpycore` pin** in `[project.dependencies]` reflects the intended core revision.
      Use `UV_NO_SOURCES=1 uv lock` so the lock resolves from PyPI, not the editable path.
- [ ] **`uv run pytest -m essential`** (or full suite) green locally with `UV_NO_SOURCES=1`.
- [ ] **No `[tool.uv.sources]` path override** in committed `pyproject.toml` (CI and
      Dependabot use PyPI via `UV_NO_SOURCES=1`).
- [ ] **`HISTORY.md`** updated (Keep a Changelog) before or with the release PR.
- [ ] Tag name follows **`vX.Y.Z`** going forward (legacy inconsistent tags still tolerated
      by `uv-dynamic-versioning` but avoid adding new ones).

## cellpy-core coordination

After each **cellpy-core** PyPI release, update cellpy's consumer pin on **`master`**:

1. Bump `cellpycore` in `[project.dependencies]` (exact `==` before a cellpy release).
2. `UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync`
3. `uv run pytest -m essential` / seam tests
4. Merge to `master`, then include in the next cellpy GitHub release

See `cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-migration.md` §2.

## v2 branch and PyPI

- **No stable PyPI releases from `v2`** until v2.0 merges to `master`.
- Optional **v2.0 alphas** (`v2.0.0a1`, …) from `v2` for early testers (`pip install cellpy --pre`).
- Stable shared fixes discovered on `v2` should **backport to `master`** and ship on the next
  **1.x** tag — do not leave 1.x users waiting for v2.0.

## One-time GitHub setup (maintainers)

1. **PyPI trusted publisher** for `cellpy` → GitHub repo `jepegit/cellpy`, workflow
   `release.yml`, environment `pypi` (mirror cellpy-core setup).
2. **GitHub environment `pypi`** with protection rules if desired (optional approval gate).

## Tracking

- Workflow: `.github/workflows/release.yml`
- Branching + release line policy: [`cellpy-v2-branching.md`](cellpy-v2-branching.md)
- Build/versioning basics: [`build-and-versioning.md`](build-and-versioning.md)
- Epic: [#402](https://github.com/jepegit/cellpy/issues/402)
