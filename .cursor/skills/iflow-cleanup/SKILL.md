---
name: iflow-cleanup
description: >-
  Post-merge branch hygiene: switch to the default branch and delete merged
  local branches under one consolidated confirm. Never -D.
disable-model-invocation: true
---

# issue-flow — issue cleanup (`/iflow-cleanup`)

Follow this skill to **run post-merge branch hygiene** after a PR has been merged (typically the PR opened by `/iflow-close`).


### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

1. **Detect the default branch.** Prefer `gh repo view --repo <owner/repo> --json defaultBranchRef -q .defaultBranchRef.name`, else `git -C <project_root> symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`.

2. **Identify the target branch.** If the user named a branch after `/iflow-cleanup`, use it. Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 4 (folder sweep only).

3. **Check PR / merge state.** Prefer `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`. If `gh` is unavailable, approximate with `git fetch --prune` then `git cherry origin/<default> <branch>` (all commits marked `-` means squash-merged).
   - **If not merged:** remind the user that the working copy is still on the issue branch; suggest `git switch <default>` before unrelated work and re-run `/iflow-cleanup` after the PR merges. **Stop.** Do not delete anything.
   - **If merged:** continue.

4. **Consolidated confirm** — one yes/no prompt listing every action:
   - `git switch <default>`
   - `git pull --ff-only`
   - `git fetch --prune`
   - Every local branch whose tip is already reachable from `origin/<default>` (include squash-merges via `git cherry`). List them explicitly before running `git branch -d <branch>` for each. Never use `-D`; if `-d` refuses, report the branch and move on.

5. **Optional folder sweep** (safe; no destructive git). In `.issueflows/01-current-issues/`, for each `issue<N>_*` group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`. Leave groups without a checked `Done` in place — routing them to `.issueflows/02-partly-solved-issues/` is `/iflow-pause`'s job.

6. **Report.** Summarize: default branch, PR/merge status, commands run, branches deleted, branches skipped (with reason), folder sweep result. If `issue-flow agent resolve --json` reports `sibling_roots`, list them and remind the user that **each scaffolded repo needs its own `/iflow-cleanup`** — do not loop automatically in this step.

## Constraints

- Never use `git branch -D` or `git push --force`.
- Never delete the default branch.
- If anything is ambiguous (detached HEAD, multiple remotes, missing tracking info), report and stop rather than guess.
- Do not open or update PRs. Do not bump versions. Those belong to `/iflow-close`.
