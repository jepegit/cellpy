---
name: issueflow-issue-close
description: >-
  Run the /issue-close workflow: verify tests, optional uv semver bump, update
  issue status and folder locations, commit, push, and open a PR with a clear
  summary. Post-merge branch cleanup now lives in /issue-cleanup.
disable-model-invocation: true
---

# issue-flow — issue close (`/issue-close`)

Follow this skill when the user wants to **finish and land** work: tests, optional version bump, issue-folder updates, git, and PR. Match `.cursor/commands/issue-close.md`.

Post-merge branch hygiene now lives in `/issue-cleanup` — this skill no longer deletes branches.

## When to use

- The user runs `/issue-close`, mentions **issue-close**, or asks to commit, push, or open a PR after issue-flow work.

## Optional version bump (command input)

If the user included text after `/issue-close` that requests a version bump:

- **`bump`** or **`patch`** → `uv version --bump patch`
- **`bump minor`** or **`minor`** → `uv version --bump minor`
- **`bump major`** or **`major`** → `uv version --bump major`
- Otherwise infer **patch** / **minor** / **major** from natural language; ask once if ambiguous.

When a bump applies: read `.cursor/skills/issueflow-version-bump/SKILL.md`, run the bump from the **project root** **after** the sanity check and **before** issue-folder updates and **before** commit / push / PR.

## Changelog update tokens (command input)

- **`nohistory`** or **`skip history`** → skip step 3 entirely.
- **`log "..."`** or **`note "..."`** → override the bullet summary verbatim. Otherwise the GitHub issue title is used.

## Instructions

1. **Sanity check** — Run the project test suite (e.g. `uv run pytest`) and any checks the repo relies on. Skim the diff; avoid bundling unrelated changes.

2. **Optional version bump** — If the user asked for a bump (see above), follow `.cursor/skills/issueflow-version-bump/SKILL.md` and run `uv version --bump <patch|minor|major>`. If there is no bumpable `pyproject.toml`, skip and continue.

3. **Update `HISTORY.md`** — Unless the user passed `nohistory`, follow `.cursor/skills/issueflow-history-update/SKILL.md`. If step 2 did not bump the version, append a bullet to the `## [Unreleased]` section. If step 2 bumped the version, promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` and open a fresh empty `## [Unreleased]` above it. Show the diff and confirm once before writing. Skip with a note if `HISTORY.md` does not exist at the project root.

4. **Issue tracking** — Under `.issueflows/01-current-issues/`, update the status file: remaining work, checklists, and **`- [x] Done`** only when the issue is fully resolved. If fully resolved, move that issue's markdown files (`issue<n>_*`) to `.issueflows/03-solved-issues/`. If partially resolved, move to `.issueflows/02-partly-solved-issues/`. Follow any stricter rules in `.cursor/rules/issueflow-rules.mdc` if present.

5. **Commit** — First check `git status`; if there are unrelated uncommitted changes, surface them and ask the user whether to include them — do not auto-include or drop silently. Then stage intentionally (include `pyproject.toml` and `uv.lock` if changed after a bump, and `HISTORY.md` if step 3 updated it); write a commit message in full sentences describing what changed and why.

6. **Branch hygiene before push** — Run `git fetch --prune`, then sync with the default branch using `git pull --ff-only` (rebase or merge per project preference). Use `--ff-only` so unrelated history never gets pulled in silently; if it refuses, stop and ask how to reconcile. Resolve merge conflicts before pushing.

7. **Push** — Push to the remote the project uses (typically `origin`).

8. **Pull request** — Open (or update) a PR against the default branch. Body should explain the change, how to test, and link the GitHub issue (`Closes #n` / `Refs #n`).

9. **After review** — Remind the user the working copy is still on the issue branch (not the default). Suggest `git switch <default>` before starting unrelated work. Tell them to run **`/issue-cleanup`** once the PR is merged so the standard post-merge cleanup runs (switch to default, `git pull --ff-only`, `git fetch --prune`, `git branch -d` on merged local branches under a single consolidated confirm).

10. **Output** — Summarize commit, push result, PR URL, and next step (`/issue-cleanup` after merge, or "blocked on …" if stuck).

## Constraints

- Do not skip failing tests without the user's explicit agreement.
- Prefer focused commits; do not rewrite unrelated history unless asked.
- Never delete branches from `/issue-close`. Branch deletion belongs to `/issue-cleanup`.
