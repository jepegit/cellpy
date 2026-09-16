---
name: iflow-pr-sync
description: >-
  Refresh open PR heads onto the default branch after another merge left them
  DIRTY (usually HISTORY.md). Uses sync-branch keep-both + force-with-lease.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — PR queue sync (`/iflow-pr-sync`)

Follow this skill when **one or more open PRs need updating** after another PR
merged — typically `mergeable: CONFLICTING` / `mergeStateStatus: DIRTY` because
both sides edited `HISTORY.md`.

Do **not** use this from `/iflow`. Off-path only. Sibling of `/iflow-cleanup`
(post-merge local hygiene) and of `issue-flow agent sync-branch` (single branch).


**Invoke:** type `iflow pr-sync` in chat, or `/iflow-pr-sync` from the slash menu (`iflow-pr-sync` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.


## Input

- **(nothing)** — refresh every open PR GitHub marks as needing update (DIRTY /
  BEHIND / CONFLICTING).
- **PR numbers** — e.g. `/iflow-pr-sync 259 261` — only those heads.
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
   `--dry-run`, `--all-open`). Default is `--fail-fast`: first non-HISTORY /
   non-keep-both conflict stops the batch and leaves later PRs untouched.
5. **Report.** Per PR: synced / pushed / changelog_resolved / failure notes.
   Remind that CI must re-run on rewritten heads. Do **not** auto-merge.
6. **When to offer.** After `/iflow-cleanup` when other open PRs remain dirty;
   after `/iflow-yolo` / `/iflow-close` merge when siblings are open; whenever
   the user says a PR “needs update” and the only conflict is changelog-shaped.

## Constraints

- Off-path; never auto-dispatch from `/iflow`.
- Never bare `--force`; only `--force-with-lease` via the CLI.
- Never `--admin` merge; never skip required checks.
- Non-changelog / heading-promote conflicts → stop that head (and the batch
  under fail-fast); human decides.
- Prevention (`defer_changelog`) is separate — see
  `.issueflows/04-designs-and-guides/pr-queue-sync.md`.
