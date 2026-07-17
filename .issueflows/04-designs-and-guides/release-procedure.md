# Release procedure — GitHub release → PyPI

**Context.** cellpy publishes to **PyPI as `cellpy`**. A published GitHub release
triggers `.github/workflows/release.yml`: validate tag/branch → test → build →
PyPI trusted publishing.

**Authoritative companions (do not contradict these):**

| Doc | Owns |
|-----|------|
| [`cellpy-v2-branching.md`](cellpy-v2-branching.md) | Branch layout after the 2026-07-16 flip |
| `architecture-plan/cellpy2-release-and-branching-plan.md` (sibling repo) | Support matrix, cross-repo merge order (F9), final-legacy gates |
| [`build-and-versioning.md`](build-and-versioning.md) | Tag-derived versioning (`uv-dynamic-versioning`) |

> **Scheme (post-v1.1):** **`master` = v2 development**; **`v1.x` = 1.x
> maintenance**. Old long-lived `v2` branch is retired — do not release from it.

---

## The moving parts

- **Version** comes from the **git tag** via `uv-dynamic-versioning`. No
  hand-edited `project.version`. Tag `vX.Y.Z` → PyPI `X.Y.Z`.
- **Cut a release** with `gh release create --target <branch>`. CI checks that
  the tagged commit is on that branch.
- **`.github/workflows/release.yml`** on `release: published`:
  - **validate** — `v1.*` on `origin/v1.x`; `v2.*` on `origin/master`; else fail
  - **test** — `UV_NO_SOURCES=1 uv sync` → `pytest -m essential`
  - **publish** — `uv build` → PyPI trusted publishing (`pypi` env)

---

## Which branch to release from

| Tag pattern | Branch | PyPI channel |
|-------------|--------|--------------|
| `v1.x.y` / `v1.x.y.postN` | **`v1.x`** | stable |
| `v1.x.yaN` / `bN` / `rcN` | **`v1.x`** | pre-release (`--pre`) |
| `v2.0.0aN` / `bN` / `rcN` | **`master`** | pre-release only |
| `v2.0.0` and later `v2.x.y` | **`master`** | stable |

As of 2026-07-17: 1.x line at **`v1.1.0.post1`** on `v1.x`; v2 pre-releases from
`master` (e.g. **`v2.0.0a1`**).

---

## Do this before any tag (hygiene)

Releases tag **whatever commit is at HEAD**. Unrelated files on that commit ship
with the release (and pollute `master` / `v1.x` history).

1. **Be on the release branch**, not a feature branch.
2. **`git status` must be empty** — no staged/unstaged changes **and no
   untracked files**. Stray `.issueflows/01-current-issues/*` on `master` is a
   common trap; those belong on the issue branch only.
3. **Never `git add .` as release prep.** If you need a pin/HISTORY commit,
   stage those paths explicitly.
4. **Do not merge `master` into a feature branch** just to “get the release doc”
   or move focus-issue files. Cherry-pick or recreate the file on the issue
   branch instead.
5. Prefer a **PR into the release line** for pin/HISTORY changes; direct pushes
   to `master` bypass required checks (repo allows admin bypass — avoid it).

---

## Cutting a release (happy path)

### A. 1.x maintenance (`v1.x`)

```bash
git switch v1.x && git pull --ff-only

# Only if this release needs a pin / HISTORY commit — stage those files by name
UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync
uv run pytest          # full suite before a real 1.x ship

git status             # must show a clean tree (no untracked)

gh release create v1.1.1 --target v1.x --generate-notes

gh run list --workflow release.yml --limit 1
gh run watch <run-id>   # ID from first column; not the workflow filename
```

### B. v2 pre-release or stable (`master`)

```bash
git switch master && git pull --ff-only

UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync
uv run pytest -m essential   # full suite before v2.0.0 stable

git status                   # must show a clean tree (no untracked)

# Pre-release while v2 is unfinished:
gh release create v2.0.0a2 --target master --generate-notes
# Stable only when flip + gates are done:
# gh release create v2.0.0 --target master --generate-notes

gh run list --workflow release.yml --limit 1
gh run watch <run-id>
```

**Optional:** check out the tag, `uv build`, inspect `dist/` metadata.

### Failure modes

- **Validate red (wrong branch):** delete the GitHub release **and** the tag;
  recreate with the correct `--target`. Fix the tree first if the commit was wrong.
- **Test job red:** fix on the release line, merge, cut a **new** tag — never reuse.
- **Publish red but release exists:** PyPI may lack that version; ship the next tag.
- **Accidental files in the tagged commit:** next patch/pre tag from a clean
  commit; remove the stray paths on the release line via a normal PR (do not
  rewrite published tags).

---

## Pre-release checklist (both lines)

- [ ] On the **correct branch** (`v1.x` or `master`), not a feature branch.
- [ ] `git status` clean — **including no untracked** issue-flow / scratch files.
- [ ] Exact **`cellpycore==…`** pin for the release commit (see
      `cellpy-v2-branching.md` for per-line policy).
- [ ] `UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync`.
- [ ] Release build does not depend on a local `[tool.uv.sources]` path.
- [ ] Tests green (`-m essential` min; full suite before stable).
- [ ] **`HISTORY.md`** updated.
- [ ] Tag is **`vX.Y.Z`** (or `aN` / `bN` / `rcN` / `.postN` as appropriate).

### Extra gates — final legacy 1.x ship

Architecture plan §1 / §6.1 and
`architecture-plan/cellpy-v103-vs-v104a3-observations.md`: CE /
coulombic-difference, dropped columns, step classification must be intended
**and** release-noted (or fixed). User notes:
`architecture-plan/cellpy-v104-migration-notes.md`.

### Extra gates — `v2.0.0` stable

`cellpy-v2-branching.md` “At v2.0 release” + architecture release plan (support
matrix, benchmarks, dependency budget). No stable 2.x until flip criteria pass.

---

## cellpy-core coordination (F9)

**Additions:** core PR → core PyPI release → cellpy re-pin on the line → cellpy
PR → cellpy GitHub release.

**Removals:** cellpy migrates off first; then core deletes.

After a core release a line needs:

1. Bump `cellpycore` in that line’s `[project.dependencies]`
2. `UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync`
3. `uv run pytest -m essential`
4. Merge, then include in the next cellpy release on that line

`v1.x` stays on a conservative pin; `master` tracks newer core as v2 needs.
See `cellpy-core` migration guide §2.

---

## One-time GitHub setup (maintainers)

1. PyPI trusted publisher for `cellpy` → `jepegit/cellpy`, workflow `release.yml`,
   environment `pypi`.
2. Optional approval gate on the `pypi` environment.
3. Branch protection on **`master`** and **`v1.x`** (`cellpy-v2-branching.md`).

---

## Tracking

- Workflow: `.github/workflows/release.yml`
- Branching: [`cellpy-v2-branching.md`](cellpy-v2-branching.md)
- Build/versioning: [`build-and-versioning.md`](build-and-versioning.md)
- Architecture: `architecture-plan/cellpy2-release-and-branching-plan.md`
- Epic: [#402](https://github.com/jepegit/cellpy/issues/402)
