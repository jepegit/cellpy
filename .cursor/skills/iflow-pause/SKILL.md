---
name: iflow-pause
description: >-
  Park work on the current issue without closing it: update status, move
  the group to 02-partly-solved-issues/, optional WIP commit.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — issue pause (`/iflow-pause`)

Follow this skill to **park work on the current issue** without closing it. The issue is **not** done — this is not `/iflow-close`.


**Invoke:** type `iflow pause` in chat, or `/iflow-pause` from the slash menu (`iflow-pause` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).

## Instructions

1. **Find the focus issue.** In `.issueflows/01-current-issues/`, identify the `issue<N>_*` group. If multiple groups exist and the focus is ambiguous, ask. If none exist, **stop** and say there is nothing to pause.

2. **Update `issue<N>_status.md`.** Create or update it under `.issueflows/01-current-issues/` with:
   - `- [ ] Done` (must remain **unchecked** — a pause is not a close).
   - **Done so far** — short bullets of what has landed or been tried.
   - **Remaining work** — explicit next steps so work can resume later.
   - **Paused on** — date, branch name, any blockers.

   Preserve earlier user-written content; only add or update these sections. If the user passed a short note after `/iflow-pause`, use it verbatim as the **Remaining work** text.

3. **Move the issue group.** Move every `issue<N>_*` file from `.issueflows/01-current-issues/` to `.issueflows/02-partly-solved-issues/`. Report each move.

4. **Working-tree guard.** Run `git status --porcelain`. Report what is dirty, then offer — as **one** consolidated prompt — any combination of:
   - **WIP commit** — stage tracked changes and commit `WIP: pause issue #<N> — <short note>`. List untracked files separately and ask before including them.
   - **Switch to default branch** — detect default (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`) and run `git switch <default>`. Only after the WIP commit if the tree is dirty.
   - **Stay put** — leave branch and working tree untouched.

5. **Report.** Summarize the status update, the issue-group moves, working-tree actions taken, and remind the user how to resume (running `/iflow-pick <N>` re-opens the archived issue after its archived-issue guard, or they can simply switch back to the issue branch).

## Constraints

- The focus issue's `- [ ] Done` checkbox **must** stay unchecked. `/iflow-pause` is not `/iflow-close`.
- Do not delete branches. Do not `git reset`, `git stash drop`, or force-push.
- Do not open a PR. Do not bump versions. Do not run tests.
