---
name: issueflow-issue-pause
description: >-
  Run the /issue-pause workflow: update the status file with remaining work,
  move the issue group to .issueflows/02-partly-solved-issues/,
  and optionally make a WIP commit and switch to the default branch.
disable-model-invocation: true
---

# issue-flow — issue pause (`/issue-pause`)

Follow this skill when the user wants to **park work on the current issue** without closing it, matching `.cursor/commands/issue-pause.md`.

## When to use

- The user runs `/issue-pause`, mentions **issue-pause**, or asks to park / stash / shelve work on an issue to switch context.
- The issue is **not** done — this is not `/issue-close`.

## Instructions

1. **Find the focus issue.** In `.issueflows/01-current-issues/`, identify the `issue<N>_*` group. If multiple groups exist and the focus is ambiguous, ask. If none exist, **stop** and say there is nothing to pause.

2. **Update `issue<N>_status.md`.** Create or update it under `.issueflows/01-current-issues/` with:
   - `- [ ] Done` (must remain **unchecked** — a pause is not a close).
   - **Done so far** — short bullets of what has landed or been tried.
   - **Remaining work** — explicit next steps so work can resume later.
   - **Paused on** — date, branch name, any blockers.

   Preserve earlier user-written content; only add or update these sections. If the user passed a short note after `/issue-pause`, use it verbatim as the **Remaining work** text.

3. **Move the issue group.** Move every `issue<N>_*` file from `.issueflows/01-current-issues/` to `.issueflows/02-partly-solved-issues/`. Report each move.

4. **Working-tree guard.** Run `git status --porcelain`. Report what is dirty, then offer — as **one** consolidated prompt — any combination of:
   - **WIP commit** — stage tracked changes and commit `WIP: pause issue #<N> — <short note>`. List untracked files separately and ask before including them.
   - **Switch to default branch** — detect default (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`) and run `git switch <default>`. Only after the WIP commit if the tree is dirty.
   - **Stay put** — leave branch and working tree untouched.

5. **Report.** Summarize the status update, the issue-group moves, working-tree actions taken, and remind the user how to resume (running `/issue-init <N>` re-opens the archived issue after its archived-issue guard, or they can simply switch back to the issue branch).

## Constraints

- The focus issue's `- [ ] Done` checkbox **must** stay unchecked. `/issue-pause` is not `/issue-close`.
- Do not delete branches. Do not `git reset`, `git stash drop`, or force-push.
- Do not open a PR. Do not bump versions. Do not run tests.
