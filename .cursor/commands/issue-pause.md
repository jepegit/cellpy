# Pause work on the current issue

Use this when you need to switch context without closing the issue. The command records where things stand, archives the issue group into `.issueflows/02-partly-solved-issues/`, and (optionally) parks your working tree safely.

## Input

Optional free-form text after the command. Examples:

- **No extra text** — update status from what is visible in the diff and current TODOs.
- Short note — used as the "Remaining work" text verbatim (e.g. `/issue-pause waiting on design input from @user`).

## Steps

0. **Locate the focus issue.** In `.issueflows/01-current-issues/`, identify the `issue<N>_*` group (original, plan, status). If multiple groups exist and the focus is ambiguous, ask which one to pause. If there is none, **stop** and tell the user there is nothing to pause.

1. **Update the status file.** Create or update `issue<N>_status.md` in `.issueflows/01-current-issues/` with:

   ```markdown
   # Status for issue #<N>: <title>

   - [ ] Done

   ## Done so far
   - Short bullets of what has landed or been tried.

   ## Remaining work
   - Explicit next steps so a future you (or someone else) can resume.

   ## Paused on
   <date, branch name, and any blockers — e.g. waiting on external input, blocked on another PR>.
   ```

   Keep any earlier content the user wrote; only add / update the sections above. The `- [ ] Done` checkbox **must** remain unchecked — a pause is not a close.

2. **Move the issue group.** Move every `issue<N>_*` file from `.issueflows/01-current-issues/` to `.issueflows/02-partly-solved-issues/`. Report the moves.

3. **Working-tree guard.** Run `git status --porcelain`. Report what is dirty. Then offer, as **one** consolidated prompt, up to three actions and let the user pick any combination:
   - **WIP commit** — stage all tracked changes and commit with a message like `WIP: pause issue #<N> — <short note>`. Never silently include untracked files; list them and ask.
   - **Switch to default branch** — detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`) and run `git switch <default>` (only after the WIP commit if the tree is dirty, to avoid `git switch` refusing).
   - **Stay put** — leave branch and working tree untouched.

4. **Branch hygiene note (non-destructive).** Tell the user the issue branch (typically `<N>-<slug>`) is still on the remote / local list. `/issue-pause` never deletes branches — resume with `/issue-init <N>` (or just check out the branch) when ready to continue. The matching folder is now `.issueflows/02-partly-solved-issues/`.

## Output

Report:
- status file path updated
- issue group moves (source → destination)
- working-tree actions taken (WIP commit SHA, branch switched to, or "left as-is")
- next step hint (e.g. "to resume: `/issue-init <N>` will pull the group back into `.issueflows/01-current-issues/` after confirming the archived-issue guard")

## Constraints

- The focus issue's `- [ ] Done` checkbox must stay unchecked. `/issue-pause` is **not** `/issue-close`.
- Do not delete branches. Do not `git reset` or `git stash drop`.
- Do not open a PR. Do not bump the version. Those are `/issue-close`.
- Do not run tests. Pausing should be quick.
