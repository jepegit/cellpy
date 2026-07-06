---
name: iflow-status
description: >-
  Read-only snapshot of where every issue stands, locally and on GitHub.
disable-model-invocation: true
---

# issue-flow — issue status overview (`/iflow-status`)

Follow this skill for a bird's-eye view of every issue's status — local tracking state (focus / parked / solved) plus open GitHub issues — rather than acting on the single focus issue.

Do **not** use this skill to *change* anything. It is read-only and off-path; for acting on the focus issue use `/iflow`, and to choose the next issue use `/iflow-pick`.


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
