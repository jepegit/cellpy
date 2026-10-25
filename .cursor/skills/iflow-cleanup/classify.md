# Cleanup step 4 — classify local branches without the CLI

Per local branch (skipping the current branch and the default):
1. `git merge-base --is-ancestor <branch> origin/<default>` — exit 0 → **`reachable`**.
2. Else `git cherry origin/<default> <branch>` — no `+` lines → **`squash_landed`** (every commit has an equivalent patch upstream).
3. Else `gh pr list --repo <owner/repo> --state all --head <branch> --json number,state,mergedAt,url`. With a merged PR, compare `git log --no-merges --format=%cI origin/<default>..<branch>` against its `mergedAt`: no commit **newer** than the merge → **`merged_pr_divergent`** (the squash rewrote these commits); any newer commit → **`unique_work`** (real work pushed after the PR merged).
4. Anything else → **`unique_work`**.
5. Record `git rev-parse --short <branch>` for every branch you might delete.

> **Why the extra buckets:** this project merges PRs with **squash**, which lands a *new* commit on the default branch. A squash-merged branch tip is therefore never an ancestor of the default, so `git branch -d` refuses it forever — `-d` alone can never prune landed branches here.

