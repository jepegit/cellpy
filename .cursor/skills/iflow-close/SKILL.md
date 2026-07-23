---
name: iflow-close
description: >-
  Finish and land the focus issue: tests, optional version bump, status
  update, commit, push, and PR.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — issue close (`/iflow-close`)

Follow this skill to **finish and land** work: tests, optional version bump, issue-folder updates, git, and PR.

Post-merge branch hygiene lives in `/iflow-cleanup` — this skill never deletes branches.

## Optional version bump (command input)

If the user included text after `/iflow-close` that requests a version bump:

- **`bump`** (no level) → apply the pre-release-aware default.
- **A named level** (`patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev`) → use exactly that.
- Otherwise infer the level from natural language (e.g. "bugfix release" → `patch`); ask once if ambiguous. Never auto-pick `major`.

The exact semantics and the default rule live in `.cursor/skills/iflow-version-bump/SKILL.md` — that skill is the source of truth. When a bump applies: read it, then run the bump from the **project root** **after** the sanity check and **before** issue-folder updates and **before** commit / push / PR.

## Changelog update tokens (command input)

- **`nohistory`** or **`skip history`** → skip step 3 entirely.
- **`log "..."`** or **`note "..."`** → override the bullet summary verbatim. Otherwise the GitHub issue title is used.

## Branch switch tokens (command input)

- **`stay`**, **`stay on branch`**, **`don't switch`**, or **`dont switch to main`** → after the PR step, stay on the issue branch instead of switching back to the default branch.

## Draft PR token (command input)

- **`draft`** → when creating a PR in step 8, use `gh pr create --draft`. If an open PR already exists, leave it draft (do not mark ready). **`draft` skips yolo merge** entirely (step 8a).

## Hands-off token (command input)

- **`yolo`** (used by `/iflow-yolo`) → close the loop without user input: write the `HISTORY.md` bullet without a confirm prompt (step 3), **merge the PR** right after opening/updating it (step 8a), then switch back to the default branch and `git pull --ff-only` (step 9, unless `stay` was also passed).


