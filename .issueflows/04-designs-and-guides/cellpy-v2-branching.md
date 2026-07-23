# cellpy v2.0 — branching conventions

How to develop **v2** without disrupting **1.x** work on `master`. Companion to
[`cellpy-v2-epic.md`](cellpy-v2-epic.md) and GitHub epic [#402](https://github.com/jepegit/cellpy/issues/402).

## Summary

| Branch | Role | PR target | Releases |
|--------|------|-----------|----------|
| **`v1.x`** | Stable **1.x** maintenance line | `v1.x` | Tags `v1.x.y` / `v1.x.y.postN` |
| **`master`** | **2.x** development (was 1.x before the split) | `master` | Tags `v2.x.y` after v2 merge |
| **`v2`** | Long-lived **v2.0** integration (epic #402) | `v2` | None until v2.0; then merge → `master` and tag `v2.0.0` |
| **`<N>-<slug>`** | Short-lived issue branches | Parent line (see below) | — |

**Golden rule:** Same repo, same issues/CI — branch, don't fork (no `cellpy-next` clone).

**Parity goal (both directions):** `master` and `v2` should not drift. Stable, shared work
belongs on **`master` as soon as it is verified** — not only at v2.0. The `v2` branch carries
v2-only design ahead of release; everything else should flow through `master` promptly.

## Who branches from where

```
master  ──►  391-batch-collector-default     ──►  master     (v1 maintenance / features)
master  ──►  384-bump-core-parity           ──►  master     (Phase 0 — preferred if 1.x-safe)
v2      ──►  402-v2-testmeta-on-data        ──►  v2         (v2 epic themes V2-01+)
master  ──merge before each v2 issue──►  v2   (1.x fixes into integration line)
v2      ──backport when stable──►  master    (shared fixes/cleanup — see below)
v2      ──once at release──►  master          (full v2.0 integration merge only)
```

### Default PR target

- **Unlabeled / general work → `master`**
- **Epic #402 / label `v2` / title prefix `v2:` → `v2`**

### What belongs on `master` vs `v2`

| Work | Branch | Rationale |
|------|--------|-----------|
| Bugfixes, docs, plot/batch/CLI tweaks | **`master` first** | 1.x users get fixes immediately; merge into `v2` before next v2 issue |
| Phase 0 gate (#384, #385, STEP-12 units) | **`master` first** when parity tests show no behaviour change | Shared cleanup — ideal on `master` ASAP |
| Phase 0 that might change output | `v2` first, then **backport** to `master` only after proven stable | Protect 1.x until verified |
| V2-01 … V2-15 (metadata, merge, API, file format) | **`v2` only** | Breaking / v2-only surface — do not backport |
| `cellpycore` pin bump | **`master`** once essential + full suite green; mirror on `v2` at next sync | 1.x line stays current |

## Keeping 1.x safe on `master`

1. **No v2 data model or file-format work on `master`** — even behind flags, if persistence or public API changes.
2. **CI must pass** before merge (`uv run pytest`; use `-m essential` for inner loop).
3. **Conservative core pin on `master`:** e.g. `cellpycore>=0.1.2,<0.2` until v2 needs a newer API.
4. **Do not wholesale-merge `v2` → `master`** except the single v2.0 release — but **do
   backport** stable, 1.x-safe commits promptly (see below).

## Backporting stable work to `master`

When work lands on `v2` first but is **100% stable** and **does not depend on v2-only design**
(metadata model, file format v2, breaking API), get it onto **`master` as soon as possible**
— do not wait for v2.0.

### Prefer `master` first (best case)

If you already know a change is behaviour-neutral for 1.x (bugfix, CI, docs, Phase 0 cleanup
with green `-m essential` + full suite):

1. Branch from **`master`**, PR to **`master`**
2. After merge, sync into `v2` (`git merge origin/master` on `v2`)

This keeps the source of truth for shared code on the line everyone uses.

### Backport from `v2` (when work started there)

If a merged `v2` PR contains **only** 1.x-safe commits (or a subset of a PR):

1. **Cherry-pick** those commits onto a branch from `master`, or open a **dedicated backport
   PR** with the same diff scoped to shared files
2. Run **`uv run pytest -m essential`** (minimum) and full suite before merging to `master`
3. Reference the original `v2` PR in the backport PR body

| Safe to backport to `master` | Never backport (v2-only until release) |
|------------------------------|----------------------------------------|
| Bugfixes in shared modules | `TestMetaCollection` / keyed metadata |
| Phase 0 engine cleanup (#384, #385) after parity proof | HDF5 / cellpy file format v2 |
| Unit delegation to `cellpycore.units` | Public API removals / deprecations shipped as v2 |
| Tests, CI, docs (non-v2) | Multi-test merge behaviour |
| Conservative `cellpycore` pin bump | Native-schema opt-in defaults |

**Rule of thumb:** if a 1.x user would not notice the change (or only benefits), it belongs
on `master` now. If it requires v2 metadata or breaks saved files, keep it on `v2`.

### Split PRs when mixed

If one piece of work touches both shared cleanup and v2-only design, **split into two PRs**:

- PR A → `master` (stable slice, merge first)
- PR B → `v2` (v2-only slice, branch after syncing `v2` with updated `master`)

## Before starting a v2 issue

**Always update `v2` from `master` before you create an issue branch.** Do not branch from a
stale `v2` — you will miss 1.x bugfixes and make the eventual v2.0 merge harder.

```bash
git fetch origin
git checkout v2
git pull --ff-only origin v2
git merge origin/master   # bring 1.x fixes into the integration line
# resolve conflicts (see below), then:
uv sync
uv run pytest -m essential
git checkout -b 402-v2-testmeta-on-data
```

### What to take from `master`

| From `master` | Action on `v2` |
|---------------|----------------|
| Bugfixes, CI, docs, behaviour-neutral refactors | **Take** — keep v2 current |
| Phase 0 shared cleanup (#384, #385) if already on `master` | **Take** if parity tests still pass on `v2` |
| 1.x-only behaviour you intentionally changed on `v2` | **Resolve in favour of `v2`** during the merge |
| New 1.x features that **conflict with the v2 epic** (e.g. alternate data model, API v2 rejects) | **Do not blindly keep** — resolve consciously; prefer the v2 design and drop or re-implement the 1.x path on `v2` only |

There is no automatic “exclude list”. During `git merge origin/master`, read conflicting
commits: if a `master` change **directly works against a v2 goal** documented in
[`cellpy-v2-epic.md`](cellpy-v2-epic.md), keep the **`v2` side** (or a v2-appropriate rewrite),
not the 1.x version. When unsure, note the conflict in the PR and link epic #402.

### What not to do

- **Do not** wholesale-merge the **`v2` branch** into `master` until v2.0 (backport **commits**, not the integration branch).
- **Do not** let stable shared fixes **only** live on `v2` — backport or land on `master` first.
- **Do not** branch a v2 issue from `master` — branch from **updated `v2`**.
- **Do not** assume `git pull` on `v2` alone is enough if `master` has moved; you must
  **merge `origin/master` into `v2`** (or rebase `v2` onto `master` if the team agrees —
  merge is the default here).

After your issue branch is done, open the PR against **`v2`**, not `master`.

## Reality check: what “1.x on master” means today

`master` already includes the **cellpy-core seam** (#377), Python **≥ 3.13**, and a PyPI
`cellpycore` dependency. “1.x” here means **post-seam 1.x** — not pre-core cellpy. v2 adds
metadata, multi-test merge, API cleanup, and file-format changes on top.

## Releases and PyPI

Full procedure: [`release-procedure.md`](release-procedure.md). Summary:

| Line | GitHub release from | Tag examples | PyPI |
|------|---------------------|--------------|------|
| **1.x maintenance** | **`v1.x`** (preferred; `master` still accepted) | `v1.1.0.post2`, `v1.1.1` | stable |
| **v2 integration** | **`v2`** (optional) | `v2.0.0a1` | pre-release only (`--pre`) |
| **2.x (after v2.0 merge)** | **`master`** | `v2.0.0`, `v2.1.0` | stable |

**Workflow:** `release: published` → validate tag/branch → test (`UV_NO_SOURCES=1`) →
`uv build` → PyPI trusted publish (`.github/workflows/release.yml`).

**1.x maintenance:** ship bugfixes on **`v1.x`** and cut GitHub releases with
`--target v1.x`. Do not accumulate 1.x-only fixes on `v2` / current `master` (2.x work).

**Versioning:** tag name = version (`uv-dynamic-versioning`); no separate bump in
`pyproject.toml`. Pin exact `cellpycore==…` in the release commit on `v1.x` when cutting
1.x tags.

## Local development

### v1 work (default)

```bash
git checkout master
git pull --ff-only
git checkout -b 391-batch-collector-default
uv sync
uv run pytest -m essential   # fast smoke
```

### v2 work

**Prerequisite:** merge `origin/master` into `v2` first — see
[Before starting a v2 issue](#before-starting-a-v2-issue).

```bash
git fetch origin
git checkout v2
git pull --ff-only origin v2
git merge origin/master          # sync 1.x fixes; resolve conflicts (v2 wins on v2-only design)
uv sync
uv run pytest -m essential
git checkout -b 402-v2-testmeta-on-data
```

### Side-by-side with worktrees

```bash
git fetch origin
git worktree add ../cellpy-v2 v2
# ../cellpy     → master (v1)
# ../cellpy-v2  → v2
```

Editable `cellpycore` (`[tool.uv.sources]` in `pyproject.toml`) applies in both; use **uv**,
not conda, for integration tests.

## GitHub hygiene

- **Default branch stays `master`** for clones and casual contributors.
- Label **`v2`** on issues/PRs tied to epic #402; set PR base to `v2`. (Label created:
  purple **`v2`** — *cellpy v2.0 epic work — PRs should target the v2 branch*.)
- Child issues carved from the epic should state **Target branch: `v2`** in the body.
- **Branch protection** on **`master`** and **`v2`** (configured 2026-07-03):
  - Require PR before merge (0 approvals — merge when CI green, no reviewer gate)
  - Required checks: **`Run pytest on linux (conda)`**, **`Installing using pip on posix`**
  - Branches must be up to date before merge (`strict`)
  - No force-push; no branch deletion
  - Admins may bypass (`enforce_admins: false`)
- Close **#334** as superseded by #377 — do not merge that branch.

## Dependency policy (cellpy-core)

| Line | `pyproject.toml` | Notes |
|------|------------------|-------|
| `master` | `cellpycore>=0.1.2,<0.2` (example) | Avoid pulling breaking core API accidentally |
| `v2` | Pin exact or tighter range as needed | Can trail core `#67` / `#68` fixes |

Before tagging any **1.x** release, ensure `[tool.uv.sources]` editable override is not relied
on for the release build (PyPI pin is consumer truth — see cellpy-core migration guide).

## At v2.0 release (checklist)

- [ ] Full `uv run pytest` green on `v2`
- [ ] Merge `master` → `v2` one last time; resolve conflicts
- [ ] Merge `v2` → `master` (single integration PR)
- [ ] Tag `v2.0.0` on `master`
- [ ] Pin exact `cellpycore==…` in release commit
- [ ] Publish migration guide (v1 files → v2 read path)
- [ ] Update epic #402; archive issue-flow docs to `03-solved-issues`

## Tracking

- **Epic:** [#402](https://github.com/jepegit/cellpy/issues/402)
- **Release procedure:** [`release-procedure.md`](release-procedure.md)
- **Architecture:** [`cellpy-v2-architecture.excalidraw`](cellpy-v2-architecture.excalidraw)
- **Epic doc:** [`cellpy-v2-epic.md`](cellpy-v2-epic.md)
