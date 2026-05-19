---
name: issueflow-issue-cleanup
description: >-
  Run the /issue-cleanup workflow: detect merge status, switch to the default
  branch, and — with a single consolidated confirm — delete every local branch
  already reachable from origin/<default> (including squash-merges). Never -D.
disable-model-invocation: true
---

# issue-flow — issue cleanup (`/issue-cleanup`)

Follow this skill when the user wants to **run post-merge branch hygiene** after a PR has been merged, matching `.cursor/commands/issue-cleanup.md`.

## When to use

- The user runs `/issue-cleanup`, mentions **issue-cleanup**, or asks you to delete local branches whose PRs have merged.
- The PR opened by `/issue-close` just merged and the user wants the standard post-merge tidy-up.

## Instructions

1. **Detect the default branch.** Prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`.

2. **Identify the target branch.** If the user named a branch after `/issue-cleanup`, use it. Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 4 (folder sweep only).

3. **Check PR / merge state.** Prefer `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`. If `gh` is unavailable, approximate with `git fetch --prune` then `git cherry origin/<default> <branch>` (all commits marked `-` means squash-merged).
   - **If not merged:** remind the user that the working copy is still on the issue branch; suggest `git switch <default>` before unrelated work and re-run `/issue-cleanup` after the PR merges. **Stop.** Do not delete anything.
   - **If merged:** continue.

4. **Consolidated confirm** — one yes/no prompt listing every action:
   - `git switch <default>`
   - `git pull --ff-only`
   - `git fetch --prune`
   - Every local branch whose tip is already reachable from `origin/<default>` (include squash-merges via `git cherry`). List them explicitly before running `git branch -d <branch>` for each. Never use `-D`; if `-d` refuses, report the branch and move on.

5. **Optional folder sweep** (safe; no destructive git). In `.issueflows/01-current-issues/`, for each `issue<N>_*` group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`. Leave groups without a checked `Done` in place — routing them to `.issueflows/02-partly-solved-issues/` is `/issue-pause`'s job.

6. **Report.** Summarize: default branch, PR/merge status, commands run, branches deleted, branches skipped (with reason), folder sweep result.

## Constraints

- Never use `git branch -D` or `git push --force`.
- Never delete the default branch.
- If anything is ambiguous (detached HEAD, multiple remotes, missing tracking info), report and stop rather than guess.
- Do not open or update PRs. Do not bump versions. Those belong to `/issue-close`.
