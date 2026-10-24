# Status — workspace git (`/iflow-status git`)

Read this for a **git hygiene snapshot** of every scaffolded
workspace member (branch, dirty paths, ahead/behind). Do **not** confuse
this with `/iflow-status` / `issue-flow workspace status` (issue-flow
lifecycle + GitHub).

## Input

- **(nothing)** or **`status`** — `issue-flow workspace git status [--json]`.
  No fetch.
- **`fetch`** — `issue-flow workspace git fetch [--json]`, then status.

## Instructions

1. Resolve the workspace (toml walk-up). If there is no
   `issueflow-workspace.toml`, stop and point at `issue-flow workspace
   init` / `bootstrap`. Do **not** guess sibling folders.
2. If the user passed `fetch`, run `issue-flow workspace git fetch --json`
   first. Report per-member ok/fail. Continue after a single-member
   failure.
3. Run `issue-flow workspace git status --json`. Present each member:
   name, branch, ahead/behind vs `origin/<default>`, clean/dirty, dirty
   paths. Note locked skips.
4. Never pull, rebase, merge, push, stash, or reset. Those stay
   per-repo (`default-sync`, `/iflow-cleanup`).

## Constraints

  `/iflow-close`.
- Status is read-only. Fetch is `--prune` only.
- Locked members are skipped, same as other `workspace` commands.
