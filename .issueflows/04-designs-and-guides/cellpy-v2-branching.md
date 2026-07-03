# cellpy v2.0 — branching conventions

How to develop **v2** without disrupting **1.x** work on `master`. Companion to
[`cellpy-v2-epic.md`](cellpy-v2-epic.md) and GitHub epic [#402](https://github.com/jepegit/cellpy/issues/402).

## Summary

| Branch | Role | PR target | Releases |
|--------|------|-----------|----------|
| **`master`** | Stable **1.x** line | `master` | Tags `v1.x.y` |
| **`v2`** | Long-lived **v2.0** integration (epic #402) | `v2` | None until v2.0; then merge → `master` and tag `v2.0.0` |
| **`<N>-<slug>`** | Short-lived issue branches | Parent line (see below) | — |

**Golden rule:** Same repo, same issues/CI — branch, don't fork (no `cellpy-next` clone).

## Who branches from where

```
master  ──►  391-batch-collector-default     ──►  master     (v1 maintenance / features)
master  ──►  384-bump-core-parity           ──►  master     (Phase 0, if behaviour-neutral)
v2      ──►  402-v2-testmeta-on-data        ──►  v2         (v2 epic themes V2-01+)
master  ──periodic merge──►  v2              (bring v1 fixes into v2)
v2      ──once at release──►  master        (v2.0 launch only)
```

### Default PR target

- **Unlabeled / general work → `master`**
- **Epic #402 / label `v2` / title prefix `v2:` → `v2`**

### What belongs on `master` vs `v2`

| Work | Branch | Rationale |
|------|--------|-----------|
| Bugfixes, docs, plot/batch/CLI tweaks | `master` | 1.x contract |
| Phase 0 gate (#384, #385, STEP-12 units) | `master` **if** parity tests show no behaviour change | Shared cleanup benefits 1.x |
| Phase 0 that might change output | `v2` or split PR | Protect 1.x users |
| V2-01 … V2-15 (metadata, merge, API, file format) | **`v2` only** | Breaking / v2-only surface |
| `cellpycore` pin bump | `master` with conservative range; `v2` may pin exact | See dependency policy below |

## Keeping 1.x safe on `master`

1. **No v2 data model or file-format work on `master`** — even behind flags, if persistence or public API changes.
2. **CI must pass** before merge (`uv run pytest`; use `-m essential` for inner loop).
3. **Conservative core pin on `master`:** e.g. `cellpycore>=0.1.2,<0.2` until v2 needs a newer API.
4. **Merge `master` → `v2` regularly** (weekly or before each v2 PR) so v2 does not diverge.
5. **Never merge `v2` → `master`** except the single v2.0 release merge.

## Reality check: what “1.x on master” means today

`master` already includes the **cellpy-core seam** (#377), Python **≥ 3.13**, and a PyPI
`cellpycore` dependency. “1.x” here means **post-seam 1.x** — not pre-core cellpy. v2 adds
metadata, multi-test merge, API cleanup, and file-format changes on top.

## Releases and versioning

- **1.x:** tag on `master` (`v1.0.4`, …); version from git tags via `uv-dynamic-versioning`
  (see [`build-and-versioning.md`](build-and-versioning.md)).
- **v2 development:** no consumer release from `v2` until ready; optional pre-release tags on
  `v2` only (`v2.0.0-a1`) for alpha installs.
- **v2.0 launch:** merge `v2` → `master`, tag `v2.0.0`, publish.
- **Extended 1.x support (optional):** after v2 ships, branch `release/1.x` from the last 1.x
  tag for critical fixes only — only if the team commits to maintaining it.

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

```bash
git fetch origin
git checkout v2
git pull --ff-only
git checkout -b 402-v2-testmeta-on-data
uv sync
uv run pytest -m essential
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
- **Architecture:** [`cellpy-v2-architecture.excalidraw`](cellpy-v2-architecture.excalidraw)
- **Epic doc:** [`cellpy-v2-epic.md`](cellpy-v2-epic.md)
