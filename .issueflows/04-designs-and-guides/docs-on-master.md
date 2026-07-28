# Documentation lives on `master`

**Context.** After cellpy 2.1 (#768), the long-lived `v2-docs-stable` branch is
**retired**. Dual-branch docs sync was harder to maintain than it was worth;
`docs/` on `master` and the tip of `v2-docs-stable` were already identical when
we stopped.

## Decision

| Surface | Where |
|---------|--------|
| Docs PRs / day-to-day edits | **`master`** (same as code) |
| Read the Docs **`latest`** | build **`master`** |
| Read the Docs **`stable`** | build the latest **stable release tag** (e.g. `v2.1.0`) — not a docs-only branch |

Do **not** open PRs against `v2-docs-stable`. Do **not** sync `master` ↔ that
branch. The remote branch may be deleted; treat any leftover clone as stale.

## Release + RTD

Cutting a GitHub release / tag (see [`release-procedure.md`](release-procedure.md))
is what refreshes RTD **stable**. After `gh release create vX.Y.Z --target master`:

1. Confirm the tag exists: `git fetch --tags && git show vX.Y.Z`
2. In [Read the Docs admin](https://readthedocs.org/projects/cellpy/):
   - **latest** → `master`
   - **stable** → “latest from tags” / point at `vX.Y.Z` (not `v2-docs-stable`)
3. Trigger a rebuild of `stable` if RTD does not auto-build the new tag.

As of 2026-07-28 the ship tag for RTD stable is **`v2.1.0`**.

## Local / CI

Unchanged: `uv run --group docs zensical serve|build`,
`.github/workflows/docs.yml`, `.readthedocs.yaml`. Details in
[`docs/contributing/developers_guide/dev_docs.md`](../../docs/contributing/developers_guide/dev_docs.md).

## Related

- Marimo spike withdrawn: [`marimo-docs.md`](marimo-docs.md)
- Branching overview: [`cellpy-v2-branching.md`](cellpy-v2-branching.md)
