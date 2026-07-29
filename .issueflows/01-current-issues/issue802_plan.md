# Issue #802 — Plan

## Goal

Backfill `HISTORY.md` for the already-shipped **2.1.0.post1** and **2.1.1**
releases (and clear the stale Unreleased stub), then do a light pass for other
obviously stale public docs. Prep the tree so a docs-only **`v2.1.1.post1`**
can be cut after merge if desired.

## Constraints

- Keep a Changelog shape at repo root (`## [Unreleased]` then
  `## [x.y.z] - YYYY-MM-DD`) — see `iflow-history-update`.
- Match tone/density of existing `HISTORY.md` bullets (user-facing summary +
  `(#NNN)`); prefer the published GitHub release notes over inventing detail.
- **Docs-only** change set — no runtime/API edits.
- Do **not** create the `v2.1.1.post1` tag/release in this PR; that follows
  [`release-procedure.md`](../04-designs-and-guides/release-procedure.md) on
  `master` after merge (same pattern as `v2.1.0.post1`).
- Scope of “other docs stale”: quick public-facing check only (README / docs
  index / getting_started version or `v2-docs-stable` leftovers). No deep docs
  rewrite.

### Prior art

- Toolbox: no HISTORY helper in `.issueflows/00-tools/` (none applicable).
- `.cursor/skills/iflow-history-update/SKILL.md` — Keep a Changelog append /
  promote conventions for per-issue close; this issue is a **retroactive
  multi-release backfill**, so apply the same heading/bullet style manually.
- GitHub releases `v2.1.0.post1` and `v2.1.1` — authoritative bullet source
  (already written).
- `git log v2.1.0..v2.1.0.post1` / `v2.1.0.post1..v2.1.1` — PR inventory to
  cross-check the release bodies.
- Graph: skipped (docs/HISTORY-only; no code graph needed).

## Approach

1. **Inventory (already done in planning)**  
   - `HISTORY.md` has `[Unreleased]` (only the #768/`v2-docs-stable` retirement
     note) and jumps to `[2.1.0]` — **no** `[2.1.0.post1]` or `[2.1.1]`.  
   - Tags/releases exist: `v2.1.0.post1` (2026-07-28), `v2.1.1` (2026-07-29,
     tip of `master`).

2. **Rewrite the top of `HISTORY.md`**
   - Keep an empty `## [Unreleased]` (or only truly unreleased items — none
     expected on tip).
   - Insert `## [2.1.1] - 2026-07-29` with bullets distilled from the GitHub
     2.1.1 release notes (#785, #787, #790, #789, #788, #786, #791 / #798).
     Skip Dependabot-only noise unless the release notes mention it.
   - Insert `## [2.1.0.post1] - 2026-07-28` with bullets from that release
     (#771/#777 docstring cleanup, #775/#776 RTD / docs-on-master). Move the
     current Unreleased `v2-docs-stable` retirement bullet into this section
     (merge with #775 — do not duplicate).
   - Leave the existing `## [2.1.0]` block intact (including its historical
     “synced to `v2-docs-stable`” line — that was true at 2.1.0 ship).

3. **Stale-docs skim**  
   Grep README / `docs/` for leftover “edit on `v2-docs-stable`” instructions
   or wrong “latest is 2.1.0” claims. Fix only clear public falsehoods found;
   do not churn issueflow archive text.

4. **Verify**  
   Head of `HISTORY.md` reads Unreleased → 2.1.1 → 2.1.0.post1 → 2.1.0 → …  
   No code tests required beyond a quick visual check.

## Files to touch

| Path | Change |
|------|--------|
| [`HISTORY.md`](../../HISTORY.md) | Add `[2.1.1]` + `[2.1.0.post1]`; clear/move Unreleased stub |
| Public docs (only if skim finds a clear falsehood) | Minimal fix |

## Test strategy

- No pytest — changelog/docs only.
- Manual: `git log` / `gh release view` vs `HISTORY.md` headings and bullets
  match; `rg` for leftover stale `v2-docs-stable` edit instructions in
  `README.md` + `docs/`.

## Open questions

1. **Tag after merge?** After this PR lands, cut `v2.1.1.post1` as a
   docs-only post-release (like `v2.1.0.post1`), or leave HISTORY corrected on
   `master` without a new tag?  
   **Recommended:** cut `v2.1.1.post1` after merge (out of band of this PR).
2. **Dependabot bumps in 2.1.0.post1?** Those commits sit on the post1 tag but
   are not in the GitHub release notes.  
   **Recommended:** omit from HISTORY (match the published release body).