**Invoke:** type `iflow close` in chat, or `/iflow-close` from the slash menu (`iflow-close` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

1. **Sanity check** — Run the project test suite (e.g. `uv run pytest`) and any checks the repo relies on. **Ruff (when present):** if the project uses ruff (`[tool.ruff]` in `pyproject.toml`, ruff in dev dependencies, or `.issueflows/04-designs-and-guides/python-quality-tools.md` exists), run auto-fix lint through the documented Python runner before committing — e.g. `uv run ruff check --fix …` then `uv run ruff format …` (match paths to what the project documents). Skim the diff; avoid bundling unrelated changes. Confirm that any design decisions or good practices that emerged from this issue are captured under `.issueflows/04-designs-and-guides/` before committing. If this change touched project structure (new modules, big refactor, removed files) and `graphify-out/` exists, *suggest* `/iflow-graphify` (AST-only default) — do not run it automatically.

2. **Optional version bump** — If the user asked for a bump (see above), follow `.cursor/skills/iflow-version-bump/SKILL.md` — it resolves the project's **release strategy** first (the "Release & version bump" section of `.issueflows/04-designs-and-guides/this-project.md`, else `pyproject.toml` detection, else the uv default). **Static version:** run `uv version --bump <level>`. **Git-tag derived:** edit nothing — compute and report the **planned tag** (e.g. `v1.0.4a3`), record it in the status file, and defer creating it until after the merge (step 9 with `yolo`, else `/iflow-cleanup`). If neither strategy applies, skip and continue.

3. **Update `HISTORY.md`** — Unless the user passed `nohistory`, follow `.cursor/skills/iflow-history-update/SKILL.md`. If step 2 did not bump (or plan) a version, append a bullet to the `## [Unreleased]` section. If step 2 bumped or planned a version, promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` (for tag-derived projects use the planned tag's version) and open a fresh empty `## [Unreleased]` above it. Write without a confirm prompt (`confirm_changelog_update` is false) so the bullet is in the PR commit. Skip with a note if `HISTORY.md` does not exist at the project root. With the `yolo` token, do not ask — decide yourself and write the bullet (issue title, or `log "..."` text) directly. Write this step **even when a draft PR already exists** from `/iflow-build` early PR — the bullet must land in the close commit that updates that PR. **Never** propose a changelog update *after close finishes* (PR already updated/merged) or after merge.

4. **Issue tracking** — Under `.issueflows/01-current-issues/`, update the status file: remaining work, checklists, and **`- [x] Done`** only when the issue is fully resolved. If fully resolved, move that issue's markdown files (`issue<n>_*`) to `.issueflows/03-solved-issues/`. If partially resolved, move to `.issueflows/02-partly-solved-issues/`. Follow any stricter rules in `.cursor/rules/issueflow-rules.mdc` if present.

5. **Commit** — First check `git status`; if any changes are **not relevant** to this issue, tell the user which ones and ask whether to include them — do not auto-include or drop silently. Then stage intentionally (include `pyproject.toml` and `uv.lock` if changed after a bump, and `HISTORY.md` if step 3 updated it); write a commit message in full sentences describing what changed and why.

6. **Branch hygiene before push** — Run `git fetch --prune`, then sync with the default branch using `git pull --ff-only` (rebase or merge per project preference). Use `--ff-only` so unrelated history never gets pulled in silently; if it refuses, stop and ask how to reconcile. Resolve merge conflicts before pushing.

7. **Push** — Push to the remote the project uses (typically `origin`).

8. **Pull request** — Against the default branch; always pass `--repo <owner/repo>`.
   - **List before create.** Run `gh pr list --repo <owner/repo> --head <branch> --state open --json number,url,title,isDraft`. If an open PR already exists for this head (including a draft from `/iflow-build` early PR), **update** it (title/body as needed; prefer `Closes #n` when shipping) instead of opening a second one. Otherwise `gh pr create` — add `--draft` when the user passed the `draft` token. Body should explain the change, how to test, and link the GitHub issue (`Closes #n` / `Refs #n`).
   - **Ready from draft (when not `draft`).** If the open PR is still a draft and the user did **not** pass `draft`, mark it ready for review (`gh pr ready <number> --repo <owner/repo>`) before the checks snapshot / yolo merge.
   - **Checks snapshot.** After the PR exists, run `gh pr checks <number> --repo <owner/repo>` and report pass / fail / pending. "CI is green" means this command exits 0 (or JSON buckets are all `pass` / `skipping`). Without `yolo`, prefer this one-shot list; offer `gh pr checks <number> --repo <owner/repo> --watch --fail-fast` only when the user wants to wait in-session, and still honour the **15-minute** wall-clock cap (agent-enforced — `gh` has no max-duration flag).

8a. **Merge the PR (`yolo` token only)** — Never `--delete-branch`; branch deletion stays in `/iflow-cleanup`. Without the `yolo` token, skip this step — merging stays a user decision (step 10). With `yolo`:
   1. If the user passed `draft`, **skip merge entirely** and say so.
   2. Try `gh pr merge <number> --squash` immediately (repos with no required checks stay fast).
   3. If GitHub refuses for pending/required checks: run `gh pr checks <number> --repo <owner/repo> --watch --fail-fast` under a hard wall-clock budget of **15 minutes** (baked from `[issueflow].checks_watch_minutes` / `ISSUEFLOW_CHECKS_WATCH_MINUTES`, default 15; agent stops the watch when the cap hits).
   4. Watch succeeds (exit 0) within the cap → retry `gh pr merge <number> --squash`.
   5. Watch fails (red / `--fail-fast`) → stop hands-off behaviour, leave the PR open, report failing check links.
   6. Cap elapses while still pending, or checks never register / watch unavailable → last resort `gh pr merge <number> --squash --auto`, report the merge as queued, continue. If even `--auto` fails, stop hands-off, report the error, leave the PR open.

9. **Switch back when safe** — If the input included `stay`, `stay on branch`, `don't switch`, or `dont switch to main`, stay on the issue branch and report that opt-out. Otherwise, after the PR is open or updated:
   - **CLI fast path (preferred).** If the `issue-flow` CLI is on `PATH`, run `issue-flow agent switchback --json`. It performs this whole step deterministically: refuses while the working tree is dirty (listing the paths), else switches to the detected default branch and runs `git pull --ff-only`. On exit 1, report its `notes` to the user and stop — do not force anything.
   - **Manual fallback.** Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git status --porcelain`; if clean, run `git switch <default>` and then `git pull --ff-only` (a clean tree here means the branch work has been committed and pushed to the PR branch). If dirty, stay on the current branch, list the uncommitted paths, and explain that switching is unsafe until those changes are committed, stashed, or discarded by the user.
   - Never delete the issue branch here. With the `yolo` token this step runs **after** the merge from step 8a so the pull brings the merged commit into the local default branch (a queued auto-merge arrives later; note that).
   - **Planned release tag (`yolo` + tag-derived strategy only):** if step 2 planned a tag, create it now — after the pull, standing on the merge commit — with `git tag <planned>` then `git push origin <planned>` (covered by the yolo consolidated confirm). If the merge was only queued via `--auto`, leave the tag to `/iflow-cleanup` and say so.

10. **After review** — With the `yolo` token the PR was already merged in step 8a; skip to the `/iflow-cleanup` reminder. Otherwise address feedback, push updates, and merge when approved and `gh pr checks <number> --repo <owner/repo>` is green (exit 0). If step 9 switched back to the default branch, switch to the PR branch again before making review fixes. Tell the user to run **`/iflow-cleanup`** once the PR is merged so the standard post-merge cleanup runs (`git fetch --prune`, `git branch -d` on merged local branches under a single consolidated confirm — and, for tag-derived projects, the offer to create the release tag planned in step 2).

11. **Output** — Summarize commit, push result, PR URL, whether the working copy switched back to the default branch or stayed on the issue branch, the merge result when `yolo` applied (merged, or queued via `--auto`), and next step (`/iflow-cleanup` after merge, or "blocked on …" if stuck).

## Constraints

- Do not skip failing tests without the user's explicit agreement.
- Prefer focused commits; do not rewrite unrelated history unless asked.
- Never delete branches from `/iflow-close`. Branch deletion belongs to `/iflow-cleanup`.
- **Changelog timing:** unless `nohistory`, the `HISTORY.md` bullet must be written in step 3 and staged in the close commit that feeds (or updates) the PR — including when a draft was opened earlier via `/iflow-build` early PR. Never offer a HISTORY/CHANGELOG update after close has finished or after merge.
