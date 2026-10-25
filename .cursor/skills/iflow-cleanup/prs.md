# Cleanup — PR queue sync (`/iflow-cleanup prs`)

Read this when **one or more open PRs need updating** after another PR
merged — typically `mergeable: CONFLICTING` / `mergeStateStatus: DIRTY` because
both sides edited `HISTORY.md`.

Sibling of the default cleanup (post-merge local hygiene) and of `issue-flow agent sync-branch` (single branch).

## Input

- **(nothing)** — refresh every open PR GitHub marks as needing update (DIRTY /
  BEHIND / CONFLICTING).
- **PR numbers** — e.g. `/iflow-cleanup prs 259 261` — only those heads.
- **`dry-run` / `dryrun`** — list candidates; do not sync or push.
- **`nopush` / `no-push`** — sync locally but do not push.
- **`all`** — every open PR, not only dirty ones (rare).

## Instructions

1. **Preflight.** Resolve `<project_root>` / `<owner/repo>`. Prefer standing on
   the **default** branch with a clean home tree (worktrees are used for each
   head). `git fetch --prune`.
2. **List candidates.** Prefer CLI:
   ```bash
   issue-flow agent pr-sync --dry-run --json -C <project_root>
   # or with numbers:
   issue-flow agent pr-sync 259 261 --dry-run --json -C <project_root>
   ```
   Show the user: PR number, head branch, mergeable / mergeStateStatus, URL.
3. **Confirm once.** Consolidated yes/no listing every head that will be
   rebased (or merged) onto `origin/<default>` and force-with-lease pushed.
   Decline → stop; nothing rewritten.
4. **Run.** On yes:
   ```bash
   issue-flow agent pr-sync [numbers…] --json -C <project_root>
   ```
   Honour trailing `nopush` / `dry-run` / `all` as flags (`--no-push`,
   `--dry-run`, `--all-open`). Default is `--fail-fast`: the first conflict the
   keep-both resolvers cannot take (product code, headings, prose — anything
   outside additive `HISTORY.md` bullets, `04-designs-and-guides/*.md`
   bullets / table rows and `issue<N>_status.md`) stops the batch and leaves
   later PRs untouched. A head stacked on a **squash-landed** sibling is
   handled by the same `sync-branch` auto-detect (`base_detected`); for a
   single head you can run `issue-flow agent sync-branch --base <parent> --json`
   in its worktree yourself.
5. **Report.** Per PR: synced / pushed / `resolvers` (which file took which
   keep-both) / `base_detected` / failure notes. Remind that CI must re-run on
   rewritten heads. Do **not** auto-merge. A PR that GitHub reports as
   **already merged** is dropped from the batch as success, not a failure.
6. **When to offer.** After `/iflow-cleanup` when other open PRs remain dirty;
   after `/iflow-run yolo` / `/iflow-close` merge when siblings are open; whenever
   the user says a PR “needs update” and the only conflict is changelog-shaped.

## Constraints

- Never bare `--force`; only `--force-with-lease` via the CLI.
- Never `--admin` merge; never skip required checks.
- Non-changelog / heading-promote conflicts → stop that head (and the batch
  under fail-fast); human decides.
- New closes put the bullet in commit trailers instead of `HISTORY.md`. This skill still repairs a queue that went dirty on a leftover `[Unreleased]` section.
