# Release procedure — GitHub release → PyPI

**Context.** cellpy publishes to **PyPI as `cellpy`**. A published GitHub release
triggers `.github/workflows/release.yml`: validate tag/branch → test → build →
PyPI trusted publishing.

**Authoritative companions (do not contradict these):**

| Doc | Owns |
|-----|------|
| [`cellpy-v2-branching.md`](cellpy-v2-branching.md) | Branch layout after the 2026-07-16 flip |
| [`architecture-plan/cellpy2-release-and-branching-plan.md`](../../../architecture-plan/cellpy2-release-and-branching-plan.md) | Support matrix, cross-repo merge order (F9), final-legacy gates |
| [`build-and-versioning.md`](build-and-versioning.md) | Tag-derived versioning (`uv-dynamic-versioning`) |

> **Scheme (post-v1.1):** **`master` = v2 development**; **`v1.x` = 1.x
> maintenance**. The old long-lived `v2` branch is retired — do not release from
> it. See `cellpy-v2-branching.md`.

---

## The moving parts

- **Version** comes from the **git tag** via `uv-dynamic-versioning`. There is no
  hand-edited `project.version`. Tag `vX.Y.Z` → PyPI version `X.Y.Z`.
- **Cut a release** with `gh release create` targeting the correct branch. CI
  checks that the tag’s commit is on that branch.
- **`.github/workflows/release.yml`** on `release: published`:
  - **validate** — `v1.*` must be on `origin/v1.x`; `v2.*` must be on
    `origin/master`; anything else fails
  - **test** — `UV_NO_SOURCES=1 uv sync` (PyPI `cellpycore` only) →
    `pytest -m essential`
  - **publish** — `uv build` → PyPI trusted publishing (`pypi` environment,
    `id-token: write`)

---

## Which branch to release from

| Tag pattern | Branch | PyPI channel |
|-------------|--------|--------------|
| `v1.x.y` / `v1.x.y.postN` | **`v1.x`** | stable |
| `v1.x.yaN` / `bN` / `rcN` | **`v1.x`** | pre-release (`pip install cellpy --pre`) |
| `v2.0.0aN` / `bN` / `rcN` | **`master`** | pre-release only |
| `v2.0.0` and later `v2.x.y` | **`master`** | stable |

Current line (as of mid-2026): stable 1.x tops out at **`v1.1.0.post1`** on
`v1.x`; v2 pre-releases (e.g. **`v2.0.0a1`**) ship from `master`.

---

## Cutting a release (happy path)

### A. 1.x maintenance (`v1.x` branch)

```bash
git switch v1.x && git pull --ff-only

# Pin / HISTORY / tests — see checklist below
UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync
uv run pytest -m essential   # full suite before a real 1.x ship

git status   # must be clean

gh release create v1.1.1 --target v1.x --generate-notes

gh run list --workflow release.yml --limit 1
gh run watch <run-id>
```

### B. v2 pre-release or stable (`master`)

```bash
git switch master && git pull --ff-only

UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync
uv run pytest -m essential   # full suite before v2.0.0 stable

git status   # must be clean

# Pre-release while v2 is unfinished:
gh release create v2.0.0a2 --target master --generate-notes
# Stable (only when flip + gates are done — see architecture plan):
# gh release create v2.0.0 --target master --generate-notes

gh run list --workflow release.yml --limit 1
gh run watch <run-id>
```

**Optional local preview:** check out the tag, `uv build`, inspect `dist/`
metadata.

### Failure modes

- **Validate red (wrong branch):** delete the GitHub release **and** the tag,
  recreate with `--target` set correctly. Do not reuse a bad tag name if the
  commit was wrong; fix the tree first.
- **Test job red:** fix on the release line, merge, cut a **new** patch/pre tag —
  tags are never reused.
- **Publish red but release exists:** PyPI may lack that version; ship the next
  tag after the fix.

---

## Pre-release checklist (both lines)

- [ ] Changes merged to the **correct branch** (`v1.x` or `master`).
- [ ] Exact **`cellpycore==…`** pin in `[project.dependencies]` for the release
      commit (line-specific policy in `cellpy-v2-branching.md`).
- [ ] `UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync` — lock resolves from
      PyPI, not an editable path.
- [ ] No committed `[tool.uv.sources]` path override relied on for the build
      (dev-only; CI uses `UV_NO_SOURCES=1`).
- [ ] Tests green: `-m essential` minimum; **full suite** before stable ships.
- [ ] **`HISTORY.md`** updated (Keep a Changelog).
- [ ] Tag follows **`vX.Y.Z`** (legacy inconsistent tags exist; do not add more).

### Extra gates for the final legacy 1.x ship

See architecture plan §1 / §6.1 and
[`cellpy-v103-vs-v104a3-observations.md`](../../../architecture-plan/cellpy-v103-vs-v104a3-observations.md):
behavior deltas vs 1.0.3 (CE / coulombic-difference, dropped columns, step
classification) must be intended **and** release-noted (or fixed) before that
tag. User-facing notes:
[`cellpy-v104-migration-notes.md`](../../../architecture-plan/cellpy-v104-migration-notes.md).

### Extra gates for `v2.0.0` stable

See `cellpy-v2-branching.md` “At v2.0 release” and the architecture release plan
(support matrix, benchmarks, dependency budget). No stable 2.x until the flip
criteria are met.

---

## cellpy-core coordination (F9)

**Additions** (cellpy needs new core API):

1. core PR → core release (tag / PyPI `cellpycore`)
2. cellpy re-pins on the line being released
3. cellpy PR → then cellpy GitHub release

**Removals** (core drops a cellpy-used API): cellpy migrates off first, then core
deletes.

After each core PyPI release that a line needs:

1. Bump `cellpycore` in that line’s `[project.dependencies]`
2. `UV_NO_SOURCES=1 uv lock && UV_NO_SOURCES=1 uv sync`
3. `uv run pytest -m essential` (seam tests as appropriate)
4. Merge, then include in the next cellpy release on that line

`v1.x` stays on a conservative pin unless a fix demands a bump; `master` tracks
newer core as v2 needs it. Details:
`cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-migration.md` §2.

---

## One-time GitHub setup (maintainers)

1. **PyPI trusted publisher** for `cellpy` → repo `jepegit/cellpy`, workflow
   `release.yml`, environment `pypi`.
2. Optional: protection rules on the GitHub `pypi` environment.
3. Branch protection on **`master`** and **`v1.x`** (see
   `cellpy-v2-branching.md`).

---

## Tracking

- Workflow: `.github/workflows/release.yml`
- Branching: [`cellpy-v2-branching.md`](cellpy-v2-branching.md)
- Build/versioning: [`build-and-versioning.md`](build-and-versioning.md)
- Architecture release plan:
  [`architecture-plan/cellpy2-release-and-branching-plan.md`](../../../architecture-plan/cellpy2-release-and-branching-plan.md)
- Epic: [#402](https://github.com/jepegit/cellpy/issues/402)
