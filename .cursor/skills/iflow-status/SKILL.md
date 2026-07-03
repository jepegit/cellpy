---
name: iflow-status
description: >-
  Run the /iflow-status report: a read-only snapshot of where every issue stands
  — local issue-flow tracking state under .issueflows/ (focus / parked /
  solved) plus open GitHub issues cross-referenced against the local folders.
  Off-path: never auto-dispatched by /iflow. Writes nothing.
disable-model-invocation: true
---

# issue-flow — issue status overview (`/iflow-status`)

Follow this skill when the user wants a bird's-eye view of every issue's status
rather than acting on the single focus issue.

## When to use

- The user runs `/iflow-status`, mentions "status of issues", "what's the state of all issues", "where do things stand", or asks for an issue overview / dashboard.
- You want to see parked work, the focus issue's lifecycle stage, and open GitHub issues in one place.

Do **not** use this skill to *change* anything. It is read-only and off-path; for acting on the focus issue use `/iflow`, and to choose the next issue use `/iflow-pick`.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow status` (add `--local` to skip the GitHub query, `--json` for a
> machine-readable object) — it produces this whole overview deterministically.
> The CLI is optional: if it is missing or errors, fall back to the manual
> instructions below. (`issue-flow` is only present when the user installed it,
> e.g. `uv tool install issue-flow`.)

1. **Context / preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else `main`). Report current branch, clean/dirty tree (`git status --porcelain`), and ahead/behind vs `origin/<default>`. If the branch matches `^(\d+)-.+`, treat the leading digits as the focus issue `N`.

2. **Focus issue** (`.issueflows/01-current-issues/`). For the focus group, read its title from `issue<n>_original.md` and classify the lifecycle stage with the `/iflow` first-match logic:
   - **init** — no `issue<n>_original.md` → `/iflow-init`.
   - **plan** — original exists, no `issue<n>_plan.md` → `/iflow-plan`.
   - **start** — plan exists, status missing or `- [x] Done` unchecked → `/iflow-start`.
   - **close** — status contains `- [x] Done` (case-insensitive) → `/iflow-close`.
   Report the stage and suggested next step.

3. **Parked work** (`.issueflows/02-partly-solved-issues/`). List each `issue<n>_*` group: number, title, one-line status if present.

4. **Solved archive** (`.issueflows/03-solved-issues/`). Report the count of distinct solved issue numbers and the most recent few.

5. **Open GitHub issues** (skip if the user passed `local`). Run `gh issue list --state open --json number,title,labels,milestone,updatedAt` and tag each issue's local state: **focus**, **parked**, **solved-locally**, or **untracked**. If `gh` is missing/unauthenticated, skip this section and note it (suggest `gh auth login`) — never fail.

6. **Summary line.** One terse line, e.g. `Focus: #20 (start). Parked: 2. Solved: 31. Open on GitHub: 7 (5 untracked).`

## Constraints

- **Read-only.** Writes nothing, moves no files, creates no branches/commits/GitHub issues. Only reads `.issueflows/` and runs read-only `git` / `gh` queries.
- **Off-path.** Never auto-dispatch from `/iflow`, `/iflow-start`, or `/iflow-close`.
- **Degrade gracefully.** Missing `gh`, no network, or an empty `.issueflows/` must still yield a useful local report.
- Present sections in order (Context, Focus, Parked, Solved, Open GitHub, Summary); note any skipped section.
