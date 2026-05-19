# Post-merge branch and folder cleanup

Run this after a PR has been merged (typically the one opened by `/issue-close`). It detects the merge, switches back to the default branch, and — with a **single consolidated confirm** — deletes every local branch whose commits are already in the default branch (including squash-merged branches).

`/issue-cleanup` is the only command in the workflow that touches local branches destructively (via `git branch -d`, never `-D`).

## Input

Optional free-form text after the command. Examples:

- **No extra text** — detect the current branch's PR, clean that up, plus any other local branches already merged into the default.
- A branch name — clean up that specific branch instead of the current one (e.g. `/issue-cleanup 42-fix-login`).

## Steps

1. **Detect the default branch.**
   - Prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.
   - Else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`.
   - Else fall back to `main`.

2. **Identify the branch to clean.**
   - If the user passed a branch name, use it.
   - Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 5 (group sweep only); there is no issue branch to merge-check.

3. **Check PR / merge state for the issue branch.**
   - Prefer `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`.
   - If `gh` is unavailable, approximate with `git fetch --prune` then `git cherry origin/<default> <branch>`. All commits prefixed `-` means the branch is effectively merged (including squash-merges).
   - **If the branch is not merged:**
     - Remind the user that the working copy is still on the issue branch (not the default). Suggest `git switch <default>` before starting unrelated work.
     - Tell them to re-run `/issue-cleanup` after the PR merges.
     - **Stop.** Do not delete anything.

4. **Consolidated confirm for post-merge cleanup.** Gather the full action list into a single yes/no prompt:
   - `git switch <default>`
   - `git pull --ff-only`
   - `git fetch --prune`
   - List **every** local branch whose tip is already reachable from `origin/<default>` (use `git for-each-ref --format='%(refname:short)' refs/heads/` combined with `git cherry origin/<default> <branch>` to catch squash-merges). Present the list explicitly and ask **once** before running `git branch -d <branch>` for each.
   - Never use `-D` automatically. If `-d` refuses (unmerged changes), report that branch and leave it alone.

5. **Optional folder sweep** (safe; no destructive git).
   - Group files in `.issueflows/01-current-issues/` by issue number (`issue<N>_*`).
   - For each group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`.
   - Groups without a checked `Done` stay put — do not route them to `.issueflows/02-partly-solved-issues/` from `/issue-cleanup`. That is `/issue-pause`'s job and requires a human decision.

## Output

Report:
- default branch resolved
- PR/merge status of the target branch
- post-merge commands run (if any)
- list of local branches deleted (with `-d` output per branch)
- list of branches skipped because `-d` refused, with a one-line reason
- folder sweep summary (`issue<N>` → `03-solved-issues/`, or "nothing to sweep")

## Constraints

- Never use `git branch -D` or `git push --force`.
- Never delete the default branch.
- If anything is ambiguous (detached HEAD, multiple remotes, missing tracking info), report and stop rather than guessing.
- Do not open or update PRs. Do not bump versions. Those belong to `/issue-close`.
