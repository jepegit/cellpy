---
name: iflow-status
description: >-
  Where every issue stands, locally and on GitHub (read-only). Modes: doctor
  (audit and repair .issueflows/), git (workspace git snapshot), graph
  (rebuild the graphify knowledge graph).
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — status (`/iflow-status`)

A bird's-eye view of every issue: local tracking state (focus / parked / solved) plus open GitHub issues. The default mode is read-only.

## Pick the mode

| Input | Mode file | What it does |
|---|---|---|
| nothing, `local`, `workspace` / `all` | this file | Read-only overview (steps below). |
| `doctor [repair]` | `doctor.md` | Audit `.issueflows/` for dirty conditions; repair only after a confirm. |
| `git [fetch]` | `git.md` | Git snapshot per workspace member (branch, dirty paths, ahead/behind). |
| `graph [args]` | `graph.md` | Rebuild the graphify knowledge graph (`issue-flow graphify`). |

For a mode other than the overview, read only that mode's file in this skill folder and follow it.


**Invoke:** type `iflow status` in chat, or `/iflow-status` from the slash menu (`iflow-status` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow status` (add `--local` to skip the GitHub query, `--json` for a
> machine-readable object) — it produces this whole overview deterministically.
> **Workspace fan-out:** trailing `workspace` / `all`, or cwd is the workspace
> root (`issueflow-workspace.toml` present and not a member scaffold) → run
> `issue-flow workspace status [--local] [--json]` instead of the single-repo
> command. The CLI is optional: if it is missing or errors, fall back to the manual
> instructions below. (`issue-flow` is only present when the user installed it,
> e.g. `uv tool install issue-flow`.)

0. **Workspace scope.** If the user passed `workspace` / `all`, or resolve
   shows you are at the workspace root (toml present, cwd is not a member),
   run `issue-flow workspace status` and present each member. Do **not** guess
   a single repo. Then stop (skip the single-repo steps unless they also named
   `root:` / `repo:`).

1. **Context / preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else `main`). Report current branch, clean/dirty tree (`git status --porcelain`), and ahead/behind vs `origin/<default>`. If the branch matches `^(\d+)-.+`, treat the leading digits as the focus issue `N`.

2. **Focus issue** (`.issueflows/01-current-issues/`). For the focus group, read its title from `issue<n>_original.md` and classify the lifecycle stage with the `/iflow` first-match logic:
   - **init** — no `issue<n>_original.md` → `/iflow-pick`.
   - **plan** — original exists, no `issue<n>_plan.md` → `/iflow-plan`.
   - **build** — plan exists, status missing or `- [x] Done` unchecked → `/iflow-build`.
   - **close** — status contains `- [x] Done` (case-insensitive) → `/iflow-close`.
   Report the stage and suggested next step.

3. **Parked work** (`.issueflows/02-partly-solved-issues/`). List each `issue<n>_*` group: number, title, one-line status if present.

4. **Solved archive** (`.issueflows/03-solved-issues/`). Report the count of distinct solved issue numbers and the most recent few.

4a. **In-flight cycle.** If `.issueflows/01-current-issues/cycle_status.md` exists, a `/iflow-run cycle` batch run is paused or active — report it and its progress (from the file's checklist), and note that `/iflow-run cycle resume` continues it. (`issue-flow status --json` reports this as `cycle_active`.)

5. **Open GitHub issues** (skip if the user passed `local`). Run `gh issue list --state open --json number,title,labels,milestone,updatedAt` and tag each issue's local state: **focus**, **parked**, **solved-locally**, or **untracked**. If `gh` is missing/unauthenticated, skip this section and note it (suggest `gh auth login`) — never fail.

6. **Summary line.** One terse line, e.g. `Focus: #20 (start). Parked: 2. Solved: 31. Open on GitHub: 7 (5 untracked).`

## Constraints

- **Read-only** (overview mode). Writes nothing, moves no files, creates no branches/commits/GitHub issues. Only reads `.issueflows/` and runs read-only `git` / `gh` queries.
- **Degrade gracefully.** Missing `gh`, no network, or an empty `.issueflows/` must still yield a useful local report.
- Present sections in order (Context, Focus, Parked, Solved, Open GitHub, Summary); note any skipped section.
