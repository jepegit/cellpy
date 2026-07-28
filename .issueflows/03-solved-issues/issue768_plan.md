# Plan: issue #768 — Release v2.1

## Goal

Ship **cellpy 2.1.0** (stable) from clean `master`: green tests/CI → PyPI via
`gh release create v2.1.0` → sync docs to `v2-docs-stable` → conda-forge
`2.1.0` (bot or manual feedstock bump).

## Constraints

- Follow
  [`.issueflows/04-designs-and-guides/release-procedure.md`](../04-designs-and-guides/release-procedure.md)
  and
  [`build-and-versioning.md`](../04-designs-and-guides/build-and-versioning.md):
  version = git tag (`uv-dynamic-versioning`); cut from **`master`**, not
  `768-release-v21`.
- Tag only a **clean** tree (no untracked `.issueflows/01-current-issues/*` on
  the tagged commit). Prefer a HISTORY PR; never `git add .` as release prep.
- Keep exact `cellpycore==0.2.4` unless a new core release lands first (F9 order
  in `v2-cellpycore-pin-gate.md`). Current pin already matches feedstock.
- Feedstock follows **stable only** (same rule as #574 / `v2.0.0`).
- This issue is **ops + release notes**, not new features. Fix only what blocks
  green CI / a correct tag.

### Prior art

| Hit | Role |
| --- | --- |
| `release-procedure.md` + `build-and-versioning.md` | Authoritative cut/tag/publish path |
| `cellpy-v2-branching.md` / `ci-tiers.md` | `master` = v2 line; Tier 1 essential vs Tier 2 scheduled |
| `#574` plan/status (`03-solved-issues/`) | Template for HISTORY fold + tag + feedstock |
| Sibling `cellpy-feedstock/` (`recipe/meta.yaml` @ `2.0.0`) | Manual conda bump if autotick stalls |
| `HISTORY.md` `[Unreleased]` / “cellpy 2.1 (Stage 4)” | Notes already drafted — fold to `[2.1.0]` |
| Toolbox (`00-tools/`) | No release helper — N/A |

## Approach

Ordered phases. Stop on red; do not tag around failures.

### A — Unblock `master` CI (blocker today)

Latest `master` push (#760) fails Tier 1 / full:

- `tests/test_loader_goldens.py::…[loader_arbin_sql_h5]` (raw temporal + meta)

**Do:** diagnose (likely tz / timestamp golden drift), fix or regenerate that
loader’s goldens, PR → `master`, wait for green `ci.yml` on the merge commit.

If the fix is large or policy-ambiguous, **pause** and open a focused issue —
do not inflate the release PR (same rule as #574).

### B — Release-notes PR (into `master`)

On `768-release-v21` (or a short-lived branch from updated `master`):

1. Fold `HISTORY.md` `[Unreleased]` → `## [2.1.0] - <ship date>` (keep Stage 4
   bullets; leave a fresh empty `[Unreleased]` if useful).
2. Confirm pin still `cellpycore==0.2.4`; `UV_NO_SOURCES=1 uv lock` only if
   deps change.
3. PR → `master`. **Do not** merge issue-flow focus files into that PR.

Dependabot PRs (#763–#767) stay **out of scope** unless you explicitly want
them in 2.1.0 (see Open questions).

### C — Pre-tag verification

On clean `master` after A+B:

1. `git status` empty (including no untracked).
2. Local: `uv run pytest -m essential`, then `uv run pytest` (full suite before
   stable — per `release-procedure.md`).
3. Confirm latest GHA `ci.yml` on `master` is green.
4. Optional but recommended: manually run **CI (scheduled)** Tier 2 if the
   weekly run is stale (`ci-tiers.md`).

### D — Tag + PyPI

```bash
git switch master && git pull --ff-only
git status   # must be clean
gh release create v2.1.0 --target master --generate-notes
# optionally edit notes to point at migration_v2.0_to_2.1.md
gh run list --workflow release.yml --limit 1
gh run watch <run-id>
```

Validate job must see `v2.*` on `origin/master`. On failure: delete release+tag,
fix, **new** tag — never reuse.

### E — Docs → `v2-docs-stable`

Issue asks: merge documentation changes **from `master` into `v2-docs-stable`**.

Docs commits on `master` not yet on `v2-docs-stable` (at least):

- #754 marimo integrate (context; marimo later withdrawn on docs branch)
- #755 2.0→2.1 migration guide (#720)
- #756 batch/collect API reference (#719)

**Do:** PR into `v2-docs-stable` that brings those docs (cherry-pick or
docs-scoped merge — prefer cherry-pick of the docs commits / paths to avoid
pulling unrelated master churn). Confirm Read the Docs / site build as usual
for that branch.

### F — conda-forge

1. After PyPI has `cellpy==2.1.0`, watch
   [conda-forge/cellpy-feedstock](https://github.com/conda-forge/cellpy-feedstock)
   for the autotick PR (version + sha256).
2. If bot fails / stalls: in sibling `cellpy-feedstock`, bump
   `recipe/meta.yaml` to `2.1.0`, set sdist sha256 from PyPI, keep
   `cellpycore ==0.2.4` unless pin changed, open feedstock PR, merge when CI
   green (same path as feedstock #59 for 2.0.0).

### G — Close-out

Record ship evidence in `issue768_status.md` (CI URLs, PyPI, docs PR,
feedstock PR). Close #768 via `/iflow-close` when A–F done.

## Files to touch

| Path | Change |
| --- | --- |
| `HISTORY.md` | Fold Unreleased → `[2.1.0]` |
| Loader golden / support under `tests/` (as needed for A) | Fix `loader_arbin_sql_h5` red CI |
| `.issueflows/01-current-issues/issue768_status.md` | Phase log |
| `cellpy-feedstock/recipe/meta.yaml` (sibling, only if bot fails) | `2.1.0` + sha256 |
| `v2-docs-stable` (via PR) | Docs sync from master |

No intentional `pyproject.toml` version edit. Pin change only if core ships first.

## Test strategy

- Gate: green GHA `essential` (+ `full` job if still in `ci.yml`) on the
  release commit.
- Local (conda `cellpy_dev_313` or `uv run` per project norms):
  `pytest -m essential` then full `pytest` before tag.
- Release workflow re-runs essential before PyPI publish.
- No new product tests unless Phase A needs a regression guard.

## Open questions

**Resolved on Accept (2026-07-28):**

1. **CI red on #760 (`loader_arbin_sql_h5`)** — fix inside #768 Phase A if
   small (golden/tz); split only if it blows up.
2. **Dependabot (#763–#767)** — **out of 2.1.0**; cut from tip after A+B.
3. **Tier 2 scheduled** — trigger once before tag; don’t block forever on
   flaky platform jobs; do not ignore new essential-class failures.
4. **Docs sync** — cherry-pick / docs-path PR into `v2-docs-stable` (not a
   full `master` merge).
