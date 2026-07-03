---
name: iflow-close
description: >-
  Run the /iflow-close workflow: verify tests, optional uv semver bump, update
  issue status and folder locations, commit, push, and open a PR with a clear
  summary. Post-merge branch cleanup now lives in /iflow-cleanup.
disable-model-invocation: true
---

# issue-flow — issue close (`/iflow-close`)

Follow this skill when the user wants to **finish and land** work: tests, optional version bump, issue-folder updates, git, and PR.

Post-merge branch hygiene now lives in `/iflow-cleanup` — this skill no longer deletes branches.

## When to use

- The user runs `/iflow-close`, mentions **issue-close**, or asks to commit, push, or open a PR after issue-flow work.

## Optional version bump (command input)

If the user included text after `/iflow-close` that requests a version bump:

- **`bump`** (no level) → **pre-release-aware default**: stay on the current channel (alpha→`alpha`, beta→`beta`, rc→`rc`, dev→`dev`) or `patch` when the current version is already stable.
- **A named level** → `uv version --bump <level>` for any uv level: `patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev` (`dev` must be paired, e.g. `--bump patch --bump dev`).
- Otherwise infer the level from natural language (e.g. "bugfix release" → `patch`, "promote to beta" → `beta`); ask once if ambiguous. Never auto-pick `major`.

The exact semantics and the default rule live in `.cursor/skills/iflow-version-bump/SKILL.md` — that skill is the source of truth.

When a bump applies: read `.cursor/skills/iflow-version-bump/SKILL.md`, run the bump from the **project root** **after** the sanity check and **before** issue-folder updates and **before** commit / push / PR.

## Changelog update tokens (command input)

- **`nohistory`** or **`skip history`** → skip step 3 entirely.
- **`log "..."`** or **`note "..."`** → override the bullet summary verbatim. Otherwise the GitHub issue title is used.

## Branch switch tokens (command input)

- **`stay`**, **`stay on branch`**, **`don't switch`**, or **`dont switch to main`** → after the PR step, stay on the issue branch instead of switching back to the default branch.

## Hands-off token (command input)

- **`yolo`** (used by `/iflow-yolo`) → close the loop without user input: write the `HISTORY.md` bullet without a confirm prompt (step 3), **merge the PR** right after opening it (step 8a), then switch back to the default branch and `git pull --ff-only` (step 9, unless `stay` was also passed).

## Instructions

1. **Sanity check** — Run the project test suite (e.g. `uv run pytest`) and any checks the repo relies on. Skim the diff; avoid bundling unrelated changes. Confirm that any design decisions or good practices that emerged from this issue are captured under `.issueflows/04-designs-and-guides/` before committing.

2. **Optional version bump** — If the user asked for a bump (see above), follow `.cursor/skills/iflow-version-bump/SKILL.md` and run `uv version --bump <patch|minor|major>`. If there is no bumpable `pyproject.toml`, skip and continue.

3. **Update `HISTORY.md`** — Unless the user passed `nohistory`, follow `.cursor/skills/iflow-history-update/SKILL.md`. If step 2 did not bump the version, append a bullet to the `## [Unreleased]` section. If step 2 bumped the version, promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` and open a fresh empty `## [Unreleased]` above it. Show the diff and confirm once before writing. Skip with a note if `HISTORY.md` does not exist at the project root. With the `yolo` token, do not ask — decide yourself and write the bullet (issue title, or `log "..."` text) directly.

4. **Issue tracking** — Under `.issueflows/01-current-issues/`, update the status file: remaining work, checklists, and **`- [x] Done`** only when the issue is fully resolved. If fully resolved, move that issue's markdown files (`issue<n>_*`) to `.issueflows/03-solved-issues/`. If partially resolved, move to `.issueflows/02-partly-solved-issues/`. Follow any stricter rules in `.cursor/rules/issueflow-rules.mdc` if present.

5. **Commit** — First check `git status`; if any changes are **not relevant** to this issue, tell the user which ones and ask whether to include them — do not auto-include or drop silently. Then stage intentionally (include `pyproject.toml` and `uv.lock` if changed after a bump, and `HISTORY.md` if step 3 updated it); write a commit message in full sentences describing what changed and why.

6. **Branch hygiene before push** — Run `git fetch --prune`, then sync with the default branch using `git pull --ff-only` (rebase or merge per project preference). Use `--ff-only` so unrelated history never gets pulled in silently; if it refuses, stop and ask how to reconcile. Resolve merge conflicts before pushing.

7. **Push** — Push to the remote the project uses (typically `origin`).

8. **Pull request** — Open (or update) a PR against the default branch. Body should explain the change, how to test, and link the GitHub issue (`Closes #n` / `Refs #n`).

8a. **Merge the PR (`yolo` token only)** — Merge immediately with `gh pr merge <number> --squash` (never `--delete-branch`; branch deletion stays in `/iflow-cleanup`). If GitHub refuses (branch protection, pending checks), fall back to `gh pr merge <number> --squash --auto` and report the merge as queued. If even `--auto` fails, stop the hands-off behaviour, report the error, and leave the PR open. Without the `yolo` token, skip this step — merging stays a user decision (step 10).

9. **Switch back when safe** — Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). If the input included `stay`, `stay on branch`, `don't switch`, or `dont switch to main`, stay on the issue branch and report that opt-out. Otherwise run `git status --porcelain` after the PR is open or updated. If it is clean, run `git switch <default>` and then `git pull --ff-only`; a clean tree here means the branch work has been committed and pushed to the PR branch. If dirty, stay on the current branch, list the uncommitted paths, and explain that switching is unsafe until those changes are committed, stashed, or discarded by the user. Never delete the issue branch here. With the `yolo` token this step runs **after** the merge from step 8a so the pull brings the squash commit into the local default branch (a queued auto-merge arrives later; note that).

10. **After review** — With the `yolo` token the PR was already merged in step 8a; skip to the `/iflow-cleanup` reminder. Otherwise address feedback, push updates, and merge when approved and CI is green. If step 9 switched back to the default branch, switch to the PR branch again before making review fixes. Tell the user to run **`/iflow-cleanup`** once the PR is merged so the standard post-merge cleanup runs (`git fetch --prune`, `git branch -d` on merged local branches under a single consolidated confirm).

11. **Output** — Summarize commit, push result, PR URL, whether the working copy switched back to the default branch or stayed on the issue branch, the merge result when `yolo` applied (merged, or queued via `--auto`), and next step (`/iflow-cleanup` after merge, or "blocked on …" if stuck).

## Constraints

- Do not skip failing tests without the user's explicit agreement.
- Prefer focused commits; do not rewrite unrelated history unless asked.
- Never delete branches from `/iflow-close`. Branch deletion belongs to `/iflow-cleanup`.
