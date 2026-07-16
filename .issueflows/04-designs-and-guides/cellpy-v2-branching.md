# cellpy v2.0 — branching conventions (post-v1.1)

How to develop **v2 on `master`** while keeping a quiet **`v1.x`** maintenance line
for 1.x fixes. Companion to [`cellpy-v2-epic.md`](cellpy-v2-epic.md) and GitHub epic
[#402](https://github.com/jepegit/cellpy/issues/402).

> **Scheme change (2026-07-16).** Up to v1.1 this document prescribed the inverse
> layout (`master` = stable 1.x, long-lived `v2` integration branch). With v1.1
> released and v2 becoming the dominant line of development, the scheme was
> flipped: **v2 develops on `master`**, and 1.x maintenance moved to the **`v1.x`**
> branch (created at `v1.1.0.post1`). The old `origin/v2` branch is retired — its
> only unique commits were sync/workflow artifacts whose content is already on
> `master`; do not base new work on it. This section is the marker for anyone
> holding stale clones or reading old issue references.

## Summary

| Branch | Role | PR target | Releases |
|--------|------|-----------|----------|
| **`master`** | **v2 development** (epic #402) — *unstable during the v2 cycle* | `master` | Pre-releases `v2.0.0a1`, … then `v2.0.0` |
| **`v1.x`** | Stable **1.x maintenance** — fixes only | `v1.x` | Tags `v1.1.1`, `v1.2.0`, … |
| **`<N>-<slug>`** | Short-lived issue branches | Parent line (see below) | — |

**Golden rule:** same repo, same issues/CI — branch, don't fork.

**Direction of flow:** shared fixes land on **`master` first**, then are
**cherry-picked to `v1.x`** when 1.x users need them. `v1.x` never merges back
wholesale; only the rare fix developed directly on `v1.x` (because master has
diverged too far) flows master-ward, also as a cherry-pick.

## Who branches from where

```
master ──► 501-v2-testmeta-on-data  ──► master   (v2 development — the default)
master ──► 502-fix-shared-bug       ──► master   (bugfix), then cherry-pick → v1.x
v1.x   ──► 503-v1-only-fix          ──► v1.x     (only when the fix doesn't apply to master)
```

### Default PR target

- **Everything → `master`** unless it is a 1.x-only fix.
- **1.x backports / v1-only fixes → `v1.x`** (label `v1x`, or state
  "Target branch: `v1.x`" in the issue).

### What belongs where

| Work | Branch | Rationale |
|------|--------|-----------|
| V2 themes (metadata, merge, API, file format) | **`master`** | The active line |
| Bugfixes in shared modules | **`master` first**, cherry-pick to `v1.x` if 1.x users are affected | One source of truth |
| Docs, CI, tests | **`master`**; backport only if the `v1.x` release process needs them | Keep `v1.x` quiet |
| Fix that only makes sense pre-v2 (removed/rewritten code on master) | **`v1.x` directly** | Nothing to cherry-pick from |
| `cellpycore` pin bump | **`master`** freely as v2 needs; **`v1.x`** stays on the conservative exact pin (`cellpycore==0.2.1`) unless a fix demands a patch bump | Protect the stable line |

## Backporting to `v1.x`

When a merged `master` fix should reach 1.x users:

1. `git checkout v1.x && git pull --ff-only`, branch `<N>-backport-<slug>`.
2. **Cherry-pick the squash commit(s)** from master (`git cherry-pick <sha>`);
   resolve conflicts in favour of the 1.x code.
3. Run `uv run pytest -m essential` (minimum) — full suite before a `v1.x` release.
4. PR against **`v1.x`**, referencing the original master PR.

**Rule of thumb:** if a 1.x user is hurting, backport; otherwise let master carry it.
Do not backport v2 design (metadata model, file format, API changes) under any flag.

## Keeping the lines healthy

1. **`v1.x` is fixes-only.** No features, no refactors, no dependency churn beyond
   what a fix requires. Every commit should be releasable as `v1.1.x`.
2. **CI must pass on both lines** before merge (`uv run pytest`; `-m essential`
   for the inner loop).
3. **Do not merge `v1.x` ↔ `master`** in either direction — cherry-pick individual
   commits. The lines are allowed to diverge; that is the point.
4. **master may be unstable** during the v2 cycle. Users installing from GitHub
   master get v2-in-progress; released versions come from PyPI tags only.

## Releases and PyPI

Full procedure: [`release-procedure.md`](release-procedure.md). Summary:

| Line | GitHub release from | Tag examples | PyPI |
|------|--------------------|--------------|------|
| **1.x maintenance** | **`v1.x`** | `v1.1.1`, `v1.2.0` | stable |
| **v2 pre-releases** | **`master`** | `v2.0.0a1`, `v2.0.0b1` | pre-release only (`--pre`) |
| **v2.0 and beyond** | **`master`** | `v2.0.0`, `v2.1.0` | stable |

**Workflow:** `release: published` → validate tag/branch → test (`UV_NO_SOURCES=1`)
→ `uv build` → PyPI trusted publish (`.github/workflows/release.yml`).
**Check per release line:** the workflow's tag/branch validation must accept
`v1.x.y` tags cut from the **`v1.x` branch** (it historically assumed `master`) —
verify before cutting the first `v1.1.1`.

**Versioning:** tag name = version (`uv-dynamic-versioning`); no separate bump in
`pyproject.toml`. Pin exact `cellpycore==…` in the release commit on **whichever
line** is being released.

## Local development

### v2 work (default)

```bash
git checkout master
git pull --ff-only
git checkout -b 501-v2-testmeta-on-data
uv sync
uv run pytest -m essential   # fast smoke
```

### v1 maintenance work

```bash
git checkout v1.x
git pull --ff-only
git checkout -b 503-backport-fix-xyz
uv sync
uv run pytest -m essential
```

### Side-by-side with worktrees

```bash
git fetch origin
git worktree add ../cellpy-v1x v1.x
# ../cellpy      → master (v2)
# ../cellpy-v1x  → v1.x  (1.x maintenance)
```

Editable `cellpycore` (`[tool.uv.sources]` in `pyproject.toml`) applies in both;
use **uv**, not conda, for integration tests.

## GitHub hygiene

- **Default branch stays `master`** — now the v2 line; clones and casual PRs land
  on active development by default.
- **Branch protection:** `master` keeps its existing rules; apply the same to
  **`v1.x`** (require PR, required checks `Run pytest on linux (conda)` +
  `Installing using pip on posix`, strict up-to-date, no force-push, no deletion).
  The old `v2` branch's protection can be dropped when the branch is deleted.
- The **`v2` PR label** is obsolete for targeting (everything targets master);
  use a **`v1x`** label for backport/maintenance PRs instead.
- Issues that are 1.x-only should state **Target branch: `v1.x`** in the body.

## Dependency policy (cellpy-core)

| Line | `pyproject.toml` | Notes |
|------|------------------|-------|
| `master` | Track newer `cellpycore` as v2 needs (exact `==` pin at each release commit) | v2 co-evolves with core |
| `v1.x` | `cellpycore==0.2.1` (the v1.1 pin) | Bump only for a fix, and only to a patch release |

Before tagging any release, ensure the `[tool.uv.sources]` editable override is
not relied on for the release build (PyPI pin is consumer truth — see the
cellpy-core migration guide).

## At v2.0 release (checklist)

- [ ] Full `uv run pytest` green on `master`
- [ ] Tag `v2.0.0` on `master`
- [ ] Pin exact `cellpycore==…` in the release commit
- [ ] Publish migration guide (v1 files → v2 read path; see
      `architecture-plan/cellpy-v104-migration-notes.md` for the 1.0.3→1.0.4 part)
- [ ] Update epic #402; archive issue-flow docs to `03-solved-issues`
- [ ] `v1.x` remains open for critical fixes as long as needed; announce its
      end-of-life explicitly when the time comes

## Tracking

- **Epic:** [#402](https://github.com/jepegit/cellpy/issues/402)
- **Release procedure:** [`release-procedure.md`](release-procedure.md)
- **Architecture:** [`cellpy-v2-architecture.excalidraw`](cellpy-v2-architecture.excalidraw)
- **Epic doc:** [`cellpy-v2-epic.md`](cellpy-v2-epic.md)
