# Close out the current issue

Run this when implementation is done and you are ready to land the work (commit, push, PR). Post-merge branch hygiene now lives in a separate command, `/issue-cleanup`, which you run **after** the PR is merged.

## Input

Optional text after the command (same line). Examples:

- **No extra text** — close the issue without bumping the package version.
- **`bump`** or **`patch`** — bump the **patch** semver (e.g. `1.2.0` → `1.2.1`).
- **`bump minor`** or **`minor`** — bump **minor**.
- **`bump major`** or **`major`** — bump **major**.
- **Free text** — if it clearly asks to release or bump the version, infer `patch`, `minor`, or `major` from wording (e.g. "bugfix release" → patch); if unclear, ask once.
- **`nohistory`** or **`skip history`** — skip the `HISTORY.md` update step (step 3) for this run.
- **`log "..."`** or **`note "..."`** — use the quoted text verbatim as the `HISTORY.md` bullet summary (otherwise the GitHub issue title is used).

Other optional notes still apply: branch name, PR title, draft PR, skip issue doc update, commit all changes, etc.

## Typical steps

1. **Sanity check**
   - Run tests and any checks you rely on (e.g. `uv run pytest`).
   - Skim the diff so the commit matches what you intend to ship.
   - Confirm that any design decisions or good-practices that emerged from this issue are captured under `.issueflows/04-designs-and-guides/` before committing. If something is missing, add it now (short markdown: context, decision, alternatives, link back to the issue).
   - **Graph freshness (optional).** If this change touched the project's structure (new modules, big refactor, removed files) and `graphify-out/` exists, suggest the user run `/build` (default: `graphify update`, AST-only, no LLM key needed) before pushing so teammates pull a current `GRAPH_REPORT.md`. Do not run `/build` automatically — it is opt-in. Skip this bullet entirely if `graphify-out/` is not present.

2. **Optional version bump** (only if the user asked for it in the command input)
   - Read `.cursor/skills/issueflow-version-bump/SKILL.md` and follow it.
   - From the project root, run `uv version --bump patch`, `uv version --bump minor`, or `uv version --bump major` according to the input rules above.
   - Do this **before** updating issue markdown and **before** commit / push / PR so the new version is in the tree that gets merged.
   - If the project has no bumpable `pyproject.toml` version, skip and say so; continue with the remaining steps.

3. **Update `HISTORY.md`** (opt-out via `nohistory`)
   - Read `.cursor/skills/issueflow-history-update/SKILL.md` and follow it.
   - Default summary for the new bullet is the GitHub issue title; override with `log "..."` / `note "..."` from the command input.
   - If step 2 did **not** bump the version, append a bullet to the existing `## [Unreleased]` section: `- <summary>. (#<N>)`.
   - If step 2 **did** bump the version, promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>`, prepend a fresh empty `## [Unreleased]` above it, and put the new bullet inside the just-closed release section.
   - If `HISTORY.md` does not exist at the project root, skip this step with a short note and continue. Never create it here.
   - Show the proposed diff and confirm once before writing. If declined, leave `HISTORY.md` untouched and move on.

4. **Issue tracking in the repo** (see project rules under `.issueflows/01-current-issues`)
   - Update the status file for this issue: clear checklist, remaining work, and use `- [x] Done` only when fully resolved.
   - If the issue is fully resolved, move its markdown files from `.issueflows/01-current-issues` to `.issueflows/03-solved-issues`. If partially resolved, move to `.issueflows/02-partly-solved-issues`.

5. **Commit and fix merge conflicts**
   - Before staging, run `git status` to list all modified/untracked files. If any changes are **not relevant** to this issue, tell the user which ones and ask whether to include them in this commit or leave them for later. Do not silently drop or include unrelated changes.
   - Unless told to commit all, stage the right files (avoid unrelated changes). Include `pyproject.toml` (and `uv.lock` if it changed) when a version bump ran. Include `HISTORY.md` when step 3 updated it.
   - Write a commit message that states what changed and why in normal sentences.
   - Sync with the default branch before pushing: run `git fetch --prune` then `git pull --ff-only` from the default branch (e.g. `main`) merged into the issue branch (or rebase, per project preference). Use `--ff-only` so unrelated work never gets merged in silently; if it refuses, stop and ask how to reconcile. Check for and fix merge conflicts.

6. **Push**
   - Push your branch to `origin` (or the remote you use).

7. **Pull request**
   - Open a PR against the default branch (e.g. `main`).
   - Describe the change, how to test it, and link the GitHub issue (e.g. `Closes #123` or `Refs #123` in the PR body).

8. **After review**
   - Address feedback, push updates, and merge when approved and CI is green.
   - Remind the user that the working copy is still on the issue branch, not the default. Suggest `git switch <default>` before starting unrelated work so new changes don't accidentally land on the issue branch.
   - Once the PR is merged, run **`/issue-cleanup`** to switch back to the default branch, `git pull --ff-only`, `git fetch --prune`, and delete local branches whose commits are already in the default branch (single consolidated confirm). `/issue-close` no longer does post-merge cleanup itself.

## Output

Summarize what was committed, pushed, and the PR URL (or next step if blocked). Remind the user to run `/issue-cleanup` after the PR merges.
